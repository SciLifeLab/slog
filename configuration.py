""" slog: Simple sample tracker system.

Configuration.

Per Kraulis
2011-02-07
"""

import socket, re, os.path

import couchdb


HOSTNAME = socket.gethostname()

VERSION = '1.0'

if HOSTNAME == 'maggie':
    URL_BASE = 'http://test2.scilifelab.se/slog'
else:
    URL_BASE = 'http://localhost/slog'

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

VALID_NAME_RX = re.compile(r'^[a-z0-9][a-z0-9_-]*$', re.IGNORECASE)

ROLES = ['customer',  # The PI of a project. Can only read his own stuff.
         'engineer',  # Lab engineer working on the samples in projects.
         'manager',   # Lab manager. May create projects.
         'admin'      # System administrator. Is allowed to do anything.
         ]



def get_db():
    if HOSTNAME == 'maggie':
        db = couchdb.Server("http://maggie.scilifelab.se:5984/")['slog']
        ## db.resource.credentials = ('admin', '250znW6G/Z8!o')
    else:
        db = couchdb.Server()['slog']
    return db

def get_url(entity, name=None, attachment=None):
    "Return the URL for the item of given entity and name."
    assert entity                       # Entity type
    parts = [URL_BASE, entity]
    if name:
        parts.append(name)
    if attachment:
        parts.append(attachment)
    return '/'.join(parts)

def get_entity_url(doc):
    assert isinstance(doc, dict)
    return get_url(doc['entity'], name=doc['name'])

def get_static_path(filename):
    path = os.path.normpath(os.path.join(STATIC_DIR, filename))
    if not path.startswith(STATIC_DIR):
        raise ValueError('access outside of static directory')
    return path
    

if __name__ == '__main__':
    print get_db().info()
