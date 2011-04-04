""" slog: Simple sample tracker system.

Protocol specifying data and steps required for a Task.

Per Kraulis
2011-03-04
"""

import utils
from .entity import *


class ProtocolNameField(NameField):
    "Name must be unique among protocols."

    def check_value(self, dispatcher, value):
        value = super(ProtocolNameField, self).check_value(dispatcher, value)
        try:
            dispatcher.get_named_document('protocol', value)
        except ValueError:
            return value
        else:
            raise ValueError("Protocol name '%s' is already in use" % value)


class StepsDefinitionField(Field):
    "Definition of steps in a protocol."

    def get_view(self, entity):
        steps = entity.doc.get(self.name) or []
        return TABLE(*[TR(TD(s)) for s in steps])

    def get_edit_form_field(self, entity):
        try:
            steps = entity.doc.get(self.name) or []
        except AttributeError:          # '.doc' not set when creating
            steps = []
        return TEXTAREA('\n'.join(steps), name=self.name, rows=4)

    def get_value(self, dispatcher, request, required=True):
        """Get the value for the field from the CGI form inputs.
        Raise KeyError if no such named field in the CGI form inputs
        and 'required' is True, else try to use the value None.
        Raise ValueError if invalid value for the field."""
        try:
            value = request.cgi_fields[self.name].value
        except KeyError:
            if required:
                raise
            else:
                value = None
        else:
            value = value.strip().replace('\r\n', '\n').split('\n')
        return self.check_value(dispatcher, value)


class Protocol(Entity):
    """A protocol is a template for a task. It specifies the steps that
the samples in the workset of a task are to be taken through.
The protocol may be associated with any number of applications
and instruments."""

    fields = [ProtocolNameField('name',
                                required=True,
                                fixed=True,
                                description='Unique protocol identifier.'
                                ' Cannot be changed once set.'),
              StepsDefinitionField('steps',
                                   required=True,
                                   description='The steps that the task and'
                                   ' the samples in its workset are to be'
                                   ' taken through.'),
              ReferenceListField('applications',
                                 referred='application',
                                 description='Applications for which this'
                                 ' protocol is relevant.'),
              ReferenceListField('instruments',
                                 referred='instrument',
                                 description='Instruments for which this'
                                 ' protocol is relevant.'),
              TextField('description')]

    def get_editable_privilege(self, user):
        """Is the given user allowed to edit this page?
        Roles 'admin' and 'manager' may edit a protocol."""
        return user.get('role') in ('admin', 'manager')

    def view(self, page):
        "Produce the HTML page for GET."
        self.view_fields(page)
        self.view_tasks(page)
        self.view_attachments(page)
        self.view_log(page)
        self.view_locked(page)
        self.view_tags(page)
        self.view_xrefs(page)

    def view_tasks(self, page):
        "View the tasks using this protocol."
        page.append(H2('Tasks'))

        rows = [TR(TH('Task'),
                   TH('Workset'),
                   TH('Operator'),
                   TH('Timestamp'))]
        view = self.db.view('task/protocol', include_docs=True)
        for result in view[self.doc['name']]:
            doc = result.doc
            task = A(doc['name'], href=configuration.get_entity_url(doc))
            workset = doc.get('workset') or ''
            if workset:
                url = configuration.get_url('workset', workset)
                workset = A(workset, href=url)
            operator = A(doc['operator'],
                         href=configuration.get_url('account', doc['operator']))
            rows.append(TR(TD(task),
                           TD(workset),
                           TD(operator),
                           TD(doc['timestamp'])))
        page.append(TABLE(border=1, *rows))


class ProtocolCreate(EntityCreate):
    "Create a protocol."
    
    entity_class = Protocol

    def get_privilege(self):
        return self.user.get('role') in ('admin', 'manager')


class Protocols(Dispatcher):
    "Protocols list page dispatcher."

    def get_editable(self, user):
        "Only 'admin' and 'manager' may create a protocol."
        return user.get('role') in ('admin', 'manager')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Protocols')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(Protocol.__doc__))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit',
                                     value='Create new protocol'),
                               method='GET',
                               action=configuration.get_url('protocol'))))

        view = self.db.view('protocol/name', include_docs=True)
        rows = [TR(TH('Protocol'),
                   TH('Timestamp'))]
        for result in view:
            doc = result.doc
            protocol = A(doc['name'],
                        href=configuration.get_url('protocol', doc['name']))
            rows.append(TR(TD(protocol),
                           TD(doc['timestamp'])))
        page.append(TABLE(border=1, *rows))

        page.write(response)
