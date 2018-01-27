''' display.py
    This module contains the display logic and implements the View component 
    of the MVC pattern. It currently uses tkinter but could be reimplemented 
    with another graphics engine as long as it can work with cartesian
    coordinates.
    Class: Display
           This class is created by the Controller and communicates with the 
           planet objects through the controller. It also is responsible
           for calling destroy() when the user decides to exit or close the 
           window
'''
''' Changes:
    1/25/2018
    - changes to support updating and using an array of doubles for the orbit
      coordinates instead of a list of floats; calcpoints() now updates an array
      in place instead of building and returning a list
    1/26/2018
    - use Tk event handling and exit logic more correctly
    - remove unused code and comments
    1/26/2018
    - added xview_moveto, yview_moveto to better position initial canvas display
'''
''' Known issues:
    -Changing the scale should cancel-and-reschedule drawplanets immediately
     instead of waiting the for the old interval to complete first
'''

from tkinter import *
from tkinter import ttk
import sys

def calcpoints(pts, mult, center, func):
    ''' function passed to an orbit object (indirectly) to call to convert the 
        base list of x, y coordinates in pts into coordinates suitable to draw 
        an orbital polygon. It is called at startup and when zooming occurs
        pts: a list of (unscaled) alternating x and y coordinates reflecting
             the planet's position as seen by the sun at sample intervals. 
        mult: a positional scaling factor to apply, initially created based on
              screen and orbit dimensions
        center: the location on the screen of the orbit center
        func:   the function object originally passed to the orbit method
        returns: the list with the current scaling applied. This is the list
                 that create_polygon will use to draw the orbit, and that the
                 planet can query for its location on the orbit
        Note: The setgeometry() method passes mult, center and this function's
              function object as opaque tuples to the controller and onward. 
              The orbit expects args[-1] to be the function to call.
              Also, scaling must be managed by the class and not tkinter, 
              because the planet object must be able to determine its own
              point on the orbit when queried by drawplanets()
    '''
    nlst = []
    for idx in range(len(pts)):
        itm = pts[idx] * mult
        if idx % 2: #y
            nlst.append(center[1] - itm)
        else: #x
            nlst.append(center[0] + itm)
    return nlst



