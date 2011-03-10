""" slog: Simple sample tracker system.

Instrument entity and dispatchers.

Per Kraulis
2011-02-16
"""

import utils
from .entity import *


class InstrumentNameField(NameField):
    "Name must be unique among instruments."

    def check_value(self, dispatcher, value):
        value = super(InstrumentNameField, self).check_value(dispatcher, value)
        try:
            dispatcher.get_named_document('instrument', value)
        except ValueError:
            return value
        else:
            raise ValueError("Instrument name '%s' is already in use" % value)


class Instrument(Entity):
    """An instrument (sequencer, robot, analyzer, etc.) with a specification
describing the layout of the samples in one run."""

    fields = [InstrumentNameField('name', required=True, fixed=True,
                                  description='Unique instrument identifier.'
                                  ' Cannot be changed once set.'),
              StringField('label',
                          description='Descriptive one-liner, nickname.'),
              StringField('type', required=True,
                          description='Type of instrument: company and model.'),
              IntegerField('max_rows', required=True, default=1,
                           description="The maximum number of rows (or similar)"
                           " in the instrument's sample array."),
              IntegerField('max_columns', required=True, default=1,
                           description="The maximum number of columns (lanes,"
                           " or similar) in the instrument's sample array."),
              IntegerField('max_multiplex', required=True, default=1,
                           description="The maximum number of samples in"
                           " each lane/well of the instrument's sample array."),
              TextField('description')]

    def view(self, page):
        "Produce the HTML page for GET."
        self.view_fields(page)
        self.view_protocols(page)
        self.view_attachments(page)
        self.view_log(page)
        self.view_tags(page)
        self.view_xrefs(page)

    def view_protocols(self, page):
        "Show list of protocols for application."
        page.append(H2("Protocols"))

        rows = [TR(TH('Protocol'),
                   TH('Timestamp'))]
        view = self.db.view('protocol/instrument', include_docs=True)
        docs = [r.doc for r in view[self.doc['name']]]
        docs.sort(lambda i, j: cmp(i['name'], j['name'])) # Sort by name
        for doc in docs:
            url = configuration.get_url('protocol', doc['name'])
            rows.append(TR(TD(A(doc['name'], href=url)),
                           TD(doc.get('timestamp'))))
        page.append(TABLE(border=1, *rows))


class InstrumentCreate(EntityCreate):
    "Instrument creation dispatcher."

    entity_class = Instrument

    def get_privilege(self):
        return self.user.get('role') in ('admin', 'manager')


class Instruments(Dispatcher):
    "Instrument list dispatcher."

    def get_editable(self, user):
        "Only admin and manager may create an instrument."
        return user.get('role') in ('admin', 'manager')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Instruments')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(Instrument.__doc__))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit',
                                     value='Create new instrument'),
                               method='GET',
                               action=configuration.get_url('instrument'))))

        rows = [TR(TH('Instrument'),
                   TH('Label'),
                   TH('Type'),
                   TH('Timestamp'))]
        view = self.db.view('instrument/name', include_docs=True)
        for result in view:
            doc = result.doc
            instrument = A(doc['name'],
                           href=configuration.get_url('instrument',doc['name']))
            rows.append(TR(TD(instrument),
                           TD(doc['label'] or ''),
                           TD(doc['type']),
                           TD(doc['timestamp'])))
        page.append(TABLE(border=1, *rows))

        page.write(response)
