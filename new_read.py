import re
import datetime as dt
import databank as databank
import databank_util as util


tab = 1
fill = -999.9

def get_valid_lines(filename):
    '''--------------------------------------------------------------------
    Read the specified file, returning an ordered list of strings.
    Each string is a line in the file that has valid data and all
    comments are removed. Comments are defined as anything on a
    line that comes after a # character.  If a line ends up being
    blank, it is not included in the returned list.  Quick example...
    File content:
      # this is a header comment
      # Year Mon Day Value
        1990  01  01 10.50
        1990  01  02  3.10
        1990  01  03 -9.99    # this is a missing value
        1990  01  04 21.00
        #  a bunch of data is missing here
                            # BLANK LINE
        1990  12  31  4.44

    Returned list:
    ('  1990  01  01 10.50', '  1990  01  02  3.10',
     '  1990  01  03 -9.99', '  1990  01  04 21.00',
     '  1990  12  31  4.44')

    The 9-line file turned into a 5-string list.
    --------------------------------------------------------------------
    '''
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

def get_meta_data(all_lines):
    '''--------------------------------------------------------------------
    Parse all lines of the file looking for lines that match the format
    of metadata specifiers.  When one of those is encountered, try to
    parse out the metadata in it.

    Note that with old CGLRRM files, the kind (type) and location metadata
    was not part of the header.  It was suggested to include it as part of
    the comments, but they were not part of a defined header entry.

    The old CGLRRM looked at only the first character of interval
    specification, so we will handle that as a special case.
    '''
    mkind  = 'na'
    munits = 'na'
    mintvl = 'na'
    mloc   = 'na'

    for line in all_lines:
        try:
            if line.find(':'):
                items = line.split(':')
                if len(items) == 2:
                    lstr = items[0].strip().lower()
                    rstr = items[1].strip().lower()
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
                            if rstr[0] == 'd': t = 'dy'
                            if rstr[0] == 'w': t = 'wk'
                            if rstr[0] == 'q': t = 'qm'
                            if rstr[0] == 'm': t = 'mn'
                            if rstr[0] == 'y': t = 'yr'
                            mintvl = databank.DataInterval(t).primaryName()
        except:
            raise Exception('Error in header of the file')

    return mkind, munits, mintvl, mloc


