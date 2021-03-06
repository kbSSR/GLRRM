#/bin/python

#----------------------------------------------------------------
#  This is a really basic example of how the overall GLRRM might
#  be structured to use the databank repository.  The actual
#  implementation of GLRRM will be very different, once it is
#  developed.  This is mainly intended as a demonstration of how
#  to use the repository, while also illustrating the basic structure
#  that Tim Hunter had in mind when he developed the design documents.
#-----------------------------------------------------------------

import sys
from copy import copy, deepcopy
import datetime

import databank
import databank_io
import databank_util

#------------------------------------------------------
#  Define lake surface areas for each basin
#  We will use the coordinated values, in sq meters
sup_area = 8.21e10
mhu_area = 1.17e11
stc_area = 1.11e09
eri_area = 2.57e10

#------------------------------------------------------
#  Define a few other constants that I will use.
#  e.g. I am assuming a fixed 30-day month
#
seconds_per_month = 30.0 * 86400.0

#---------------------------------------------------------------------------------
def read_main_config(filename):
    outdir = None
    sdate  = None
    edate  = None
    suplev = -99.9
    mhulev = -99.9
    stclev = -99.9
    erilev = -99.9

    with open(filename, "r") as f:
        for line in f:
            s1 = line_for_parsing(line)
            if s1.find('#') < 0:
                p=parse1(s1)
                if (p):
                    if p[0].strip() == 'title1':
                        title1 = p[1]
                    elif p[0].strip() == 'title2':
                        title2 = p[1]
                    elif p[0].strip() == 'title3':
                        title3 = p[1]
                    elif p[0].strip() == 'startdate':
                        print('Found start date: ', p[1])
                        y,m,d = p[1].split(',')
                        sdate = datetime.date(int(y), int(m), int(d))
                    elif p[0].strip() == 'enddate':
                        print('Found end date: ', p[1])
                        y,m,d = p[1].split(',')
                        edate = datetime.date(int(y), int(m), int(d))
                    elif p[0].strip() == 'output directory':
                        outdir = p[1].strip()
                    elif p[0].strip() == 'sup start level':
                        s = p[1].split()
                        suplev = float(s[0])
                    elif p[0].strip() == 'mhu start level':
                        s = p[1].split()
                        mhulev = float(s[0])
                    elif p[0].strip() == 'st. c start level':
                        s = p[1].split()
                        stclev = float(s[0])
                    elif p[0].strip() == 'eri start level':
                        s = p[1].split()
                        erilev = float(s[0])
                else:
                    print('parse1 failed')

    return outdir, sdate, edate, suplev, mhulev, stclev, erilev



#---------------------------------------------------------------------------------
#  Given a line of text (i.e. a string)
#  1. strip off any comments (everything at/after the first # character)
#  2. convert to all lowercase
#
def line_for_parsing(line):
    i = line.find('#')
    s = line
    if (i >= 0):
       s = line[0:i-1].rstrip()
    return s.lower()


#---------------------------------------------------------------------------------
#  Given a line of text (i.e. a string)
#  Look for the first colon.  If you find one return a tuple with
#  everything to the left of the colon and everything to the right
#  of the colon.
#  If no colon is found, return None.
#  e.g.
#     'startdate: 2001,01,01'          -> ('startdate', ' 2001,01,01')
#     'starttime: 2001-01-01 18:00:00' -> ('starttime', ' 2001-01-01 18:00:00')
#     'startdate= 2001,01,01'          -> None
#
def parse1(line):
    i=line.find(':')
    if (i > 0):
        a = line[0:i]
        b = line[i+1:]
        return a,b




#--------------------------------------------------------------------------------
#
#  Create the data repository object.  This will persist
#  IN MEMORY until the script exits.  It does NOT create any
#  kind of run-to-run persistent file or database.  This is
#  the behavior requested by the committee.
#
the_vault = databank.DataVault()

#
#  Read the main configuration file.  This file will specify
#  which models are being used, dates, etc.  i.e. the overall
#  behavior for this run. The procedure returns a tuple with:
#  (output_dir, start_date, end_date, sup_level, mh_level,
#  stc_level, eri_level).  A real implementation, of course,
#  would need to contain much more.
#
maincfg = read_main_config('data/example/example_config.txt')
outdir      = maincfg[0]
model_sdate = maincfg[1]
model_edate = maincfg[2]
suplev      = maincfg[3]
mhulev      = maincfg[4]
stclev      = maincfg[5]
erilev      = maincfg[6]

