import numpy as np
import datetime as dt
import databank as databank
import databank_util as util


tab=1
fill=-999.9

#--------------------------------------------------------------------
#  Read the specified file, returning an ordered list of strings.
#  Each string is a line in the file that has valid data and all
#  comments are removed. Comments are defined as anything on a
#  line that comes after a # character.  If a line ends up being
#  blank, it is not included in the returned list.  Quick example...
#  File content:
#    # this is a header comment
#    # Year Mon Day Value
#      1990  01  01 10.50
#      1990  01  02  3.10
#      1990  01  03 -9.99    # this is a missing value
#      1990  01  04 21.00
#      #  a bunch of data is missing here
#                            # BLANK LINE
#      1990  12  31  4.44
#
#  Returned list:
#  ('  1990  01  01 10.50', '  1990  01  02  3.10',
#   '  1990  01  03 -9.99', '  1990  01  04 21.00',
#   '  1990  12  31  4.44')
#
#  The 9-line file turned into a 5-string list.
#--------------------------------------------------------------------
def getValidLines(filename):
    linelist = []
    with open(filename, "r") as f:
        for line in f:
            i = line.find('#')
            if i == -1:
                s1 = line
            else:
                s1 = line[:i]
            s2 = s1.rstrip()
            if len(s2) > 0:
                linelist.append(s2)
    return linelist

#--------------------------------------------------------------------
#  Parse all lines of the file looking for lines that match the format
#  of metadata specifiers.  When one of those is encountered, try to
#  parse out the metadata in it.
#
#  Note that with old CGLRRM files, the kind (type) and location metadata
#  was not part of the header.  It was suggested to include it as part of
#  the comments, but they were not part of a defined header entry.
#
#  The old CGLRRM looked at only the first character of interval
#  specification, so we will handle that as a special case.
#
def getMetaData(all_lines):
    mkind  = 'na'
    munits = 'na'
    mintvl = 'na'
    mloc   = 'na'

    for line in all_lines:
        try:
            if line.find(':'):
                items = line.split(':')
                if (len(items) == 2):
                    lstr = items[0].lower()
                    rstr = items[1].lower()
                    if (lstr == 'kind') or (lstr == 'type'): 
                        mkind = databank.DataKind(rstr).primaryName()
                    if lstr == 'location':
                        mloc = databank.DataLocation(rstr).primaryName()
                    if lstr == 'units':
                        munits = databank.DataUnits(rstr).primaryName()
                    if lstr == 'interval':
                        mintvl = databank.DataInterval(rstr).primaryName()
                        if mintvl == 'na':
                            t = 'na'
                            if rstr[0] == 'd':  t = 'dy'
                            if rstr[0] == 'w':  t = 'wk'
                            if rstr[0] == 'q':  t = 'qm'
                            if rstr[0] == 'm':  t = 'mn'
                            if rstr[0] == 'y':  t = 'yr'
                            mintvl = databank.DataInterval(t).primaryName()
        except:
            raise Exception('Error in header of the file')

    return mkind, munits, mintvl, mloc

# DAILY
#--------------------------------------------------------------------
#  Parse the data lines of a file that is assumed to be daily data.
#  Determine which of the allowable formats it matches.
#    A. The old CGLRRM daily format where each data line had
#       7 or 8 values corresponding to the days of a quarter-month.
#    B. The new tabular format where each line has 31 values
#    C. The new single-column format where each line is just one day.
#  Return value is 'cglrrm' or 'table' or 'column' or 'unknown'.
#
#  We explicitly check the range of the date information
#  values, but do not check the range of the data values.
#  If they convert to float ok we assume they are valid.
#
#  Note that year is only checked for being a positive number, and
#  not verified to be within any range.  This is because existing
#  files used for the old CGLRRM for some studies had year values
#  ranging from 1 to over 50,000.
#
def detectDailyFormat(data_lines):
    #
    #  First check for matching the CGLRRM format.
    #  Valid lines have year, mn, q plus 7 or 8 data values.
    #
    matches = True
    for line in data_lines:
        if matches:
            try:
                items = [s.strip() for s in line.split()]
                if (len(items) < 10) or (len(items) > 11):
                    matches = False
                try:
                    vals = [int(s) for s in items[0:3]]
                    if  vals[0] < 1:   matches = False
                    if (vals[1] < 1) or (vals[1] > 12): matches = False
                    if (vals[2] < 1) or (vals[2] > 4):  matches = False
                    vals = [float(s) for s in items[3:len(items)]]  # JAK?: this may be problematic for negative values???
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'cglrrm'

    #
    #  Second check for matching the new daily tabular format.
    #  Valid lines have YYYY-MM plus 31 data values.
    #
    matches = True
    for line in data_lines:
        if matches:
            try:
                items = [s.strip() for s in line.split(',')]
                if len(items) < 32:
                    matches = False
                try:
                    vals = [int(s) for s in items[0].split('-')]
                    if  vals[0] < 1: matches = False
                    if (vals[1] < 1) or (vals[1] > 12): matches = False
                    vals = [float(s) for s in items[2:len(items)]]
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'table'

    #
    #  Third check is for matching the new daily columnar format.
    #  Valid lines have YYYY-MM-DD plus 1 data value.
    #
    matches = True
    for line in data_lines:
        if matches:
            try:
                items = [s.strip() for s in line.split(',')]
                if len(items) != 2:
                    matches = False
                try:
                    vals = [int(s) for s in items[0].split('-')]
                    if  vals[0] < 1: matches = False
                    if (vals[1] < 1) or (vals[1] > 12): matches = False
                    if (vals[2] < 1) or (vals[2] > 31): matches = False
                    vals = float(items[1])
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'column'

    #
    #  If we get to here it means all 3 tests failed.
    #
    return 'unknown'

