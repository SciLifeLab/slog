/* Index workset documents by sample name.
   Value: null. */
function(doc) {
    var i;
    if (doc.entity !== 'workset') return;
    if (!doc.samples) return;
    for (i=0;  i<doc.samples.length; i+=1) {
	emit(doc.samples[i], null);
    }
}