#
#  Read monthly NBS values for each lake, and store each of them
#  into the vault.
#
#  Note that each of these read operations creates/clears the
#  DataSeries object, which I reuse, because I don't need to keep
#  it around persistently.  The data is stored into the vault and I
#  can retrieve a copy at any time.
#
#  Another thing to note is that I don't need to worry about units
#  at this stage, because the databank will normalize things internally
#  and I can specify the units I need when I retrieve the data.
#
nbs = databank_io.read_file('data/example/nbs_sup.txt')
the_vault.deposit(nbs)

nbs = databank_io.read_file('data/example/nbs_mhu.txt')
the_vault.deposit(nbs)

nbs = databank_io.read_file('data/example/nbs_stc.txt')
the_vault.deposit(nbs)

nbs = databank_io.read_file('data/example/nbs_eri.txt')
the_vault.deposit(nbs)

#
#  Now I need to know what the overall period of record is for
#  the data that I stored.  I will retrieve each of the monthly
#  NBS data sets, and find the overlapping period of record.
#
#  I don't care about the units because I will not be using the
#  actual data here, but I have to specify something, so I arbitrarily 
#  have chosen 'cfs'.
#
data_start = datetime.date(1900, 1, 1)      # initialize to far past date
data_end   = datetime.date(2099, 1, 1)      # initialize to far future date

nbs = the_vault.withdraw(kind='nbs', units='cfs', intvl='mon', loc='sup')
if nbs.startDate > data_start:
    data_start = nbs.startDate
if nbs.endDate < data_end:
    data_end = nbs.endDate

nbs = the_vault.withdraw(kind='nbs', units='cfs', intvl='mon', loc='mhu')
if nbs.startDate > data_start:
    data_start = nbs.startDate
if nbs.endDate < data_end:
    data_end = nbs.endDate


nbs = the_vault.withdraw(kind='nbs', units='cfs', intvl='mon', loc='stc')
if nbs.startDate > data_start:
    data_start = nbs.startDate
if nbs.endDate < data_end:
    data_end = nbs.endDate


nbs = the_vault.withdraw(kind='nbs', units='cfs', intvl='mon', loc='eri')
if nbs.startDate > data_start:
    data_start = nbs.startDate
if nbs.endDate < data_end:
    data_end = nbs.endDate

#
#  Do I have sufficient data stored to run my model for the period that
#  was specified in the config file?
#
if model_start < data_start:
    print('Insufficient data to run the model.')
    print('Data in files starts too late.')
    sys.exit(1)

if model_end > data_end:
    print('Insufficient data to run the model.')
    print('Data in files ends too soon.')
    sys.exit(1)

#
#  Compute the sequence of lake levels using our
#  super-unrealistic water balance models.
#  Note how these models retrieve their inputs from the
#  vault and store their outputs into the vault.
#  I am simply passing to them the required period of record
#  and starting levels.
#
ok = silly_supreg(the_vault, model_start, model_end, suplev)
if !ok:
    print('Error in the Superior regulation model')
    sys.exit(1)

ok = silly_midlakes(the_vault, model_start, model_end, mhulev, stclev, erilev)
if !ok:
    print('Error in the middle lakes model')
    sys.exit(1)



