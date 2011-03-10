/* Index all sample documents by the project.
   Value: The name. */
function(doc) {
    if (doc.entity !== 'sample') return;
    if (!doc.project) return;
    emit(doc.project, doc.name);
}