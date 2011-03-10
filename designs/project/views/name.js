/* Index project documents by name.
   Value: label, or null. */
function(doc) {
    if (doc.entity !== 'project') return;
    emit(doc.name, doc.label || null);
}