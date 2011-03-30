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
    """A project consists of a set of samples to be analysed using a specific
application. The samples belong to this and only this project.
The customer is usually the Principal Investigator (PI) of the project."""

    fields = [ProjectNameField('name', required=True, fixed=True,
                               description=\
"""The SciLifeLab name of the project. The name must be unique among projects.
It is set at creation and cannot be changed. It has the form
'In_Name_year_number', where 'In' and 'Name' are the initials and surname of
the project customer (=PI), 'year' is the two-digit year the project started,
and 'number' is the consecutive number of the project in that year."""),
              StringField('label',
                          description='Descriptive one-liner, nickname.'),
              ReferenceField('customer',
                             referred='account',
                             required=True,
                             description='The PI of the project.'),
              ReferenceField('application', 'application',
                             required=True,
                             description="Experimental strategy."),
              StringField('reference',
                          required=False,
                          description='Reference for the project,'
                          ' e.g. species or genome.'
                          ' Samples created within the project will'
                          ' be assigned this reference by default.'),
              StatusField('status',
                          statuses=[dict(name='defined',
                                         values=['yes'],
                                         description='After customer application.'),
                                    dict(name='approved',
                                         values=['yes'],
                                         description='By review committee.'),
                                    dict(name='started',
                                         values=['yes'],
                                         description='All samples received.'),
                                    dict(name='finished',
                                         values=['yes'],
                                         description='No more work to be done.')],
                          description='Status flags for the project.'),
              TextField('description')]

    def get_viewable(self, user):
        """Everyone except customer may view any project.
        Customer may view his own project."""
        if user.get('role') in ('admin', 'manager', 'engineer'): return True
        return user['name'] == self.doc['customer']

    def get_editable(self, user):
        "Everyone except customer may edit any project."
        if self.locked: return False
        return user.get('role') in ('admin', 'manager', 'engineer')

    def view(self, page):
        "Produce the HTML page for GET."
        self.view_fields(page)
        self.view_samples(page)
        self.view_attachments(page)
        self.view_log(page)
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
                   TH('Altname'),
                   TH('Amount'),
                   TH('Concentration'),
                   TH('Status'),
                   TH('Timestamp'))]
        view = self.db.view('sample/project', include_docs=True)
        results = list(view[self.doc['name']])
        results.sort(lambda i, j: cmp(i.value, j.value)) # Sort by name
        status_field = Sample.get_field('status')
        for result in results:
            doc = result.doc
            rows.append(TR(TD(A(result.value,
                                href=configuration.get_url('sample',
                                                           result.value))),
                           TD(doc.get('altname', '')),
                           TD(doc.get('amount', '')),
                           TD(doc.get('concentration', '')),
                           TD(status_field.get_view_doc(doc)),
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
                   TH('Application'),
                   TH('Status'),
                   TH('# Samples'),
                   TH('Timestamp'))]
        status_field = Project.get_field('status')
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
            # Defensive programming: in reality always defined
            application = doc.get('application')
            if application:
                url = configuration.get_url('application', application)
                application = A(application, href=url)
            rows.append(TR(TD(project),
                           TD(result.value or ''),
                           TD(customer),
                           TD(application),
                           TD(status_field.get_view_doc(doc)),
                           TD(str(counts.get(doc['name'], 0))),
                           TD(result.key)))
        page.append(TABLE(border=1, *rows))

        page.write(response)
