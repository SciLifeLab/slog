""" slog: Simple sample tracker system.

Tool dispatcher and abstract base tool class.

Per Kraulis
2011-03-10
"""

import utils
from .dispatcher import *


class ToolDispatcher(Dispatcher):
    "Dispatcher to access the specified tool."

    def prepare(self, request, response):
        super(ToolDispatcher, self).prepare(request, response)
        name = request.path_named_values['name']
        try:
            module = __import__("slog.%s" % name, globals(), locals(), ['Tool'])
            tool_class = getattr(module, 'Tool')
        except (ImportError, AttributeError):
            raise HTTP_NOT_FOUND
        try:
            entity = request.cgi_fields['entity'].value.strip()
            if not entity: raise KeyError
            parts = entity.split('/', 1)
            if len(parts) != 2: raise KeyError
            self.doc = self.get_named_document(parts[0], parts[1])
        except (KeyError, ValueError):
            raise HTTP_BAD_REQUEST('Invalid entity specified.')
        self.tool = tool_class(self)
        if not self.tool.is_enabled(self.doc):
            raise HTTP_BAD_REQUEST("Tool '%s' is not enabled for entity '%s'."
                                   % (self.tool, self.doc['name']))

    def GET(self, request, response):
        # XXX implement check_viewable properly
        self.check_viewable(self.user)
        page = HtmlPage(self, title="Tool %s" % self.tool)
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(self.tool.__doc__))
        page.append(FORM(self.tool.get_view(self),
                         INPUT(type='hidden', name='entity',
                               value=self.tool.get_entity_tag(self.doc)),
                         method='POST',
                         action=self.tool.get_url()))
        page.write(response)

    def POST(self, request, response):
        # XXX implement check_editable properly
        self.check_editable(self.user)
        initial = dict(self.doc)
        try:
            comment = self.tool.do_operation(self, request)
        except ValueError, msg:
            raise HTTP_BAD_REQUEST(str(msg))
        self.log(self.doc.id, "tool %s" % self.tool.modulename,
                 initial=initial, comment=comment)
        raise HTTP_SEE_OTHER(Location=configuration.get_entity_url(self.doc))


class BaseTool(object):
    "Abstract base tool class: perform an operation for an entity."

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    @property
    def modulename(self):
        "Must return the filename of the module."
        raise NotImplementedError

    def get_entity_tag(self, doc):
        "Get the tag to identify the entity to operate on."
        return "%s/%s" % (doc['entity'], doc['name'])

    def get_url(self):
        "Get the URL for this tool to operate on the given document."
        return configuration.get_url('tool', self.modulename)

    def is_enabled(self, doc):
        "Can the tool be used with the entity described by the given document?"
        raise NotImplementedError

    def get_view(self, dispatcher):
        "Produce the HTML containing all input elements for the operation."
        raise NotImplementedError

    def do_operation(self, dispatcher, request):
        """Perform the operation.
        Save the document to the database.
        Return the comment for the log entry."""
        raise NotImplementedError
