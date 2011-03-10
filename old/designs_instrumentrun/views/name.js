/* Index instrumentrun documents by name.
   Value: null. */
function(doc) {
  if (doc.entity !== 'instrumentrun') return;
  emit(doc.name, null);
}