import numpy as np
import matplotlib.pyplot as plt
import databank_io as io
import databank as db
import databank_util as util


# check daily files

#compare set 1 (same values in column and table format)
dscol = r.read_file('DataFiles/dy/set1_col.txt')
dstab = r.read_file('DataFiles/dy/set1_tab.txt')

vals1 = np.array(dscol.dataVals)
vals2 = np.array(dstab.dataVals)

plt.figure()
plt.plot(vals1-vals2)


#compare set 1 (same values in column and table format)
dscol2 = r.read_file('DataFiles/dy/set2_col.txt')
dscglr = r.read_file('DataFiles/dy/set2_cglrrm.txt',loc='eri',kind='nbs')

vals1 = np.array(dscol2.dataVals)
vals2 = np.array(dscglr.dataVals)

plt.figure()
plt.plot(vals1-vals2)



plt.show()
