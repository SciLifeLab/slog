/* Index all sample documents by altname.
   Value: The project. */
function(doc) {
    if (doc.entity !== 'sample') return;
    if (!doc.altname) return;
    emit(doc.altname, doc.project);
}