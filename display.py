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
    1/31/2018
    - deleted unneccessary code (call to getplanetsdata() in draworbits() and 
      import ttk, leftover from earlier development phases)
    - use grid manager for all geometry management 
      (self.pack(fill = BOTH, expand = YES) worked fine, but better to be 
      completely consistent, which means making the root window also be gridded
    2/1/2018
    - added support for 'moving' a planet instead of deleting and redrawing
      every time; the later is only needed when the scale changes via zooming
    2/1/2018
    - Add event cancellation for zooming and quitting 
    - Better handling of exiting and when the user closes the window so that
      Tk/Tcl issues are managed
    2/1/2018
    - Cancel and reschedule drawplanets() events immediately whe changing the 
      speed instead of waiting for the cycle period to expire
    - minor improvements to the speed slider
'''
''' Known issues:
    -Setting the initial viewing position should be better linked to window 
     geometry
'''

from tkinter import *
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
        ''' Initializes the Display instance. It is ecpected that the 
            controller instance has a root member which is a Tk instance
        '''
        Frame.__init__(self, controller.root)
        self.ctrl = controller
    
        #set some screen geometry
        screen= self.ctrl.root.winfo_screenwidth(), \
                self.ctrl.root.winfo_screenheight()
        vcw = 3200                        # canvas width 
        vch = 3200                        # canvas height
        self.makewinframe(screen, vcw, vch)
        self.maketopframe()
        self.ctrl.root.grid_rowconfigure(0, weight = 1)
        self.ctrl.root.grid_columnconfigure(0, weight = 1)

        self.scalefactor=1.0
        self.span = self.ctrl.getlargestspan()
        self.mult = (vcw-100) //self.span  #scale orbits to virtual screen

        #slide settings:0 is unused, 7 is unrealistic...
        self.cycle_periods=(10000, 5000, 500, 250, 100, 50, 20, 5)
        self.speed.set(4)

        self.sundim = 13                  #sun relative size//100          
        self.afterid = None
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
        self.ctrl.root.protocol("WM_DELETE_WINDOW", self.destroy_)
        self.exit = Button(self.topfr,text = 'Exit', \
                command = self.stopdrawing)
        self.speedlabel = Label(self.topfr, text = '     Orbit speed:', \
                justify='right',\
                bg='white') #keep the slider slim, precede with title
        scalevar=IntVar()
        self.speed = Scale(self.topfr, from_=1, to=7, variable = scalevar, \
                activebackground='white', command=self.chgspeed,  \
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


    def destroy_(self):
        ''' tknter and tcl can get out of sync when tcl thinks an after() or
            after_cancel() command has command has been completed but tkinter 
            doesn't. The problem doesn't occur on the second call to destroy() 
        '''
        try:
            self.ctrl.root.destroy()
        except TclError as te:
            #print('err', te)
            self.ctrl.root.destroy()


    def stopdrawing(self):
        ''' exit after drawing has stopped '''
        self.keepdrawing = False
        if self.afterid:
            self.after_cancel(self.afterid)
        self.destroy_()


    def chgspeed(self, scl):
        ''' when the slider speed is changed, cancel any pending drawplanets() 
            events and reschedule immediately
        ''' 
        if self.afterid:
            self.after_cancel(self.afterid)
            self.afterid = None
            if self.keepdrawing:
                self.after_idle(self.drawplanets)



    def draworbits(self):
        ''' called during initialization and when the zoom factor changes, 
            this function updates the geometry and redraws the orbits
        '''
        if self.afterid:
            self.after_cancel(self.afterid)
            self.afterid = None

        self.ctrl.setgeometry(self.mult * self.scalefactor, self.center, calcpoints)
        sunrad = self.sundim * self.scalefactor
        nlst = self.ctrl.getorbits()
        self.canvas1.delete('orbit', 'sun')
        olst = []
        for o in nlst:
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
            next cycle. A planet description dictionary won't be appended to 
            the list if there is insufficient movement from the last position.
            p['MOVE'] == None when the planet has to be created or recreated 
            due to scaling changes.
        '''
        self.after_id = None
        pscale = .1
        rad = 0.0
        plst = self.ctrl.getplanetsdata()
        for p in plst:
            #print(p['NAME'], p['DRAW'], p['MOVE'])
            if p['MOVE']:
                #p['MOVE'] is a tuple of x and y move deltas
                self.canvas1.move(p['PLANET'], p['MOVE'][0], p['MOVE'][1])
                if p['RING']:
                    self.canvas1.move(p['RING'], p['MOVE'][0], p['MOVE'][1])
            else:
                self.canvas1.delete(p['NAME'])
                rad = self.scalefactor * pscale * p['SIZE']
                p['PLANET'] = self.canvas1.create_oval(p['DRAW'][0]-rad, \
                        p['DRAW'][1]-rad, \
                        p['DRAW'][0]+rad, p['DRAW'][1]+rad, fill = p['COLOR'],\
                        tags = ('planet', p['NAME']), outline = p['COLOR'])
                if p['RING']:
                    rad = 1.5 * rad
                    p['RING'] = self.canvas1.create_line(p['DRAW'][0]-rad, \
                            p['DRAW'][1]-rad, p['DRAW'][0]+rad, \
                            p['DRAW'][1]+rad, fill = p['COLOR'],\
			    tags = ('planet', p['NAME']), width = 2)
        if not self.keepdrawing:
            return
        per = self.speed.get()
        self.afterid = self.canvas1.after(self.cycle_periods[per], \
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
        self.canvas1.after_idle(self.drawplanets)

