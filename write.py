import re
import datetime as dt
import databank as databank
import databank_util as util
import os


tab = 1
fill = -999.9



#--------------------------------------------------------------------
def write_file(filename, file_format, dataseries, overwrite=False, float_format=None):
	'''

	Write dataseries (metadata and datavals) to filename 

	Parameters
	----------
	filename: string
		The desired filename to write to.
	file_format: string
		The format of the output file ("table" or "column")
		note that weekly data only can be written as column format
	dataseries: object
		The dataseries object created by databank or read_file
		to be written to filename.
	overwrite: boolean, optional
		Flag to indicate whether or not to overwrite existing file 
		named "filename". default is False (i.e don't overwrite files)
	float_format: string, optional 
		String to specify the formatting of values  written to filename.  
		This uses the "new style" defined at www.pyformat.info 
		default is "{0:9.2f}" (9 spaces, 2 digits after decimal)
	'''

	if not float_format: float_format = "{0:9.2f}"


	try:
		__write_metadata(filename, dataseries, overwrite)
	except:
		raise Exception('Unable to write metadata to ' + filename)

	try:
		__write_datavals(filename, file_format, dataseries, float_format)
	except:
		raise Exception('Unable to write datavals to ' + filename)





def __write_metadata(filename, dataseries, overwrite):
	''' writes metadata to filename '''

	# check if file exists already
	if not overwrite and os.path.isfile(filename): raise Exception(filename + ' already exists')

	# create new file for writing
	try:
		f = open(filename, 'w')
	except:
		raise Exception('could not open ' + filename + ' for writing')

	# write metadata
	line = ':'.join(['KIND', dataseries.dataKind])
	f.write(line + '\n')
	line = ':'.join(['UNITS', dataseries.dataUnits])
	f.write(line + '\n')
	line = ':'.join(['INTERVAL', dataseries.dataInterval])
	f.write(line + '\n')
	line = ':'.join(['LOCATION', dataseries.dataLocation])
	f.write(line + '\n')


	# write comment line with date of generation
	now_str=dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	line= ''.join(['# file created: ', now_str]) 
	f.write(line + '\n')
	
	f.close()
	

def __write_datavals(filename, file_format, dataseries, float_format):
	''' Write the dataseries.dataVals to filename'''	
	
	intvl = dataseries.dataInterval
	vals = dataseries.dataVals
	start = dataseries.startDate
	end = dataseries.endDate

	# define fill value # JAK?
	fill = -999.9
	#fill = -9.29e-11? 

	f = open(filename,'a')


	header_format = float_format

	days = range(1,32)
	hdr = [ 'D{:d}'.format(d) for d in days ]
	#hdr = header_format (get width rigth so header aligns with columns)

	# daily 
	if intvl == 'dy':
		if file_format == 'table':
			date = start # initialize date for loop
			dom = util.days_in_month(date.year, date.month)
			first = 0          # vals index for first day of the month
			last = first + dom # vals index for last day of the month
			while date <= end:
				# construct the line to write to filename
				data_line = [ fill ] * 31
				data_line[0:dom] = vals[first:last]
				data_line = ', '.join([ float_format.format(d) for d in data_line ])
				full_line = ', '.join(['{:%Y-%m}'.format(date), data_line])
				f.write(full_line + '\n') 
				
				# update date and indices for next iteration
				date = date + dt.timedelta(days = dom)
				dom = util.days_in_month(date.year, date.month)
				first = last
				last = first + dom

		if file_format == 'column':
			date = start
			i = 0
			while date <= end:
				# construct a line to write to file
				data_line = float_format.format(vals[i])
				full_line = ', '.join(['{:%Y-%m-%d}'.format(date), data_line])
				f.write(full_line + '\n')
				
				# update
				i = i + 1 
				date = date + dt.timedelta(days = 1)


	# weekly
	if intvl == 'wk':
		date = start
		i = 0
		while date <= end:
			# construct a line to write to file
			data_line = float_format.format(vals[i])
			full_line = ', '.join(['{:%Y-%m-%d}'.format(date), data_line])
			f.write(full_line + '\n')
			
			# update
			i = i + 1 
			date = date + dt.timedelta(days = 7)


	# quarter-monthly
	if intvl == 'qm':
		# this is not actually the format that we discussed, but I think its better
		if file_format == 'table':
			date = start
			i = 0
			while date <= end:
				# construct line and write
				data_line = vals[i:i+4]
				data_line = ', '.join([ float_format.format(d) for d in data_line ])
				full_line = ', '.join(['{:%Y-%m}'.format(date), data_line])
				f.write(full_line + '\n')

				# update 
				i = i + 4
				dom = util.days_in_month(date.year, date.month)	
				date = date + dt.timedelta(days = dom)
		
		if file_format == 'column':
			date = start
			i = 0
			q = 1  # quarter
			while date <= end:
				# construct line to write
				data_line = float_format.format(vals[i])		
				date_str = '-'.join(['{:%Y-%m}'.format(date), '{:02d}'.format(q)])
				full_line = ', '.join([date_str, data_line])
				f.write(full_line + '\n')
				
				# update
				i = i + 1	
				q = q + 1
				if i % 4 is 0: 
					q = 1 
					dom = util.days_in_month(date.year, date.month)
					date = date + dt.timedelta(days = dom)





	if intvl == 'mn':
		if file_format == 'column':
			date = start
			i = 0 
			while date <= end:
				# construct line to write
				data_line = float_format.format(vals[i])
				full_line = ', '.join(['{:%Y-%m}'.format(date), data_line])
				f.write(full_line + '\n')
			
				# update 
				i = i + 1
				dom = util.days_in_month(date.year, date.month)
				date = date + dt.timedelta(days = dom)

		if file_format == 'table':
			date = int('{:%Y}'.format(start))
			end = int('{:%Y}'.format(end))
			i = 0
			while date <= end:
				# construct line to write
				data_line = vals[i:i+12]
				data_line = ', '.join([float_format.format(d) for d in data_line ])	
				full_line = ', '.join(['{:4d}'.format(date), data_line])
				f.write(full_line + '\n')
				
				# update
				i = i + 12
				date = date + 1
				
				
		f.close()




