/* Index all protocol documents by instrument.
   Value: name. */
function(doc) {
    if (doc.entity !== 'protocol') return;
    if (!doc.instruments) return;
    var i;
    for (i=0; i<doc.instruments.length; i+=1) {
	emit(doc.instruments[i], doc.name);
    }
}