/* Index all log documents by logged document id and timestamp.
   Value: The action. */
function(doc) {
  if (doc.entity !== 'log') return;
  if (!doc.docid) return;
  if (!doc.timestamp) return;
  emit([doc.docid, doc.timestamp], doc.action);
}