""" slog: Simple sample tracker system.

Machine type entity and dispatchers.

Per Kraulis
2011-02-16
"""

import utils
from .entity import *


class Machinetype(Entity):
    """A type of machine: instrument, robot, analyzer, etc.
With information on the arrangement of the array of samples in one run."""

    fields = [NameField(),
              StringField('label',
                          description='Descriptive one-liner, nickname.'),
              IntegerField('multiplexing', required=True, default=1,
                           description="The maximum number of samples in"
                           " each lane/well of the machine's sample array."),
              IntegerField('rows', required=True, default=1,
                           description="The number of rows (or similar)"
                           " in the machine's sample array."),
              IntegerField('columns', required=True, default=1,
                           description="The number of columns (lanes,"
                           " or similar) in the machine's sample array."),
              TextField('description')]


class MachinetypeCreate(EntityCreate):
    "Machinetype creation dispatcher."

    entity_class = Machinetype

    def get_privilege(self):
        return self.user.get('role') in ('admin', 'manager')


class Machinetypes(Dispatcher):
    "Machinetype list dispatcher."

    def get_editable(self, user):
        "Only admin and manager may create an experiment."
        return user.get('role') in ('admin', 'manager')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Machine types')

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit',
                                     value='Create new machine type'),
                               method='GET',
                               action=configuration.get_url('machinetype'))))

        ## view = self.db.view('machine/machinetype_count', group=True)
        ## counts = dict([(r.key, r.value) for r in view])

        rows = [TR(TH('Machine type'),
                   TH('Label'),
                   ## TH('# Machines'),
                   TH('Timestamp'))]
        view = self.db.view('machinetype/name', include_docs=True)
        for result in view:
            doc = result.doc
            machinetype = A(doc['name'],
                            href=configuration.get_url('machinetype',
                                                       doc['name']))
            rows.append(TR(TD(machinetype),
                           TD(doc['label'] or ''),
                           ## TD(str(counts.get(doc['name'], 0))),
                           TD(doc['timestamp'])))
        page.append(TABLE(border=1, *rows))

        page.write(response)
