""" slog: Simple sample tracker system.

A run involving an instrument and a set of samples.

Per Kraulis
2011-02-18
"""

import logging, tempfile, shutil

import utils
from .entity import *


class InstrumentRun(Entity):
    """A run involving an instrument (sequence, robot, analyzer, etc.)
and a set of samples. The name of an InstrumentRun must be possible to
change since the official name may not be known when the run is planned."""

    fields = [NameField('name',
                          description='Unique name of the instrument run.'
                        ' May be changed; use a temporary name until'
                        ' the final name of the run becomes defined.'),
              ReferenceField('operator', 'account',
                             default=utils.get_login_account,
                             required=True,
                             description='Operator of this entity;'
                             ' instrument run operator.'),
              ReferenceField('instrument', 'instrument',
                             required=True,
                             description="Instrument used to process"
                             " the samples in a run. Don't change unless"
                             " the layout is identical."),
              StringField('aux_unit',
                          required=False,
                          description='Specification of an auxiliary unit'
                          ' used with the instrument during the run,'
                          ' such as a flowcell id or a microarray id.'),
              SampleLayoutField('samples',
                                description='Layout of the samples in the run.'
                                ' The structure of the layout depends on the'
                                ' properties specified for the instrument.'
                                ' The samples are input using workset names'
                                ' or explicit sample names.'),
              TimestampField('started',
                             required=False,
                             description='Date for when run was started.'),
              TimestampField('finished',
                             required=False,
                             description='Date for when run was finished.'),
              TextField('description')]

    def get_editable(self, user):
        """Is the given user allowed to edit this page?
        The operator of the instrument run, and admin and manage may edit."""
        return user.get('name') == self.user['name'] or \
               user.get('role') in ('admin', 'manager')

    def view(self, page):
        "Produce the HTML page for GET."
        self.view_fields(page)
        self.view_create_samplesheet(page)
        self.view_create_report(page)
        self.view_attachments(page)
        self.view_log(page)
        self.view_tags(page)
        self.view_xrefs(page)

    def view_create_samplesheet(self, page):
        "HTML for button to create the samplesheet CSV file."
        page.append(H2('Illumina run samplesheet'))
        page.append(utils.rst_to_html(
"""An Illumina instrument run samplesheet can be created by pressing the button
below. It will be added as a file attachment (listed below).

Requirements:

* The flowcell id must be defined in the data field 'aux_unit' above.
* The data field 'multiplex_sequence' or 'multiplex_label' must be defined
  for each sample. If the sequence is not defined but the index is, then
  the sequence will be set for the sample using file 'multiplex_sequences.csv'
  attached to the application for the project, which must exist.
* The instrument referred to above must have a file 'illumina_indexes.csv'
  attached, containing the name and actual sequence for each barcode.
* All samples in one lane must have unique multiplex sequences.

"""))
        page.append(TABLE(FORM(
            TR(TD('Sample sheet filename'),
               TD(INPUT(type='text', size=40,
                        name='samplesheet_filename', value='samplesheet.csv')),
               TD(INPUT(type='submit', value='Create'),
                  INPUT(type='hidden',
                        name='action', value='samplesheet_create')),
               TD(B('Note:'), ' Any already existing attachement of'
                  ' the same name will be overwritten!')),
            method='POST',
            action=self.get_url())))

    def view_create_report(self, page):
        "HTML for button to create the report PDF file."
        page.append(H2('Illumina run report'))
        page.append(utils.rst_to_html(
"""An Illumina instrument run report can be created by pressing the button
below. It will be added as a file attachment (listed below).

**Note:** Not yet implemented.
"""))
        page.append(TABLE(FORM(
            TR(TD('Report filename'),
               TD(INPUT(type='text', size=40,
                        name='report_filename', value='report.pdf')),
               TD(INPUT(type='submit', value='Create'),
                  INPUT(type='hidden',
                        name='action', value='report_create')),
               TD(B('Note:'), ' Any already existing attachement of'
                  ' the same name will be overwritten!')),
            method='POST',
            action=self.get_url())))

    def on_field_modified(self, name):
        """When the 'started' or 'finished' fields are changed,
        then also make log entry about this in each sample."""
        if name in ('started', 'finished'):
            comment = "InstrumentRun %s" % self.doc.get('name')
            array = self.doc.get('samples').get('array') or []
            for sample in utils.flatten(array):
                try:
                    doc = self.get_named_document('sample', sample)
                except ValueError:
                    pass
                else:
                    self.log(doc.id, name, initial=dict(doc), comment=comment)

    def action_samplesheet_create(self, request):
        """Create an Illumina instrument run sample sheet using the available
        information. Some information, such as flow cell id and sample
        multiplex sequences, must be defined."""
        import csv, cStringIO
        try:
            flowcellid = self.doc.get('aux_unit', '').strip()
            if not flowcellid: raise KeyError
        except KeyError:
            raise HTTP_BAD_REQUEST("no flowcell id set (in 'aux_unit')")
        try:
            filename = request.cgi_fields['samplesheet_filename'].value.strip()
            if not filename: raise KeyError
        except KeyError:
            filename = 'samplesheet.csv'
        else:
            if not filename.endswith('.csv'):
                filename += '.csv'
        operator = self.get_named_document('account', self.doc['operator'])
        operator = operator.get('initials') or operator['name']

        # Get the samples
        array = self.doc.get('samples').get('array') or []
        samples = utils.flatten(array)
        if not samples:
            raise HTTP_BAD_REQUEST('no samples in InstrumentRun')

        # Get the file 'illumina_indexes.csv' attached to the instrument;
        # for translating multiplex index to sequence.
        instrument = self.get_named_document('instrument',
                                             self.doc['instrument'])
        lookup_filename = 'illumina_indexes.csv'
        lookup_file = self.db.get_attachment(instrument, lookup_filename)
        if not lookup_file:
            raise HTTP_BAD_REQUEST("no attachment '%s' for instrument"
                                   % lookup_filename)
        index_lookup = dict()
        for row in csv.reader(lookup_file.read().strip().split('\n')):
            index_lookup[row[0]] = row[1]

        # Set sequence from index name, if required
        # Check for sequence collisions
        # There is only one row for Illumina run; one flowcell!
        for pos, lane in enumerate(array[0]):
            sequences = set()
            for sample in lane:
                if not sample: continue
                doc = self.get_named_document('sample', sample)
                sequence = doc.get('multiplex_sequence')
                try:
                    if sequence: # Existing sequence overrides index name
                        if sequence in sequences: raise ValueError
                        sequences.add(sequence)
                    else:        # Find sequence from lookup using index name
                        initial = dict(doc)
                        index_name = doc.get('multiplex_label')
                        if not index_name:
                            raise HTTP_BAD_REQUEST("missing 'multiplex_label'"
                                                   " for sample '%s'"
                                                   % doc['name'])
                        try:
                            sequence = index_lookup[index_name]
                        except KeyError:
                            raise HTTP_BAD_REQUEST("undefined sequence"
                                                   " for multiplex_label ='%s'"
                                                   " for sample '%s'"
                                                   % doc['name'])
                        if sequence in sequences: raise ValueError
                        sequences.add(sequence)
                        doc['multiplex_sequence'] = sequence
                        self.db.save(doc)
                        self.log(doc.id, 'modified multiplex_sequence',
                                 initial=initial,
                                 comment='when creating Illumina sample sheet')
                except ValueError:
                    raise HTTP_BAD_REQUEST("multiplex_sequence='%s' for"
                                           " sample '%s' already in use"
                                           % (sequence, sample))

        # Create the CSV file and attach it to the entity
        outfile = cStringIO.StringIO()
        writer = csv.writer(outfile, quoting=csv.QUOTE_NONNUMERIC)
        writer.writerow(('FCID',
                         'Lane',
                         'SampleID',
                         'SampleRef',
                         'Index',
                         'Description',
                         'Control',
                         'Recipe',
                         'Operator'))
        # There is only one row for Illumina run; one flowcell!
        for pos, lane in enumerate(array[0]):
            for sample in lane:
                if not sample: continue
                doc = self.get_named_document('sample', sample)
                writer.writerow((flowcellid,
                                 pos+1,
                                 sample,
                                 doc.get('reference') or '',
                                 doc['multiplex_sequence'],
                                 doc['project'],
                                 'N',   # XXX Where to define this?
                                 'R1',  # XXX Protocol should be used...
                                 operator))
        content = outfile.getvalue()
        initial = dict(self.doc)
        self.db.put_attachment(self.doc, content, filename=filename)
        self.log(self.doc.id, 'created sample sheet',
                 initial=initial,
                 comment="filename %s" % filename)
        self.doc = self.db[self.doc.id] # Get fresh instance

    def action_report_create(self, request, project=None):
        """Create an Illumina instrument run report using the available
        information. Some information, such as the 'read1.xml' and
        'read2.xml' files, must be defined.
        XXX The 'project' argument is not implemented."""
        try:
            filename = request.cgi_fields['report_filename'].value.strip()
            if not filename: raise KeyError
        except KeyError:
            filename = 'report.pdf'
        else:
            if not filename.endswith('.pdf'):
                filename += '.pdf'

        import cStringIO
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle, Image, PageBreak)
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.rl_config import defaultPageSize
        from reportlab.lib import units, colors
        from PIL import Image as PILImage

        PAGE_WIDTH, PAGE_HEIGHT = defaultPageSize
        styles = getSampleStyleSheet()

        TMPDIRPATH = tempfile.mkdtemp()

        def standardPage(canvas, doc):
            canvas.setTitle('SciLifeLab Instrument Run Report')
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.drawString(units.cm, PAGE_HEIGHT - units.cm,
                              "SciLifeLab Stockholm Instrument Run Report")
            canvas.drawRightString(PAGE_WIDTH - units.cm,
                                   PAGE_HEIGHT - units.cm,
                                   "Page %i" % canvas.getPageNumber())
            user = self.user.get('fullname') or self.user['name']
            line = "Generated from slog %s by %s" % (utils.now_iso(), user)
            canvas.drawString(units.cm, units.cm, line)
            canvas.restoreState()

        outfile = cStringIO.StringIO()
        ## pdf = SimpleDocTemplate(outfile, showBoundary=True)
        pdf = SimpleDocTemplate(outfile)
        story = []
        story.append(Paragraph("Instrument Run %s" % self.doc['name'],
                               styles['Heading1']))

        # Description
        story.append(Paragraph('Description', styles['Heading2']))
        description = self.doc.get('description') or ''
        lines = []
        for line in description.split('\n'):
            if line:
                lines.append(line)
            elif lines:
                story.append(Paragraph('\n'.join(lines), styles['Normal']))
                story.append(Spacer(1, 0.5*units.cm))
                lines = []
        if lines:
            story.append(Paragraph('\n'.join(lines), styles['Normal']))
            story.append(Spacer(1, 0.5*units.cm))

        # Lane information
        array = self.doc.get('samples').get('array') or []
        data = [['Lane', 'Sample(s)', 'Project']]
        for pos, lane in enumerate(array[0]):
            row = [str(pos+1)]
            samples = []
            projects = set()
            for sample in lane:
                if not sample: continue
                doc = self.get_named_document('sample', sample)
                samples.append("%s (%s)" % (doc.get('altname') or '-',
                                            doc['name']))
                projects.add(doc.get('project'))
            row.append('\n'.join(samples))
            row.append('\n'.join(projects))
            data.append(row)
        ts = TableStyle([('FONT', (0,0), (-1,-1), 'Helvetica', 8),
                         ('VALIGN', (0,1), (-1, -1), 'TOP'),
                         ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.black),
                         ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 8)])
        story.append(Table(data, style=ts))

        # Optional summary read files
        import xml.etree.ElementTree
        for readnumber in [1, 2]:
            readfilename = "read%i.xml" % readnumber
            readfile = self.db.get_attachment(self.doc, readfilename)
            infile = cStringIO.StringIO(readfile.read())
            try:
                tree = xml.etree.ElementTree.parse(infile)
            except IOError:
                continue
            summary = dict()
            for lane in tree.getroot().getchildren():
                values = dict()
                summary[int(lane.get('key'))] = values
                for name, value in lane.items():
                    try:
                        value = int(value)
                    except ValueError:
                        value = float(value)
                    values[name] = value
            data = [['Lane',
                     'Cluster\nDens.\n(#/mm2)',
                     '% PF\nClusters',
                     'Cluster\nPF\n(#/mm2)',
                     '% Phas.\n/Preph.',
                     '% Aligned\n(PhiX)',
                     '% Error rate',
                     'Comment']]
            for lane in sorted(summary.keys()):
                values = summary[lane]
                CluDens = "%.0fK" % (values['ClustersRaw'] / 1000.0)
                CluDensSD = "+/- %.0fK" % (values['ClustersRawSD'] / 1000.0)
                PFClusters = "%.1f" % values['PrcPFClusters']
                PFClustersSD = "+/- %.1f" % values['PrcPFClustersSD']
                CluPF = "%.0fK" % (values['ClustersPF'] / 1000.0)
                CluPFSD = "+/- %.0fK" % (values['ClustersPFSD'] / 1000.0)
                Phasing = "%.3f" % values['Phasing']
                PrePhasing = "%.3f" % values['Prephasing']
                Aligned = "%.2f" % values['PrcAlign']
                AlignedSD = "+/- %.3f" % values['PrcAlignSD']
                ErrorRate = "%.2f" % values['ErrRatePhiX']
                ErrorRateSD = "+/- %.3f" % values['ErrRatePhiXSD']
                data.append([lane,
                             "%s\n%s" % (CluDens, CluDensSD),
                             "%s\n%s" % (PFClusters, PFClustersSD),
                             "%s\n%s" % (CluPF, CluPFSD),
                             "%s\n%s" % (Phasing, PrePhasing),
                             "%s\n%s" % (Aligned, AlignedSD),
                             "%s\n%s" % (ErrorRate, ErrorRateSD),
                             '-'])
            story.append(PageBreak())
            story.append(Paragraph("Summary Read %i" % readnumber,
                                   styles['Heading2']))
            ts = TableStyle([('FONT', (0,0), (-1,-1), 'Helvetica', 8),
                             ('ALIGN', (0,1), (-1, -1), 'RIGHT'),
                             ('VALIGN', (0,1), (-1, -1), 'TOP'),
                             ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.black),
                             ('FONT', (0,0), (-1,0), 'Helvetica-Bold', 8)])
            story.append(Table(data, style=ts))

        # Optional summary plots
        for nametemplate, title in [('QScore_L%i.png', 'Quality Score'),
                                    ('NumGT30_L%i.png', 'Q >= 30'),
                                    ('ErrRate_L%i.png', 'Error Rate')]:
            filepaths = []
            for i in xrange(len(array[0])):
                imgfilename = nametemplate % (i+1)
                attachment = self.db.get_attachment(self.doc, imgfilename)
                if not attachment: continue
                imgfile = cStringIO.StringIO(attachment.read())
                image = PILImage.open(imgfile)
                # Shrink image if too large for report page
                if image.size[0] > 500:
                    # 'thumbnail' keeps the aspect ratio
                    image.thumbnail((500, 500), PILImage.ANTIALIAS)
                filepath = os.path.join(TMPDIRPATH, imgfilename)
                image.save(filepath, 'PNG')
                filepaths.append((i+1, filepath))
            if filepaths:
                story.append(PageBreak())
                story.append(Paragraph(title, styles['Heading2']))
                for number, filepath in filepaths:
                    story.append(Paragraph("Lane %i" % number,
                                           styles['Heading3']))
                    story.append(Image(filepath))

        # Output the result
        pdf.build(story, onFirstPage=standardPage, onLaterPages=standardPage)
        content = outfile.getvalue()
        initial = dict(self.doc)
        self.db.put_attachment(self.doc, content, filename=filename)
        self.log(self.doc.id, 'created report',
                 initial=initial,
                 comment="filename %s" % filename)
        self.doc = self.db[self.doc.id] # Get fresh instance
        try:
            shutil.rmtree(TMPDIRPATH)
        except (IOError, OSError):
            pass


