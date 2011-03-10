"Make a dummy Illumina barcode index file."

import csv


outfile = open('illumina_indexes.csv', 'w')
outcsv = csv.writer(outfile)
for row in [('index1', 'ATCACG'),
                  ('index2', 'CGATGT'),
                  ('index3', 'TTAGGC'),
                  ('index4', 'TGACCA'),
                  ('index5', 'ACAGTG'),
                  ('index6', 'GCCAAT'),
                  ('index7', 'CAGATC'),
                  ('index8', 'ACTTGA'),
                  ('index9', 'GATCAG'),
                  ('index10', 'TAGCTT'),
                  ('index11', 'GGCTAC'),
                  ('index12', 'CTTGTA')]:
    outcsv.writerow(row)
outfile.close()