# WEEKLY 
#--------------------------------------------------------------------
#  Parse the data lines of a file that is assumed to be weekly data.
#  Determine which of the allowable formats it matches.
#    A. The old CGLRRM weekly format where each data line had
#       7 or 8 values corresponding to the days of a quarter-month.
#    B. The new single-column format where each line is just one week.
#  Return value is 'cglrrm' or 'column' or 'unknown'.

def detectWeeklyFormat(data_lines):
    #
    #  First check for matching the CGLRRM format.
    #  Valid lines have year mn d data_value
    #
    matches = True
    for line in data_lines:
        if matches:
            try:
                items = [s.strip() for s in line.split()]
                if len(items) != 4:
                    matches = False
                try:
                    vals = [int(s) for s in items[0:3]]
                    if  vals[0] < 1:   matches = False
                    if (vals[1] < 1) or (vals[1] > 12): matches = False
                    if (vals[2] < 1) or (vals[2] > 31):  matches = False
                    vals = float(items[3])
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'cglrrm'

    #  Second check is for matching the new weekly columnar format.
    #  Valid lines have date in format YYYY-MM-DD plus 1 data value.
    #
    matches = True
    for line in data_lines:
        if matches:
            try:
                items = [s.strip() for s in line.split(',')]
                if len(items) != 2:
                    matches = False
                try:
                    vals = [int(s) for s in items[0].split('-')]
                    if  vals[0] < 1: matches = False
                    if (vals[1] < 1) or (vals[1] > 12): matches = False
                    if (vals[2] < 1) or (vals[2] > 31): matches = False
                    val = float(items[1])
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'column'

    #
    #  If we get to here it means all 3 tests failed.
    #
    return 'unknown'


# QtrMonthly
#--------------------------------------------------------------------
#  Parse the data lines of a file that is assumed to be QtrMonthly data.
#  Determine which of the allowable formats it matches.
#    A. The old CGLRRM QtrMonthly format where each data line had
#       12 values corresponding to the nth Qtr of each month of the year
#    B. The new tabular format (also with 12 data values) but hyphenated dates.
#    C. The new single-column format where each line has one data value for qtr-month.
#  Return value is 'cglrrm' or 'table' or 'column' or 'unknown'.
def detectQtrMonthlyFormat(data_lines):
    #
    #  First check for matching the CGLRRM format.
    #  Valid lines have YYYY QQ followed by 12 data values
    #
    matches = True
    for line in data_lines:
        if matches:
            try:
                items = [s.strip() for s in line.split()]
                if len(items) != 14: matches = False
                try:
                    vals = [int(s) for s in items[0:2]]
                    if  vals[0] < 1: matches = False
                    if (vals[1] < 1) or (vals[1] > 4): matches = False
                    vals = [float(s) for s in items[2:len(items)]]
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'cglrrm'

    #
    #  Second check for matching the new QtrMonthly tabular format.
    #  Valid lines have YYYY-QQ followed by 12 data values.
    #
    matches = True
    for line in data_lines:
        if matches:
            try:
                #items = [s.strip() for s in line.split(',')] # this breaks if there's a trailing comma
                items = [s.strip() for s in line.split(',') if s]
                print(items)
                if len(items) != 13:  # allow a trailing comma  (PROB NOT NECCESSARY DUE TO ABOVE FIX)
                    matches = False
                try:
                    vals = [int(s) for s in items[0].split('-')]
                    if  vals[0] < 1: matches = False
                    if (vals[1] < 1) or (vals[1] > 12): matches = False
                    vals = [float(s) for s in items[1:len(items)]]
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'table'

    #
    #  Third check is for matching the new QtrMonthly columnar format.
    #  Valid lines have date in format YYYY-MM-QQ plus 1 data value.
    #
    matches = True
    for line in data_lines:
        if matches:
            try:
                items = [s.strip() for s in line.split(',')]
                if len(items) != 2:
                    matches = False
                try:
                    vals = [int(s) for s in items[0].split('-')]
                    if  vals[0] < 1: matches = False
                    if (vals[1] < 1) or (vals[1] > 12): matches = False
                    if (vals[2] < 1) or (vals[2] > 4): matches = False
                    val = float(items[1])
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'column'

    #
    #  If we get to here it means all 3 tests failed.
    #
    return 'unknown'



