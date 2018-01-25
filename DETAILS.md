#Project Orrery: a Solar System model in Python3
# Table of contents
1. [Introduction](#introduction)
2. [Design choices](#design)
3. [Directories and files](#files)
4. [Running the model](#running)
5. [Improvements and additions](#todo)
3. [Directories and files](#files)
3. [References](#references)


## Introduction <a name="introduction"></a>
The Orrery project resulted from a programming challenge: could I design and create an on-screen model of the Solar system with moving planets and a slider to modify the planet speeds? This needed to be done in a reasonable time-frame, which I interpreted as weeks instead of months. (Days instead of weeks would have been better, but I had a bit of research to do first: kernel-girls don't have a lot of experience with graphics development!)

I chose Python 3 for the language, Tk for the graphics implementation, and Fedora Linux for the environment. I have easy access to the latter and really enjoy developing with the former. Tk seemed like a good choice for the first implementation as I had used it before and some quick research showed that it could do what I wanted. It is well documented and ubiquitous in forum discussions. See [References](#references) for some of my favorite references.)

The next step was determining the functionality. I decided that my minimum feature set should include:
1. a 2-D canvas with the sun in the center, orbits that trace real planetary motion relative to each other and the sun, and planets with reasonably accurate locations and velocities relative to one another
2. planets drawn with accurate relative sizes and colors
3. user controls for scrolling around the window and zooming in and out; without this creating a scaled model would not deliver a good user experience. A slider for changing the speed was needed to meet the challenge, and finally the user should be able to enlarge the window and exit the program.

Data for the the model primarily came from NASA and Nasa's Jet Propulsion Laboratory (JPL). In particular, JPL provides excellent tools for generating planet location tables ('Ephemerides', singular: 'Ephemeris') with a high degree of granularity and accuracy. The Horizon's web interface at https://ssd.jpl.nasa.gov/horizons.cgi allows files to be created and downloaded by specifying source and target bodies, time spans and sample intervals. The 'Vectors' ephemeris type produces cartesian coordinates; this type of data works very well with Tkinter.

Tkinter draws shapes in regions determined by coordinates. A circle is drawn in a rectangle specified by upper-left and lower-right x and y coordinates. A polygon can be drawn by providing coordinates for a series of points that can be connected. If a polgon has enough points, it can take on the appearance of a circle or ellipse. If a circle is drawn at each of those points rapidly, it can have the appearance of moving around the circle. This was the foundation for the project design and many of the implementation choices.

## Design rationale and choices <a name="design"></a>
The  components of this project lend themselves very well to an object oriented design and to implementation of the Model-View-Controller pattern. The objects in the Model are the orbits, planets, and solar-system. The display object implements the User interface/view, and the controller object creates the display and solar system objects and manages initialization and event communication between them. In particular, it is intended that the view hides the use of tkinter from the model components such that different graphics implementations may be implemented.

The amount of data needed to draw reasonably smooth orbits for all planets can be large. After looking at many samples and prototyping orbits I chose to sample enough data that I could collect enough points to capture complete orbits and identify the positions of each planet on a given day (1/25/2018). I chose 1 day sampling intervals for the four planets closest to the sun, and intervals that approximated 1/4 degree radial movement for the others. Because it seemed impractical for each planet to be parsing files at runtime, I created buildorbit.py to preprocess the ephemerides and generate binary data files containing orbit dimensions and points, as well as sampling interval and initial location specifiers The binary file contains integers and floats in native form. This data is sufficient to support the model requirements. The Python pickle module is used to create the binary files dynamically and they are not delivered as part of the package.
 
Because there are 8 planets there are 8 instances of the planet class and 8 binary data files named binNAME.pkl, wher NAME is replaced with the planet's name. In addition to their location, planet objects need to know their names, relative sizes, colors, and whether they have a ring. This data is contained in a text file in the config subdirectory.   

Horizons data provides x, y, and z coordinates for a planet's position on a given date. Looking at the data for planet positions relative to the sun, with one exception only the x and y coordinates contribute materially to a 2-D model. The 8 currently recognized planets lie very near the ecliptic plane. Pluto is an outlier in many ways. Aside from being smaller than some moons, Pluto's orbit is not in the ecliptic and is very elongated compared to all other planets. For this version of the project, Pluto, the other dwarf planets, and planet moons are excluded from the model, and the z coordinate is not used in plotting orbit points and planet locations.
  
  
## Directories and files <a name="files"></a>
The Directory layout and files are as follows:  
<pre>
--main directory--        \  
buildorbit.py           Utility for building binary data files  
builder.py              Utility for batch processing; creates /bin if needed  
planetstructs.py        namedtuple definitions used by buildorbits and planets.py  
orrery.py               The main program for the project; the MVC controller  
planets.py              Module for all planet and orbit classes and data; the Model  
display.py              The module that implements the GUI; the View  
Makefile                Used to build and run the project  
        /bin            This directory and its content are created dynamically.  
                        binary data files are constructed here: they include  
                        binEarth.pkl binMars.pkl binNeptune.pkl binUranus.pkl  
                        binJupiter.pkl binMercury.pkl binSaturn.pkl binVenus.pkl  
        /build          Contains the ephemerides created by the JPL Horizons  
                horizons_results_earth_sb_1.txt  
                horizons_results_jupiter_sb_3.txt  
                horizons_results_mars_sb_1.txt  
                horizons_results_mercury_1.txt  
                horizons_results_neptune_sb_41.txt  
                horizons_results_saturn_sb_7.txt  
                horizons_results_uranus_sb_21.txt  
                horizons_results_venus_1.txt  
        /config          contains any configuration files  
                planet_config  per-planet configuration information  
<\pre>
<p>

## Running the model <a name="running"></a>
The make file is simplistic and currently has some rough edges. However it can be used to run the program, build the binary files, and do some cleanup. It can also install Python3 and Tk on Ubuntu if sudo can be run.  
make  
make run	these commands will build the binaries and run the program  
make build	builds the binaries  
make clean	removes the binary files and pycache  
make prepUbuntu installs Python 3.6 and tkinter  

python3 builder.py	runs the batch build program and populates bin/  
python3 orrery.py	runs the model  
 

## Development testing <a name="testing"></a>
While developing the code I thought about using Python unitTest. In practice, the majority of the program complexity centered around looking at large amounts of the planet data and determining whether it had the required information, was parsed and used correctly, and whether the GUI behaved correctly. In a sense this is a closed system at the moment, designed to work with a specific data set, and input checking with that data set has been done. However, if the program functionality is extended tests should be added for regression testing in the new areaso.
 Having said that, the program was tested with two dozen ephemeris files and in three environments: Fedora 20 with Python 3.2, Fedora 26 with Python 3.6, and Ubuntu 16.04

## Improvements and additions <a name="todo"></a>
Near term:  
- Better window management, in particular, initializing with the sun as the center of the visible screen  
- Mousewheel zooming  
- Converting points from lists to arrays/numpy arrays  
- Prorating motion in the outer planets. This was coded but removed because of complexity and runtime performance.  
- Update the references, which are in the history files of four different machines  
- Explore more automated unit testing.    
-Add/scale images  
  
Longer term:  
- Experiment with other documentation tools and formats (eg. Sphinx)  
- Add moons, Dwarf planets  
- Prototype with orbital elements  
- Try different graphics engines (eg. Matplotlib and Open GL)  

## References <a name="references"></a>
Some data links for this project:  

https://ssd.jpl.nasa.gov/horizons.cgi#top   
https://nssdc.gsfc.nasa.gov/planetary/factsheet/jupiterfact.html  
https://nssdc.gsfc.nasa.gov/planetary/factsheet/index.html  
https://ssd.jpl.nasa.gov/?orbits  
https://www.universetoday.com/33642/the-colors-of-the-planets/  

  
Tk:  
http://www.dabeaz.com/special/Tkinter.pdf  
http://effbot.org/tkinterbook/canvas.htm  
http://www.tkdocs.com/tutorial/canvas.html  
https://www.tutorialspoint.com/python/tk_scrollbar.htm  
http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/scrollbar.html  



