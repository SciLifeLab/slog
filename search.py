""" slog: Simple sample tracker system.

Search dispatcher.

Per Kraulis
2011-02-15
"""

import logging

from wireframe.response import *

from .dispatcher import *


class Search(Dispatcher):
    "Search dispatcher."

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Search')

        try:
            key = request.cgi_fields['key'].value.strip()
        except KeyError:
            key = None

        page.search = ''
        page.append(P(FORM(INPUT(type='text', name='key', value=key or ''),
                           INPUT(type='submit', value='Search'),
                           method='GET',
                           action=configuration.get_url('search'))))
        result = set()
        if key:
            # Search fields occurring in all entities
            for entity in ['account',
                           'project',
                           'sample',
                           'workset',
                           'application',
                           'protocol',
                           'task',
                           'instrument']:
                # Search 'name' field
                logging.info("search index %s", entity)
                view = self.db.view("%s/name" % entity)
                for row in view[key : "%sZZZZZZ" % key]:
                    result.add((entity, row.key))
                # Search 'tags' field
                view = self.db.view("%s/tag" % entity)
                for row in view[key : "%sZZZZZZ" % key]:
                    result.add((entity, row.value))
            # Special case for altname in Sample entities
            view = self.db.view("sample/altname")
            for row in view[key : "%sZZZZZZ" % key]:
                result.add((entity, row.key))
        rows = []
        for entity, name in sorted(result):
            url = configuration.get_url(entity, name)
            rows.append(TR(TD(entity.capitalize()),
                           TD(A(name, href=url))))
        if not rows:
            rows.append(TR(TD('[nothing found]')))
        page.append(TABLE(*rows))

        page.write(response)
