#!/usr/bin/python3.4
import new_read  as r




def do_test(file,myKind,myLoc):
	ds = r.read_file(file, kind=myKind, loc=myLoc)
	print(ds.startDate)
	print(ds.endDate)
	print(ds.dataInterval) 
	print(ds.dataLocation)
	print(ds.dataKind) 
	print(ds.dataUnits) 
	try:
		print(min(ds.dataVals))
		print(max(ds.dataVals))
	except:
		print('could not print min/max')




# test daily files
print('\n testing daily files.....')
daily_list=[]
f=open('daily_files')
for line in f: daily_list.append(line.strip())

for file in daily_list:
	print('testing file:'+file)
	#r.read_file(file,kind='prec',loc='detroit')	
	do_test(file,myKind='prec',myLoc='detroit')	


# test weekly
print('\n\n\n testing weekly files.....')
weekly_list=[]
f=open('weekly_files')
for line in f: weekly_list.append(line.strip())
for file in weekly_list:
	print('testing file:'+file)
	#r.read_file(file,kind='prec',loc='detroit')
	do_test(file,myKind='prec',myLoc='detroit')	


#
# test monthly
print('\n\n\n testing monthly files.....')
monthly_list=[]
f=open('monthly_files')
for line in f: monthly_list.append(line.strip())
for file in monthly_list:
	print('testing file:'+file)
	#r.read_file(file,kind='prec',loc='detroit')
	do_test(file,myKind='prec',myLoc='detroit')	



# test qm
print('\n\n\n testing qm files.....')
qm_list=[]
f=open('qm_files')
for line in f: qm_list.append(line.strip())
for file in qm_list:
	print('testing file:'+file)
	#r.read_file(file,kind='prec',loc='detroit')
	do_test(file,myKind='prec',myLoc='detroit')	