# MONTHLY 
#--------------------------------------------------------------------
#  Parse the data lines of a file that is assumed to be monthly data.
#  Determine which of the allowable formats it matches.
#    A. The old CGLRRM daily format where each data line had
#       7 or 8 values corresponding to the days of a quarter-month.
#    B. The new tabular format where each line has 31 values
#    C. The new single-column format where each line is just one day.
#  Return value is 'cglrrm' or 'table' or 'column' or 'unknown'.
#
def detectMonthlyFormat(data_lines):
    #
    #  First check for matching the CGLRRM format.
    #  Valid lines have the year plus 12 data values.
    #  We explicitly check the range of the 3 date infomation
    #  values, but do not check the range of the data values.
    #  If they convert to float ok we assume they are valid.
    #
    matches = True
    for line in data_lines:
        if matches:
            try:
                items = [s.strip() for s in line.split()]
                if len(items) != 13:
                    matches = False
                try:
                    yr = int(items[0])
                    if yr < 1: matches = False
                    vals = [float(s) for s in items[1:len(items)]]
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'cglrrm'

    #
    #  Second check for matching the new monthly tabular format.
    #  Valid lines have year plus 12 data values.
    #
    matches = True
    lnum = 0
    for line in data_lines:
        if matches:
            try:
                items = [s.strip() for s in line.split(',')]
                if len(items) != 13:
                    matches = False
                try:
                    yr = int(items[0])
                    if yr < 1: matches = False
                    vals = [float(s) for s in items[1:len(items)]]
                except:
                    matches = False
            except:
                matches = False
    if matches:
        return 'table'

    #
    #  Third check is for matching the new monthly columnar format.
    #  Valid lines have year, month, plus 1 data value.
    #
    matches = True
    lnum = 0
    for line in data_lines:
        if matches:
            try:
                lnum += 1
                items = [s.strip() for s in line.split(',')]
                if len(items) != 3:
                    matches = False
                try:
                    yr = int(items[0])
                    mn = int(items[1])
                    if yr < 1: matches = False
                    if (mn < 1) or (mn > 12):  matches = False
                    val = float(items[2])
                except:
                    matches = False
            except:
                print('column detect fails due some other error; lnum=', lnum)
                matches = False
    if matches:
        return 'column'

    #
    #  If we get to here it means all 3 tests failed.
    #
    return 'unknown'


#--------------------------------------------------------------------
def read_file(filename=None, kind=None, units=None, intvl=None, loc=None):
    #
    #  Get all of the non-comment content from the file as 
    #  a list of strings
    #
    all_lines = getValidLines(filename)

    #
    #  Create objects for each of the supplied metadata items
    #
    try:
        mkind  = None
        munits = None
        mintvl = None
        mloc   = None
        if kind:
            mkind = databank.getPrimaryName(meta='kind', name=kind)
        if units:
            munits = databank.getPrimaryName(meta='units', name=units)
        if intvl:
            mintvl = databank.getPrimaryName(meta='interval', name=intvl)
        if loc:
            mloc = databank.getPrimaryName(meta='location', name=loc)
    except:
        raise Exception('Invalid metadata passed to read_file()')

    #
    #  Parse the data file lines to get any metadata
    #  specified within the file.
    #
    try:
        fkind, funits, fintvl, floc = getMetaData(all_lines)
    except:
        raise Exception('Unable to process metadata from ' + filename)

    #
    #  If any of the metadata items from the file are undefined,
    #  set that metadata object to None
    #
    if fkind  == 'na':  fkind  = None
    if funits == 'na':  funits = None
    if fintvl == 'na':  fintvl = None
    if floc   == 'na':  floc   = None

    #
    #  Do we have sufficient metadata to continue?
    #
    ok = True
    if (not mkind)  and (not fkind):  ok = False; mis_kind=True
    if (not munits) and (not funits): ok = False; mis_unit=True
    if (not mintvl) and (not fintvl): ok = False; mis_intvl=True
    if (not mloc)   and (not floc):   ok = False; mis_loc=True
    if not ok:
        raise Exception('Missing metadata for processing ' + filename)

    #
    #  If we have metadata from both caller and file, do they match?
    #
    ok = True
    if mkind and fkind:
        if mkind != fkind:
            ok = False
    if munits and funits:
        if munits != funits:
            ok = False
    if mintvl and fintvl:
        if mintvl != fintvl:
            ok = False
    if mloc and floc:
        if mloc != floc:
            ok = False
    if not ok:
        raise Exception('Inconsistent metadata for processing ' + filename)

    #
    #  If needed, assign metadata from file to our primary variables
    #
    if not mkind:  mkind  = fkind
    if not munits: munits = funits
    if not mintvl: mintvl = fintvl
    if not mloc:   mloc   = floc

    #
    #  Process the file appropriately.  Note that the
    #  DataSeries object that is returned may have some missing
    #  metadata items if they were left blank in the file, but
    #  specified by the caller of this procedure.
    #
    tds = None
	
    try:
        if mintvl == 'dy':
            tds = procDailyData(all_lines)
        elif mintvl == 'wk':
            tds = procWeeklyData(all_lines)
        elif mintvl == 'qm':
            tds = procQtrMonthlyData(all_lines)
        elif mintvl == 'mn':
            tds = procMonthlyData(all_lines)
        else:
            raise Exception('Invalid interval')
    except:
        raise Exception('Unable to process data from ' + filename)

    #
    #  Create a new DataSeries object, filling in all of the
    #  metadata values.  This completed DataSeries object is the
    #  result that is returned.
    #
    if tds:
        sd = tds.startDate
        ed = tds.endDate
        datavals = tds.dataVals
        ds = databank.DataSeries(kind=mkind, units=munits, intvl=mintvl,
                loc=mloc, first=sd, last=ed, values=datavals)
        return ds
    else:
        return None

