''' module for planets and orbits. In the Model-View-Controller pattern, this 
    is the Model.
    Classes:
    Planets: the object created and owned by the Controller. It instantiates 
             the individual planet objects and communicates with each of them
             when invoked from the controller on behalf of the View component
    Planet: objects in this class read the configuration and binary orbit data
            and instantiate the orbit objects. They manage planet appearance 
            and return planet position when requested by the controller. They
            supply the orbit instances with a base list of coordinates read
            from the binary data file and depend on the orbit instance to 
            suplly real coordinates from which to determine planet position.
    Orbit: Owns the coordinates for the orbit. Using a function passed from 
           the View, it maintains the calculated coordinates list and returns 
           a position on the orbit to its parent planet object when the 
           planet needs to know its current positon. It also returns the 
           entire list when the View wants to draw an orbit.
'''
''' Changes:
    2/1/2018
    -Move the planet instead of recreating it unless the geometry has been set 
     or changed.
    -Don't return the planet object for display unless it has moved far enough 
     to be worthwhile
    -Support prorated movement for planets that have sample intervals > 1
    -simplify getpoints(); it doesn't need to get more than 1 point at a time.
''' 
''' Known issues:
    - The distance used to determine whether a planets movement is noteable is 
      hard-coded; this should probably be tied to screen geometry
'''

import pickle
import math
from collections import namedtuple
import planetstructs as ps

class Orbit():
    ''' class that represents the orbit. It is drawn and doesn't change unless 
        scaling occurs. A planet object supplies the initial points, but the
        orbit location can change via scaling. The planet instance can get 
        current location data from its orbit instance 
    '''

    def __init__(self, cpoints):
       self.orbit = []
       self.cpoints = cpoints

    def setorbit(self, pts, *args):
        '''using the supplied information, set or reset the location of the 
           orbits coordinates using the supplied calc() function which is the
           last itm in args.
           pts: the base orbit coordinates read from the binary orbit file
           args: calculation data from the display manager (View). They
                 are opaque to the orbit object except for the final arg
        '''
        self.orbit = args[-1](pts, *args) 

    def getpoints(self, idx = 0, lst = None):
        '''return the current values for the points selected. Two values 
           will be returned for each point. lst = None means return the 
           whole list (suitable for drawing the orbit). Allow an index error 
           to be raised if lst isn't large enough for count points
           idx: the starting point. Since each point on the orbit has two
                coordinates, must be multiplied by 2 before indexing the list
           count: the number of points to fetch
           lst: if provided, the container that receives the coordinates
        '''
        if not lst:
            return self.orbit
        ix = idx * 2
        lst[0] = self.orbit[ix]
        lst[1] = self.orbit[ix + 1]


