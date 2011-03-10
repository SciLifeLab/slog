/* Index project documents by application.
   Value: label, or null. */
function(doc) {
    if (doc.entity !== 'project') return;
    emit(doc.application, doc.label || null);
}