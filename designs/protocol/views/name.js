/* Index all protocol documents by name.
   Value: Null. */
function(doc) {
    if (doc.entity !== 'protocol') return;
    emit(doc.name, null);
}