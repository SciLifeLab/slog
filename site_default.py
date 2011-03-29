""" slog: Simple sample tracker system.

Site-dependent configuration for a default machine.

This works if:
1) The Apache and CouchDB servers are run locally.
2) The database is called 'slog'.
3) There is no login for accessing the CouchDB system
   (so-called admin party mode).

This is only valid for test or development situations.
Make a copy of this file called 'site_{hostname}.py',
where {hostname} is the value returned by the function
'gethostname' in the standard module 'socket'.

Per Kraulis
2011-03-29
"""

NETLOC   = 'localhost'
PATH     = '/slog'
BASE     = NETLOC + PATH
URL_BASE = "http://%s" % BASE

COUCHDB_SERVER   = 'http://localhost:5984/'
COUCHDB_DATABASE = 'slog'
COUCHDB_USER     = None
COUCHDB_PASSWORD = None
