""" slog: Simple sample tracker system.

Configuration to specify version and site.

Per Kraulis
2011-02-07
2011-03-29  split out site-specific config info
"""

import socket, sys, re, os.path

import couchdb


VERSION = '1.0'

STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')

VALID_NAME_RX = re.compile(r'^[a-z0-9][a-z0-9_-]*$', re.IGNORECASE)

ROLES = ['customer',  # The PI of a project. Can only read his own stuff.
         'engineer',  # Lab engineer working on the samples in projects.
         'manager',   # Lab manager. May create projects.
         'admin'      # System administrator. Is allowed to do anything.
         ]

# Load the site-specific configuration info.
MODULENAME = "slog.site_%s" % socket.gethostname()
try:
    __import__(MODULENAME)
except ImportError:
    MODULENAME = 'slog.site_default'
    __import__(MODULENAME)
site = sys.modules[MODULENAME]


def get_db():
    "Get the database instance, possibly with credentials loaded."
    db = couchdb.Server(site.COUCHDB_SERVER)[site.COUCHDB_DATABASE]
    if site.COUCHDB_USER and site.COUCHDB_PASSWORD:
        db.resource.http.add_credentials(site.COUCHDB_USER,
                                         site.COUCHDB_PASSWORD)
    return db

def get_url(entity, name=None, attachment=None):
    "Return the URL for the item of given entity and name."
    assert entity                       # Entity type
    parts = [site.URL_BASE, entity]
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