def detect_format(filename, data_lines, intvl):
    ''' Detect the format of filename based on the given data_lines
    and intvl.

    Loop through data_lines and check the number of items on each line,
    check for the type of delimitter, and confirm that all date strings
    can be cast as integers and that all data values can be cast as
    floats.

    Returns:
    --------
    a string representing format name (cglrrm, column, table or unknown)
    '''
    yy = None
    mm = None
    dd = None
    qq = None
    range_ok = True # are the date values possible (month=[1,12])?
    data_ok = True  # are the dates and data values actually numbers?
    format_ok = True # does this file match and acceptable format?
    if not data_lines: raise Exception('data_lines are empty in '+filename)

    if intvl == 'dy':
        #      ACCEPTED DAILY FORMATS
        #  CGLRRM: YYYY MM QQ VAL1 VAL2 ... VAL7 (VAL8)
        #  TABLE: YYYY-MM, VAL1, VAL2, ... VAL31(,)
        #  COLUMN: YYYY-MM-DD, VAL1(,)
        for num, line in enumerate(data_lines):
            cglrrm = False
            table = False
            column = False
            items = [s.strip() for s in line.split() if s]  # old format (space delim)
            if (len(items) == 10 or len(items) == 11) and ',' not in line:
                cglrrm = True
                first = 3
                yy = items[0]
                mm = items[1]
                qq = items[2]
            else:
                items = [s.strip() for s in line.split(',') if s] # new format (comma delim)
                if len(items) == 32:
                    table = True
                    first = 2
                    yy = items[0].split('-')[0]
                    mm = items[0].split('-')[1]
                if len(items) == 2:
                    column = True
                    first = 2
                    yy = items[0].split('-')[0]
                    mm = items[0].split('-')[1]
                    dd = items[0].split('-')[2]

            # ensure one and only one format was matched
            if sum([cglrrm, table, column]) != 1: format_ok = False

            # check that data/dates are numbers
            try:
                vals = [float(s) for s in items[first::]]
                yy = int(yy)
                mm = int(mm)
                if qq: qq = int(qq)
                if dd: dd = int(dd)
            except:
                data_ok = False
                break

            # check date range
            if yy < 1: range_ok = False
            if mm < 1 or mm > 12: range_ok = False
            if qq:
                if qq < 1 or qq > 4: range_ok = False
            if dd:
                if dd < 1 or dd > 31: range_ok = False


            if not all([format_ok, data_ok, range_ok]): break


    if intvl == 'wk':
        #      ACCEPTED WEEKLY FORMATS
        #  CGLRRM: YYYY MM DD VAL1
        #  COLUMN: YYYY-MM-DD, VAL1(,)
        for num, line in enumerate(data_lines):
            cglrrm = False
            column = False
            items = [s.strip() for s in line.split() if s]  # old format (space delim)
            if len(items) == 4 and ',' not in line:
                cglrrm = True
                first = 3
                yy = items[0]
                mm = items[1]
                dd = items[2]
            else:
                items = [s.strip() for s in line.split(',') if s] # new format (comma delim)
                if len(items) == 2:
                    column = True
                    first = 1
                    yy = items[0].split('-')[0]
                    mm = items[0].split('-')[1]
                    dd = items[0].split('-')[2]

            # ensure one and only one format was matched
            if sum([cglrrm, column]) != 1: format_ok = False

            # check that data/dates are numbers
            try:
                vals = [float(s) for s in items[first::]]
                yy = int(yy)
                mm = int(mm)
                dd = int(dd)
            except:
                data_ok = False
                break

            # check that dates are possible
            if yy < 1:             range_ok = False
            if mm < 1 or mm > 12:  range_ok = False
            if dd < 1 or dd > 31: range_ok = False

            if not all([format_ok, data_ok, range_ok]): break

    if intvl == 'qm':
        #    ACCEPTED QTR-MONTHLY FORMATS
        #  CGLRRM: YYYY QQ VAL1 VAL2 ... VAL12
        #  TABLE: YYYY-QQ, VAL1, VAL2, ... VAL12(,)
        #  COLUMN: YYYY-MM-QQ, VAL1(,)
        for num, line in enumerate(data_lines):
            cglrrm = False
            table = False
            column = False
            items = [s.strip() for s in line.split() if s]
            if len(items) == 14 and ',' not in line:
                cglrrm = True
                first = 2
                yy = items[0]
                qq = items[1]
            else:
                items = [s.strip() for s in line.split(',') if s]
                if len(items) == 13:
                    table = True
                    first = 1
                    yy = items[0].split('-')[0]
                    qq = items[0].split('-')[1]
                if len(items) == 2:
                    column = True
                    first = 1
                    yy = items[0].split('-')[0]
                    mm = items[0].split('-')[1]
                    qq = int(items[0].split('-')[2])

            # ensure one and only one format was matched
            if sum([cglrrm, table, column]) != 1: format_ok = False

            # check that data/dates are numbers
            try:
                vals = [float(s) for s in items[first::]]
                yy = int(yy)
                qq = int(qq)
                if mm: mm = int(mm)
            except:
                data_ok = False
                break

            # check that dates are possible
            if yy < 1: range_ok = False
            if qq < 1 or qq > 4: range_ok = False
            if mm:
                if mm < 1 or mm > 12:  range_ok = False

            if not all([format_ok, data_ok, range_ok]): break


    if intvl == 'mn':
        #      ACCEPTED MONTHLY FORMATS
        #  CGLRRM: YYYY VAL1 VAL2 ... VAL12
        #  TABLE: YYYY, VAL1, VAL2, ... VAL12(,)
        #  COLUMN: YYYY-MM, VAL1(,)
        for num, line in enumerate(data_lines):
            cglrrm = False
            table = False
            column = False
            items = [s.strip() for s in line.split() if s]
            if len(items) == 13 and ',' not in line:
                cglrrm = True
                first = 2
                yy = int(items[0])
            else:
                items = [s.strip() for s in line.split(',') if s]
                if len(items) == 13:
                    table = True
                    first = 2
                    yy = items[0].split('-')[0]
                if len(items) == 2:
                    column = True
                    first = 1
                    yy = items[0].split('-')[0]
                    mm = items[0].split('-')[1]


            # ensure one and only one format was matched
            if sum([cglrrm, table, column]) != 1: format_ok = False

            # check that data/dates are numbers
            try:
                vals = [float(s) for s in items[first::]]
                yy = int(yy)
                if mm: mm = int(mm)
            except:
                data_ok = False
                break


            # check that dates are possible
            if yy < 1:             range_ok = False
            if mm:
                if mm < 1 or mm > 12:  range_ok = False

            if not all([format_ok, data_ok, range_ok]): break


    # raise exceptions
    if not format_ok:
        raise Exception('Error determining format for ' +filename+' near line '
                        '#:'+str(num)+' (not counting hdrs/comments)')
    if not range_ok:
        raise Exception('Dates exceed acceptable range in '+filename+' near '
                        'line #:'+str(num)+' (not counting hdrs/comments)')
    if not data_ok:
        raise Exception('Data vals or dates could not be cast as floats in '
                        + filename+' near line #:'+str(num)+' (not counting '
                        'hdrs/comments)')

    if cglrrm: return 'cglrrm'
    if table: return 'table'
    if column: return 'column'
    return 'unknown'