#todo, this should make itself a singleton. 
class Display(Frame):
    ''' manages the orrery display. See description above '''
    def __init__(self, controller):
        Frame.__init__(self, controller.root)
        self.ctrl = controller
    
        #set some screen geometry
        screen= self.ctrl.root.winfo_screenwidth(), \
                self.ctrl.root.winfo_screenheight()
        vcw = 3200                        # canvas width 
        vch = 3200                        # canvas height
        self.makewinframe(screen, vcw, vch)
        self.maketopframe()
        self.pack(fill = BOTH, expand = YES)

        self.scalefactor=1.0
        self.span = self.ctrl.getlargestspan()
        self.mult = (vcw-100) //self.span  #scale orbits to virtual screen

        self.cycle_periods=(10000, 750, 500, 250, 100, 50, 20, 1)
        self.speed.set(4)

        self.sundim = 13                  #sun relative size//100          
        self.draworbits()
        self.drawplanets()

    def makewinframe(self, screen, vcw, vch):
        ''' initialize all widgets in the main/drawing frame
            screen: display physical dimensions
            vcw: vitual canvas width
            vch: virtual canvas height
        '''
        self.grid(column = 0, row = 0, sticky = (N, W, E, S))
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(0, weight = 1)

        cw = screen[0]/2                  # canvas width 
        ch = screen[1]/2                  # canvas height

        self.xscrbar = Scrollbar(
                self, orient ='horizontal', activebackground='dark gray')
        self.xscrbar.grid(row = 1, column = 0, sticky = E+W)
        self.yscrbar = Scrollbar(
                self, orient = 'vertical', activebackground='dark gray')
        self.yscrbar.grid(row = 0, column = 1, sticky = N+S)

        self.center = vcw/2, vch/2   

        self.canvas1 = Canvas(self, width=cw, height=ch, background="black",\
                xscrollcommand = self.xscrbar.set,\
                scrollregion = (0,0,vcw,vch), \
                yscrollcommand = self.yscrbar.set)
        self.canvas1.grid(row=0, column=0, sticky = N+S+E+W)
        self.xscrbar.config(command = self.canvas1.xview)
        self.yscrbar.config(command = self.canvas1.yview)
        #set initial viewing position
        self.canvas1.xview_moveto(.35)
        self.canvas1.yview_moveto(.4)


    def maketopframe(self):
        ''' make the user cmds frame '''
        self.topfr = Frame(self, bg='white')
        self.keepdrawing = True
        self.exit = Button(self.topfr,text = 'Exit', \
                command = self.ctrl.root.destroy)
        self.speedlabel = Label(self.topfr, text = '     Orbit speed:', \
                justify='right',\
                bg='white') #keep the slider slim, precede with title
        scalevar=IntVar()
        self.speed = Scale(self.topfr, from_=0, to=7, variable = scalevar, \
                activebackground='white', \
                orient = 'horizontal', tickinterval=1)
        self.zi = Button(self.topfr, text='ZOOM IN',\
                command = lambda:self.zoom(1), bg='white')
        self.zo = Button(self.topfr, text='ZOOM OUT',\
                command = lambda:self.zoom(0), bg='white')
        self.exit.grid(row=0, column=0)
        self.speedlabel.grid(row=0, column=1)
        self.speed.grid(row=0,column=2)
        self.zi.grid(row=0, column=4)
        self.zo.grid(row=0, column=5)
        self.topfr.grid(row=2, column=0, sticky=E+W)

    def draworbits(self):
        ''' called during initialization and when the zoom factor changes, 
            this function updates the geometry and redraws the orbits
        '''
        self.ctrl.setgeometry(self.mult * self.scalefactor, self.center, calcpoints)
 
        sunrad = self.sundim * self.scalefactor
       
        nlst = self.ctrl.getorbits()
        plst = self.ctrl.getplanetsdata()
        self.canvas1.delete('orbit', 'sun')
        olst = []
        for i, o in enumerate(nlst):
            olst.append(self.canvas1.create_polygon(o, fill = 'black', 
                outline = 'red', width = 1, tags = 'orbit', smooth = 1))
        self.canvas1.create_oval(self.center[0]-sunrad, self.center[1]-sunrad, \
                self.center[0]+sunrad, self.center[1]+sunrad, fill = 'yellow', \
                tags = 'sun')
        self.canvas1.update()

    def drawplanets(self):
        ''' The movement engine for the planets. at cycle_periods intervals it
            asks the planets for their new positions until keepdrawing changes
            Note that zooming and speed changes will always be reflected in the
            next cycle. Also, the planet object may indicate that the planet 
            should maintain its previous position perhaps because of 
            insufficient movement
        '''
        pscale = .1
        rad = 0.0
        plst = self.ctrl.getplanetsdata()
        for p in plst:
            if p['DRAW']:
                self.canvas1.delete(p['NAME'])
                rad = self.scalefactor * pscale * p['SIZE']
                self.canvas1.create_oval(p['XLOC']-rad, p['YLOC']-rad, \
			p['XLOC']+rad, p['YLOC']+rad, fill = p['COLOR'],\
			tags = ('planet', p['NAME']), outline = p['COLOR'])
                if p['RING']:
                    rad = 1.5 * rad
                    self.canvas1.create_line(p['XLOC']-rad, p['YLOC']-rad, \
			    p['XLOC']+rad, p['YLOC']+rad, fill = p['COLOR'],\
			    tags = ('planet', p['NAME']), width = 2)
        per = self.speed.get()
        self.canvas1.after(self.cycle_periods[per], \
                self.drawplanets)

    #todo, add mousewheel zoom support, consider limits on zooming
    def zoom(self, val):
        ''' sets the scaling factor based on user scaling actions.
            draworbits() will trigger a call to setgeometry to get the
            point positions set with the new scalefactor
            val: 1 if scaling in, else 0
        '''
        self.scalefactor *= 2 if val else .5
        self.draworbits()

