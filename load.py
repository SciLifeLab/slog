""" slog: Simple sample tracker system.

Load initial documents into the database.

Per Kraulis
2011-02-01
"""

import couchdb

from slog import utils
from slog.configuration import get_db


def put_document(doc):
    "Add or update the given dictionary as a document."
    db = get_db()
    if not doc.has_key('_id'):
        doc['_id'] = utils.id_uuid()
    try:
        (id, rev) = db.save(doc)
    except couchdb.http.ResourceConflict:
        doc['_rev'] = db.revisions(doc['_id']).next().rev
        (id, rev) = db.save(doc)
    return (id, rev)
