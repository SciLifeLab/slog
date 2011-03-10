/* Index all task documents by protocol.
   Value: null. */
function(doc) {
    if (doc.entity !== 'task') return;
    emit(doc.protocol, null);
}