#--------------------------------------------------------------------
#  Process a list of lines that contains all of the non-comment
#  contents of a data file.  The all_lines variable is a list of
#  strings after the file was read and:
#    1) all comments were removed
#    2) blank lines were removed
#    3) trailing whitespace on each line was removed
#
#  Note that leading whitespace, if it existed, was preserved.
#
def procDailyData(all_lines):
    datavals = []
    sdate = util.MISSING_DATE       # "missing" date value
    edate = util.MISSING_DATE       # "missing" date value

    #
    #  The first thing we will do is strip off any lines that look like
    #  header info, making sure they match the general keyword:value
    #  format.  If the line does NOT look like a header line, we put
    #  it into a data_lines list that will be parsed separately.
    #  Note that if a line has a colon, but does not match the
    #  keyword:value format, that immediately disqualifies the file.
    #
    data_lines = []
    for line in all_lines:
        try:
            if line.find(':') > 0:
                items = line.split(':')
                if (len(items) != 2):
                    raise Exception('Invalid content')
            else:
                data_lines.append(line)
        except:
            raise Exception('Error separating header and data lines.')

    #
    #  Now parse the data_lines list to get a format name.
    #
    format_name = detectDailyFormat(data_lines)
    success = True
    try:
        if format_name == 'cglrrm':
            return parseDailyCGLRRM(all_lines)
        elif format_name == 'table':
            return parseDailyTable(all_lines)
        elif format_name == 'column':
            return parseDailyColumn(all_lines)
        else:
            success = False
    except:
        success = False
        
    if not success:
        raise Exception('Error parsing daily data file')


def procWeeklyData(all_lines):
    datavals = []
    sdate = util.MISSING_DATE       # "missing" date value
    edate = util.MISSING_DATE       # "missing" date value

 
    data_lines = []
    for line in all_lines:
        try:
            if line.find(':') > 0:
                items = line.split(':')
                if (len(items) != 2):
                    raise Exception('Invalid content')
            else:
                data_lines.append(line)
        except:
            raise Exception('Error separating header and data lines.')

    #
    #  Now parse the data_lines list to get a format name.
    #
    format_name = detectWeeklyFormat(data_lines)
    success = True
    try:
        if format_name == 'cglrrm':
            return parseWeeklyCGLRRM(all_lines)
        elif format_name == 'column':
            return parseWeeklyColumn(all_lines)
        else:
            success = False
    except:
        success = False
        
    if not success:
        raise Exception('Error parsing weekly data file')



def procQtrMonthlyData(all_lines):
    datavals = []
    sdate = util.MISSING_DATE       # "missing" date value
    edate = util.MISSING_DATE       # "missing" date value

    #
    #  The first thing we will do is strip off any lines that look like
    #  header info, making sure they match the general keyword:value
    #  format.  If the line does NOT look like a header line, we put
    #  it into a data_lines list that will be parsed separately.
    #  Note that if a line has a colon, but does not match the
    #  keyword:value format, that immediately disqualifies the file.
    #
    data_lines = []
    for line in all_lines:
        try:
            if line.find(':') > 0:
                items = line.split(':')
                if (len(items) != 2):
                    raise Exception('Invalid content')
            else:
                data_lines.append(line)
        except:
            raise Exception('Error separating header and data lines.')

    #
    #  Now parse the data_lines list to get a format name.
    #
    format_name = detectQtrMonthlyFormat(data_lines)
    success = True
    try:
        if format_name == 'cglrrm':
            return parseQtrMonthlyCGLRRM(all_lines)
        elif format_name == 'table':
            return parseQtrMonthlyTable(all_lines)
        elif format_name == 'column':
            return parseQtrMonthlyColumn(all_lines)
        else:
            success = False
    except:
        success = False
        
    if not success:
        raise Exception('Error parsing daily data file')



#--------------------------------------------------------------------
#  Process a list of lines that contains all of the non-comment
#  contents of a data file.  The all_lines variable is a list of
#  strings after the file was read and:
#    1) all comments were removed
#    2) blank lines were removed
#    3) trailing whitespace on each line was removed
#
#  Note that leading whitespace, if it existed, was preserved.
#
def procMonthlyData(all_lines):
    datavals = []

    #
    #  The first thing we will do is strip off any lines that look like
    #  header info, making sure they match the general keyword:value
    #  format.  If the line does NOT look like a header line, we put
    #  it into a data_lines list that will be parsed separately.
    #  Note that if a line has a colon, but does not match the
    #  keyword:value format, that immediately disqualifies the file.
    #
    data_lines = []
    for line in all_lines:
        try:
            if line.find(':') > 0:
                items = line.split(':')
                if (len(items) != 2):
                    raise Exception('Invalid content')
            else:
                data_lines.append(line)
        except:
            raise Exception('Error separating header and data lines.')

    #
    #  Now parse the data_lines list to get a format name.
    #
    format_name = detectMonthlyFormat(data_lines)
    success = True
    try:
        if format_name == 'cglrrm':
            return parseMonthlyCGLRRM(all_lines)
        elif format_name == 'table':
            return parseMonthlyTable(all_lines)
        elif format_name == 'column':
            return parseMonthlyColumn(all_lines)
        else:
            success = False
    except:
        success = False
    if not success:
        raise Exception('Error parsing monthly data file')


