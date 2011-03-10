/* Index task documents by operator.
   Value: null. */
function(doc) {
    if (doc.entity !== 'task') return;
    emit(doc.operator, null);
}