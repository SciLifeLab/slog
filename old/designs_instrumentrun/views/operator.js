/* Index instrumentrun documents by operator.
   Value: null. */
function(doc) {
    if (doc.entity !== 'instrumentrun') return;
    emit(doc.operator, null);
}