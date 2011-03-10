""" slog: Simple sample tracker system.

Fix up all documents.

Per Kraulis
2011-02-18
"""

from slog import configuration, utils


def change_multiplex_index_to_multiplex_label(doc):
    try:
        value = doc.pop('multiplex_index')
    except KeyError:
        return
    doc['multiplex_label'] = value
    return doc

def change_customername_to_altname(doc):
    try:
        customername = doc.pop('customername')
    except KeyError:
        return
    doc['altname'] = customername
    return doc

def change_owner_to_operator(doc):
    try:
        owner = doc.pop('owner')
    except KeyError:
        return
    doc['operator'] = owner
    return doc

def change_sample_received_to_available(doc):
    if doc.get('entity') != 'sample': return
    try:
        status = doc['status']
    except KeyError:
        return
    try:
        received = status.pop('received')
    except KeyError:
        return
    status['available'] = received
    return doc

def change_project_started_to_status(doc):
    if doc.get('entity') != 'project': return
    try:
        started = doc.pop('started')
    except KeyError:
        return
    if started:
        doc['status']['started'] = dict(value='yes', timestamp=utils.now_iso())
    return doc

def change_sample_status_received(doc):
    if doc.get('entity') != 'sample': return
    try:
        received = doc.pop('received')
    except KeyError:
        return
    status = doc.get('status', dict())
    if received:
        status['received'] = dict(timestamp=received, value='yes')
    doc['status'] = status
    return doc

def correct_status_field(doc):
    try:
        doc.pop('statuses')
    except KeyError:
        return
    return doc

def update_status_field(doc):
    status = doc.get('status')
    if isinstance(status, basestring):
        statuses = {status: dict(timestamp=utils.now_iso(), value='yes')}
        doc['status'] = statuses
        return doc
    elif isinstance(status, list):
        statuses = dict()
        for old in status:
            name = old['name']
            new = dict()
            for key in ['value', 'timestamp']:
                try:
                    new[key] = old[key]
                except KeyError:
                    pass
            statuses[name] = new
        doc['status'] = statuses
        return doc

def change_experiment_to_application(doc):
    entity = doc.get('entity')
    if entity == 'project':
        try:
            doc['application'] = doc['experiment']
        except KeyError:
            pass
        else:
            del doc['experiment']
        return doc
    elif entity == 'experiment':
        doc['entity'] = 'application'
        return doc

def change_species_to_reference(doc):
    try:
        species = doc['species']
    except KeyError:
        return
    doc['reference'] = species
    del doc['species']
    return doc

def add_initials_to_account(doc):
    if doc.get('entity') != 'account': return
    if doc.has_key('initials'): return
    try:
        fullname = doc['fullname']
    except KeyError:
        return
    parts = [s.strip() for s in fullname.split(',')]
    parts.reverse()
    doc['initials'] = ''.join([s[0] for s in parts])
    return doc

def change_document_to_docid(doc):
    "For a document having type 'log' change the field 'document' to 'docid'."
    if doc.get('entity') != 'log': return
    try:
        doc['docid'] = doc['document']
    except KeyError:
        return
    del doc['document']
    return doc

def change_type_to_entity(doc):
    """For a document having a key 'type' change it to 'entity',
    except for documents already having an 'entity' key."""
    try:
        type = doc['type']
    except KeyError:
        return
    if doc.has_key('entity'): return
    doc['entity'] = type
    del doc['type']
    return doc

def for_all_documents(modify):
    """For all documents, apply the given function 'modify',
    which makes inline changes to the document, and returns
    the document if it was changed, or None if not.
    Return a list of tuples (id, rev) for all changed documents."""
    db = configuration.get_db()
    result = []
    for row in db.view('_all_docs'):
        doc = modify(db[row.id])
        if doc:
            result.append(db.save(doc))
    return result
    

if __name__ == '__main__':
    for id, rev in for_all_documents(change_owner_to_operator):
        print id, rev
    for id, rev in for_all_documents(change_customername_to_altname):
        print id, rev
    for id, rev in for_all_documents(change_multiplex_index_to_multiplex_label):
        print id, rev
