""" slog: Simple sample tracker system.

Tool to create an Illumina HiSeq samplesheet for a task.

Per Kraulis
2011-03-10
"""

import logging, csv, cStringIO

from .tool import *


class Tool(BaseTool):
    """For an Illumina HiSeq instrument run task, produce a sample sheet
in CSV format which is attached to the task. The following must hold:

* The protocol must have the attachement 'illumina_indexes.csv'.
* The instrument must be of type 'Illumina HiSeq'.
* The arrangement of the workset must be compatible with Illumina HiSeq.
* The samples in the arrangement must have multiplex labels or sequences defined.

"""

    def __str__(self):
        "Display name for the tool."
        return 'Illumina HiSeq samplesheet'

    @property
    def modulename(self):
        "Must return the filename of the module."
        return 'illumina_samplesheet'

    def is_enabled(self, doc):
        "Does the entity document satisfy all conditions for this tool?"
        if doc.get('entity') != 'task': return False

        # Workset defined
        workset = doc.get('workset')
        if not workset: return False
        self.workset = self.dispatcher.get_named_document('workset', workset)

        # Protocol defined, and Illumina index file attached to it
        protocol = doc.get('protocol')
        if not protocol: return False
        try:
            self.protocol = self.dispatcher.get_named_document('protocol',
                                                               protocol)
        except ValueError:
            return False
        self.indexfile = self.dispatcher.db.get_attachment(
                             self.protocol, 'illumina_indexes.csv')
        if not self.indexfile: return False

        # Instrument type 'Illumina HiSeq'
        instrument = doc.get('instrument')
        if not instrument: return False
        try:
            instrument = self.dispatcher.get_named_document('instrument',
                                                            instrument)
        except ValueError:
            return False
        instrument_type = instrument.get('type') or ''
        if not instrument_type.lower() == 'illumina hiseq': return False
        return True

    def get_view(self, dispatcher):
        "Produce the HTML containing all input elements for the operation."
        doc = dispatcher.doc
        divs = [TABLE(
            TR(TH('Task'),
               TD(A(doc['name'], href=configuration.get_entity_url(doc)))),
            TR(TH('Protocol'),
               TD(A(self.protocol['name'],
                    href=configuration.get_entity_url(self.protocol))))),
                P(TABLE(
            TR(TD(INPUT(type='text',
                        name='samplesheet_filename',
                        value='samplesheet.csv')),
               TD(INPUT(type='submit', value='Create samplesheet')))))]
        return DIV(*divs)

    def do_operation(self, dispatcher, request):
        "Create the samplesheet and attach to the task document."
        doc = dispatcher.doc
        try:
            flowcellid = doc.get('aux_unit', '').strip()
            if not flowcellid: raise KeyError
        except KeyError:
            raise ValueError("no flowcell id set: 'aux_unit' field")
        try:
            filename = request.cgi_fields['samplesheet_filename'].value.strip()
            if not filename: raise KeyError
        except KeyError:
            filename = 'samplesheet.csv'
        else:
            if not filename.endswith('.csv'):
                filename += '.csv'
        operator = self.dispatcher.get_named_document('account',doc['operator'])
        operator = operator.get('initials') or operator['name']

        # Get the arrangement of samples from the workset
        grid = self.workset.get('grid')
        arrangement = grid.get('arrangement')
        if not arrangement:
            raise ValueError('no arrangement defined for workset')
        if grid.get('rows') != 1:
            raise ValueError('arrangement must have 1 and only 1 row')
        if grid.get('columns') > 8:
            raise ValueError('arrangement contains more than 8 columns (lanes)')
        if grid.get('multiplex') > 12:
            raise ValueError('arrangement contains more than 12 multiplex')

        # Get the content of the file 'illumina_indexes.csv'
        index_lookup = dict()
        for row in csv.reader(self.indexfile.read().strip().split('\n')):
            index_lookup[row[0]] = row[1]

        # Set sequence from index name, if required
        # Check for sequence collisions
        # There is only one row for Illumina run; one flowcell!
        for pos, lane in enumerate(arrangement[0]):
            sequences = set()
            for sample in lane:
                if not sample: continue
                doc = self.dispatcher.get_named_document('sample', sample)
                sequence = doc.get('multiplex_sequence')
                try:
                    if sequence: # Existing sequence overrides index name
                        if sequence in sequences: raise ValueError
                        sequences.add(sequence)
                    else:        # Find sequence from lookup using index name
                        initial = dict(doc)
                        index_name = doc.get('multiplex_label')
                        if not index_name:
                            raise ValueError("missing 'multiplex_label'"
                                             " for sample '%s'"
                                             % doc['name'])
                        try:
                            sequence = index_lookup[index_name]
                        except KeyError:
                            raise ValueError("undefined sequence for"
                                             " multiplex_label ='%s'"
                                             " for sample '%s'"
                                             % doc['name'])
                        if sequence in sequences: raise ValueError
                        sequences.add(sequence)
                        doc['multiplex_sequence'] = sequence
                        self.db.save(doc)
                        self.log(doc.id, 'modified multiplex_sequence',
                                 initial=initial,
                                 comment='while creating Illumina sample sheet')
                except ValueError:
                    raise ValueError("multiplex_sequence='%s' for"
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
        for pos, lane in enumerate(arrangement[0]):
            for sample in lane:
                if not sample: continue
                doc = self.dispatcher.get_named_document('sample', sample)
                writer.writerow((flowcellid,
                                 pos+1,
                                 sample,
                                 doc.get('reference') or '',
                                 doc['multiplex_sequence'],
                                 doc['project'],
                                 'N',   # XXX Where to define this?
                                 'R1',  # XXX Protocol should be used...
                                 operator))
        self.dispatcher.put_attachment(outfile.getvalue(), filename=filename)
        return "filename %s" % filename
