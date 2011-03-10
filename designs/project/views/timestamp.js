/* Index project documents by timestamp.
   Value: The project label, or null. */
function(doc) {
    if (doc.entity !== 'project') return;
    emit(doc.timestamp, doc.label || null);
}