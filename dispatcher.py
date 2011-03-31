""" slog: Simple sample tracker system.

Base dispatcher class.

Per Kraulis
2011-02-02
"""

import json, mimetypes, logging

import couchdb

from wireframe.dispatcher import BaseDispatcher
from wireframe.response import *
from wireframe import basic_authenticate

from . import configuration, utils
from .html_page import *


class Dispatcher(BaseDispatcher):

    def prepare(self, request, response):
        self.db = configuration.get_db()
        try:
            user, password = basic_authenticate.decode(request)
            self.user = self.get_named_document('account', user)
            if self.user.get('password') != utils.hexdigest(password):
                raise ValueError
        except ValueError:
            raise HTTP_UNAUTHORIZED_BASIC_CHALLENGE(realm='slog')
        self.user_agent = request.environ.get('HTTP_USER_AGENT')

    def get_named_document(self, entity, name):
        """Get the document for the given entity and name.
        Raise ValueError if not found."""
        view = self.db.view("%s/name" % entity, include_docs=True)
        result = view[name]
        if len(result) != 1:
            raise ValueError("no such %s document '%s'" % (entity, name))
        return result.rows[0].doc

    def get_viewable(self, user):
        """Is the given user allowed to view this page?
        By default, any user may view anything."""
        return True

    def check_viewable(self, user):
        "Check that the given user is allowed to view this page."
        if not self.get_viewable(user):
            raise HTTP_FORBIDDEN("User '%s' may not view page." % user['name'])

    def get_editable(self, user):
        """Is the given user allowed to edit this page?
        By default, only the role 'admin' is allowed to edit any page."""
        return user.get('role') == 'admin'

    def check_editable(self, user):
        "Check that the given user is allowed to edit this page."
        if not self.get_editable(user):
            raise HTTP_FORBIDDEN("User '%s' may not edit page." % user['name'])

    def check_revision(self, request):
        """Check that the revision of the current document matches
        the revision of the document on which the edit was based."""
        assert hasattr(self, 'doc'), "dispatcher document must be set"
        try:
            rev = request.cgi_fields['_rev'].value
        except KeyError:
            return
        if rev != self.doc.rev:
            raise HTTP_CONFLICT("Your edit was based on an entity document that"
                                " was changed by someone else after you loaded"
                                " the edit page; the document revisions do"
                                " not match. Go back to the entity ('Cancel')"
                                " and retry your edit...")

    def get_selected_operator(self, request):
        "Get the specified operator, or 'all'. If none, then logged-in user."
        try:
            operator = request.cgi_fields['operator'].value.strip()
            if not operator: raise KeyError
        except KeyError:
            operator = self.user['name']
        else:
            if operator == 'all':
                operator = None
        return operator

    def get_operator_select_form(self, entities, operator=None):
        "Return the HTML form for selecting the operator to show entities of."
        options = [OPTION('all')]
        for result in self.db.view('account/name'):
            if operator == result.key:
                options.append(OPTION(result.key, selected=True))
            else:
                options.append(OPTION(result.key))
        return FORM(SELECT(name='operator', *options),
                    INPUT(type='submit', value='Select operator'),
                    method='GET',
                    action=configuration.get_url(entities))

    def put_attachment(self, content, filename):
        "Put the attachment onto the current document."
        assert hasattr(self, 'doc'), "dispatcher document must be set"
        self.db.put_attachment(self.doc, content, filename=filename)

    def log(self, docid, action, initial=None, comment=None):
        "Add a log entry for a given document."
        self.db.save(dict(_id=utils.id_uuid(),
                          entity='log',
                          docid=docid,
                          action=action,
                          account=self.user['name'],
                          initial=initial,
                          comment=comment,
                          timestamp=utils.now_iso()))


class Id(Dispatcher):
    "Redirect from the id URL to the entity URL."

    def GET(self, request, response):
        try:
            id = request.path_named_values['id']
        except KeyError:
            raise HTTP_NOT_FOUND
        try:
            doc = self.db[id]
        except couchdb.ResourceNotFound:
            raise HTTP_NOT_FOUND
        try:
            entity = doc['entity']
            name = doc['name']
        except KeyError:
            raise HTTP_NOT_FOUND
        url = "%s/%s/%s" % (configuration.site.URL_BASE, entity, name)
        raise HTTP_SEE_OTHER(Location=url)


class Doc(Dispatcher):
    "Return the JSON document for the given docid."

    indent = 2                          # For development
    ## indent = None                       # For production

    def get_viewable(self, user):
        return user.get('role') in ('admin', 'manager')

    def GET(self, request, response):
        self.check_viewable(self.user)
        id = request.path_named_values['id']
        try:
            doc = self.db[id]
        except couchdb.ResourceNotFound:
            raise HTTP_NOT_FOUND
        response['Content-Type'] = 'text/plain;charset=utf-8'
        response.append(json.dumps(doc, indent=self.indent))


class Static(Dispatcher):
    "Return a static file."

    def GET(self, request, response):
        filename = request.path_named_values['filename']
        try:
            data = open(configuration.get_static_path(filename)).read()
        except (ValueError, IOError):
            raise HTTP_NOT_FOUND
        mimetype = mimetypes.guess_type(filename)
        if mimetype:
            response['Content-Type'] = mimetype
        response.append(data)


class Attachment(Dispatcher):
    "Handle attachments to documents."

    def get_document(self, request):
        id = request.path_named_values['id']
        try:
            self.doc = self.db[id]
        except couchdb.ResourceNotFound:
            raise HTTP_NOT_FOUND

    def get_viewable(self, user):
        """All except customer may view the attachment.
        Customer may view only if owner of the document.
        """
        if user.get('role') in ('admin', 'manager', 'engineer'):
            return True
        return user['name'] == self.doc.get('owner')

    def get_editable(self, user):
        """The parent document must not be locked.
        All except customer may edit the attachment.
        """
        if self.doc.get('locked'): return False
        return user.get('role') in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.get_document(request)
        self.check_viewable(self.user)
        filename = request.path_named_values['filename']
        try:
            stub = self.doc['_attachments'][filename]
        except KeyError:
            raise HTTP_NOT_FOUND
        infile = self.db.get_attachment(self.doc, filename)
        if not infile:
            raise HTTP_NOT_FOUND
        response['Content-Type'] = stub['content_type']
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        response.append(infile.read())

    def PUT(self, request, response):
        self.get_document(request)
        self.check_editable(self.user)
        filename = request.path_named_values['filename']
        initial = dict(self.doc)
        self.db.put_attachment(self.doc,
                               request.file.read(),
                               filename)
        self.log(self.doc.id,
                 'uploaded attachment',
                 initial=initial,
                 comment="filename %s" % filename)
        raise HTTP_NO_CONTENT

    def DELETE(self, request, response):
        self.get_document(request)
        self.check_editable(self.user)
        filename = request.path_named_values['filename']
        initial = dict(self.doc)
        self.db.delete_attachment(self.doc, filename)
        self.log(self.doc.id,
                 'deleted attachment',
                 initial=initial,
                 comment="filename %s" % filename)
        raise HTTP_NO_CONTENT
