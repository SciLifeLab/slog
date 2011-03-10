/* Count the number of samples per project; map function */
function(doc) {
    if (doc.entity !== 'sample') return;
    emit(doc.project, 1);
}