#
#  Quick little demo file showing a few capabilities
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
#  echo the data to a new output file
#
databank_io.write_file(filename='demo_output1.txt', file_format='column', ds=ds1)

#
#  store the data in the repository
#
the_vault.deposit(ds1)

#
#  retrieve monthly Lake Michigan NBS from the repository in cfs
#
ds_cfs = the_vault.withdraw(kind='nbs', units='cfs', intvl='mon', loc='mic')

#
#  output lake Michigan monthly NBS values to a new file
#
databank_io.write_file('demo_output2.txt', file_format='column', ds=ds_cfs)

#
#  try to retrieve daily data from the vault (fails)
#
ds_fail = the_vault.withdraw(kind='nbs', units='cfs', intvl='dly', loc='mic')

