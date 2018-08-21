#
#  Quick little demo file showing a few capabilities, including the
#  multi-set feature
#
import sys
import databank
import databank_io
import databank_util

#
#  Create the big data repository object
#
the_vault = databank.DataVault()

#
#  read a file that has self-contained metadata (new format)
#  File has sample Lake Michigan monthly NBS values in cms for 1999-2002
#
ds1 = databank_io.read_file('data/mn/tab_monthly.txt')

#
#  Assign "setA" as the dataset identifier for this timeseries of data
#
ds1.dataSet = 'setA'

#
#  echo the data to a new output file
#
databank_io.write_file(filename='demo_output1.txt', file_format='column', dataseries=ds1,
        overwrite=True)

#
#  store the data in the repository
#
the_vault.deposit(ds1)

print('after adding setA')
print('----------------')
the_vault.printVault()
print('----------------')

#
#  Make a copy of ds1 and change it a little bit.  For generality in this
#  quick demo, I will just change the first 3 data values to be [1,2,3].
#  My only purpose is to prove that we get independent objects into the vault.
#
ds2 = ds1
ds2.dataVals[0:3] = [1,2,3]
ds2.dataSet = 'setB'

#
#  store the second data set in the repository
#
the_vault.deposit(ds2)

print('after adding setB')
print('----------------')
the_vault.printVault()
print('----------------')

#
#  retrieve monthly Lake Michigan NBS from the repository in cfs
#
ds_cfs = the_vault.withdraw(kind='nbs', units='cfs', intvl='mon', loc='mic', set='setA')

#
#  output lake Michigan monthly NBS values to a new file
#
databank_io.write_file('demo_output_setA.txt', file_format='column', dataseries=ds_cfs, overwrite=True)

#
#  retrieve and output the second data set
#
ds_cfs = the_vault.withdraw(kind='nbs', units='cfs', intvl='mon', loc='mic', set='setB')
databank_io.write_file('demo_output_setB.txt', file_format='column', dataseries=ds_cfs, overwrite=True)


#
#  try to retrieve daily data from the vault (fails)
#
ds_fail = the_vault.withdraw(kind='nbs', units='cfs', intvl='dly', loc='mic')

