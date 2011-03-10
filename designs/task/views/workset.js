/* Index all task documents by protocol.
   Value: null. */
function(doc) {
    if (doc.entity !== 'task') return;
    if (!doc.workset) return;
    emit(doc.workset, null);
}