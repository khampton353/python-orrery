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

    def getpoints(self, idx = 0, count = 1, lst = None):
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
        for i in range(count):
            if idx + i == self.cpoints:
                ix = 0
            j = i*2
            lst[j] = self.orbit[ix]
            lst[j+1] = self.orbit[ix+1]
            ix += 2

        


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
                'RING' : info.other.startswith('ring')}
        self.xtra = info.other #currently, only ring  (see self.desc)
        #convert minutes between samples to days
        self.interval = int(self.pdata.sampleinterval)//1440 
        self.span = ps.Spans._make(self.pdata.xyspan)
        self.points = \
                self.pdata.orbit #interleaved x and y coordinates for canvas
        #icurr*2 = x coord in points where planet should initially be placed
        self.icurr = self.pdata.istart  
        self.cpoints = len(self.points) / 2 #count x-y pairs
        self.orbitobj = Orbit(self.cpoints)
        self.locations = [None]*2    #retrieve current x-y position from orbit
        ''' the following items are used to manage redrawing 
            when this planet interval isn't the same as the interval of the 
            planet with the smallest orbit (currently assumed to be 1)
            Note the ratio between this planet's interval and that of the 
            smallest planet interval can be used to prorate movement, but it 
            is complex and for now has been removed.
        '''
        self.inc = 0     # ticks to increment, for now, 0 or 1
        self.incidx = 0  # tick number, between 0 and self.interval - 1

    
    def getplanetdata(self):
        ''' returns the dictionary with a current description of planet state 
            including where to draw it.
        '''
        if  self.incidx == 0: 
            self.incidx += self.inc
            self.orbitobj.getpoints(self.icurr, 1, self.locations)
            self.desc['XLOC'] = self.locations[0]
            self.desc['YLOC'] = self.locations[1]
            self.desc['DRAW'] = True
            self.icurr += 1
            if self.icurr == self.cpoints:
                self.icurr = 0
        else:
            self.incidx = (self.incidx + self.inc) % self.interval
            self.desc['DRAW'] = False
        return self.desc
            

    
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
        if self.locations[0] == None: #first time
            self.orbitobj.getpoints(self.icurr, 1, self.locations)
            self.desc['XLOC'] = self.locations[0]
            self.desc['YLOC'] = self.locations[1]


    def getorbit(self):
        ''' return the list of coordinates that currently reflects the orbit 
            based on the current geometry
        '''
        return self.orbitobj.getpoints(0,0)

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
        self.smallinterval = 1000 #articial but > largest acceptible value
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

            todo, this gets called all the time, need to create it and then
            just let the planet instances update it
        '''
        data = []
        for p in self.planets:
            data.append(p.getplanetdata())
        return data


            
    



