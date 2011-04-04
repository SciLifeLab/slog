/* Index 'account' documents by name.
   Value: fullname. */
function(doc) {
  if (doc.entity !== 'account') return;
  emit(doc.name, doc.fullname || null);
}