""" slog: Simple sample tracker system.

Load or update the design documents into the database.

Per Kraulis
2011-02-13
"""

import os, sys

from slog.load import get_db, put_document


def load_designs(root='designs', dirs=[]):
    db = get_db()
    if not dirs:
        dirs = os.listdir(root)
    for design in dirs:
        views = dict()
        doc = dict(_id="_design/%s" % design, views=views)
        path = os.path.join(root, design)
        if not os.path.isdir(path): continue
        path = os.path.join(root, design, 'views')
        for filename in os.listdir(path):
            name, ext = os.path.splitext(filename)
            if ext != '.js': continue
            with open(os.path.join(path, filename)) as codefile:
                code = codefile.read()
            if name.startswith('map_'):
                name = name[len('map_'):]
                key = 'map'
            elif name.startswith('reduce_'):
                name = name[len('reduce_'):]
                key = 'reduce'
            else:
                key = 'map'
            views.setdefault(name, dict())[key] = code
        put_document(doc)


if __name__ == '__main__':
    load_designs(dirs=sys.argv[1:])
