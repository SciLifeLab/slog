""" slog: Simple sample tracker system.

Sample entity and dispatcher.

Per Kraulis
2011-02-10
"""

import utils
from .entity import *


class SampleNameField(NameField):
    "Name must be unique among samples."

    def check_value(self, dispatcher, value):
        value = super(SampleNameField, self).check_value(dispatcher, value)
        try:
            dispatcher.get_named_document('sample', value)
        except ValueError:
            return value
        else:
            raise ValueError("Sample name '%s' is already in use" % value)


class Sample(Entity):
    """A sample is a finite amount of material to be analysed.
It is always part of one and only one project.
It may be a member of any number of worksets."""

    fields = [SampleNameField('name',
                              required=True,
                              fixed=True,
                              description='Unique sample identifier.'
                              ' Cannot be changed once set.'),
              StringField('altname',
                          required=False,
                          description="Alternative name, such as"
                          " customer's name for sample."),
              ReferenceField('project',
                             referred='project',
                             required=True,
                             description='Project for the sample.'),
              StringField('reference',
                          required=False,
                          description='Reference genome or species'
                          ' for the sample.'),
              ReferenceField('parent',
                             referred='sample',
                             required=False,
                             fixed=True,
                             description='Sample from which this was derived.'
                             ' Cannot be changed once set.'),
              FloatField('amount', description='Unit: ?'),
              FloatField('concentration', description='Unit: ?'),
              StringField('location',
                          required=False,
                          description='Physical location of sample.'),
              StatusField('status',
                          statuses=[dict(name='defined',
                                         values=['yes'],
                                         description='Defined in this system.'),
                                    dict(name='available',
                                         values=['yes'],
                                         description='Received or created.'),
                                    dict(name='finished',
                                         values=['yes'],
                                         description='No more work to be done.'),
                                    dict(name='returned',
                                         value=['yes'],
                                         description='Returned to customer.'),
                                    dict(name='scrapped',
                                         values=['yes'],
                                         description='Useless for any further work.')],
                          description='Status flags for the sample.'),
              StringField('multiplex_label',
                          description="Label representing the multiplexing"
                          " sequence. Used to defined the 'multiplex_sequence'"
                          " value from the lookup table defined for the"
                          " instrument used in an instrument run."),
              StringField('multiplex_sequence',
                          description='Actual multiplexing sequence.'
                          " If this is defined, then the 'multiplex_label'"
                          " value will be ignored."),
              TextField('description')]

    def get_viewable(self, user):
        "If role 'customer', then allow view only of own sample."
        role = user.get('role')
        if role in ('admin', 'manager', 'engineer'): return True
        if role == 'customer':
            # The database is corrupt if this generates ValueError
            doc = self.get_named_document('project', self.doc['project'])
            return doc.get('customer') == user['name']
        return False

    def view(self, page):
        "Produce the HTML page for GET."
        self.view_fields(page)
        self.view_worksets(page)
        self.view_attachments(page)
        self.view_log(page)
        self.view_locked(page)
        self.view_tags(page)
        self.view_xrefs(page)

    def view_worksets(self, page):
        "Produce the HTML for the workset list."
        page.append(H2('Worksets'))

        rows = [TR(TH('Workset'),
                   TH('Operator'),
                   TH('# samples'),
                   TH('Timestamp'))]
        view = self.db.view('workset/sample', include_docs=True)
        for result in view[self.doc['name']]:
            doc = result.doc
            workset = A(doc['name'],
                        href=configuration.get_url('workset', doc['name']))
            operator = A(doc['operator'],
                      href=configuration.get_url('account', doc['operator']))
            rows.append(TR(TD(workset),
                           TD(operator),
                           TD(str(len(doc['samples']))),
                           TD(doc['timestamp'])))
        page.append(TABLE(border=1, *rows))

    def get_editable_privilege(self, user):
        "Anyone except the customer may edit a sample."
        return user.get('role') in ('admin', 'manager', 'engineer')


