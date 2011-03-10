/* Index all protocol documents by application.
   Value: name. */
function(doc) {
    if (doc.entity !== 'protocol') return;
    if (!doc.applications) return;
    var i;
    for (i=0; i<doc.applications.length; i+=1) {
	emit(doc.applications[i], doc.name);
    }
}