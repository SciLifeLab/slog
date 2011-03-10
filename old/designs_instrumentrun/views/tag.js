/* Index instrumentrun documents by tag.
   Value: name. */
function(doc) {
    if (doc.entity !== 'instrumentrun') return;
    if (!doc.tags) return;
    var i;
    for (i=0; i<doc.tags.length; i+=1) {
	emit(doc.tags[i], doc.name);
    }
}