class SampleCreate(EntityCreate):
    "Create sample(s) within a project."

    entity_class = Sample

    def prepare(self, request, response):
        super(SampleCreate, self).prepare(request, response)
        try:
            project = request.cgi_fields['project'].value.strip()
            if not project: raise KeyError
        except KeyError:
            raise HTTP_BAD_REQUEST('no project specified for sample create')
        try:
            self.project = self.get_named_document('project', project)
        except ValueError:
            raise HTTP_BAD_REQUEST("no such project '%s'" % project)

    def get_privilege(self):
        "Everyone except the customer may create a sample."
        role = self.user.get('role')
        return role in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.check_privilege()

        page = HtmlPage(self, title='Create samples')
        page.append(P("Project %s"
                      % A(self.project['name'],
                          href=configuration.get_entity_url(self.project))))

        try:
            number = request.cgi_fields['number'].value.strip()
            if not number: raise KeyError
            number = int(number)
            if number <= 0: raise ValueError
        except (KeyError, ValueError):
            number = 4
        page.append(P(FORM('Number of samples ',
                           INPUT(type='text', size=3,
                                 name='number', value=str(number)),
                           INPUT(type='hidden',
                                 name='project', value=self.project['name']),
                           INPUT(type='submit', value='Change number'),
                           B(' Note:'), ' Any values already in the table'
                           ' below will be cleared!',
                           method='GET',
                           action=configuration.get_url('sample'))))

        reference = self.project.get('reference') or ''
        rows = [TR(TH(),
                   TH('Lab name (required)'),
                   TH('Altname'),
                   TH('Reference'),
                   TH('Amount'),
                   TH('Concentration'))]
        for slot in xrange(number):
            rows.append(TR(TD(str(slot+1)),
                           TD(INPUT(type='text', name="name_%i" % slot)),
                           TD(INPUT(type='text', name="altname_%i" %slot)),
                           TD(INPUT(type='text',
                                    name="reference_%i" % slot,
                                    value=reference)),
                           TD(INPUT(type='text', size=8,
                                    name="amount_%i" % slot)),
                           TD(INPUT(type='text', size=8,
                                    name="concentration_%i" % slot))))
        page.append(FORM(TABLE(border=1, *rows),
                         INPUT(type='hidden', name='number', value=str(number)),
                         INPUT(type='hidden',
                               name='project', value=self.project['name']),
                         P(INPUT(type='submit', value='Create')),
                         method='POST',
                         action=configuration.get_url('sample')))

        page.append(P(FORM(INPUT(type='submit', value='Cancel'),
                           method='GET',
                           action=configuration.get_entity_url(self.project))))
        page.write(response)

    def POST(self, request, response):
        self.check_privilege()

        try:
            number = int(request.cgi_fields['number'].value)
            if number <= 0: raise ValueError
        except (KeyError, ValueError):
            raise HTTP_BAD_REQUEST('Invalid number of samples specified')

        samples = []
        for slot in xrange(number):
            sample = dict(_id=utils.id_uuid(),
                          entity='sample',
                          project=self.project['name'],
                          status=[dict(name='defined',
                                       value='yes',
                                       timestamp=utils.now_iso())],
                          timestamp=utils.now_iso())
            for key, converter in [('name', str),
                                   ('altname', str),
                                   ('reference', str),
                                   ('amount', float),
                                   ('concentration', float)]:
                try:
                    value = request.cgi_fields["%s_%i" % (key,slot)].value
                    value = value.strip()
                    if not value: raise KeyError
                    value = converter(value)
                except (KeyError, ValueError, TypeError):
                    pass
                else:
                    sample[key] = value
            # Skip entry if no name given
            if not sample.has_key('name'): continue
            # Check unique name
            view = self.db.view('sample/name')
            if len(view[sample['name']]):
                raise HTTP_BAD_REQUEST("sample %i name '%s' is already used"
                                       % (slot+1, sample['name']))
            samples.append(sample)
        for sample in samples:
            self.db.save(sample)
            self.log(sample['_id'], 'defined')
        samplelist = ', '.join([s['name'] for s in samples])
        self.log(self.project.id,
                 'added samples',
                 initial=self.project,
                 comment="Samples %s" % samplelist)
        raise HTTP_SEE_OTHER(Location=configuration.get_entity_url(self.project))


class Samples(Dispatcher):
    "Samples list page dispatcher."

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Samples')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(Sample.__doc__))

        if self.user.get('role') in ('admin', 'manager', 'engineer'):
            operator = self.get_selected_operator(request)
            page.append(P(self.get_operator_select_form('samples', operator)))
        else:                           # Customer can only view his own samples
            operator = self.user['name']
        view = self.db.view('project/customer')
        if operator:
            result = list(view[operator])
        else:
            result = list(view)
        projects = [r.value for r in result]

        rows = [TR(TH('Project'),
                   TH('Sample'),
                   TH('Altname'),
                   TH('Status'))]
        status_field = Sample.get_field('status')
        for project in projects:
            link_project = A(project,
                             href=configuration.get_url('project', project))
            view = self.db.view('sample/project', include_docs=True)
            samples = [r.doc for r in view[project]]
            if samples:
                samples.sort(lambda i, j: cmp(i['name'], j['name']))
                for sample in samples:
                    if link_project:
                        cells = [TD(link_project, rowspan=len(samples))]
                        link_project = None # Skip after first row
                    else:
                        cells = []
                    url = configuration.get_entity_url(sample)
                    cells.append(TD(A(sample['name'], href=url)))
                    cells.append(TD(sample.get('altname') or ''))
                    cells.append(TD(status_field.get_view_doc(sample)))
                    rows.append(TR(*cells))
            else:
                rows.append(TR(TD(link_project)))
        page.append(TABLE(border=1, *rows))
        page.write(response)
