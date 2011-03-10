/* Index application documents by timestamp.
   Value: label, or null. */
function(doc) {
    if (doc.entity !== 'application') return;
    emit(doc.timestamp, doc.label || null);
}