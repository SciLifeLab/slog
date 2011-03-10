/* Index project documents by customer.
   Value: name. */
function(doc) {
  if (doc.entity !== 'project') return;
  emit(doc.customer, doc.name);
}