/* Index workset documents by name.
   Value: null. */
function(doc) {
    if (doc.entity !== 'workset') return;
    emit(doc.name, null);
}