#--------------------------------------------------------------------
#  Process a set of lines (list of strings) that contain daily data in
#  the format used by the old CGLRRM.  Note that all comment lines from the
#  original file have already been removed at this point. It is just valid
#  data (and header metadata) lines.
#  Example list of lines (shown here with just one string per line) is:
#  ("INTERVAL: Daily",
#   "UNITS: 10m3s",
#   "2018  3 1 -99999. -99999. -99999. -99999. -99999. -99999. -99999. -99999."
#   "2018  3 2     57.     57.    122.    -10.    -17.     51.    266."
#   "2018  3 3    352.    154.    161.    796.    329.    973.    739.    389."
#   "2018  3 4    272.    196.    392.    536.    127.    140.    156.    422."
#   "2018  4 1    242.    136.     64.     65.    206.    310.    167.    147."
#   "2018  4 2    -23.     59.    558.    213.    362.    402.    182."
#   "2018  4 3    142.      6.     58.     84.    157.     82.     29.     99."
#   "2018  4 4    141.     85.     98.    424.    202.     39.      1.")
#
#  This function returns a complete DataSeries object.
#--------------------------------------------------------------------
def parseDailyCGLRRM(all_lines):
    #
    #  Separate the header lines from the data lines.
    #
    hdr_lines  = []
    data_lines = []
    for line in all_lines:
        if line.find(':') > 0:
            hdr_lines.append(line)
        else:
            data_lines.append(line)
    
    #
    #  Parse the header lines to get metadata
    #
    try:
        kind, units, intvl, loc = getMetaData(hdr_lines)
    except:
        raise Exception('Error parsing the metadata')

    #
    #  First parse the data lines just to find
    #  the date extents.
    #
    early = dt.date(2999,12,31)    # ridiculously far into future
    late  = dt.date(1000, 1, 1)    # ridiculously far into past
    for line in data_lines:
        items = line.split()   # split at whitespace
        if 10 <= len(items) <= 11:
            try:
                yr = int(items[0])
                mn = int(items[1])
                q  = int(items[2])
            except:
                yr = -9999
                mn = -1
                q  = -1

            ok = True
            if (yr < 1700) or (yr > 2200): ok = False
            if (mn < 1)    or (mn > 12):   ok = False
            if (q < 1)     or (q > 4):     ok = False
            if ok:
                try:
                    sd,ed = util.getQtrMonthStartEnd(year=yr, month=mn, qtr=q)
                    d1 = dt.date(yr, mn, sd)
                    d2 = dt.date(yr, mn, ed)
                    early = min(early, d1)
                    late  = max(late,  d2)
                except:
                    pass

    #
    #  How many days of data?
    #
    td = late - early
    ndays = td.days + 1
    if ndays < 1:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl, loc=loc,
                    first=util.MISSING_DATE, last=util.MISSING_DATE,
                    values=[])
        return ds

    #
    #  Now parse the lines to get data values and assign.
    #
    datavals = [util.MISSING_REAL] * ndays
    for line in data_lines:
        items = line.split()   # split at whitespace
        if 10 <= len(items) <= 11:
            try:
                yr = int(items[0])
                mn = int(items[1])
                q  = int(items[2])
                sd,ed = util.getQtrMonthStartEnd(year=yr, month=mn, qtr=q)
                d1 = dt.date(yr, mn, sd)
                for i in range(3,len(items)):
                    val = float(items[i])
                    ndx = (d1 - early).days + i - 3
                    datavals[ndx] = val
            except:
                pass

    #
    #  return value
    #
    try:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl,
                    loc=loc, first=early, last=late, values=datavals)
        return ds
    except:
        raise Exception('Error building DataSeries object for daily CGLRRM')


#--------------------------------------------------------------------
#  Process a set of lines (list of strings) that contain daily data in the
#  new tabular CSV format we have defined.  Note that all comment lines
#  from the original file have already been removed at this point. It is
#  just valid data (and header metadata) lines.
#  Example list of lines (shown here with just one string per line) is:
#  ("INTERVAL: Daily",
#   "UNITS: 10m3s",
#   "2018-03,  57.1, 57.9, 122.1, -10.7, -17.0, [25 more values], 41.3 "
#   "2018-04,  22.3,  9.2, -20.4, -41.6,   1.0, [25 more values],  2.8 "
#
#  This function returns a complete DataSeries object.
#--------------------------------------------------------------------
def parseDailyTable(all_lines):
    #
    #  Separate the header lines from the data lines.
    #
    hdr_lines  = []
    data_lines = []
    for line in all_lines:
        if line.find(':') > 0:
            hdr_lines.append(line)
        else:
            data_lines.append(line)

    #
    #  Parse the header lines to get metadata
    #
    try:
        kind, units, intvl, loc = getMetaData(hdr_lines)
    except:
        raise Exception('Error parsing the metadata')

    #
    #  First parse the data lines just to find
    #  the date extents.
    #
    early = dt.date(2999,12,31)    # ridiculously far into future
    late  = dt.date(1000, 1, 1)    # ridiculously far into past
    for line in data_lines:
        items = [s.strip() for s in line.split(',')]
        if len(items) >= 32:  #JAK?: why allow items > 32?  Shouldnt comments be removed at this point
            try:
                yr = int(items[0].split('-')[0])
                mn = int(items[0].split('-')[1])
            except:
                yr = -9999
                mn = -1

            ok = True
            if (yr < 1700) or (yr > 2200): ok = False
            if (mn < 1)    or (mn > 12):   ok = False
            if ok:
                try:
                    sd = dt.date(yr, mn, 1)
                    ed = dt.date(yr, mn, util.days_in_month(yr,mn))
                    early = min(early, sd)
                    late  = max(late,  ed)
                except:
                    pass

    #
    #  How many days of data?
    #
    td = late - early
    ndays = td.days + 1
    if ndays < 1:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl, loc=loc,
                    first=util.MISSING_DATE, last=util.MISSING_DATE,
                    values=[])
        return ds

    #
    #  Now parse the lines to get data values and assign.
    #
    datavals = [util.MISSING_REAL] * ndays
    for line in data_lines:
        items = [s.strip() for s in line.split(',')]
        if len(items) >= 32:
            try:
                yr = int(items[0].split('-')[0])
                mn = int(items[0].split('-')[1])
                d1 = dt.date(yr, mn, 1)
                mdays = util.days_in_month(yr,mn)
                for i in range(0,mdays):
                    val = float(items[i+2])
                    ndx = (d1 - early).days + i
                    datavals[ndx] = val
            except:
                pass

    #
    #  return value
    #
    try:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl,
                    loc=loc, first=early, last=late, values=datavals)
        return ds
    except:
        raise Exception('Error building DataSeries object for daily table')

