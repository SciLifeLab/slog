/* Index instrument documents by name.
   Value: label, or null. */
function(doc) {
  if (doc.entity !== 'instrument') return;
  emit(doc.name, doc.label || null);
}