""" slog: Simple sample tracker system.

Base entity class, with data field classes.

Per Kraulis
2011-02-08
"""

import logging, os.path, base64, quopri

from wireframe.response import *

from .dispatcher import *
from .fields import *


class Entity(Dispatcher):
    "Base entity class, with data field classes."

    fields = []                         # List of Field instances
    tool_classes = []                   # List of Tool subclasses

    @classmethod
    def get_field(cls, name):
        "Return the field instance by name."
        for field in cls.fields:
            if field.name == name: return field

    def get_url(self):
        "Return the absolute URL for this entity."
        return configuration.get_url(self.__class__.__name__.lower(),
                                     self.doc['name'])

    def prepare(self, request, response):
        super(Entity, self).prepare(request, response)
        entity = self.__class__.__name__.lower()
        name = request.path_named_values['name']
        try:
            self.doc = self.get_named_document(entity, name)
        except ValueError:
            raise HTTP_NOT_FOUND("entity %s %s" % (entity, name))

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title="%s %s" % (self.__class__.__name__,
                                               self.get_title()))
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(self.__doc__))
        page.set_context(self.doc)
        # Edit mode; allow change of data
        edit = request.get('edit')
        if edit:
            if edit == '_attachments':
                self.edit_attachments(page)
            elif edit == '_tags':
                self.edit_tags(page)
            elif edit == '_xrefs':
                self.edit_xrefs(page)
            else:
                self.edit_data_field(page, edit)
            page.log = ''             # Don't clutter view with useless log
        # View mode: display data
        else:
            self.view(page)
        page.write(response)

    def get_title(self):
        "Return the title to represent this entity."
        return self.doc['name']

    def view(self, page):
        "Produce the HTML page for GET."
        self.view_fields(page)
        self.view_attachments(page)
        self.view_tools(page)
        self.view_log(page)
        self.view_tags(page)
        self.view_xrefs(page)

    def view_fields(self, page):
        "HTML for the entity data fields."
        page.append(H2('Information'))
        rows = []
        for field in self.fields:
            rows.append(TR(TH(field.name),
                           TD(field.get_view(self)),
                           TD(field.get_edit_button(self)),
                           TD(field.get_description())))
        page.append(TABLE(border=1, *rows))

    def view_attachments(self, page):
        "HTML for the attachments list."
        page.append(H2('Attachments'))
        cells = [TH('Attachment'),
                 TH('Mimetype'),
                 TH('Size (bytes)')]
        if self.get_editable(self.user):
            cells.append(TD(FORM(INPUT(type='submit', value='Edit'),
                                 INPUT(type='hidden',
                                       name='edit', value='_attachments'),
                                 method='GET',
                                 action=self.get_url())))
        rows = [TR(*cells)]
        stubs = self.doc.get('_attachments', dict())
        for filename in sorted(stubs.keys()):
            rows.append(TR(TD(A(filename,
                                href=configuration.get_url('attachment',
                                                           self.doc.id,
                                                           filename))),
                           TD(stubs[filename]['content_type']),
                           TD(stubs[filename]['length'])))
        page.append(TABLE(border=1, *rows))

    def view_tools(self, page):
        "HTML for the tools list."
        page.append(H2('Tools'))
        rows = []
        for tool_class in self.tool_classes:
            tool = tool_class(self)
            disabled = not tool.is_enabled(self.doc)
            rows.append(TR(TH(str(tool)),
                           TD(FORM(INPUT(type='submit', value='Apply',
                                         disabled=disabled),
                                   INPUT(type='hidden', name='entity',
                                         value=tool.get_entity_tag(self.doc)),
                                   method='GET',
                                   action=tool.get_url())),
                           TD(utils.rst_to_html(tool.__doc__))))
        if not rows:
            rows.append(TR(TH(I('None'))))
        page.append(TABLE(*rows))

    def view_log(self, page):
        "HTML for the log list."
        rows = [TR(TH('Action'),
                   TH('Account'),
                   TH('Timestamp'),
                   TH('Comment'),
                   TH('Log document'))]
        view = self.db.view('log/docid_timestamp',
                            descending=True,
                            include_docs=True)
        for result in view[[self.doc.id, 'Z']:[self.doc.id, '']]:
            doc = result.doc
            rows.append(TR(TD(doc['action']),
                           TD(A(doc['account'],
                                href=configuration.get_url('account',
                                                           doc['account']))),
                           TD(doc['timestamp']),
                           TD(doc.get('comment') or ''),
                           TD(A(doc.id,
                                href=configuration.get_url('doc', doc.id)))))
        page.log = DIV(H2('Log'),
                       TABLE(border=1, *rows))

    def view_tags(self, page):
        tags = self.doc.get('tags', [])
        if self.get_editable(self.user):
            edit = FORM(INPUT(type='submit', value='Edit'),
                        INPUT(type='hidden', name='edit', value='_tags'),
                        method='GET',
                        action=self.get_url())
        else:
            edit = ''
        if tags:
            tags.sort()
            first = tags[0]
        else:
            first = '-'
        rowspan = max(1, len(tags))
        rows = [TR(TH('Tags', rowspan=rowspan),
                   TD(first),
                   TD(edit, rowspan=rowspan))]
        for tag in tags[1:]:
            rows.append(TR(TD(tag)))
        page.meta.append(DIV(TABLE(klass='tags', *rows)))

    def view_xrefs(self, page):
        xrefs = self.doc.get('xrefs', [])
        if self.get_editable(self.user):
            edit = FORM(INPUT(type='submit', value='Edit'),
                        INPUT(type='hidden', name='edit', value='_xrefs'),
                        method='GET',
                        action=self.get_url())
        else:
            edit = ''
        if xrefs:
            xrefs.sort()
            xref = xrefs[0]
            first = A(xref.get('title') or xref['uri'], href=xref['uri'])
        else:
            first = '-'
        rows = [TR(TH('Xrefs', rowspan=len(xrefs)),
                   TD(first),
                   TD(edit, rowspan=len(xrefs)))]
        for xref in xrefs[1:]:
            rows.append(TR(TD(A(xref.get('title') or xref['uri'],
                                href=xref['uri']))))
        page.meta.append(DIV(TABLE(klass='xrefs', *rows)))

    def edit_attachments(self, page):
        self.check_editable(self.user)
        page.append(H2('Edit attachments'))
        rows = [TR(TD(),
                   TH('Filename'),
                   TH('Mimetype'),
                   TH('Size'))]
        stubs = self.doc.get('_attachments', dict())
        for filename in sorted(stubs.keys()):
            rows.append(TR(TD(INPUT(type='checkbox',
                                    name='_attachment_delete',
                                    value=filename)),
                           TD(A(filename,
                                href=configuration.get_url('attachment',
                                                           self.doc.id,
                                                           filename))),
                           TD(stubs[filename]['content_type']),
                           TD(stubs[filename]['length'])))
        page.append(P(FORM(TABLE(
            TR(TH('Delete'),
               TD(TABLE(border=1, *rows))),
            TR(TH('Comment'),
               TD(TEXTAREA(name='comment', cols=60, rows=3))),
            TR(TD(),
               TD(INPUT(type='submit', value='Delete checked')))),
                           method='POST',
                           action=self.get_url())))
        page.append(P(FORM(TABLE(
            TR(TH('Attach file'),
               TD(INPUT(type='file', size=40, name='_attachment'))),
            TR(TH('Comment'),
               TD(TEXTAREA(name='comment', cols=60, rows=3))),
            TR(TD(),
               TD(INPUT(type='submit', value='Upload')))),
                           enctype='multipart/form-data',
                           method='POST',
                           action=self.get_url())))
        page.append(P(FORM(INPUT(type='submit', value='Cancel'),
                           method='GET',
                           action=self.get_url())))

    def edit_tags(self, page):
        self.check_editable(self.user)
        page.append(H2('Edit tags'))
        tags = self.doc.get('tags', [])
        if tags:
            tags.sort()
            tag = tags[0]
            rows = [TR(TH('Current tags', rowspan=len(tags)),
                       TD(INPUT(type='checkbox',name='_tag_remove',value=tag)),
                       TD(tag))]
            rows.extend([TR(TD(INPUT(type='checkbox',
                                     name='_tag_remove', value=tag)),
                            TD(tag)) for tag in tags[1:]])
            rows.append(TR(TD(),
                           TD(INPUT(type='submit', value='Remove checked'),
                              colspan=2)))
            page.append(FORM(TABLE(klass='tags', *rows),
                             method='POST',
                             action=self.get_url()))
            page.append(P())
        page.append(FORM(TABLE(
            TR(TH('New tags'),
               TD(TEXTAREA(name='_tags_add', cols=20, rows=8))),
            TR(TD(),
               TD(INPUT(type='submit', value='Add')))),
                         method='POST',
                         action=self.get_url()))
        page.append(P(FORM(INPUT(type='submit', value='Cancel'),
                           method='GET',
                           action=self.get_url())))

    def edit_xrefs(self, page):
        self.check_editable(self.user)
        page.append(H2('Edit xrefs'))
        xrefs = self.doc.get('xrefs', [])
        if xrefs:
            xrefs.sort()
            xref = xrefs[0]
            rows = [TR(TH('Current xrefs', rowspan=len(xrefs)),
                       TD(INPUT(type='checkbox',
                                name='_xref_remove', value=xref['uri'])),
                       TD(A(xref.get('title') or xref['uri'],
                            href=xref['uri'])))]
            rows.extend([TR(TD(INPUT(type='checkbox',
                                     name='_xref_remove', value=xref['uri'])),
                            TD(A(xref.get('title') or xref['uri'],
                                 href=xref['uri'])))
                         for xref in xrefs[1:]])
            rows.append(TR(TD(),
                           TD(INPUT(type='submit', value='Remove checked'),
                              colspan=2)))
            page.append(FORM(TABLE(klass='xrefs', *rows),
                             method='POST',
                             action=self.get_url()))
            page.append(P())
        page.append(FORM(TABLE(
            TR(TH('New xref'),
               TD('URI'),
               TD(INPUT(type='text', name='_xref_add_uri'))),
            TR(TD(),
               TD('Title'),
               TD(INPUT(type='text', name='_xref_add_title'))),
            TR(TD(),
               TD(INPUT(type='submit', value='Add')))),
                         method='POST',
                         action=self.get_url()))
        page.append(P(FORM(INPUT(type='submit', value='Cancel'),
                           method='GET',
                           action=self.get_url())))

    def edit_data_field(self, page, name):
        for field in self.fields:
            if field.name == name: break
        else:
            raise HTTP_BAD_REQUEST("No such editable field '%s'." % name)
        self.check_editable(self.user)
        field.check_editable(self, self.user)
        page.append(H2('Edit information field'))
        page.append(TABLE(TR(TD(field.get_edit_form(self))),
                          TR(TD(FORM(INPUT(type='submit', value='Cancel'),
                                     method='GET',
                                     action=self.get_url())))))

    def POST(self, request, response):
        "Modify according to which CGI inputs were provided."
        self.check_editable(self.user)
        self.check_revision(request)

        # Save initial document state
        try:
            initial = dict(self.doc)
        except (AttributeError, TypeError):
            initial = None

        # Get user comment, if any
        try:
            comment = request.cgi_fields['comment'].value
        except KeyError:
            comment = None
        else:
            comment = comment.strip()
            comment = comment.replace('\r\n', '\n')

        # Data fields
        modified = []                   # Names of fields that were modified
        for field in self.fields:
            if not field.get_editable(self, self.user): continue
            try:
                self.doc[field.name] = field.get_value(self, request)
            except KeyError:            # No such field in CGI inputs
                pass
            except ValueError, msg:
                raise HTTP_BAD_REQUEST(str(msg))
            else:
                modified.append(field.name)
        if modified:
            if initial is None:
                action = 'created'
            else:
                action = "modified %s" % ', '.join(modified)
            map(self.on_field_modified, modified)
            id, rev = self.db.save(self.doc) # Create or update
            self.doc = self.db[id]           # Get fresh instance
            self.log(self.doc.id, action, initial=initial, comment=comment)

        # Delete attachments
        stubs = self.doc.get('_attachments', dict())
        for filename in request.cgi_fields.getlist('_attachment_delete'):
            if stubs.has_key(filename):
                initial = dict(self.doc)
                self.db.delete_attachment(self.doc, filename)
                self.doc = self.db[self.doc.id] # Get fresh instance
                comment2 = "filename %s" % filename
                if comment:
                    comment2 += '; ' + comment
                self.log(self.doc.id,
                         'deleted attachment',
                         initial=initial,
                         comment=comment2)

        # Upload attachment
        try:
            field = request.cgi_fields['_attachment']
            if not field.filename: raise KeyError
        except KeyError:
            pass
        else:
            initial = dict(self.doc)
            filename = os.path.basename(field.filename)
            content = field.file.read()
            try:
                encoding = field.headers['content-transfer-encoding'].lower()
            except KeyError:
                pass
            else:
                if encoding == 'base64':
                    content = base64.standard_b64decode(content)
                elif encoding == 'quoted-printable':
                    content = quopri.decodestring(content)
            self.db.put_attachment(self.doc,
                                   content,
                                   filename,
                                   field.type)
            self.doc = self.db[self.doc.id] # Get fresh instance
            comment2 = "filename %s" % filename
            if comment:
                comment2 += '; ' + comment
            self.log(self.doc.id,
                     'uploaded attachment',
                     initial=initial,
                     comment=comment2)

        # Remove tags
        initial = dict(self.doc)
        tags = set(self.doc.get('tags', []))
        original = tags.copy()
        for tag in request.cgi_fields.getlist('_tag_remove'):
            tags.discard(tag)
        if tags != original:
            self.doc['tags'] = list(tags)
            id, rev = self.db.save(self.doc) # Create or update
            self.doc = self.db[id]           # Get fresh instance
            self.log(self.doc.id,
                     'removed tags',
                     initial=initial)

        # Add tags
        initial = dict(self.doc)
        tags = set(self.doc.get('tags', []))
        original = tags.copy()
        try:
            new = request.cgi_fields['_tags_add'].value.strip()
            if not new: raise KeyError
        except KeyError:
            pass
        else:
            for tag in new.split():
                tags.add(tag)
            if tags != original:
                self.doc['tags'] = list(tags)
                id, rev = self.db.save(self.doc) # Create or update
                self.doc = self.db[id]           # Get fresh instance
                self.log(self.doc.id,
                         'added tags',
                         initial=initial)

        # Remove xrefs
        initial = dict(self.doc)
        xrefs = dict([(x['uri'], x.get('title'))
                      for x in self.doc.get('xrefs', [])])
        original = xrefs.copy()
        for uri in request.cgi_fields.getlist('_xref_remove'):
            try:
                del xrefs[uri]
            except KeyError:
                pass
        if xrefs != original:
            result = []
            for uri, title in sorted(xrefs.items()):
                result.append(dict(uri=uri, title=title))
            self.doc['xrefs'] = result
            id, rev = self.db.save(self.doc) # Create or update
            self.doc = self.db[id]           # Get fresh instance
            self.log(self.doc.id,
                     'removed xrefs',
                     initial=initial)

        # Add xrefs
        initial = dict(self.doc)
        xrefs = dict([(x['uri'], x.get('title'))
                      for x in self.doc.get('xrefs', [])])
        original = xrefs.copy()
        try:
            uri = request.cgi_fields['_xref_add_uri'].value.strip()
            if not uri: raise KeyError
        except KeyError:
            pass
        else:
            try:
                title = request.cgi_fields['_xref_add_title'].value.strip()
                if not title: raise KeyError
            except KeyError:
                title = None
            xrefs[uri] = title
            if xrefs != original:
                result = []
                for uri, title in sorted(xrefs.items()):
                    result.append(dict(uri=uri, title=title))
                self.doc['xrefs'] = result
                id, rev = self.db.save(self.doc) # Create or update
                self.doc = self.db[id]           # Get fresh instance
                self.log(self.doc.id,
                         'added xref',
                         initial=initial)

        # Perform specified actions, if any:
        # The action "X" causes the method "action_X" to be executed
        # with the request instance as argument. If that action modifies
        # the document of the entity, then it must also save the document.
        for action in request.cgi_fields.getlist('action'):
            try:
                method = getattr(self, "action_%s" % action)
            except AttributeError:
                raise HTTP_BAD_REQUEST("no such action '%s'" % action)
            method(request)

        # And display result
        self.GET(request, response)

    def on_field_modified(self, name):
        """This method is called when the field of the specified name
        has been changed. This happens *before* the modification has
        been saved in the entity's document."""
        pass


