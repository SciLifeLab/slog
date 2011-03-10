/* Index all task documents by name.
   Value: null. */
function(doc) {
    if (doc.entity !== 'task') return;
    emit(doc.name, null);
}