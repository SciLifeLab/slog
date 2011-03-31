""" slog: Simple sample tracker system.

Application entity and dispatchers.

Per Kraulis
2011-02-15
"""

import utils
from .entity import *


class ApplicationNameField(NameField):
    "Name must be unique among applications."

    def check_value(self, dispatcher, value):
        value = super(ApplicationNameField, self).check_value(dispatcher, value)
        try:
            dispatcher.get_named_document('application', value)
        except ValueError:
            return value
        else:
            raise ValueError("Application name '%s' is already in use" % value)
        

class Application(Entity):
    """An application is an overall strategy for the analysis of a set
of samples."""

    fields = [ApplicationNameField('name', required=True, fixed=True,
                                   description='Unique application identifier.'
                                   ' Cannot be changed once set.'),
              StringField('label',
                          description='Descriptive one-liner, nickname.'),
              TextField('description')]

    def view(self, page):
        "Produce the HTML page for GET."
        self.view_fields(page)
        self.view_protocols(page)
        self.view_projects(page)
        self.view_attachments(page)
        self.view_log(page)
        self.view_locked(page)
        self.view_tags(page)
        self.view_xrefs(page)

    def view_protocols(self, page):
        "Show list of protocols for application."
        page.append(H2("Protocols"))

        rows = [TR(TH('Protocol'),
                   TH('Timestamp'))]
        view = self.db.view('protocol/application', include_docs=True)
        docs = [r.doc for r in view[self.doc['name']]]
        docs.sort(lambda i, j: cmp(i['name'], j['name'])) # Sort by name
        for doc in docs:
            rows.append(TR(TD(A(doc['name'],
                                href=configuration.get_url('protocol',
                                                           doc['name']))),
                           TD(doc.get('timestamp'))))
        page.append(TABLE(border=1, *rows))

    def view_projects(self, page):
        "Show list of projects for application."
        page.append(H2("Projects"))

        rows = [TR(TH('Project'),
                   TH('Timestamp'))]
        view = self.db.view('project/application', include_docs=True)
        docs = [r.doc for r in view[self.doc['name']]]
        docs.sort(lambda i, j: cmp(i['name'], j['name'])) # Sort by name
        for doc in docs:
            rows.append(TR(TD(A(doc['name'],
                                href=configuration.get_url('project',
                                                           doc['name']))),
                           TD(doc.get('timestamp'))))
        page.append(TABLE(border=1, *rows))


class ApplicationCreate(EntityCreate):
    "Application creation dispatcher."

    entity_class = Application

    def get_privilege(self):
        return self.user.get('role') in ('admin', 'manager')


class Applications(Dispatcher):
    "Application list dispatcher."

    def get_editable(self, user):
        "Only admin and manager may create an application."
        return user.get('role') in ('admin', 'manager')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Applications')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(Application.__doc__))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit',
                                     value='Create new application'),
                               method='GET',
                               action=configuration.get_url('application'))))

        view = self.db.view('project/application_count', group=True)
        counts = dict([(r.key, r.value) for r in view])

        rows = [TR(TH('Application'),
                   TH('Label'),
                   TH('# Projects'),
                   TH('Timestamp'))]
        view = self.db.view('application/timestamp',
                            descending=True,
                            include_docs=True)
        for result in view:
            doc = result.doc
            url = configuration.get_url('application',doc['name'])
            application = A(doc['name'], href=url)
            rows.append(TR(TD(application),
                           TD(doc['label'] or ''),
                           TD(str(counts.get(doc['name'], 0))),
                           TD(doc['timestamp'])))
        page.append(TABLE(border=1, *rows))

        page.write(response)
