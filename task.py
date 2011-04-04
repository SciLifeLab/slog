""" slog: Simple sample tracker system.

Task applying a protocol to sample(s).

Per Kraulis
2011-03-04
"""

import utils
from .entity import *

from . import illumina_samplesheet


class TaskNameField(NameField):
    "Name must be unique among tasks."

    def check_value(self, dispatcher, value):
        value = super(TaskNameField, self).check_value(dispatcher, value)
        try:
            dispatcher.get_named_document('task', value)
        except ValueError:
            return value
        else:
            raise ValueError("Task name '%s' is already in use" % value)


class Task(Entity):
    """A task is an application of a protocol to a sample workset.
The protocol determines the sequence of steps through which the samples
are to be taken. A task is the same as an instrument run if an instrument
is involved."""

    fields = [TaskNameField('name',
                            required=True,
                            fixed=True,
                            description='Unique task identifier.'
                            ' Cannot be changed once set.'),
              StringField('altname',
                          required=False,
                          description='Alternative name, such as an'
                          ' instrument run name.'),
              ReferenceField('protocol', 'protocol',
                             required=True,
                             fixed=True,
                             description='The protocol controlling this task.'
                            ' Cannot be changed once set.'),
              ReferenceField('workset',
                             referred='workset',
                             required=False,
                             fixed=True,
                             description='The sample workset to which'
                             ' the protocol will be applied.'
                             ' Cannot be changed once set.'),
              ReferenceField('instrument', 'instrument',
                             required=False,
                             description='The instrument used, if any.'),
              StringField('aux_unit',
                          required=False,
                          description='Auxiliary instrument unit used, if any.'
                          ' This is an identifier for a flowcell, array,'
                          ' or other essential unit.'),
              ReferenceField('operator',
                             referred='account',
                             required=True,
                             default=utils.get_login_account,
                             description='The user responsible for'
                             ' executing this task.'),
              TextField('description')]

    tool_classes = [illumina_samplesheet.Tool]

    def get_viewable(self, user):
        """Is the given user allowed to view this entity?
        Everyone except 'customer' may view the task."""
        return user.get('role') in ('admin', 'manager', 'engineer')

    def get_editable_privilege(self, user):
        """Is the given user allowed to edit this entity?
        Everyone except 'customer' may edit the task."""
        return user.get('role') in ('admin', 'manager', 'engineer')


class TaskCreate(EntityCreate):
    "Entity creation dispatcher."

    entity_class = Task

    def get_privilege(self):
        return self.user.get('role') in ('admin', 'manager', 'engineer')


class Tasks(Dispatcher):
    "Tasks list dispatcher."

    def get_viewable(self, user):
        "Everyone except customers may view the tasks list."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def get_editable(self, user):
        "Everyone except customers may create a task."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Tasks')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(Task.__doc__))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit',
                                     value='Create new task'),
                               method='GET',
                               action=configuration.get_url('task'))))

        operator = self.get_selected_operator(request)
        page.append(P(self.get_operator_select_form('tasks',operator)))

        if operator:
            view = self.db.view('task/operator', include_docs=True)
            result = view[operator]
        else:
            result = self.db.view('task/name', include_docs=True)
        tasks = [r.doc for r in result]
        tasks.sort(lambda i, j: cmp(i['name'], i['name']))

        rows = [TR(TH('Task'),
                   TH('Altname'),
                   TH('Protocol'),
                   TH('Instrument'),
                   TH('Operator'),
                   TH('Timestamp'))]
        for row in result:
            doc = row.doc
            task = A(doc['name'], href=configuration.get_entity_url(doc))
            url = configuration.get_url('protocol', doc['protocol'])
            protocol = A(doc['protocol'], href=url)
            instrument = doc.get('instrument') or ''
            if instrument:
                url = configuration.get_url('instrument', instrument)
                instrument = A(instrument, href=url)
            operator = doc.get('operator') or ''
            if operator:
                url = configuration.get_url('account', operator)
                operator = A(operator, href=url)
            rows.append(TR(TD(task),
                           TD(doc.get('altname') or ''),
                           TD(protocol),
                           TD(instrument),
                           TD(operator),
                           TD(doc['timestamp'])))
        page.append(TABLE(border=1, *rows))

        page.write(response)