#--------------------------------------------------------------------
def read_file(filename, kind=None, units=None, intvl=None, loc=None):
    '''
    Read in data and metadata from filename and return a dataseries
    object.

    Parameters
    ----------
    filename: string
        The desired filename to read from.
    kind : string, optional
        The kind of data ('precip') to be read in.  If filename    does
        not contain kind metadata (header info), kind must be set
        on the function call.
    units : string, optional
        The units of data ('mm') to be read in.  If filename does not
        contain units metadata (header info), units must be set.
    intvl : string, optional
        The intierval of data ('weekly') to be read in.  If filename
        does not contain intvl metadata (header info), intvl must be set.
    loc : string, optional
        The loc of data ('superior') to be read in.  If filename does
        not contain loc metadata (header info), loc must be set.

    Returns
    -------
    dataseries : object
        an object of class DataSeries with attributes dataKind,
        dataUnits, dataInterval, dataLocation, startDate,
        endDate, and dataVals (the actual data)

    Notes
    -----
    If keywords kind, units, intvl, or loc are included in function call
    AND included in the metadata of filename, then they must match,
    otherwise an exception will be raised.

    Classic CGLRRM files were NOT required to include loc or kind in
    the metadata (header info) so these keyword args will likely
    be required when processing these files.
    '''


    #
    #  Get all of the non-comment content from the file as
    #  a list of strings
    #
    all_lines = get_valid_lines(filename)

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
        fkind, funits, fintvl, floc = get_meta_data(all_lines)
    except:
        raise Exception('Unable to process metadata from ' + filename)

    #
    #  If any of the metadata items from the file are undefined,
    #  set that metadata object to None
    #
    if fkind  == 'na': fkind  = None
    if funits == 'na': funits = None
    if fintvl == 'na': fintvl = None
    if floc   == 'na': floc   = None

    #
    #  Do we have sufficient metadata to continue?
    #

    if not mkind  and not fkind:  raise Exception('Missing metadata (kind) for'
                                                  ' processing ' + filename)
    if not munits and not funits: raise Exception('Missing metadata (units) for'
                                                  ' processing ' + filename)
    if not mintvl and not fintvl: raise Exception('Missing metadata (interval)'
                                                  ' for processing ' + filename)
    if not mloc   and not floc:   raise Exception('Missing metadata (location)'
                                                  ' for processing ' + filename)

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


    if mintvl == 'dy' or mintvl == 'wk' or mintvl == 'qm' or mintvl == 'mn':
        # beginning of what procData did (as far as I can tell)
        start = util.MISSING_DATE       # "missing" date value
        end = util.MISSING_DATE       # "missing" date value
        data_lines = []
        for line in all_lines:
            try:
                if line.find(':') > 0:
                    items = line.split(':')
                    if len(items) != 2:
                        raise Exception('Invalid header content or misplaced colon :')
                else:
                    data_lines.append(line)
            except:
                raise Exception('Error separating header and data lines.')

        format_name = detect_format(filename, data_lines, mintvl)
        # end of what procData did
    else:
        raise Exception('Invalid interval')

    if format_name == 'unknown':
        raise Exception('Format of ' + filename + ' could not be recognized')
    try:
        start, end, datavals = parse_data(filename, format_name, mintvl,
                                          data_lines)
    except:
        raise Exception('Error calling parse_data for '+filename+';  format:'
                        +format_name+'; interval:'+mintvl)
    if not datavals:
        raise Exception('No data read in for '+filename+': format:'+format_name
                        +'; interval:'+mintvl)
    if start > end:
        raise Exception('endDate precedes startDate (likely that no dates were'
                        'recognized) for '+filename+': format:'+format_name
                        +'; interval:'+mintvl)

    ds = databank.DataSeries(kind=mkind, units=munits, intvl=mintvl, loc=mloc,
                             first=start, last=end, values=datavals)
    return ds


