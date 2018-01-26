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
            Julian date of the start of the orbit
            list of floats with the x and y positions taken from each sample
    The coordinates are extracted from a complete orbit of the planet around 
    the sun. The orbit starts and ends at either planet's closest or farthest 
    positions from the sun nearest to the target target date of 1/25/2018
    (Julian date 2458143.50000 as shown in the input file).

    The layout for the output file is in planetstructs.py 

'''
'''  Changes:
     1/25/2018
     -Read file once and save all parsed samples in a list. There will be at 
      most a few thousand samples. That will save the second partial pass 
      through the file and eliminate the need to save the file position.
     -only collect the largest dimension ranges on the chosen orbit
     -move Planet sample here from planetstructs.py and remove the filepos
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


'''
#data extracted from a 4-record planet sample in a JPL ephemeris and
converted to floats
-Julian date of the sample;
-distance in Astronomical units from the sun;
-x, y,and zcoordinates
'''
Planetsample = namedtuple('Planetsample', [
    'jdate',
    'distance',
    'ccoords'
    ])
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
        returns: a namedtuple with the sample date for the record, its
                 distance from the sun, and its Cartesian coordinates
    '''
    lst = []
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
    return Planetsample(date, rg, cc)



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



def getorbit(slst, first, last):
    ''' given the list of sample data and the start and end indices for the 
        most recent complete orbit at apihelion or perihelion, create a list of 
        x and y coordinates for the orbit, determine the largest and smallext 
        x and y values, and get the index of the point closest to the final
        sample taken. Note that 'last' is the start of the next, incomplete
        orbit.
        slst: the complete list of samples
        first, last: indices for a complete orbit + 1 sample
        returns: the index of the orbital point closest to the last point, a 
                 tuple with the coordinate extremes, and anarray with the 
                 orbit coordinates
    '''
    olst = []
    coords = slst[-1].ccoords  #x,y,z position at the target date
    szs = [0.0] * 4 #largest/smallest x coord, largest/smallest y coord
    citm = [] #collection of samples that fall within a given distance
    idx = 0   #number each sample, used to id planet start position in orbit 
    cnt = last - first
    while idx < cnt:
        cs = slst[idx + first].ccoords #coordinates
        if cs.x > szs[0]: szs[0] = cs.x #largest x
        elif cs.x < szs[1]: szs[1] = cs.x #smallest x (most negative 
        if cs.y > szs[2]: szs[2] = cs.y #largest y
        elif cs.y < szs[3]: szs[3] = cs.y #smallest y (most negative 
        olst.append(cs.x) #tkinter polygon needs x and y coords in series
        olst.append(cs.y) 
        if abs(cs.x - coords.x) < eps and abs(cs.y - coords.y) < eps: 
            citm.append((idx, cs,))
        idx += 1
    if len(citm) > 1:
        idx = closest(citm, slst[-1])
    else:
        idx = citm[0][0]

    return idx, tuple(szs), olst


def getorbitdata(f):
    ''' parse the file to find aphelion and perihelion dates, used to
        construct the orbit drawing. Expects a well-formed Vector file with
        samples at least 1.5 orbits and sample records between two strings
        '$$$SOE' and '$$$EOE'. Also: expects the data samples to be 
        generated without 'bobbles' that create false positives for aphelion
        and perihelion. (Hint, use barycenter coordinates for source, target)
        Note that the first record can be safely ignored. Even if it is at
        ap/perihelion, it wouldn't be part of the final chosen orbit. The
        last record can also be ignored as long as the 1.5+ orbits predicate 
        is met
        f: planet data file object
        returns: the Planetvalues namedTuple for the collected data
    '''
    smallest = [] #list of samples at perihelion 
    biggest = []  #list of samples at aphelion
    mbp = 0 #set if a date 'might-be-perihelion' (nearest the sun)
    mba = 0 #set if a date 'might-be-aphelion' (farthest)
    slst = [None] #lst of all parsed records minus the first
    name, interval = getinit(f) #leaves file position at first sample
    s = getsample(f) #don't keep it, can't be trusted as a real *helion 
    slst[0] = getsample(f)
    if slst[0].distance < s.distance:
        mbp = True
    else:
        mba = True
    records = 1
    idx = 0
    while records:
        try:
            slst.append(getsample(f))
            if slst[-1].distance > slst[-2].distance:
                if mbp:
                    smallest.append((idx, slst[-2],))
                    mbp = 0
                else:
                    mba = 1
            else:
                if mba:
                    biggest.append((idx, slst[-2],))
                    mba = 0
                else:
                    mbp = 1
            idx += 1
        except ValueError as v: # assuming got to end of samples
            records = 0
    lst = biggest if biggest[-1][0] > smallest[-1][0] else smallest
    istart, ilast =  lst[-2][0], lst[-1][0] #record indices of last two *helions
    cidx, szs, oarr = getorbit(slst, istart, ilast)
    return ps.Orbitdata(name, interval, szs, cidx, slst[istart].jdate, oarr)

    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        st = sys.argv[1]
    else:
        print('No orbit data file provided, exiting')
        sys.exit(0)
    odata = None
    with open(st, 'r') as f:
        odata = getorbitdata(f)
    oname = 'bin/bin{}.pkl'.format(odata.planetname)
    with open(oname, 'wb') as ofile:
        pickle.dump(odata, ofile)


