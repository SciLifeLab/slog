""" slog: Simple sample tracker system.

Project entity and dispatchers.

Per Kraulis
2011-02-06
"""

import utils
from .entity import *


class ProjectNameField(NameField):
    "Name must be unique among projects."

    def check_value(self, dispatcher, value):
        value = super(ProjectNameField, self).check_value(dispatcher, value)
        try:
            dispatcher.get_named_document('project', value)
        except ValueError:
            return value
        else:
            raise ValueError("Project name '%s' is already in use" % value)


class Project(Entity):
    """A project consists of a set of samples to be analysed using a particular
experimental strategy. The samples belong to this and only this project."""

    fields = [ProjectNameField('name',
                               required=True,
                               fixed=True,
                               description=\
"""The SciLifeLab name of the project. The name must be unique among projects.
It is set at creation and cannot be changed. It has the form
'In_Name_year_number', where 'In' and 'Name' are the initials and surname of
the project customer (=PI), 'year' is the two-digit year the project started,
and 'number' is the consecutive number of the project in that year."""),
              TextField('description', description='Explanation, comments.'),
              ReferenceField('customer',
                             referred='account',
                             required=True,
                             description='The customer is usually the Principal'
                             ' Investigator (PI) of the project.'),
              ReferenceField('operator',
                             referred='account',
                             required=True,
                             default=utils.get_login_account,
                             description='The engineer responsible for'
                             ' overseeing this project.'),
              StringField('reference',
                          required=False,
                          description='Reference for the project,'
                          ' e.g. species or genome.'
                          ' Samples created within the project will'
                          ' be assigned this reference by default.'),
              BooleanField('approved',
                           required=False,
                           description='Has been approved by the review'
                           ' committee.'),
              BooleanField('started',
                           required=False,
                           description='Go-ahead has been given for work.'),
              BooleanField('finished',
                           required=False,
                           description='Work has been finalized.'),
              BooleanField('archived',
                           required=False,
                           description='Samples and results are no longer'
                           ' directly available.'),
              StringField('results',
                          required=False,
                          description='Pointer to where the results can be'
                          ' found. For example: the UPPNEX project name,'
                          ' or the SweStore identifier.')]

    def get_viewable(self, user):
        """Everyone except customer may view any project.
        Customer may view his own project."""
        if user.get('role') in ('admin', 'manager', 'engineer'): return True
        return user['name'] == self.doc.get('customer')

    def get_editable_privilege(self, user):
        "Only the manager and the operator may edit the project."
        if user.get('role') in ('admin', 'manager'): return True
        return user['name'] == self.doc.get('operator')

    def view(self, page):
        "Produce the HTML page for GET."
        self.view_fields(page)
        self.view_samples(page)
        self.view_attachments(page)
        self.view_log(page)
        self.view_locked(page)
        self.view_tags(page)
        self.view_xrefs(page)

    def view_samples(self, page):
        "Show list of all samples within the project."
        from .sample import Sample

        page.append(H2('Samples'))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit', value='Create samples'),
                               INPUT(type='hidden',
                                     name='project', value=self.doc['name']),
                               method='GET',
                               action=configuration.get_url('sample'))))

        rows = [TR(TH('Name'),
                   TH('Customername'),
                   TH('Amount'),
                   TH('Concentration'),
                   TH('Timestamp'))]
        view = self.db.view('sample/project', include_docs=True)
        results = list(view[self.doc['name']])
        results.sort(lambda i, j: cmp(i.value, j.value)) # Sort by name
        for result in results:
            doc = result.doc
            rows.append(TR(TD(A(result.value,
                                href=configuration.get_url('sample',
                                                           result.value))),
                           TD(doc.get('customername', '')),
                           TD(doc.get('amount', '')),
                           TD(doc.get('concentration', '')),
                           TD(doc.get('timestamp'))))
        page.append(TABLE(border=1, *rows))


class ProjectCreate(EntityCreate):
    "Project creation dispatcher."

    entity_class = Project

    def get_privilege(self):
        return self.user.get('role') in ('admin', 'manager')


class Projects(Dispatcher):
    "Projects list page dispatcher."

    def get_viewable(self, user):
        "Everyone except customers may view the projects list."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def get_editable(self, user):
        "Everyone except customers may create a project."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Projects')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(Project.__doc__))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit', value='Create new project'),
                               method='GET',
                               action=configuration.get_url('project'))))

        view = self.db.view('sample/project_count', group=True)
        counts = dict([(r.key, r.value) for r in view])
        rows = [TR(TH('Project'),
                   TH('Label'),
                   TH('Customer'),
                   TH('# Samples'),
                   TH('Timestamp'))]
        view = self.db.view('project/timestamp',
                            descending=True,
                            include_docs=True)
        for result in view:
            doc = result.doc
            project = A(doc['name'],
                        href=configuration.get_url('project', doc['name']))
            # Defensive programming: in reality always defined
            customer = doc.get('customer')
            if customer:
                customer = A(customer,
                             href=configuration.get_url('account', customer))
            rows.append(TR(TD(project),
                           TD(result.value or ''),
                           TD(customer),
                           TD(str(counts.get(doc['name'], 0))),
                           TD(result.key)))
        page.append(TABLE(border=1, *rows))

        page.write(response)
