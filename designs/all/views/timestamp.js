/* Index entity documents by timestamp.
   Value: entity type and name. */
function(doc) {
    if (!doc.timestamp) return;
    if (!doc.entity) return;
    emit(doc.timestamp, [doc.entity, doc.name]);
}