#--------------------------------------------------------------------
#  Process a set of lines (list of strings) that contain daily data in the
#  new columnar CSV format we have defined.  Note that all comment lines
#  from the original file have already been removed at this point. It is
#  just valid data (and header metadata) lines.
#  Example list of lines (shown here with just one string per line) is:
#  ("INTERVAL: Daily",
#   "UNITS: 10m3s",
#   "2018-3-1, 57.1"
#   "2018-3-2, 22.3"
#   "2018-3-3, -2.6"
#   "2018-3-4, 14.9"
#
#  This function returns a complete DataSeries object.
#--------------------------------------------------------------------
def parseDailyColumn(all_lines):
    #
    #  Separate the header lines from the data lines.
    #
    hdr_lines  = []
    data_lines = []
    for line in all_lines:
        if line.find(':') > 0:
            hdr_lines.append(line)
        else:
            data_lines.append(line)

    #
    #  Parse the header lines to get metadata
    #
    try:
        kind, units, intvl, loc = getMetaData(hdr_lines)
    except:
        raise Exception('Error parsing the metadata')

    #
    #  First parse the data lines just to find
    #  the date extents.
    #
    early = dt.date(2999,12,31)    # ridiculously far into future
    late  = dt.date(1000, 1, 1)    # ridiculously far into past
    for line in data_lines:
        try:
            items = [s.strip() for s in line.split(',')]
            if len(items) != 2:
                matches = False
            try:
                vals = [int(s) for s in items[0].split('-')]
                if (vals[0] < 1700) or (vals[0] > 2200): ok = False
                if (vals[1] < 1)    or (vals[1] > 12):   ok = False
                if (vals[2] < 1)    or (vals[2] > 31):   ok = False
            except:
                raise Exception('Error parsing the date info')

            ok = True
            if (vals[0] < 1700) or (vals[0] > 2200): ok = False
            if (vals[1] < 1)    or (vals[1] > 12):   ok = False
            if (vals[2] < 1)    or (vals[2] > 31):   ok = False
            if ok:
                try:
                    sd = dt.date(vals[0], vals[1], vals[2])
                    early = min(early, sd)
                    late  = max(late,  sd)
                except:
                    pass
        except:
            raise Exception('Error processing daily data in column format')

    #
    #  How many days of data?
    #
    td = late - early
    ndays = td.days + 1
    if ndays < 1:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl, loc=loc,
                    first=util.MISSING_DATE, last=util.MISSING_DATE,
                    values=[])
        return ds

    #
    #  Now parse the lines to get data values and assign.
    #
    datavals = [util.MISSING_REAL] * ndays
    for line in data_lines:
        items = [s.strip() for s in line.split(',')]
        if len(items) == 2:
            try:
                vals = [int(s) for s in items[0].split('-')]
                yr = vals[0]
                mn = vals[1]
                dy = vals[2]
                ndx = (dt.date(yr, mn, dy) - early).days
                datavals[ndx] = float(items[1])
            except:
                pass

    #
    #  return value
    #
    try:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl,
                    loc=loc, first=early, last=late, values=datavals)
        return ds
    except:
        raise Exception('Error building DataSeries object for daily column')



def parseWeeklyCGLRRM(all_lines):
    #
    #  Separate the header lines from the data lines.
    #
    hdr_lines  = []
    data_lines = []
    for line in all_lines:
        if line.find(':') > 0:
            hdr_lines.append(line)
        else:
            data_lines.append(line)
    
    #
    #  Parse the header lines to get metadata
    #
    try:
        kind, units, intvl, loc = getMetaData(hdr_lines)
    except:
        raise Exception('Error parsing the metadata')

    #
    #  First parse the data lines just to find
    #  the date extents.
    #
    early = dt.date(2999,12,31)    # ridiculously far into future
    late  = dt.date(1000, 1, 1)    # ridiculously far into past
    for line in data_lines:
        items = line.split()   # split at whitespace
        if len(items) == 4:
            try:
                yr = int(items[0])
                mn = int(items[1])
                day  = int(items[2])
            except:
                yr = -9999
                mn = -1
                day  = -1

            ok = True
            if (yr < 1700) or (yr > 2200): ok = False
            if (mn < 1)    or (mn > 12):   ok = False
            if (day < 1)     or (day > 31):     ok = False
            if ok:
                try:
                    d = util.getFridayDate(yr, mn, day)
                    early = min(early, d)
                    late  = max(late,  d)
                except:
                    pass

    #
    #  How many days of data?
    #
    td = late - early
    ndays = td.days + 1
    if ndays < 1:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl, loc=loc,
                    first=util.MISSING_DATE, last=util.MISSING_DATE,
                    values=[])
        return ds

    #
    #  Now parse the lines to get data values and assign.
    #
    datavals = [util.MISSING_REAL] * ndays
    for line in data_lines:
        items = line.split()   # split at whitespace
        if len(items) == 4:
            try:
                yr = int(items[0])
                mn = int(items[1])
                day  = int(items[2])
                d1 = util.getFridayDate(year=yr, month=mn, day=day)
                val = float(items[3])
                ndx = int((d1 - early).days/7)
                datavals[ndx] = val
            except:
                pass

    #
    #  return value
    #
    try:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl,
                    loc=loc, first=early, last=late, values=datavals)
        return ds
    except:
        raise Exception('Error building DataSeries object for daily CGLRRM')


