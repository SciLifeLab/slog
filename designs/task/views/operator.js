/* Index 'task' documents by operator.
   Value: name. */
function(doc) {
    if (doc.entity !== 'task') return;
    emit(doc.operator, doc.name);
}