class Planet():
    ''' class that represents information about a planet. Propogates errors
        back to the invoker 
    '''
    def __init__(self, info):
        ''' initialize with data from the binary info and configuration files
        '''
        self.name = info.planetname
        fname = 'bin/bin{}.pkl'.format(self.name)
        with open(fname, 'rb') as ifile:
            self.pdata = ps.Orbitdata(*pickle.load(ifile))
        self.desc = {'NAME' : self.name, 'COLOR' : info.color, \
                'SIZE' : float(info.relativesize.strip()),\
                'RING' : info.other.startswith('ring'), 'PLANET' : None}
        self.xtra = info.other #currently, only ring  (see self.desc)
        #convert minutes between samples to days
        self.interval = int(self.pdata.sampleinterval)//1440 
        self.span = ps.Spans._make(self.pdata.xyspan)
        self.points = \
                self.pdata.orbit #interleaved x and y coordinates for canvas
        #icurr*2 = x coord in points where planet should initially be placed
        self.icurr = self.pdata.istart  
        self.cpoints = int(len(self.points) / 2) #count x-y pairs
        self.orbitobj = Orbit(self.cpoints)
        self.locations = [None]*4    #retrieve current x-y position from orbit
        ''' the following items as well as the last two entries in 
            self.locations are used to manage redrawing when this planet 
            sampling interval isn't the same as the interval of the planet 
            with the smallest rate (currently assumed to be 1)
        '''
        self.inc = 0     # ticks to increment, for now, 0 or 1
        self.incidx = 0  # tick number, between 0 and self.interval - 1
        self.xinc = 0
        self.yinc  = 0
    
    def getplanetdata(self):
        ''' updates the planets description dictionary with a current 
            description of planet location state 
            Returns: the value of the dictionary's 'MOVE' key. This indicates
                     to the caller whether the planet should be drawn, moved, 
                     or ignored.   
            Note that there is an effort to improve smoothness and performance 
            by not passing the planet description back for display if it
            hasn't moved far enough. The determination of 'far enough' should 
            be programmatically calculated but for now is hard-coded to being 
            at least 1 pixel
        '''
        if self.locations[0] == None:
            #geometry has just been set or changed
            self.orbitobj.getpoints(self.icurr, self.locations)
            self.icurr = (self.icurr + 1) % self.cpoints
            self.desc['DRAW'][0] = self.locations[0]
            self.desc['DRAW'][1] = self.locations[1]
            self.desc['MOVE'] = None
            self.incidx = 0
        elif self.incidx == 0: 
            #time to get the next location on the orbit
            self.incidx += self.inc
            self.orbitobj.getpoints(self.icurr, self.locations)
            self.icurr = (self.icurr + 1) % self.cpoints
            self.xinc = (self.locations[0] - self.desc['DRAW'][0])/self.interval
            self.yinc = (self.locations[1] - self.desc['DRAW'][1])/self.interval
            if abs(self.xinc) > 1.0 or abs(self.yinc) > 1.0: #make 1.0 a var?
                self.desc['MOVE'] = (self.xinc, self.yinc,)
                self.desc['DRAW'][0] += self.xinc
                self.desc['DRAW'][1] += self.yinc
            else:
                #not a big enough distance to be worth moving
                self.desc['MOVE'] = (0, 0,)
                #set last 2 entries in self_locations to where self should be
                self.locations[2] = self.desc['DRAW'][0] + self.xinc
                self.locations[3] = self.desc['DRAW'][1] + self.yinc
        else:
            # in between samples, calculate a prorated point on the orbit
            self.incidx = (self.incidx + self.inc) % self.interval
            if abs(self.xinc) > 1.0 or abs(self.yinc) > 1.0:
                #incrementas are big enough, self.desc['MOVE'] can stay the same
                self.desc['DRAW'][0] += self.xinc
                self.desc['DRAW'][1] += self.yinc
            else:
                self.locations[2] += self.xinc
                self.locations[3] += self.yinc
                if abs(self.locations[2] - self.desc['DRAW'][0]) > 1 and \
                        abs(self.locations[3] - self.desc['DRAW'][1]) > 1:
                    self.desc['MOVE'] = \
                            (self.locations[2] - self.desc['DRAW'][0],\
                            self.locations[3] - self.desc['DRAW'][1],)
                    self.desc['DRAW'][0] = self.locations[2]
                    self.desc['DRAW'][1] = self.locations[3]
                else:
                    self.desc['MOVE'] = (0, 0,) #Nothing to draw this time
        return self.desc['MOVE']
            

    
    def settickincrement (self, smallinterval):
        ''' limits movement of planets according to their sampling interval. 
            For now, assumes a baseline of 1 day intervals and sets self.inc 
            for planets with larger samples. smallinterval can be saved for
            proration calculations if later desired
        '''
        if self.interval != smallinterval:
            self.inc = 1


    def setgeometry(self, *args):
        ''' tell the orbit object to create its orbit coordinates using the
            base coordinates and the arguments from the View. Then, set the
            planets initial position in the orbit
            args: values for the orbit calculation. Note that the final arg
                  is a function object in the View that actually sets the 
                  orbit coordinates based on the physical display and zoom 
                  factor
        '''
        self.orbitobj.setorbit(self.points, *args)
        self.locations[0] = None  #Triggers 'DRAW'
        self.desc['DRAW'] = [0, 0]


    def getorbit(self):
        ''' return the list of coordinates that currently reflects the orbit 
            based on the current geometry
        '''
        return self.orbitobj.getpoints(0)

    def getspans(self):
        ''' return the tuple of coordinates representing the orbit shape 
            (the x width and y width)
        '''
        return self.span.bigx - self.span.smallx,\
                self.span.bigy - self.span.smally

    def getinterval(self, smallest):
        ''' return the #days between coordinate samples
            and the smaller of self.interval and smallest
        '''
        return self.interval,\
                smallest if smallest < self.interval else self.interval 




class Planets():
    ''' Class that creates and contains the planet objects 
    ''' 
    def __init__(self, pdata):
        '''creates the planet instances from the config data in pdata
        '''
        self.ospan = 0.0
        self.pdata = pdata
        self.smallinterval = 1000 #artificial but > largest acceptible value
        self.planets = []
        for itm in pdata:
            if itm[0] == '#':
                continue
            if itm[0] == '$':
                break
            self.planets.append(Planet(ps.Configdata._make(
                itm.split(':', maxsplit = 4))))
            for s in self.planets[-1].getspans():
                if s > self.ospan:
                    self.ospan = s
            self.smallinterval = \
                    self.planets[-1].getinterval(self.smallinterval)[1]

        self.settickincrements()



    def settickincrements(self):
        ''' tell planets to set their tick increments relative to the
            smallest interval '''
        for p in self.planets:
            ''' a note about intervals. for now, this uses the interval of the 
                planet with the smalles orbit as having a tick-day of 1. It is
                possible that zooming may make small orbit planets disappear
                so that this will need to be reset. todo
            '''
            p.settickincrement(self.smallinterval)


    def setgeometry(self, *args):
        for p in self.planets:
            p.setgeometry(*args)

            

    def getorbits(self):
        ''' tell planets to collect orbit data and return a list of it
        '''
        orbits = []
        for p in self.planets:
            orbits.append(p.getorbit())
        return orbits

    def getlargestspan(self):
        ''' ask Planets for the coordinates representing the largest orbital
            radius and return that tuple
        '''
        return self.ospan

    def getplanetsdata(self):
        ''' ask Planets for a list of dictionaries representing each planet
            at its current position
            returns: a list with planet description dictionaries which are
            appended if there is something to move (['MOVE'][0] != 0) or 
            draw (p.getplanetdata() == None).  
        '''
        data = [p.desc for p in self.planets if \
                (not p.getplanetdata() or p.desc['MOVE'][0] != 0)]
        return data


            
    



