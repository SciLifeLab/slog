""" slog: Simple sample tracker system.

Accounts list page dispatcher.

Per Kraulis
2011-02-05
"""

from .dispatcher import *


class Accounts(Dispatcher):
    "Accounts list page dispatcher."

    def get_viewable(self, user):
        "Everyone except customers may view the accounts list."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Accounts')

        if self.get_editable(self.user):
            page.append(FORM(INPUT(type='submit', value='Create new account'),
                             method='GET',
                             action=configuration.get_url('account')))
            page.append(P())

        rows = [TR(TH('Account'), TH('Full name'))]
        for result in self.db.view('account/name'):
            rows.append(TR(TD(A(result.key,
                                href=configuration.get_url('account', result.key))),
                           TD(result.value or '')))
        page.append(TABLE(border=1, *rows))

        page.write(response)
