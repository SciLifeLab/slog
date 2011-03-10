""" slog: Simple sample tracker system.

Projects list page dispatcher.

Per Kraulis
2011-02-05
"""

import logging

import utils
from .dispatcher import *


class Projects(Dispatcher):
    "Projects list page dispatcher."

    def get_viewable(self, user):
        "Everyone except customers may view the projects list."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def get_editable(self, user):
        "Everyone except customers may create a project."
        return user.get('role') in ('admin', 'manager', 'engineer')

    def GET(self, request, response):
        self.check_viewable(self.user)
        page = HtmlPage(self, title='Projects')

        if self.get_editable(self.user):
            page.append(FORM(INPUT(type='submit', value='Create new project'),
                             method='GET',
                             action=configuration.get_url('project')))
        page.append(P())

        counts = dict()
        for result in self.db.view('sample/project_count', group=True):
            counts[result.key] = result.value
        rows = [TR(TH('Project'),
                   TH('Title'),
                   TH('Customer'),
                   TH('Status'),
                   TH('Started'),
                   TH('# Samples'),
                   TH('Timestamp'))]
        view = self.db.view('project/timestamp',
                            descending=True,
                            include_docs=True)
        for result in view:
            doc = result.doc
            project = A(doc['name'],
                        href=configuration.get_url('project', doc['name']))
            customer = doc.get('customer')
            if customer:
                customer = A(customer,
                             href=configuration.get_url('account', customer))
            rows.append(TR(TD(project),
                           TD(result.value or ''),
                           TD(customer),
                           TD(doc.get('status')),
                           TD(doc.get('started', 'not yet')),
                           TD(counts.get(doc['name'], 0)),
                           TD(result.key)))
        page.append(TABLE(border=1, *rows))

        page.write(response)
