/* Count the number of projects per application; map function */
function(doc) {
    if (doc.entity !== 'project') return;
    emit(doc.application, 1);
}