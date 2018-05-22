#!/usr/bin/python3.4
import new_read_jak  as r

def do_test(fn):
	print('file:'+fn+'...',end='\0')
	ds=r.read_file(fn,kind='prec',loc='detroit')	
	ds.dict
	print('success!')


# test daily files
print('\n testing daily files.....')
daily_list=[]
f=open('daily_files')
for line in f: daily_list.append(line.strip())
for fn in daily_list:
	do_test(fn)		


# test weekly
print('\n\n\n testing weekly files.....')
weekly_list=[]
f=open('weekly_files')
for line in f: weekly_list.append(line.strip())
for file in weekly_list:
	do_test(fn)		


# test monthly
print('\n\n\n testing monthly files.....')
monthly_list=[]
f=open('monthly_files')
for line in f: monthly_list.append(line.strip())
for file in monthly_list:
	do_test(fn)		

# test qm
print('\n\n\n testing qm files.....')
qm_list=[]
f=open('qm_files')
for line in f: qm_list.append(line.strip())
for file in qm_list:
	do_test(fn)		