class EntityCreate(Dispatcher):
    "Base page for creating an entity instance."

    entity_class = None

    def get_privilege(self):
        "Return True of the logged-in user is allowed to create the entity."
        raise NotImplementedError

    def check_privilege(self):
        if not self.get_privilege():
            raise HTTP_FORBIDDEN("User '%s' may not create %s."
                                 % (self.user['name'],
                                    self.entity_class.__name__.lower()))

    def get_url(self, name=None):
        return configuration.get_url(self.entity_class.__name__.lower(),
                                     name=name)

    def GET(self, request, response):
        "Display the CGI form for creating the entity."
        self.check_privilege()

        page = HtmlPage(self,
                        title="Create %s" % self.entity_class.__name__.lower())

        rows = []
        for field in self.entity_class.fields:
            rows.append(TR(TH(field.name),
                           TD(field.get_create_form_field(self)),
                           TD(I(field.required and 'required' or 'optional')),
                           TD(field.get_description())))

        page.append(FORM(TABLE(border=1, *rows),
                         P(INPUT(type='submit', value='Create')),
                         method='POST',
                         action=self.get_url()))

        page.write(response)

    def POST(self, request, response):
        "Create the entity given the CGI input fields."
        self.check_privilege()

        doc = dict()
        for field in self.entity_class.fields:
            try:
                doc[field.name] = field.get_value(self, request, required=False)
            except KeyError:            # No such field in CGI inputs
                pass
            except ValueError, msg:
                raise HTTP_BAD_REQUEST(str(msg))

        entity = self.entity_class.__name__.lower()
        try:
            self.get_named_document(entity, doc['name'])
        except ValueError:              # Does not exist; OK
            pass
        else:
            raise HTTP_BAD_REQUEST("%s '%s' exists already"
                                   % (entity, doc['name']))

        self.setup(doc)
        doc.update(dict(_id=utils.id_uuid(),
                        entity=entity,
                        timestamp=utils.now_iso()))
        id, rev = self.db.save(doc)
        self.log(id, 'created', initial=None)
        raise HTTP_SEE_OTHER(Location=self.get_url(doc['name']))

    def setup(self, doc):
        "Modify the contents of the as yet unsaved document for the new entity."
        pass
