/* Index 'workset' documents by operator.
   Value: name. */
function(doc) {
    if (doc.entity !== 'workset') return;
    emit(doc.operator, doc.name);
}