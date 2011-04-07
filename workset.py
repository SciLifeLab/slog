""" slog: Simple sample tracker system.

Workset entity and dispatcher.

Per Kraulis
2011-02-12
"""

import logging

import utils
from .entity import *


class WorksetNameField(NameField):
    "Name must be unique among worksets."

    def check_value(self, dispatcher, value):
        value = super(WorksetNameField, self).check_value(dispatcher, value)
        try:
            dispatcher.get_named_document('workset', value)
        except ValueError:
            return value
        else:
            raise ValueError("Workset name '%s' is already in use" % value)


class Workset(Entity):
    """A collection of samples to be collectively handled, for example to
be processed by a task.
It may contain samples from different projects.
A workset has the following properties:

* Dynamic: Samples may be added or removed.
* Non-exclusive: A sample may be part of any number of worksets.
* Arranged: The samples may optionally be placed in a rectangular grid
  consisting of rows, columns and multiplex.

"""

    fields = [NameField('name',
                        required=True,
                        fixed=True,
                        description='Unique workset identifier.'
                        ' Cannot be changed once set.'),
              TextField('description'),
              ReferenceField('operator',
                             referred='account',
                             required=True,
                             default=utils.get_login_account,
                             description='The user responsible for'
                             ' this workset.'),
              SampleSetField('samples',
                             required=True,
                             description='The set of samples.'),
              SampleGridField('grid',
                              required=True,
                              description='Arrangement of the samples'
                              ' in a grid of specified dimensions.'
                              ' All dimension sizes must be positive integers'
                              ' for the grid to be defined. Shrinking the'
                              ' dimension sizes may implicitly remove some'
                              ' samples from the arrangement.')]

    def get_editable_privilege(self, user):
        "Everyone except customer may edit any project."
        return user.get('role') in ('admin', 'manager', 'engineer')

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
                   TH('Protocol'),
                   TH('Operator'),
                   TH('Timestamp'))]
        view = self.db.view('task/workset', include_docs=True)
        for result in view[self.doc['name']]:
            doc = result.doc
            task = A(doc['name'], href=configuration.get_entity_url(doc))
            protocol = doc.get('protocol') or ''
            if protocol:
                url = configuration.get_url('protocol', protocol)
                protocol = A(protocol, href=url)
            operator = A(doc['operator'],
                         href=configuration.get_url('account', doc['operator']))
            rows.append(TR(TD(task),
                           TD(protocol),
                           TD(operator),
                           TD(doc['timestamp'])))
        page.append(TABLE(border=1, *rows))

    def get_all_samples(self):
        "Return the set of all samples in the workset."
        return set(self.doc.get('samples') or [])

    def get_arranged_samples(self):
        """Get a dictionary of samples placed in the arrangement.
        Key: sample name.
        Value: arrangement coordinate (row, column, multiplex).
        """
        grid = self.doc.get('grid') or dict()
        arrangement = grid.get('arrangement') or []
        result = dict()
        for i, row in enumerate(arrangement):
            for j, column in enumerate(row):
                for k, sample in enumerate(column):
                    if sample is not None:
                        result[sample] = (i, j, k)
        return result

    def cleanup_arranged_samples(self, samples):
        "Remove all non-present samples from the arrangement."
        grid = self.doc.get('grid') or dict()
        arrangement = grid.get('arrangement') or []
        for i, row in enumerate(arrangement):
            for j, column in enumerate(row):
                for k, sample in enumerate(column):
                    if sample is None: continue
                    if sample not in samples:
                        column[k] = None


class WorksetCreate(EntityCreate):
    "Workset creation dispatcher."

    entity_class = Workset

    def prepare(self, request, response):
        super(WorksetCreate, self).prepare(request, response)
        try:
            project = request.cgi_fields['project'].value.strip()
            if not project: raise KeyError
        except KeyError:
            self.project = None
        else:
            try:
                self.project = self.get_named_document('project', project)
            except ValueError:
                raise HTTP_BAD_REQUEST("no such project '%s'" % project)

    def get_privilege(self):
        return self.user.get('role') in ('admin', 'manager', 'engineer')


class Worksets(Dispatcher):
    "Worksets list page dispatcher."

    def get_viewable(self, user):
        "Everyone except customers may view the worksets list."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def get_editable(self, user):
        "Everyone except customers may create a workset."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Worksets')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(Workset.__doc__))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit', value='Create new workset'),
                               method='GET',
                               action=configuration.get_url('workset'))))

        operator = self.get_selected_operator(request)
        page.append(P(self.get_operator_select_form('worksets', operator)))

        if operator:
            view = self.db.view('workset/operator', include_docs=True)[operator]
        else:
            view = self.db.view('workset/name', include_docs=True)
        worksets = [r.doc for r in view]
        worksets.sort(lambda i, j: cmp(i['name'], i['name']))

        rows = [TR(TH('Workset'),
                   TH('Operator'),
                   TH('Samples'),
                   TH('Timestamp'))]
        for workset in worksets:
            operator = workset.get('operator')
            if operator:
                url = configuration.get_url('account', operator)
                operator = A(operator, href=url)
            else:
                operator = ''
            samples = workset.get('samples', [])
            for i, sample in enumerate(samples):
                url = configuration.get_url('sample', sample)
                samples[i] = str(A(sample, href=url))
            samples = ', '.join(samples)

            url = configuration.get_url('workset', workset['name'])
            rows.append(TR(TD(A(workset['name'], href=url)),
                           TD(operator),
                           TD(samples),
                           TD(workset['timestamp'])))
        page.append(TABLE(border=1, *rows))

        page.write(response)