def silly_supreg(dvault, sdate, edate, sup_startlev):
    #
    #  Get nbs values for the entire period of interest.
    #  Notice that we are getting the NBS values expressed in
    #  units of meters over the lake surface.  Databank is
    #  doing that conversion for us.
    #
    nbs_sup = dvault.withdraw(kind='nbs', units='meters', intvl='mon', loc='sup',
                              first=model_start, last=model_end)
    delta = edate - sdate
    
    #
    #  Create blank lists for the 3 timeseries we will create.
    #  Daily Sup levels
    #  Daily StMarys flows
    #
    suplevd = [None] * (delta.months+1)
    smrflow = [None] * (delta.months+1)

    slev_today = sup_startlev
    for i in range(0, delta.months+1):
        thisDay = sdate + datetime.timedelta(i)

        #
        #  St Marys flow is computed by an extremely unrealistic
        #  rule created by Tim for this demo. 
        #
        #  Assume a basic flow in the St. Marys River of 2100 cms.
        #  If the nbs for Sup is more than that, increase the flow
        #  by 1/2 of the excess.
        #  If the nbs for Sup is less than that, decrease the flow
        #  by 1/2 of the deficiency.
        #  If the resulting level of Sup is > 183.80m or < 183.00m, then
        #  adjust the flow to keep Superior levels within that range.
        #
        sfnbs = (nbs_sup[i] * sup_area) / seconds_per_month      # cubic meters per second
        smflow = 2100.0 + (sfnbs-2100)/2.0
        sup_ts = sfnbs - smflow/sup_area
        slevd = sup_ts / sup_area                       # sup level delta for today
        newlev = slev_today + slevd
        if newlev > 183.80:
            adj = (newlev - 183.8) * sup_area           # cubic meters
            smflow = smflow + adj/seconds_per_month
            newlev = 183.80
        elif newlev < 183.00:
            adj = (183.0 - newlev) * sup_area           # cubic meters
            smflow = smflow - adj/seconds_per_month
            newlev = 183.00
            
        suplevd[i] = newlev
        smrflow[i] = smflow
        slev_today = newlev
        
    #
    #  Now store the suplevd and smrflow sequences in the vault
    #
    dvault.deposit_data(kind='level', units='meters', intvl='mon', loc='sup', 
                     first=sdate, last=edate, values=suplevd):
    dvault.deposit_data(kind='flow', units='cms', intvl='mon', loc='stmarys', 
                     first=sdate, last=edate, values=smrflow):


def silly_midlakes(dvault, sdate, edate, mhu_startlev, stc_startlev, eri_startlev):
    nbs_mhu = dvault.withdraw(kind='nbs', units='meters', intvl='mon', loc='mhu',
                              first=sdate, last=edate)
    nbs_stc = dvault.withdraw(kind='nbs', units='meters', intvl='mon', loc='stc',
                              first=sdate, last=edate)
    nbs_eri = dvault.withdraw(kind='nbs', units='meters', intvl='mon', loc='eri',
                              first=sdate, last=edate)
    smrflow = dvault.withdraw(kind='flow', units='cms', intvl='mon', loc='smr',
                              first=sdate, last=edate)
                              

    delta = edate - sdate
    
    #
    #  Create blank lists for the 3 timeseries we will create.
    #  Daily lake levels
    #  Daily river flows
    #
    mhulevd = [None] * (delta.months+1)
    stclevd = [None] * (delta.months+1)
    erilevd = [None] * (delta.months+1)
    stcflow = [None] * (delta.months+1)
    detflow = [None] * (delta.months+1)

    mlev_today = mhu_startlev
    slev_today = stc_startlev
    elev_today = eri_startlev
    for i in range(0, delta.months+1):
        thisDay = sdate + datetime.timedelta(i)

        
        #
        #  Now determine what the result would be for Mhu levels, using
        #  that St. Marys flow along with the Mhu nbs.
        #  
        mhu_cms = smflow + (nbs_mhu[i]*mhu_area / seconds_per_month)     # total supply in cms
        
        #  Assume a basic flow in the St. Clair River of 5100 cms.
        #  If mhu_cms is more than that, increase the flow by 1/2 of the excess.
        #  If mhu_cms is less than that, decrease the flow by 1/2 of the deficiency.
        #  If the resulting level of Mhu is > 177.50m or < 175.50m, then
        #  simply adjust the level to stay in range.
        #
        scflow = 5100.0 + (mhu_cms-5100)/2.0
        mlevd = mhu_ts / mhu_area                       # mhu level delta for today
        newlev = mlev_today + mlevd
        if newlev > 177.50:
            adj = (newlev - 177.5) * mhu_area           # cubic meters
            scflow = scflow + adj/seconds_per_month
            newlev = 177.50
        elif newlev < 175.50:
            adj = (175.5 - newlev) * sup_area           # cubic meters
            scflow = scflow - adj/seconds_per_month
            newlev = 183.00
        mhulevd[i] = newlev