def parseWeeklyColumn(all_lines):
    #
    #  Separate the header lines from the data lines.
    #
    hdr_lines  = []
    data_lines = []
    for line in all_lines:
        if line.find(':') > 0:
            hdr_lines.append(line)
        else:
            data_lines.append(line)
    
    #
    #  Parse the header lines to get metadata
    #
    try:
        kind, units, intvl, loc = getMetaData(hdr_lines)
    except:
        raise Exception('Error parsing the metadata')

    #
    #  First parse the data lines just to find
    #  the date extents.
    #
    early = dt.date(2999,12,31)    # ridiculously far into future
    late  = dt.date(1000, 1, 1)    # ridiculously far into past
    for line in data_lines:
        items = line.split(',')   # split at comma
        if len(items) == 2:
            try:
                vals = [s.strip() for s in items.split('-')]
                yr = int(vals[0])
                mn = int(vals[1])
                day  = int(vals[2])
            except:
                yr = -9999
                mn = -1
                day  = -1

            ok = True
            if (yr < 1700) or (yr > 2200): ok = False
            if (mn < 1)    or (mn > 12):   ok = False
            if (day < 1)     or (day > 31):     ok = False
            if ok:
                try:
                    d = util.getFridayDate(yr, mn, day)
                    early = min(early, d)
                    late  = max(late,  d)
                except:
                    pass

    #
    #  How many days of data?
    #
    td = late - early
    ndays = td.days + 1
    if ndays < 1:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl, loc=loc,
                    first=util.MISSING_DATE, last=util.MISSING_DATE,
                    values=[])
        return ds

    #
    #  Now parse the lines to get data values and assign.
    #
    datavals = [util.MISSING_REAL] * ndays
    for line in data_lines:
        items = line.split(',')   # split at comma
        if len(items) == 2:
            try:
                vals = [s.strip() for s in items.split('-')]
                yr = int(vals[0])
                mn = int(vals[1])
                day  = int(vals[2])
                d1 = util.getFridayDate(year=yr, month=mn, day=day)
                val = float(items[3])
                ndx = int((d1 - early).days/7) 
                datavals[ndx] = val
            except:
                pass

    #
    #  return value
    #
    try:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl,
                    loc=loc, first=early, last=late, values=datavals)
        return ds
    except:
        raise Exception('Error building DataSeries object for daily CGLRRM')



def parseQtrMonthlyCGLRRM(all_lines):
    #
    #  Separate the header lines from the data lines.
    #
    hdr_lines  = []
    data_lines = []
    for line in all_lines:
        if line.find(':') > 0:
            hdr_lines.append(line)
        else:
            data_lines.append(line)

    #
    #  Parse the header lines to get metadata
    #
    try:
        kind, units, intvl, loc = getMetaData(hdr_lines)
    except:
        raise Exception('Error parsing the metadata')

    #
    #  First parse the data lines just to find
    #  the date extents.
    #
    yr_early = 99999    # ridiculously far into future
    yr_late  =     0    # ridiculously far into past
    for line in data_lines:
        items = [s.strip() for s in line.split()]
        if len(items) == 14:
            try:
                yr = int(items[0])
                q  = int(items[1])
            except:
                yr = -9999
                s  = -1

            if yr >= 1:
                try:
                    yr_early = min(yr_early, yr)
                    yr_late  = max(yr_late,  yr)
                except:
                    pass

    #
    #  How many data points?
    #
    nmons = (yr_late - yr_early + 1) * 12
    nqtrs = nmons * 4
    if nqtrs < 1:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl, loc=loc,
                    first=util.MISSING_DATE, last=util.MISSING_DATE,
                    values=[])
        return ds

    #
    #  Now parse the lines to get data values and assign.
    #
    datavals = [util.MISSING_REAL] * nqtrs
    for line in data_lines:
        items = line.split()   # split at whitespace
        if len(items) == 14:
            try:
                yr = int(items[0])
                q  = int(items[1])
                for i in range(2,len(items)):
                    ndx = (yr - yr_early)*12*4 + i - 1  #JAK?: confirm this works with non-continuous data
                    datavals[ndx] = float(items[i])
            except:
                pass

    #
    #  return value
    #
    try:
        early = dt.date(yr_early, 1, 1)
        late  = dt.date(yr_late, 12, 31)
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl,
                    loc=loc, first=early, last=late, values=datavals)
        return ds
    except:
        raise Exception('Error building DataSeries object for monthly CGLRRM')





