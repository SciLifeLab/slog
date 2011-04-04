/* Index 'workset' documents by operator.
   Value: null. */
function(doc) {
    if (doc.entity !== 'workset') return;
    emit(doc.operator, null);
}