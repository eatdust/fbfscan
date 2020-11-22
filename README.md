# Fbfscan: a frame-by-frame HDR film scanner

---

### Summary

Fbfscan is a python script for Raspberry Pi allowing interactive and
automatic controls of a digital camera and a stepper motor to allow
for frame-by-frame film scan. Support for "flat" exposures, High Dynamical
Range (HDR), calibration... are provided. **Fbfscan** is built on top of
**gphoto2** for controlling digital cameras and **wipistepper** for
controlling stepper motors.

Please ensure that you have a working installation of
[wiringpi](http://wiringpi.com/), its python wrappers
[WiringPi-Python](https://github.com/WiringPi/WiringPi-Python),
[wipistepper](https://github.com/eatdust/wipistepper),
[gphoto2](https://github.com/gphoto/gphoto2) as well as
[python-gphoto2](https://github.com/jim-easterbrook/python-gphoto2). Fbfscan
also relies on
[curses-menu](https://github.com/pmbarrett314/curses-menu) and
[curtsies](https://github.com/bpython/curtsies).

The directory "process/" contains a few scripts for processing the raw
images into EXR images, as well as tone-mapping them afterwards. For
these scripts to work, you should have a working installation of
[pfstools](http://pfstools.sourceforge.net/),
[astropy](http://www.astropy.org/), [netpbm](http://www.astropy.org/)
and [dcraw](http://www.astropy.org/).

---

### Scanner initialization and methods

Simply plug a digical camera to the Raspberry Pi (RPI) using an USB
cable and switch it on. A **scanner** object is initialized with only
a name (see scanner.py):

```python
    def __init__(self,name='',pylog=True, summary=False):
```

Only a few method from **gphoto2** are wrapped for a scanner object:

```python
    def get_exposure_time(self):
    def set_exposure_time(self,choice):
    def get_iso(self):
    def set_iso(self,choice):
    def get_exposure_bias(self):
    def set_exposure_bias(self,choice):
    def single_capture(self,path,filename,success=True):
```

Notice that *choice* should be an integer (see **gphoto2** help) and
*single_capture()* triggers one shot with the set exposure and set iso
and save it under path/filename.

---

### Fbfscan window

Fbfscan should be started within a **xterm** and possibly in "sudo"
mode for allowing hardware access to the RPI. It is assumed that a
digital camera is plugged in (via USB), on, and **fbfscan** will first
attempt to initialize a scanner object from it. If no camera is
connected, **fbfscan** will proceed with a warning message. A stepper
motor controlled by a driver is expected to be connected to the RPI
and will be initialized, if found, as (see fbfscan.py):

```python
   def initialize_motor(stepmode):
       connections={'en':0,'clk':1,'cw':2}
       defaultvalues={'en':0,'clk':0,'cw':1}

       motor = wm.motor(drivername='Kinco-2CM880',motorname='QSH6018-65-28-210',
                        wiring=connections, states=defaultvalues,
			stepmode=stepmode,
                        pulsewidth=10,
                        clockwidth=6.5104, range=4096,
			stepangle=1.8)
```					      

These default settings should certainly be edited, such as the default
*stepmode*, storage path for scans, flats and bias images. For this
purpose, an editable **config.ini** is provided, which is initialy
read and will override most of these options. Check out your driver and stepper
motor settings, see [**wipistepper**](https://github.com/eatdust/wipistepper)
for more details. Other editable settings are:

```python
#stepmode
inistepmode = 16

#storage path for output scans
toppath ='/home/alarm/tests/'
imgpath = toppath + 'scans/'
flatpath = toppath + 'flats/'
zeropath = toppath + 'zeros/'

#img settings
imgroot = 'test'
imgtype = 'nef'

#hdr default settings
hdrframe = 3
exprange = 2

```

They specify how many *hdrframe* you want for each scan image, what
exposure range (*exprange*) they spawn (here 2 stops). These can also
be edited interactively using the **fbfscan** settings menu. A summary
of the default settings is displayed during the initialization, after
which, the main menu shows up:

---
![main](/docs/main_menu.png?raw=true)
---

The first entry allows to control the stepper interactively, using
arrows, entry key and space bar:

---
![motion](/docs/motion_controls.png?raw=true)
---

The second entry leads to the scanning control, pictures and frame
forward are taken automatically:

---
![scan](/docs/scan_controls.png?raw=true)
---

The setting menu allows to modify on the fly various default
parameters:

---
![param](/docs/params_menu.png?raw=true)
---

Finally, "calibration" allows taking flat field exposures, bias
exposures or adjust the film position by moving it by a given number
of frames:

---
![calib](/docs/calibs_menu.png?raw=true)
---

---

### Real world example

The beast running and controlled from the "motion" menu:

![front](/docs/scannerfront.jpg)

The disco lights flashing on the back:

![back](/docs/scannerback.jpg)

Good Luck!

---
