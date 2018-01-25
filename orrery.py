''' orrery.py
    The 'Controller' part of the Solar System model implemented using the MVC
    pattern. It creates the 'Model' Object, an instance of class 'Planets' that     contains all data related to planets and orbits, followed by the 'View' 
    object, an instance of class Display, which to the degree possible 
    contains and hides details about the graphics mechanism. (The caveat is 
    that cartesian coordinates are used to represent planet positions, and 
    that may not be compatible with all graphics choices))
    Class: Controller
           see class comment below

'''
import tkinter
import sys

import planets
import display

class Controller():
    '''class for the Solar System program. It creates the graphics control
       environment via tkinter as well as the planet objects and manages
       indirect communication between them in a MVC pattern. Note that 
       the Display object manages application exit.
    '''
    def __init__(self, config_data):
        root = tkinter.Tk()
        root.title('Orbital Paths')
        self.root = root
        self.model = planets.Planets(config_data)
        self.view = display.Display(self)
        self.view.mainloop()   

    def setgeometry(self, *args):
        ''' tell Planets to give this to each planet, which should result
            in each orbit calculating the real coordinates suitable for
            drawing its orbit
        '''
        self.model.setgeometry(*args)

    def getorbits(self):
        ''' tell planets to collect orbit data and return a list of it
        '''
        return self.model.getorbits()

    def getlargestspan(self):
        ''' ask Planets for the coordinates representing the largest orbital
            radius and return that tuple
        '''
        return self.model.getlargestspan()

    def getplanetsdata(self):
        ''' ask Planets for a list of dictionaries representing each planet
            at its current position
        '''
        return self.model.getplanetsdata()



''' allow open error to be propogated '''
config_file = 'config/planet_config'
pdata = None
if len(sys.argv) > 1:
    config_file = sys.argv
with open(config_file, 'r') as cf:
    pdata = list(cf)

c = Controller(pdata)
       
