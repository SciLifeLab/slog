/* Index instrumentrun documents by sample name.
   Value: name. */
function(doc) {
    if (doc.entity !== 'instrumentrun') return;
    var array = doc.samples.array;
    var row, column, sample;
    var r, c, m;
    for (r=0; r<array.length; r+=1) {
	row = array[r];
	for (c=0; c<row.length; c+=1) {
	    column = row[c];
	    for (m=0; m<column.length; m+=1) {
		sample = column[m];
		if (sample) emit(sample, doc.name);
	    }
	}
    }
}