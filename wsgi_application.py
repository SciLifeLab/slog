"""slog: Simple sample tracking system.

Apache WSGI interface using 'wireframe' package.

Per Kraulis
2011-02-02
"""

import logging

from wireframe.application import Application as WsgiApplication

from slog.home import Home
from slog.search import Search
from slog.account import Account, AccountCreate, Accounts
from slog.protocol import Protocol, ProtocolCreate, Protocols
from slog.project import Project, ProjectCreate, Projects
from slog.sample import Sample, SampleCreate, Samples
from slog.workset import Workset, WorksetCreate, Worksets
from slog.instrument import Instrument, InstrumentCreate, Instruments
from slog.task import Task, TaskCreate, Tasks
from slog.tool import ToolDispatcher
from slog.dispatcher import Id, Doc, Static, Attachment


logging.basicConfig(level=logging.INFO)


application = WsgiApplication(human_debug_output=True)

# Linear search: put most used at beginning of list!
application.add_class(r'^/?$', Home)
application.add_class(r'^/search$', Search)
application.add_class(r'^/static/(?P<filename>[^/]+)$', Static)
application.add_class(r'^/attachment/(?P<id>[a-f0-9]{32,32})/(?P<filename>[^/]+)$', Attachment)
application.add_class(r'^/accounts$', Accounts)
application.add_class(r'^/account/(?P<name>[^/]+)$', Account)
application.add_class(r'^/account/?$', AccountCreate)
application.add_class(r'^/protocols$', Protocols)
application.add_class(r'^/protocol/(?P<name>[^/]+)$', Protocol)
application.add_class(r'^/protocol/?$', ProtocolCreate)
application.add_class(r'^/projects$', Projects)
application.add_class(r'^/project/(?P<name>[^/]+)$', Project)
application.add_class(r'^/project/?$', ProjectCreate)
application.add_class(r'^/sample/(?P<name>[^/]+)$', Sample)
application.add_class(r'^/sample/?$', SampleCreate)
application.add_class(r'^/samples$', Samples)
application.add_class(r'^/workset/(?P<name>[^/]+)$', Workset)
application.add_class(r'^/workset/?$', WorksetCreate)
application.add_class(r'^/worksets$', Worksets)
application.add_class(r'^/instruments$', Instruments)
application.add_class(r'^/instrument/(?P<name>[^/]+)$', Instrument)
application.add_class(r'^/instrument/?$', InstrumentCreate)
application.add_class(r'^/tasks$', Tasks)
application.add_class(r'^/task/(?P<name>[^/]+)$', Task)
application.add_class(r'^/task/?$', TaskCreate)
application.add_class(r'^/tool/(?P<name>[^/]+)$', ToolDispatcher)
application.add_class(r'^/id/(?P<id>[a-f0-9]{32,32})$', Id)
application.add_class(r'^/doc/(?P<id>[a-f0-9]{32,32})$', Doc)
