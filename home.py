""" slog: Simple sample tracker system.

Home page dispatcher.

Per Kraulis
2011-02-02
"""

import utils
from .dispatcher import *
from account import Account
from project import Project
from sample import Sample
from workset import Workset
from protocol import Protocol
from task import Task
from instrument import Instrument


class Home(Dispatcher):
    "Home page dispatcher."

    def GET(self, request, response):
        title = 'slog: simple lab tracking'
        page = HtmlPage(self, title=title)
        page.header = DIV(H1('slog: simple lab tracking'),
                          utils.rst_to_html("""Slog is a simple tracking system
for the lab. It consists of a number of types of entities representing things
to which information is attached. The entities have defined relationships
to each other. A log of who did what when to an entity is maintained.
A log entry also contains a snapshot of the information for an entity before
the change."""))
        page.append(H2('Types of entities in the system'))
        rows = []
        for klass in [Account,
                      Project,
                      Sample,
                      Workset,
                      Protocol,
                      Task,
                      Instrument]:
            rows.append(TR(TH(klass.__name__),
                           TD(utils.rst_to_html(klass.__doc__))))
        page.append(TABLE(*rows))
        page.write(response)
