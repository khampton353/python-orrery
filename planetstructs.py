''' namedTuples used to make code more readable and maintainable,
    and in some cases to help keep modules in sync.
'''  
''' Changes:
    1/25/2018
    -changed comment formatting
    -remove namedtuple used only in buildorbit
    -added orbit start date to Orbitdata
'''

from collections import namedtuple

'''
layout of planet data in the (pickled) binary data file
-planet's name (string);
-sampleinterval:minutes between samples (int)
-xyspan: tuple of orbit dimensions (see Spans, below)
-index of the orbital point for initial planet placement (int)
-odate: Julian date of the first point in the orbit (float)
-orbit: orbit's x and y coordinates (array of double)
'''
Orbitdata = namedtuple('Orbitdata', [
    'planetname', 
    'sampleinterval', 
    'xyspan', 
    'istart', 
    'odate',
    'orbit'
    ])


'''
cartesian coordinates; float values describing a 
planet location relative to the sun
'''
CCoords = namedtuple('Coords',[
    'x',
    'y',
    'z'
    ])
 

'''
layout of colon separated values in planet_config, #used by builder.py to
find file locations and by #planets.py to get non-location planet data
-planetname : associates planets with their configurations
-datafile: file that contains the ephemeris data
-color: Tk color for the planet
-relativesize: based on planet diameter, used for
-drawing the planets to (relative) scale
'''
Configdata = namedtuple('Configdata', [
    'planetname',
    'datafile',
    'color',
    'relativesize',
    'other'
    ])


'''
-for each orbit, the highest and lowest x and y coordinates
-used to determine scaling for a given screen geometry (floats)
'''
Spans = namedtuple('Spans',[
    'bigx',
    'smallx',
    'bigy',
    'smally'
    ])


