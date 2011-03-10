/* Index application documents by name.
   Value: label, or null. */
function(doc) {
  if (doc.entity !== 'application') return;
  emit(doc.name, doc.label || null);
}