def parse_data(filename, format_name, intvl, data_lines):
    '''
    --------------------------------------------------------------------
    Process a set of lines (list of strings) that contain daily data in
    the format used by the old CGLRRM.  Note that all comment lines from the
    original file have already been removed at this point. It is just valid
    data (and header metadata) lines.
    Example list of lines (shown here with just one string per line) is:
    ("INTERVAL: Daily",
     "UNITS: 10m3s",
     "2018  3 1 -99999. -99999. -99999. -99999. -99999. -99999. -99999. -99999."
     "2018  3 2     57.     57.    122.    -10.    -17.     51.    266."
     "2018  3 3    352.    154.    161.    796.    329.    973.    739.    389."
     "2018  3 4    272.    196.    392.    536.    127.    140.    156.    422."
     "2018  4 1    242.    136.     64.     65.    206.    310.    167.    147."
     "2018  4 2    -23.     59.    558.    213.    362.    402.    182."
     "2018  4 3    142.      6.     58.     84.    157.     82.     29.     99."
     "2018  4 4    141.     85.     98.    424.    202.     39.      1.")

    This function returns a complete DataSeries object.
    --------------------------------------------------------------------
    Psuedo code:
            parse_data(args)
                 selection interval
                    selection format
                        loop thru to get start, end
                        loop thru to get data values
                return data start,end, data
     '''

    # initialize return values
    start = dt.date(2999, 12, 31)    # ridiculously far into future
    end = dt.date(1000, 1, 1)    # ridiculously far into past
    datavals = None

    if intvl == 'dy':
        #      ACCEPTED DAILY FORMATS
        #  CGLRRM: YYYY MM QQ VAL1 VAL2 ... VAL7 (VAL8)
        #  TABLE: YYYY-MM, VAL1, VAL2, ... VAL31(,)
        #  COLUMN: YYYY-MM-DD, VAL1(,)

        # first loop through to get the first/last date
        if format_name == 'cglrrm':
            for line in data_lines:
                items = [s.strip() for s in line.split() if s]
                yy = int(items[0])
                mm = int(items[1])
                qq = int(items[2])
                sd, ed = util.getQtrMonthStartEnd(year=yy, month=mm, qtr=qq)
                d1 = dt.date(yy, mm, sd)
                d2 = dt.date(yy, mm, ed)
                start = min(start, d1)
                end = max(end, d2)

        if format_name == 'table':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                mm = int(items[0].split('-')[1])
                ndays = util.days_in_month(year=yy, month=mm)
                d1 = dt.date(yy, mm, 1)
                d2 = dt.date(yy, mm, ndays)
                start = min(start, d1)
                end = max(end, d2)

        if format_name == 'column':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                mm = int(items[0].split('-')[1])
                dd = int(items[0].split('-')[2])
                d1 = dt.date(yy, mm, dd)
                d2 = d1
                start = min(start, d1)
                end = max(end, d2)


        ndays = (end - start).days + 1
        if ndays < 1:
            return start, end, datavals

        #  Now parse the lines to get data values and assign.
        datavals = [util.MISSING_REAL] * ndays
        if format_name == 'cglrrm':
            for line in data_lines:
                items = [s.strip() for s in line.split() if s]
                yy = int(items[0])
                mm = int(items[1])
                qq = int(items[2])
                sd, ed = util.getQtrMonthStartEnd(year=yy, month=mm, qtr=qq)
                d1 = dt.date(yy, mm, sd)
                for i in range(3, len(items)):
                    val = float(items[i])
                    ndx = (d1 - start).days + i - 3
                    datavals[ndx] = val

        if format_name == 'table':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                mm = int(items[0].split('-')[1])
                d1 = dt.date(yy, mm, 1)
                ndays = util.days_in_month(year=yy, month=mm)
                for i in range(1, ndays):
                    val = float(items[i])
                    ndx = (d1 - start).days + i - 1
                    datavals[ndx] = val

        if format_name == 'column':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                mm = int(items[0].split('-')[1])
                dd = int(items[0].split('-')[2])
                d1 = dt.date(yy, mm, dd)
                ndx = (d1 - start).days - 1
                datavals[ndx] = float(items[1])



    if intvl == 'wk':
        #      ACCEPTED WEEKLY FORMATS
        #  CGLRRM: YYYY MM DD VAL1
        #  COLUMN: YYYY-MM-DD, VAL1(,)
        # note: for weekly, all formats have same formatting (just different delims)
        # lets replace the delimiters so we can process them all the same way
        # This might not be very pythonic/good style but eliminates redundant code

        if format_name == 'cglrrm':
            for i, line in enumerate(data_lines):
                # replace YYYY MM DD with YYYY-MM-DD
                line = re.sub(r"(^[0-9]{4})\s+([0-9]{1,2})\s+([0-9]{1,2})", r"\1-\2-\3", line)
                # replace all white spaces with ", "
                line = re.sub(r"\s+", ", ", line)
                data_lines[i] = line

        # loop to get start/end
        for line in data_lines:
            items = [s.strip() for s in line.split(',') if s]
            yy = int(items[0].split('-')[0])
            mm = int(items[0].split('-')[1])
            dd = int(items[0].split('-')[2])
            d1 = util.getFridayDate(year=yy, month=mm, day=dd)
            start = min(start, d1)
            end = max(end, d1)


        nweeks = int((end - start).days/7) + 1
        if nweeks < 1:
            return start, end, datavals
        datavals = [util.MISSING_REAL] * nweeks

        # loop to get data values
        for line in data_lines:
            items = [s.strip() for s in line.split(',') if s]
            yy = int(items[0].split('-')[0])
            mm = int(items[0].split('-')[1])
            dd = int(items[0].split('-')[2])
            d1 = util.getFridayDate(year=yy, month=mm, day=dd)
            ndx = int((d1 - start).days/7)
            datavals[ndx] = float(items[1])


    if intvl == 'qm':
       #      ACCEPTED QM FORMATS
       #  CGLRRM: YYYY QQ VAL1 VAL2 ... VAL12
       #  TABLE: YYYY-QQ, VAL1, VAL2, ..., VAL12
       #  COLUMN: YYYY-MM-QQ, VAL1(,)

    # first loop through to get start/end dates
        if format_name == 'column':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                mm = int(items[0].split('-')[1])
                qq = int(items[0].split('-')[2])
                sd, ed = util.getQtrMonthStartEnd(year=yy, month=mm, qtr=qq)
                d1 = dt.date(yy, mm, sd)
                d2 = dt.date(yy, mm, ed)
                if d1 <= start:
                    start = d1
                    start_mon = mm
                    start_qtr = qq
                if d2 >= end:
                    end = d2
                    end_mon = mm
                    end_qtr = qq
            nqtrs = 48*(end.year - start.year) + 4*(end_mon - start_mon) + (end_qtr - start_qtr) + 1
            datavals = [util.MISSING_REAL] * nqtrs

        if format_name == 'cglrrm':
            for i, line in enumerate(data_lines):
                # replace YYYY QQ with YYYY-QQ
                line = re.sub(r"(^[0-9]{4})\s+([0-9]{1,2})", r"\1-\2", line)
                # replace all white spaces with ", "
                line = re.sub(r"\s+", ", ", line)
                data_lines[i] = line

        if format_name == 'cglrrm' or format_name == 'table':
            start_qtr = 1  # these formats can NOT have partial years
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                sd = util.getQtrMonthStartEnd(year=yy, month=1, qtr=1)[0]
                ed = util.getQtrMonthStartEnd(year=yy, month=12, qtr=4)[1]
                d1 = dt.date(yy, 1, sd)
                d2 = dt.date(yy, 12, ed)
                start = min(start, d1)
                end = max(end, d2)
            nqtrs = 48*(end.year - start.year + 1)
            datavals = [util.MISSING_REAL] * nqtrs

        # now loop through to get datavals
        if format_name == 'column':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                mm = int(items[0].split('-')[1])
                qq = int(items[0].split('-')[2])

                yy_delta = yy - start.year
                mm_delta = mm - start_mon
                qq_delta = qq - start_qtr

                ndx = 48*yy_delta + 4*mm_delta + qq_delta
                datavals[ndx] = float(items[1])


        if format_name == 'cglrrm' or format_name == 'table':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                qq = int(items[0].split('-')[1])

                yy_delta = yy - start.year
                qq_delta = qq - start_qtr

                for i in range(1, len(items)):
                    ndx = 48*yy_delta + qq_delta + 4*(i - 1)
                    datavals[ndx] = float(items[i])


    if intvl == 'mn':
       #      ACCEPTED MN FORMATS
       #  CGLRRM: YYYY VAL1 VAL2 ... VAL12
       #  TABLE: YYYY, VAL1, VAL2, ..., VAL12
       #  COLUMN: YYYY-MM, VAL1(,)

    # first loop through to get start/end dates
        if format_name == 'column':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                mm = int(items[0].split('-')[1])
                d1 = dt.date(yy, mm, 1)
                ndays = util.days_in_month(yy, mm)
                d2 = dt.date(yy, mm, ndays)
                start = min(start, d1)
                end = max(end, d2)
                nmonths = 12*(end.year - start.year) + (end.month - start.month + 1)

        if format_name == 'cglrrm':
            for i, line in enumerate(data_lines):
                line = re.sub(r"\s+", ", ", line)
                data_lines[i] = line

        if format_name == 'cglrrm' or format_name == 'table':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0])
                d1 = dt.date(yy, 1, 1)
                d2 = dt.date(yy, 12, 31)
                start = min(start, d1)
                end = max(end, d2)
                nmonths = 12*(end.year - start.year + 1)

        datavals = [util.MISSING_REAL] * nmonths
        # now loop through to get datavals
        if format_name == 'column':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0].split('-')[0])
                mm = int(items[0].split('-')[1])

                yy_delta = yy - start.year
                mm_delta = mm - start.month

                ndx = 12*yy_delta + mm_delta
                datavals[ndx] = float(items[1])


        if format_name == 'cglrrm' or format_name == 'table':
            for line in data_lines:
                items = [s.strip() for s in line.split(',') if s]
                yy = int(items[0])

                yy_delta = yy - start.year

                for i in range(1, len(items)):
                    ndx = 12*yy_delta + i - 1
                    datavals[ndx] = float(items[i])


    return start, end, datavals
