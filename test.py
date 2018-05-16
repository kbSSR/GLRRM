#! /bin/python

import read
import databank
import databank_util

#------------------------------------------------------------------------------
#  Code to test these routines.  Delete before using

print('------- ds1 (daily read) ------------------')
ds1 = read.read_file(filename='datafiles/dly_cglrrm1.txt', kind='nbs',
              intvl='dly', loc='eri')
ds1.printSummary()
print('')
print('')

myVault = databank.DataVault()
myVault.deposit(ds1)

print('-------- ds2 (daily withdrawal) -----------------')
ds2 = myVault.withdraw(kind='nbs', intvl='dly', loc='eri', units='cms')
ds2.printSummary()
print('')
print('')

print('------- ds3 (monthly read) ------------------')
ds3 = read.read_file(filename='datafiles/tab_monthly.txt')
ds3.printSummary()
print('')
print('')

myVault.deposit(ds3)

print('-------- ds4 (monthly withdrawal) -----------------')
ds4 = myVault.withdraw(kind='nbs', intvl='month', loc='mic', units='cms')
ds4.printSummary()
print('')
print('')

print('-------- ds5 (monthly withdrawal) -----------------')
ds5 = myVault.withdraw(kind='nbs', intvl='mon', loc='mic', units='mm', 
      first='2000-01-01', last='2001-12-31')
ds5.printSummary()
print('')
print('')


