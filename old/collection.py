""" slog: Simple sample tracker system.

Collection entity and dispatcher.

Per Kraulis
2011-03-07
"""

import utils
from .entity import *


class CollectionNameField(NameField):
    "Name must be unique among collections."

    def check_value(self, dispatcher, value):
        value = super(CollectionNameField, self).check_value(dispatcher, value)
        try:
            dispatcher.get_named_document('collection', value)
        except ValueError:
            return value
        else:
            raise ValueError("Collection name '%s' is already in use" % value)


class CollectionField(Field):
    "Collection of sample references."

    def get_view(self, entity):
        collection = entity.doc.get(self.name) or dict()
        n_rows = collection.get('rows')
        n_columns = collection.get('columns')
        n_multiplex = collection.get('multiplex')
        rows = [TR(TH('Rows'),
                   TD(str(n_rows is not None and n_rows or '-'))),
                TR(TH('Columns'),
                   TD(str(n_columns is not None and n_columns or '-'))),
                TR(TH('Multiplex'),
                   TD(str(n_multiplex is not None and n_multiplex or '-')))]
        rows.append(TR(TH('Grid'),
                       TD(I('not implemented'))))
        return TABLE(*rows)


class Collection(Entity):
    """A set of samples to be handled collectively.
It has the following properties:

* Dynamic; samples may be added or removed.
* Non-exclusive; a sample may be a member of any number of collections.
* Ordered; the samples are placed in a grid of rows, columns and multiplex.

"""

    fields = [CollectionNameField('name', required=True, fixed=True,
                                  description='Unique collection identifier.'
                                  ' Cannot be changed once set.'),
              ReferenceField('operator', 'account',
                             required=True,
                             default=utils.get_login_account,
                             description='The user account responsible'
                             ' for this collection.'),
              PositiveIntegerField('rows', required=False,
                                   description='Number of rows in the grid.'),
              PositiveIntegerField('columns', required=False,
                                   description='Number of columns in the grid.'),
              PositiveIntegerField('multiplex', required=False,
                                   description='Number of multiplexing in the grid.'),
              CollectionField('samples',
                              required=True,
                              description='The set of samples.'),
              TextField('description')]


class CollectionCreate(EntityCreate):
    "Collection creation dispatcher."

    entity_class = Collection

    def get_privilege(self):
        return self.user.get('role') in ('admin', 'manager', 'engineer')


class Collections(Dispatcher):
    "Collections list page dispatcher"

    def get_viewable(self, user):
        "Everyone except customers may view the collections list."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def get_editable(self, user):
        "Everyone except customers may create a collection."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Collections')
        page.header = DIV(H1(page.title),
                          utils.rst_to_html(Collection.__doc__))

        if self.get_editable(self.user):
            page.append(P(FORM(INPUT(type='submit',
                                     value='Create new collection'),
                               method='GET',
                               action=configuration.get_url('collection'))))

        operator = self.get_selected_operator(request)
        page.append(P(self.get_operator_select_form('collections', operator)))

        if operator:
            view = self.db.view('collection/operator')
            result = view[operator]
        else:
            result = self.db.view('collection/name')
        collections = [r.value for r in result]
        collections.sort()

        rows = [TR(TH('Collection')]
        for collection in collections:
            rows.append(TR(TD(A(collection,
                                href=configuration.get_url('collection',
                                                           collection)))))
        page.append(TABLE(border=1, *rows))

        page.write(response)
