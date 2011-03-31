""" slog: Simple sample tracker system.

Account entity and dispatchers.

Per Kraulis
2011-02-06
"""

import logging

import utils
from .entity import *


class AccountNameField(NameField):
    "Name must be unique among user accounts."

    def check_value(self, dispatcher, value):
        value = super(AccountNameField, self).check_value(dispatcher, value)
        try:
            dispatcher.get_named_document('account', value)
        except ValueError:
            return value
        else:
            raise ValueError("Account name '%s' is already in use" % value)
        

class RoleField(OptionField):
    "Option string field for a user account role."

    def __init__(self, name, required=True, default=None, description=None):
        super(RoleField, self).__init__(name,
                                        options=configuration.ROLES,
                                        required=required,
                                        default=default,
                                        description=description)

    def get_editable(self, dispatcher, user):
        """The document must not be locked.
        Allow only for 'admin' role, but disallow if the document
        is the predefined 'system' account."""
        if dispatcher.doc.get('locked'): return False
        return user.get('role') == 'admin' and \
               dispatcher.doc['name'] != 'system'

    def check_value(self, dispatcher, value):
        value = super(RoleField, self).check_value(dispatcher, value)
        if value not in configuration.ROLES:
            raise ValueError("invalid value '%s' for role field" % value)
        return value



class Account(Entity):
    """A user account in the system. An account has a specified role,
which determines the access privileges. The possible roles are:

* customer: May only view projects owned by the account.
* engineer: May edit samples and projects.
* manager: May add accounts and edit most entities in the system.
* admin: May do anything in the system.

"""

    fields = [AccountNameField('name', required=True, fixed=True,
                               description='Unique user account identifier.'
                               ' Cannot be changed once set.'),
              PasswordField('password'),
              RoleField('role', required=True, default='customer',
                        description='Access privilege role.'),
              StringField('fullname', size=40,
                          description="Full name as 'surname, given name'."),
              StringField('initials', size=4,
                          description='Initials of the full name.'),
              TextField('address'),
              StringField('email', size=60),
              TextField('description')]

    def view(self, page):
        self.view_fields(page)
        self.view_projects(page)
        self.view_worksets(page)
        self.view_attachments(page)
        self.view_log(page)
        self.view_locked(page)
        self.view_image(page)
        self.view_tags(page)
        self.view_xrefs(page)

    def view_worksets(self, page):
        "Produce the HTML workset list."
        page.append(H2('Worksets'))
        rows = [TR(TH('Workset'),
                   TH('# samples'),
                   TH('Timestamp'))]
        view = self.db.view('workset/operator', include_docs=True)
        for result in view[self.doc['name']]:
            doc = result.doc
            url = configuration.get_url('workset', doc['name'])
            workset = A(doc['name'], href=url)
            rows.append(TR(TD(workset),
                           TD(str(len(doc.get('samples', [])))),
                           TD(doc['timestamp'])))
        page.append(P(TABLE(border=1, *rows)))

    def view_projects(self, page):
        page.append(H2('Projects'))
        rows = [TR(TH('Project'),
                   TH('Label'),
                   TH('Timestamp'))]
        view = self.db.view('project/customer', include_docs=True)
        docs = [r.doc for r in view[self.doc['name']]]
        docs.sort(lambda i, j: cmp(i['name'], j['name']))
        for doc in docs:
            url = configuration.get_entity_url(doc)
            rows.append(TR(TD(A(doc['name'], href=url)),
                           TD(doc.get('label') or ''),
                           TD(doc.get('timestamp') or '')))
        page.append(P(TABLE(border=1, *rows)))

    def view_image(self, page):
        stubs = self.doc.get('_attachments', dict())
        for ext in ('.jpg', '.png'):
            filename = self.doc['name'] + ext
            if stubs.has_key(filename):
                page.meta.append(IMG(src=configuration.get_url('attachment',
                                                               self.doc.id,
                                                               filename)))
                return

    def get_editable_privilege(self, user):
        """A user may edit his own account.
        A 'manager' may edit an 'engineer' or 'customer' account."""
        role = user.get('role')
        if role == 'admin': return True
        if self.doc.id == user.id: return True
        if role == 'manager':
            return self.doc.get('role') in ('engineer', 'customer')
        return False


class AccountCreate(EntityCreate):

    entity_class = Account

    def get_privilege(self):
        return self.user.get('role') in ('admin', 'manager')


class Accounts(Dispatcher):
    "Accounts list page dispatcher."

    def get_viewable(self, user):
        "Everyone except customers may view the accounts list."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Accounts')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(Account.__doc__))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit', value='Create new account'),
                               method='GET',
                               action=configuration.get_url('account'))))

        rows = [TR(TH('Account'),
                   TH('Full name'),
                   TH('Role'),
                   TH('Initials'))]
        for result in self.db.view('account/name', include_docs=True):
            doc = result.doc
            ref = A(result.key,
                    href=configuration.get_url('account', result.key))
            rows.append(TR(TD(ref),
                           TD(result.value or ''),
                           TD(doc.get('role')),
                           TD(doc.get('initials') or '')))
        page.append(TABLE(border=1, *rows))

        page.write(response)
