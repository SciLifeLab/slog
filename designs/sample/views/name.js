/* Index all sample documents by name.
   Value: The project. */
function(doc) {
    if (doc.entity !== 'sample') return;
    emit(doc.name, doc.project);
}