class InstrumentRunCreate(EntityCreate):

    entity_class = InstrumentRun

    def get_privilege(self):
        "Everyone except the customer may create a sample."
        role = self.user.get('role')
        return role in ('admin', 'manager', 'engineer')

    def setup(self, doc):
        "Add the initial sample layout according to the chosen instrument."
        instrument = self.get_named_document('instrument', doc['instrument'])
        max_rows = instrument.get('max_rows', 1)
        max_columns = instrument.get('max_columns', 1)
        max_multiplex = instrument.get('max_multiplex', 1)
        doc['samples'] = dict(rows=max_rows,
                              columns=max_columns,
                              multiplex=max_multiplex,
                              array=[[[None] * max_multiplex]
                                     * max_columns] * max_rows)


class InstrumentRuns(Dispatcher):
    "Instrument runs list page dispatcher."

    def get_viewable(self, user):
        "Everyone except customers may view the projects list."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def get_editable(self, user):
        "Everyone except customers may create a project."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='InstrumentRuns')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(InstrumentRun.__doc__))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit',
                                     value='Create new instrument run'),
                               method='GET',
                               action=configuration.get_url('instrumentrun'))))

        operator = self.get_selected_operator(request)
        page.append(P(self.get_operator_select_form('instrumentruns',operator)))

        if operator:
            view = self.db.view('instrumentrun/operator',
                                include_docs=True)
            result = view[operator]
        else:
            result = self.db.view('instrumentrun/name', include_docs=True)
        instrumentruns = [r.doc for r in result]
        instrumentruns.sort(lambda i, j: cmp(i['name'], i['name']))

        rows = [TR(TH('Instrument run'),
                   TH('Operator'),
                   TH('Instrument'),
                   TH('# Samples'),
                   TH('Started'),
                   TH('Finished'),
                   TH('Timestamp'))]
        for result in view:
            doc = result.doc
            operator = doc.get('operator')
            if operator:
                operator = A(operator,
                             href=configuration.get_url('account', operator))
            else:
                operator = ''
            ref = A(doc['name'], href=configuration.get_entity_url(doc))
            url = configuration.get_url('instrument', doc['instrument'])
            instrument = A(doc['instrument'], href=url)
            array = doc.get('samples').get('array') or []
            count = len([s for s in utils.flatten(array) if s is not None])
            rows.append(TR(TD(ref),
                           TD(operator),
                           TD(instrument),
                           TD(count),
                           TD(doc.get('started') or ''),
                           TD(doc.get('finished') or ''),
                           TD(doc['timestamp'])))
        page.append(TABLE(border=1, *rows))

        page.write(response)
