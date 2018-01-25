''' namedTuples used to make code more readable and maintainable,
    and in some cases to help keep modules in sync.
'''  
from collections import namedtuple

#layout of planet data in the (pickled) binary data file
#planet's name (string); 
#sampleinterval:minutes between samples (int)
#xyspan: tuple of orbit dimensions (see Spans, below)
#index of the orbital point for initial planet placement
#orbit: list of orbit's locations: x and then y coordinates 
#formatted for tkinter
Orbitdata = namedtuple('Orbitdata', [
    'planetname', 
    'sampleinterval', 
    'xyspan', 
    'istart', 
    'orbit'
    ])

#cartesian coordinates; float values describing a 
#planet location relative to the sun
CCoords = namedtuple('Coords',[
    'x',
    'y',
    'z'
    ])
#data extracted from a 4-record planet sample
#used internally by buildorbit.py for data
#extracted from an ephemeris
#record position in a file; Julian date of the sample;
#distance in Astronomical units from the sun; coordinates
#all are floats except the filepos
Planetsample = namedtuple('Planetsample', [
    'filepos', 
    'jdate', 
    'distance',
    'ccoords'
    ])
 
#layout of colon separated values in planet_config
#used by builder.py to find file locations and by
#planets.py to get non-location planet data
#planetname : associates planets with their configurations
#datafile: file that contains the ephemeris data 
#color: Tk color for the planet
#relativesize: based on planet diameter, used for 
#drawing the planets to (relative) scale
Configdata = namedtuple('Configdata', [
    'planetname',
    'datafile',
    'color',
    'relativesize',
    'other'
    ])

#for each orbit, the highest and lowest x and y coordinates
#used to determine scaling for a given screen geometry (floats)
Spans = namedtuple('Spans',[
    'bigx',
    'smallx',
    'bigy',
    'smally'
    ])





