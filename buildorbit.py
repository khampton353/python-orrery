''' buildorbit.py
    A utility that parses a planetary ephemeris file for orbit data and
    creates a binary file for use by the planets.py. It understands the JPL 
    Horizons Jul 31, 2013 'Vector' format. It reads the file once to determine 
    points closest/farthest from the sun in order to choose an orbit, and then 
    processes records in the selected date range to generate the file.  
    Input:
    The name of a file containing orbit data.
    Each file contains cartesian coordinate samples for the position of a 
    single target planet relative to the the sun and taken at specified 
    intervals between specified dates. Files are line-oriented and in plain 
    text. They consist of three parts: a header describing the content, 
    a series of 4-line records for the samples, and a trailer describing the 
    sample content. Information about the data and Horizons can be found at:
            https://ssd.jpl.nasa.gov/horizons.cgi#top
    Output:
    A binary file created by pickling a summary list. The list is comprised of:
            planet name
            sample interval in minutes
            max and min x and y coordinates for the orbit
            location to use for initial planet placement in the orbit
            sequence of floats with the x and y positions taken from each sample
    The coordinates are extracted from a complete orbit of the planet around 
    the sun. The orbit starts and ends at either planet's closest or farthest 
    positions from the sun nearest to the target target date of 1/25/2018
    (Julian date 2458143.50000 as shown in the input file).

    The layout for the output file is in planetstructs.py 

'''

import sys
from collections import namedtuple
import planetstructs as ps
from math import sqrt
import pickle
 
eps = 1.0E-1 # planet locations this 'close' might be equivalent

def getinit(f):
    ''' strip target planet name and sample interval (in minutes) from the 
        ephemeris and advance to the start of the first data record.
        getinit() is very closely tied to the file format.
        Example file lines:
        Revised: Jul 31, 2013           Saturn Barycenter           ...
        ...
        Step-size       : 10080 minutes

        f: planet data file object. Called once from main().
        returns:name and interval
    '''
    lne = '*'
    interval = 0
    f.readline() # 79 asterisks, ignore
    name = f.readline().split()[4] #planet name in the second line
    while lne[0] != '$': # $$$SOE delineates start of planet data
        lne = f.readline()
        if not interval:
            if lne[0] == 'S' and lne[4] == '-': #Step-size
                interval = int(lne.split()[2])
    return name, interval

def getsample(f):
    ''' extract information from a 4-line data record. 
        Expects the file position to be aligned at the record.
        getsample is very closely tied to the file format.
        Expects records to follow the JPL Horizon's Vector format, with 
        the first line containing the sample (Juilian) date, the 2nd line 
        the cartesian coordinates, the 3rd line vector velocities (currently 
        unused), and the 4th line the distance from the sun in AUs.
        Example coords line:
         X = 1.309801081200231E+00 Y = 5.452635553461058E-01 Z =-2.07189791...
        Example line 4 (RG is distance to the sun in AUs):
         LT= 8.194971050395787E-03 RG= 1.418915252296812E+00 RR= 9.47995979...
        f: planet data file object
    '''
    lst = []
    pos = f.tell()
    lne = f.readline() 
    if lne[1] == '$': # end of records delineation $$$EOE 
        raise ValueError('End of Records')
    date = float(lne.split()[0]) #Julian date of first sample
    cc = ps.CCoords._make([float(coord) for vals in f.readline().split('=') \
            for coord in vals.split() if len(coord) > 6]) 
    f.readline()
    lne = f.readline()
    if lne[1] != 'L':
        rg = None
    else:
        rg = float(lne.split('=')[2].split()[0])
    return ps.Planetsample(pos, date, rg, cc)


def getcmpsample(f, szs):
    ''' wrapper for getsammple that contains the 'side-effect' of updating 
        the szs list with the smallest/largest x and y coordinates (ignoring
        the z coord for now)
        f: planet data file object
    '''
    s = getsample(f)
    lst = s.ccoords
    if lst.x > szs[0]: szs[0] = lst.x #largest x
    elif lst.x < szs[1]: szs[1] = lst.x #smallest x (most negative 
    if lst.y > szs[2]: szs[2] = lst.y #largest y
    elif lst.y < szs[3]: szs[3] = lst.y #smallest y (most negative 
    return s


def getorbitrecords(far, near):
    ''' given a list of 1 or more aphelions and another with 1 or more 
        perihelions, return the file positions for the start of the most recent
        two *helions, which will delineate the points of the captured orbit.
        Expects at least one of the lists to have at least two samples, which 
        would comprise a complete orbit. 
        far: list of Planetsample for aphelion positions
        near: list of Planetsample for perihelion positions
        returns: orbit file positions 
    '''
    lst = far if len(near) < 2 else far if far[-1][0] > near[-1][0] \
            else near
    return lst[-2].filepos, lst[-1].filepos #filepos of last two *helions