#--------------------------------------------------------------------
#  Process a set of lines (list of strings) that contain monthly data in the
#  old CGLRRM format.  Note that all comment lines
#  from the original file have already been removed at this point. It is
#  just valid data (and header metadata) lines.
#  Example list of lines (shown here with just one string per line) is:
#  ("INTERVAL: Monthly",
#   "UNITS: cms",
#   "2016  -8.8  19.2   98.5   -3.6  -55.9  41.3  75.0  106.2  26.1  -33.9    4.2   9.6"
#   "2017  57.1  57.9  122.1  -10.7  -17.0  82.0  99.1  136.7  16.8  -15.5  -27.4  41.3"
#
#  This function returns a complete DataSeries object.
#--------------------------------------------------------------------
def parseMonthlyCGLRRM(all_lines):
    #
    #  Separate the header lines from the data lines.
    #
    hdr_lines  = []
    data_lines = []
    for line in all_lines:
        if line.find(':') > 0:
            hdr_lines.append(line)
        else:
            data_lines.append(line)

    #
    #  Parse the header lines to get metadata
    #
    try:
        kind, units, intvl, loc = getMetaData(hdr_lines)
    except:
        raise Exception('Error parsing the metadata')

    #
    #  First parse the data lines just to find
    #  the date extents.
    #
    yr_early = 99999    # ridiculously far into future
    yr_late  =     0    # ridiculously far into past
    for line in data_lines:
        items = [s.strip() for s in line.split()]
        if len(items) == 13:
            try:
                yr = int(items[0])
            except:
                yr = -9999

            if yr >= 1:
                try:
                    yr_early = min(yr_early, yr)
                    yr_late  = max(yr_late,  yr)
                except:
                    pass

    #
    #  How many months of data?
    #
    nmons = (yr_late - yr_early + 1) * 12
    if nmons < 1:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl, loc=loc,
                    first=util.MISSING_DATE, last=util.MISSING_DATE,
                    values=[])
        return ds

    #
    #  Now parse the lines to get data values and assign.
    #
    datavals = [util.MISSING_REAL] * nmons
    for line in data_lines:
        items = line.split()   # split at whitespace
        if len(items) == 13:
            try:
                yr = int(items[0])
                for i in range(1,len(items)):
                    ndx = (yr - yr_early)*12 + i - 1
                    datavals[ndx] = float(items[i])
            except:
                pass

    #
    #  return value
    #
    try:
        early = dt.date(yr_early, 1, 1)
        late  = dt.date(yr_late, 12, 31)
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl,
                    loc=loc, first=early, last=late, values=datavals)
        return ds
    except:
        raise Exception('Error building DataSeries object for monthly CGLRRM')

#--------------------------------------------------------------------
#  Process a set of lines (list of strings) that contain monthly data in the
#  old CGLRRM format.  Note that all comment lines
#  from the original file have already been removed at this point. It is
#  just valid data (and header metadata) lines.
#  Example list of lines (shown here with just one string per line) is:
#  ("INTERVAL: Monthly",
#   "UNITS: cms",
#   "2016, -8.8, 19.2,  98.5,  -3.6, -55.9, 41.3, 75.0, 106.2, 26.1, -33.9,   4.2,  9.6"
#   "2017, 57.1, 57.9, 122.1, -10.7, -17.0, 82.0, 99.1, 136.7, 16.8, -15.5, -27.4, 41.3"
#
#  This function returns a complete DataSeries object.
#--------------------------------------------------------------------
def parseMonthlyTable(all_lines):
    #
    #  Separate the header lines from the data lines.
    #
    hdr_lines  = []
    data_lines = []
    for line in all_lines:
        if line.find(':') > 0:
            hdr_lines.append(line)
        else:
            data_lines.append(line)

    #
    #  Parse the header lines to get metadata
    #
    try:
        kind, units, intvl, loc = getMetaData(hdr_lines)
    except:
        raise Exception('Error parsing the metadata')

    #
    #  First parse the data lines just to find
    #  the date extents.
    #
    yr_early = 99999    # ridiculously far into future
    yr_late  =     0    # ridiculously far into past
    for line in data_lines:
        items = [s.strip() for s in line.split(',')]
        if len(items) == 13:
            try:
                yr = int(items[0])
            except:
                yr = -9999

            if yr >= 1:
                try:
                    yr_early = min(yr_early, yr)
                    yr_late  = max(yr_late,  yr)
                except:
                    pass

    #
    #  How many months of data?
    #
    nmons = (yr_late - yr_early + 1) * 12
    if nmons < 1:
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl, loc=loc,
                    first=util.MISSING_DATE, last=util.MISSING_DATE,
                    values=[])
        return ds

    #
    #  Now parse the lines to get data values and assign.
    #
    datavals = [util.MISSING_REAL] * nmons
    for line in data_lines:
        items = [s.strip() for s in line.split(',')]
        if len(items) == 13:
            try:
                yr = int(items[0])
                for i in range(1,len(items)):
                    ndx = (yr - yr_early)*12 + i - 1
                    datavals[ndx] = float(items[i])
            except:
                pass

    #
    #  return value
    #
    try:
        early = dt.date(yr_early, 1, 1)
        late  = dt.date(yr_late, 12, 31)
        ds = databank.DataSeries(kind=kind, units=units, intvl=intvl,
                    loc=loc, first=early, last=late, values=datavals)
        return ds
    except:
        raise Exception('Error building DataSeries object for monthly table')






