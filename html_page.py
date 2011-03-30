""" slog: Simple sample tracker system.

Standard HTML page.

Per Kraulis
2011-02-02
"""

from HyperText.HTML40 import *

from . import configuration


class HtmlPage(object):
    "Standard HTML page."

    def __init__(self, dispatcher, title='slog'):
        self.dispatcher = dispatcher
        self.head_meta = [META(content='text/html; charset=utf-8',
                               http_equiv='Content-Type'),
                          META(content='application/javascript',
                               http_equiv='Content-Script-Type')]
        self.title = title
        self.stylesheet = configuration.get_url('static', 'style.css')
        self.style = "form {padding:0; margin:0}"
        self.logo = A(IMG(src=configuration.get_url('static', 'slog.png'),
                          width="107", height="100",
                          alt="slog %s" % configuration.VERSION),
                      href=configuration.site.URL_BASE)
        self.set_header()
        # Logout is possible only for Firefox, Safari and Opera
        logout = False
        if dispatcher.user_agent:
            user_agent = dispatcher.user_agent.lower()
            for signature in ['firefox', 'opera', 'safari']:
                if signature in user_agent:
                    logout = True
                    break
        self.set_login(logout=logout)
        self.set_search()
        self.set_navigation()
        self.state = []                 # Current state of the entity
        self.meta = []
        self.log = ''
        self.context = "slog %s" % configuration.VERSION

    def set_header(self):
        self.header = H1(self.title)

    def set_login(self, logout=True):
        name = self.dispatcher.user['name']
        # This is a non-standard way of achieving a logout in several
        # different browsers, which should include Firefox, Opera and
        # Safari, but not Internet Explores.
        href = configuration.get_url('account', name)
        msg = "Login: %s (%s)" % (A(name, href=href),
                                  self.dispatcher.user.get('role'))
        if logout:
            href = "http://logout:byebye@%s" % configuration.site.BASE
            msg += " [%s]" % A('logout', href=href)
        self.login = DIV(msg)

    def set_search(self):
        self.search = FORM(INPUT(type='text', name='key'),
                           INPUT(type='submit', value='Search'),
                           method='GET',
                           action=configuration.get_url('search'))

    def set_navigation(self):
        rows = []
        for entities in ['Accounts',
                         'Projects',
                         'Samples',
                         'Worksets',
                         'Applications',
                         'Protocols',
                         'Tasks',
                         'Instruments']:
            rows.append(TR(TD(A(entities,
                                href=configuration.get_url(entities.lower())))))
        self.navigation = TABLE(*rows)

    def set_context(self, doc):
        "Set the standard context information for a document."
        self.context = DIV("slog %s, document %s, revision %s, timestamp %s"
                           % (configuration.VERSION,
                              A(doc.id,
                                href=configuration.get_url('doc', doc.id)),
                              doc.rev,
                              doc.get('timestamp', '?')))

    def append(self, elem):
        "Append an HTML element to the list of info items."
        self.state.append(elem)

    def create(self):
        "Create the page contents."
        raise NotImplementedError

    def write(self, response):
        head = HEAD(*self.head_meta)
        head.append(TITLE(self.title))
        if self.stylesheet:
            head.append(LINK(rel='stylesheet',
                             href=self.stylesheet,
                             type='text/css'))
        elif self.style:
            head.append(STYLE(self.style, type='text/css'))
        state = [DIV(s) for s in self.state]
        body = BODY(TABLE(TR(TH(self.logo, width='8%'),
                             TD(self.header),
                             TD(TABLE(TR(TD(self.login)),
                                      TR(TD(self.search))))),
                          TR(TD(self.navigation, rowspan=2),
                             TD(*state),
                             TD(rowspan=2, *self.meta)),
                          TR(TD(self.log)),
                          TR(TD(HR(), colspan=3)),
                          TR(TD(self.context, colspan=3)),
                          klass='body',
                          width='100%'))
        html = HTML(head, body)
        response['Content-Type'] = 'text/html'
        response.append(str(html))