#named tuple used to pass data to main()
Planetvalues = namedtuple('Planetvalues', [
    'planet', 'interval', 'lastfilepos', 'orbitstart', 'nextorbit',
    'coordextremes'])

def getvals(f):
    ''' parse the file to find aphelion and perihelion dates, used to
        construct the orbit drawing. Expects a well-formed Vector file with
        samples at least 1.5 orbits and sample records between two strings
        '$$$SOE' and '$$$EOE'. Also: expects the data samples to be 
        generated without 'bobbles' that create false positives for aphelion
        and perihelion. (Hint, use barycenter coordinates for source, target)
        Note that the first record can be safely ignored. Even if it is at
        x*helion, it wouldn't be part of the final orbit.
        f: planet data file object
    '''
    smallest = [] #list of samples at perihelion 
    biggest = []  #list of samples at aphelion
    lst=[None] * 2
    mbp = 0 #set if a date 'might-be-perihelion' (nearest the sun)
    mba = 0 #set if a date 'might-be-aphelion' (farthest)
    icurr = 0
    inext = 1
    szs = [0.0] * 4 #largest/smallest x coord, largest/smallest y coord
    poslast = 0
    name, interval = getinit(f) #leaves file position at first sample
    s = getcmpsample(f, szs) #don't keep it, can't be trusted as a real *helion 
    lst[0] = getcmpsample(f, szs)
    if lst[0].distance < s.distance:
        mbp = True
    else:
        mba = True
    
    records = 1
    while records:
        try:
            inext = (icurr+1) & 1
            lst[inext] = getcmpsample(f, szs)
            if lst[inext].distance > lst[icurr].distance:
                if mbp:
                    smallest.append(lst[icurr])
                    mbp = 0
                else:
                    mba = 1
            else:
                if mba:
                    biggest.append(lst[icurr])
                    mba = 0
                else:
                    mbp = 1
            poslast = lst[inext].filepos
            icurr = inext
        except ValueError as v: # assuming got to end of samples
            records = 0
    ostart, olast = getorbitrecords(biggest, smallest)
    return Planetvalues(name, interval, poslast, ostart, olast, tuple(szs))



def closest(olst, curr):
    ''' get the closest sample in olst to the reference
        sample in itm, needed to position the planet at the date in itm 
        correctly on the orbit
        olst: list of orbit samples within eps distance to curr 
        curr: sample for a target date
        returns: index of the sample closest to curr in distance
    '''
    diff = 50.0 #max astronomical units; Neptune is at 30, Pluto at 49.3
    coords = curr.ccoords
    idx = 0
    for samp in olst:  #idx and coord sample 
        delta = sqrt(
                ((samp[1].x - coords.x) * (samp[1].x - coords.x)) \
                    + ((samp[1].y - coords.y) * (samp[1].y - coords.y))\
                    + ((samp[1].z - coords.z) * (samp[1].z - coords.z)))
        if delta < diff:
            diff = delta
            idx = samp[0]
    return idx
    
def getorbit(f, first, last, curr):
    ''' given the start and ~end file positions for the most recent complete 
        orbit at apihelion or perihelion, and a target date, return a list of 
        coordinates and an index of a coordinate pair in the list nearest to 
        the coordinates of the date in curr
        f: file object of planet data input file
        first, last: file positions for orbit nearest to date of curr
        curr: Planetsample at file's final sample date
        returns: a tuple of the list of the orbits coordinates and location
                 of the coordinate pair closest to curr.ccoords
    '''
    pos = first
    olst = []
    coords = curr.ccoords  #x,y,z position at the target date

    citm = [] #collection of samples that fall within a given distance
    idx = 0   #number each sample, used to id planet start position in orbit  
    f.seek(first,0)
    lst = []
    while pos < last:
        info = getsample(f)
        cs = info.ccoords #coordinates
        olst.append(cs.x) #tkinter polygon needs x and y coords in series
        olst.append(cs.y) 
        pos = info.filepos
        if abs(cs.x - coords.x) < eps and abs(cs.y - coords.y) < eps: 
            citm.append((idx, cs,))
        idx += 1
    if len(citm) > 1:
        idx = closest(citm, curr)
    else:
        idx = citm[0][0]

    return olst, idx

if __name__ == '__main__':
    if len(sys.argv) > 1:
        st = sys.argv[1]
    else:
        print('No orbit data file provided, exiting')
        sys.exit(0)
    oname = ''
    olst = []
    vals=''
    citm=''
    with open(st, 'r') as f:
        vals = getvals(f)
        f.seek(vals.lastfilepos, 0)  #data record for target orbital start date
        vals2 = getsample(f)
        olst, citm = getorbit(f, vals.orbitstart, vals.nextorbit, vals2)
    oname = 'bin/bin{}.pkl'.format(vals.planet)
    with open(oname, 'wb') as ofile:
        pickle.dump(ps.Orbitdata(vals.planet, vals.interval, vals.coordextremes,
                citm, olst), ofile)


