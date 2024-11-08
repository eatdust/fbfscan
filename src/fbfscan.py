#!/usr/bin/python
import cursesmenu as cm
import curtsies as ci
from curtsies.fmtfuncs import *
import wiringpi as wp
import wipimotor as wm
import scanner as sc
import time as time
import sys as sys
import threading as th

import configparser as cp
import os as os


#maximum acceleration
rpmps = 360

#maximum motor speed in fast motion
maxrpm = 1440

#stepmode
inistepmode = 16

#storage path for output scans
toppath = '/home/alarm/' + 'tests/'
imgpath = toppath + 'scans/'
flatpath = toppath + 'flats/'
zeropath = toppath + 'zeros/'

#img settings
imgroot = 'test'
imgtype = 'nef'
imglgth = 6
hdrlgth = 2

#hdr default settings
hdrframe = 3
exprange = 2

#global image positionning counter
imgcount = 0
imginfty = 43200 #30mn

#global value recording motor states
forward = True
energize = False
scanning = False

#delay between two image scan (in msec)
mindelay = 0
maxdelay = 1000



def main():


    read_config_file()
    
    #motor = initialize_motor(stepmode=inistepmode)
    motor = []
    time.sleep(2)
    camera = sc.scanner(pylog=True, summary=False)
    time.sleep(2)
    
    menu = cm.CursesMenu("Fbfscan 16mm Film Scanner", "Actions")

    motionitem = cm.items.FunctionItem("Motion controls",motion_controls,[motor,menu])
    menu.items.append(motionitem)

    scanitem = cm.items.FunctionItem("Scan controls",scan_controls,[camera,motor,menu])
    menu.items.append(scanitem)
    
    settingmenu = cm.CursesMenu(title="Fbfscan parameters menu")
    settingitem = cm.items.SubmenuItem("Settings menu",settingmenu,menu)
    
    resetitem = cm.items.FunctionItem("Set image count",reset_imgcount,[])
    hdritem = cm.items.FunctionItem("Set HDR number",reset_hdrframe,[])
    inftyitem = cm.items.FunctionItem("Set maximum count",reset_imginfty,[])
    rangeitem = cm.items.FunctionItem("Set exposure bracket",reset_exprange,[])
    expitem = cm.items.FunctionItem("Set exposure time",reset_exptime,[camera])
    isoitem = cm.items.FunctionItem("Set ISO value",reset_iso,[camera])

    settingmenu.items.append(resetitem)
    settingmenu.items.append(hdritem)
    settingmenu.items.append(inftyitem)
    settingmenu.items.append(rangeitem)
    settingmenu.items.append(expitem)
    settingmenu.items.append(isoitem)
    
    menu.items.append(settingitem)
    
    calibmenu = cm.CursesMenu(title="Fbfscan calibration menu")
    calibitem = cm.items.SubmenuItem("Calibration menu",calibmenu,menu)
    
    nframeitem = cm.items.FunctionItem("Move by N frames",move_nframes,[motor])
    angleitem = cm.items.FunctionItem("Move by an angle",move_angle,[motor])
    flatitem = cm.items.FunctionItem("Take flat exposures",take_flats,[camera,0.0])
    zeroitem = cm.items.FunctionItem("Take zero exposures",take_zeros,[camera,0.0])

    calibmenu.items.append(nframeitem)
    calibmenu.items.append(angleitem)
    calibmenu.items.append(flatitem)
    calibmenu.items.append(zeroitem)

    menu.items.append(calibitem)
    
    menu.show()



def read_config_file():

    global toppath, imgpath, flatpath, zeropath
    global imgroot, imgtype, imgcount, imginfty
    global hdrframe, exprange, inistepmode
    global rpmps, maxrpm
    

    if not os.path.exists('config.ini'):
        return


    config = cp.ConfigParser()
    config.read('config.ini')
    toppath = config['storage']['toppath']
    imgpath = toppath + config['storage']['imgsubdir']
    flatpath = toppath + config['storage']['flatsubdir']
    zeropath = toppath + config['storage']['zerosubdir']

    imgroot = config['storage']['imgroot']
    imgtype = config['storage']['imgtype']

    imgcount = int(config['camera']['imgcount'])
    imginfty = int(config['camera']['imginfty'])
    hdrframe = int(config['camera']['hdrframe'])
    exprange = int(config['camera']['exprange'])

    inistepmode = int(config['stepper']['stepmode'])
    rpmps = int(config['stepper']['maxaccel'])
    maxrpm = int(config['stepper']['maxspeed'])

    print("---------------------------------------")
    print("Config file found")
    print("---------------------------------------")
    print("toppath   = ",toppath)
    print("imgpath   = ",imgpath)
    print("flatpath  = ",flatpath)
    print("zeropath  = ",zeropath)
    print("imgroot   = ",imgroot)
    print("imgtype   = ",imgtype)
    print("")
    print("imgcount  = ",imgcount)
    print("imginfty  = ",imginfty)
    print("hdrframe  = ",hdrframe)
    print("exprange  = ",exprange)
    print("")
    print("stepmode  = ",inistepmode)
    print("rpmps     = ",rpmps)
    print("maxrpm    = ",maxrpm)
    print("---------------------------------------")
    print("")

    time.sleep(3)
    
    
    

def initialize_motor(stepmode):
    connections={'en':0,'clk':1,'cw':2}
    defaultvalues={'en':0,'clk':0,'cw':1}

    motor = wm.motor(drivername='Kinco-2CM880',motorname='QSH6018-65-28-210',
                     wiring=connections, states=defaultvalues,
                     stepmode=stepmode, pulsewidth=10,
                     clockwidth=6.5104, range=4096,
                     stepangle=1.8)
    
    print(motor.get_drivername())
    print(motor.get_motorname())
    
    print('wiring is:  =  ',motor.get_wiring())
    print('inistates   =  ',motor.get_initial_states())
    print('stepmode    =  ',motor.get_stepmode())
    print('angle/tick  =  ',motor.get_tickangle())
    print('tick/rot    =  ',motor.get_ticknumber(360))
    print('pulse width =  ',motor.get_pulsewidth())
    print('clock width =  ',motor.get_clockwidth())
    print('clock divid =  ',motor.get_clockdivider())
    print('clock shift =  ',motor.get_clockshift())
    print('clock maxrpm=  ',motor.get_clockmaxrpm())
    print('clock minrpm=  ',motor.get_clockminrpm())
    print()
    motor.switch('en')
    return motor
    



def move_nframes(motor):
    nframe =int( input('nframe = '))
    motor.softrun_to('clk',degrun=(2*nframe-1)*180.0,degramp=90.0,rpmps=rpmps)
    return


def move_angle(motor):
    angle = float( input('angle (degrees) = '))
    if angle > 180:
        motor.softrun_to('clk',degrun=angle-180,degramp=90.0,rpmps=rpmps)
    else:
        motor.softrun_to('clk',degrun=0.5*angle,degramp=0.25*angle,rpmps=rpmps)
    return


def reset_imgcount():

    global imgcount

    imgcount = int( input('imgcount = '))

    print('Global image counter reset to: ',imgcount)
    time.sleep(3)

    
    return


def reset_hdrframe():

    global hdrframe

    hdrframe = int( input('hdrframe = '))

    print('Number of bracketting frames set to: ',hdrframe)
    time.sleep(3)
    
    return


def reset_imginfty():

    global imginfty

    imginfty = int( input('imginfty = '))

    print('Maximal image count reset to: ',imginfty)
    time.sleep(3)

    
    return



def reset_exprange():

    global exprange

    exprange = int( input('exprange = '))

    print('Exposure bracketting increment set to: ',exprange)
    time.sleep(3)
    
    return


def reset_exptime(camera):

    expchoice = int( input('expchoice (see ghoto2) = '))

    camera.connect()

    expvalue = camera.set_exposure_time(expchoice)

    print('Exposure time set to: ',expvalue)
    time.sleep(3)

    camera.deconnect()
    
    return


def reset_iso(camera):

    isochoice = int( input('isochoice (see ghoto2) = '))

    camera.connect()

    isovalue = camera.set_iso(isochoice)

    print('ISO value set to: ',isovalue)
    time.sleep(3)

    camera.deconnect()
    
    return




def scan_frames(camera,motor,delay,stopscan):

    global imgcount
    global hdrframe
    global exprange
    global scanning
    
    if hdrframe <=0:
        print('scan_frames: hdrframe <=0!')
        return

    if exprange <=0:
        print('scan_frames: exprange <=0!')
        return

    success = True
    
    camera.connect()
    
    nullExpChoice, nullExpValue = camera.get_exposure_time()
    
    while not stopscan.is_set():

        stgcount = str(imgcount).zfill(imglgth)

        hdrcount = 0

        for ihdr in range(-int(hdrframe/2),int(hdrframe/2)+1):

            expChoice = int(nullExpChoice + ihdr* exprange)
            expValue = camera.set_exposure_time(expChoice)

            
            stghdr = str(hdrcount).zfill(hdrlgth)
            
            imgname = imgroot + '_' + stgcount +'_' + stghdr + '.' + imgtype

            print('scanning: ',imgname+'                 ')
            print('exposure: ',expValue+'               ')
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[F")
            camera.single_capture(imgpath,imgname,success)

            hdrcount+=1
            

        if not success:
            print('scan_frames: ABORT, capturing failure!')
            stopscan.set()
            scanning = False
            return
            
        imgcount+=1

        if imgcount > imginfty:
            print('scan_frames: ABORT, max imgcount reached= ',imgcount)
            stopscan.set()
            scanning = False            
            return
        
        
        motor.softrun_to('clk',degrun=0.0,degramp=180.0,rpmps=rpmps)

#wait after motor move        
        if delay > 0:
            inimove = wp.millis()
            while wp.millis() - inimove < delay:
                pass

    nullExpValue = camera.set_exposure_time(nullExpChoice)
    camera.deconnect()

    return



def take_flats(camera,delay):

    nflats = int( input('nflats = '))

    success = True
    
    camera.connect(success)

    if not success:
        print('take_flats: cannot connect!')
        return
    
    for count in range(0,nflats):

        stgcount = str(count).zfill(imglgth)
            
        imgname = imgroot + '_flat_' + stgcount + '.' + imgtype

        print('scanning: ',imgname+'                 ')
        sys.stdout.write("\033[F")

        camera.single_capture(flatpath,imgname)            

#wait if needed
        if delay > 0:
            iniflat = wp.millis()
            while wp.millis() - iniflat < delay:
                pass

    camera.deconnect(success)

    if not success:
        print('take_flats: cannot disconnect!')
    
    return



def take_zeros(camera,delay):

    nzeros = int( input('nzeros = '))

    success = True

    camera.connect(success)

    if not success:
        print('take_flats: cannot connect!')
        return
    
    nullExpChoice, nullExpValue = camera.get_exposure_time()    
    
    expvalue = camera.set_exposure_time(0)
    print('Exposure time set to: ',expvalue)
    time.sleep(3)

    
    for count in range(0,nzeros):

        stgcount = str(count).zfill(imglgth)
            
        imgname = imgroot + '_zero_' + stgcount + '.' + imgtype

        print('scanning: ',imgname+'                 ')
        sys.stdout.write("\033[F")

        camera.single_capture(zeropath,imgname)            

#wait if needed
        if delay > 0:
            inizero = wp.millis()
            while wp.millis() - inizero < delay:
                pass

    nullExpValue = camera.set_exposure_time(nullExpChoice)
    print()
    print('Exposure time reset to: ',nullExpValue)
    time.sleep(3)

        
    camera.deconnect(success)

    if not success:
        print('take_flats: cannot disconnect!')
    
    return







def motion_controls(motor,menu):

    global energize
    global forward

    menu.pause()
    rpmmin = motor.get_clockminrpm()
    rpmmax = min(maxrpm,motor.get_clockmaxrpm())
    rpm = rpmmin

    izero = 5
    iss = 3 + izero
    isd = 5 + izero
    isc = 7 + izero
    isr = 9 + izero

    
    with ci.FullscreenWindow() as window:
        with ci.Input() as inputgen:
            scr = ci.FSArray(window.height, window.width)

            ilast = window.height 
            
            scr[izero-1,0:window.width-1] = ci.fsarray([u'_'*window.width])
            scr[ilast-1,0:window.width-2] = ci.fsarray([u'_'*window.width])
            scr[ilast-2,0:window.width-2] = ci.fsarray([u'_'*window.width])
            
            msg = ci.fmtstr(on_blue(bold(yellow(u'MOTION CONTROL INTERFACE'))))
            center = int((window.width-msg.width)/2)
            scr[izero, center:msg.width] = [msg]

            msgspeed = ci.fmtstr(u'speed:    ')
            scr[iss, 0:msgspeed.width] = [msgspeed]
            ispeed = msgspeed.width+1
            
            msgcw = ci.fmtstr(u'direction:')
            scr[isd, 0:msgcw.width] = [msgcw]
            icw = msgcw.width+2
            msgfwd = ci.fmtstr('FORWARD ')
            msgback = ci.fmtstr('BACKWARD')

            msgrun = ci.fmtstr(u'state:')
            scr[isr, 0:msgrun.width] = [msgrun]
            msgramp = ci.fmtstr(bold(yellow('RAMP...')))
            msgon = ci.fmtstr(bold(green('RUNNING')))
            msgoff = ci.fmtstr(bold(red('STOP   ')))

            msgamp = ci.fmtstr(u'current:')
            scr[isc, 0:msgamp.width] = [msgamp]
            msgampon = ci.fmtstr(bold(green('ON ')))
            msgampoff = ci.fmtstr(bold(red('OFF')))

            rpmlab=ci.fmtstr(on_blue(bold(yellow('rpm ='))))
            rpmstg=ci.fmtstr(on_blue(red(bold(' '+str(int(rpm))))))
            scr[izero,0:rpmlab.width]=[rpmlab]
            scr[izero,rpmlab.width:rpmlab.width+rpmstg.width+1]=[rpmstg]

            steplab=ci.fmtstr(on_blue(bold(yellow('stepmode ='))))
            stepstg=ci.fmtstr(on_blue(red(bold(' '+str(motor.stepmode)))))
            scr[izero,window.width-steplab.width-stepstg.width
                :window.width-stepstg.width]=[steplab]
            scr[izero,window.width-stepstg.width:window.width]=[stepstg]


            
            running = False

            if not running:
                scr[isr,icw:icw+msgoff.width] = [msgoff]
            else:
                scr[isr,icw:icw+msgon.width] = [msgon]
                
            if forward:
                scr[isd,icw:icw+msgfwd.width] = [msgfwd]
            else:
                scr[isd,icw:icw+msgback.width] = [msgback]

            if energize:
                scr[isc,icw:icw+msgampon.width] = [msgampon]
            else:
                scr[isc,icw:icw+msgampoff.width] = [msgampoff]


#displays initial values
                
            window.render_to_terminal(scr)
            
            for c in inputgen:
                if c == '<ESC>':
                    if running:
                        motor.pwmrun_stop('clk',rpm=rpmrun,rpmps=-rpmps)
                        scr[isr,icw:icw+msgoff.width] = [msgoff]
                        running = False
                        
                    break

                elif c == '<UP>':
                    ispeed = max(ispeed + 1,msgspeed.width+1)
                    ispeed = min(ispeed,window.width-1)
                    scr[iss,ispeed:ispeed+1] = [ci.fmtstr(yellow('|'))]
                    rpm = int(rpmmin + float(ispeed-msgspeed.width-1)/float(
                        window.width-msgspeed.width-2)*(rpmmax-rpmmin))

                elif c == '<DOWN>':
                    scr[iss,ispeed:ispeed+1] = [ci.fmtstr(u' ')]
                    ispeed = max(ispeed - 1,msgspeed.width+1)
                    ispeed = min(ispeed,window.width-1)
                    rpm = int(rpmmin + float(ispeed-msgspeed.width-1)/float(
                        window.width-msgspeed.width-2)*(rpmmax-rpmmin))

                elif c == '<RIGHT>':
                    if not running:
                        if not forward:
                            motor.switch('cw')
                            forward = True
                        scr[isd,icw:icw+msgfwd.width] = [msgfwd]

                elif c == '<LEFT>':
                    if not running:
                        if forward:
                            motor.switch('cw')
                            forward = False
                        scr[isd,icw:icw+msgback.width] = [msgback]

                elif c == '<SPACE>':
                    running = not(running)
                    if running:
                        scr[isr,icw:icw+msgramp.width] = [msgramp]
                        window.render_to_terminal(scr)
                        rpmrun = motor.pwmrun_start('clk',rpm=rpm,rpmps=rpmps)
                        scr[isr,icw:icw+msgon.width] = [msgon]
                    else:
                        scr[isr,icw:icw+msgramp.width] = [msgramp]
                        window.render_to_terminal(scr)
                        motor.pwmrun_stop('clk',rpm=rpmrun,rpmps=-rpmps)
                        scr[isr,icw:icw+msgoff.width] = [msgoff]

                elif c == '<Ctrl-j>':
                    energize = not(energize)
                    if energize:
                        motor.switch('en')
                        scr[isc,icw:icw+msgampon.width] = [msgampon]
                    else:
                        motor.switch('en')
                        scr[isc,icw:icw+msgampoff.width] = [msgampoff]

                else:
                    msghelp = ci.fmtstr(bold(yellow(
                        u'Use enter, arrow keys and space bar for control. Escape to exit')))
                    centerhelp = int((window.width-msghelp.width)/2)
                    scr[ilast-1,centerhelp:centerhelp+msghelp.width] = [msghelp]

#display updated values                    


#                rpmlab=ci.fmtstr(on_blue(bold(yellow('rpm ='))))
                rpmstg=ci.fmtstr(on_blue(red(bold(' '+str(int(rpm))))))
                scr[izero,0:rpmlab.width]=[rpmlab]
                scr[izero,rpmlab.width:rpmlab.width+rpmstg.width+1]=[rpmstg]
                    
                window.render_to_terminal(scr)

    menu.resume()
    return


def scan_controls(camera,motor,menu):

    global imgcount
    global hdrframe
    global exprange
    global energize
    global forward
    global scanning
    
    menu.pause()

    delay = mindelay
    stopscan = th.Event()
    stopscan.clear()
    
    izero = 5
    iss = 3 + izero
    isd = 5 + izero
    isc = 7 + izero
    isr = 9 + izero
    iim = 11 + izero
    ihd = 13 + izero
    
    with ci.FullscreenWindow() as window:
        with ci.Input() as inputgen:
            scr = ci.FSArray(window.height, window.width)

            ilast = window.height 

            scr[izero-1,0:window.width-1] = ci.fsarray([u'_'*window.width])
            scr[ilast-1,0:window.width-2] = ci.fsarray([u'_'*window.width])
            scr[ilast-2,0:window.width-2] = ci.fsarray([u'_'*window.width])
            
            msg = ci.fmtstr(on_blue(bold(yellow(u'SCAN CONTROL INTERFACE'))))
            center = int((window.width-msg.width)/2)
            scr[izero, center:msg.width] = [msg]

            msgspeed = ci.fmtstr(u'delay:    ')
            scr[iss, 0:msgspeed.width] = [msgspeed]
            ispeed = msgspeed.width+1
            
            msgcw = ci.fmtstr(u'direction:')
            scr[isd, 0:msgcw.width] = [msgcw]
            icw = msgcw.width+2
            msgfwd = ci.fmtstr('FORWARD ')
            msgback = ci.fmtstr('BACKWARD')

            msgamp = ci.fmtstr(u'position:')
            scr[isc, 0:msgamp.width] = [msgamp]
            msgampon = ci.fmtstr(bold(green('LOCKED  ')))
            msgampoff = ci.fmtstr(bold(yellow('UNLOCKED')))
            
            msgrun = ci.fmtstr(u'state:')
            scr[isr, 0:msgrun.width] = [msgrun]
            msgon = ci.fmtstr(bold(green('SCANNING')))
            msgoff = ci.fmtstr(bold(red('STOP    ')))

            msgimg = ci.fmtstr(u'imgcount: ')
            scr[iim, 0:msgimg.width] = [msgimg]
            imgstg=ci.fmtstr(str(imgcount).zfill(imglgth))
            scr[iim,icw:icw+imgstg.width] = [imgstg]
            
            delaylab=ci.fmtstr(on_blue(bold(yellow('delay (ms) ='))))
            delaystg=ci.fmtstr(on_blue(red(bold(' '+str(int(delay))))))
            scr[izero,0:delaylab.width]=[delaylab]
            scr[izero,delaylab.width:delaylab.width+delaystg.width+1]=[delaystg]

##info not really needed on scan (displayed in the motion control
##interface)
#
#            steplab=ci.fmtstr(on_blue(bold(yellow('stepmode ='))))
#            stepstg=ci.fmtstr(on_blue(red(bold(' '+str(motor.stepmode)))))
#            scr[izero,window.width-steplab.width-stepstg.width
#                :window.width-stepstg.width]=[steplab]
#            scr[izero,window.width-stepstg.width:window.width]=[stepstg]

            isolab=ci.fmtstr(on_blue(bold(yellow('iso ='))))
            if camera.error == 0:
                isostg=ci.fmtstr(on_blue(red(bold(' '+str(camera.get_iso())))))
            else:
                isostg = ci.fmtstr(on_blue(red(bold(' '+'No Cam'))))
            scr[izero,window.width-isolab.width-isostg.width
                :window.width-isostg.width]=[isolab]
            scr[izero,window.width-isostg.width:window.width]=[isostg]

            shutlab=ci.fmtstr(on_blue(bold(yellow('exptime ='))))

            if camera.error == 0:
                shutstg=ci.fmtstr(on_blue(red(bold(' '+str(camera.get_exposure_time())))))
            else:
                shutstg = ci.fmtstr(on_blue(red(bold(' '+'No Cam'))))

            icenter=int((window.width+shutlab.width+shutstg.width)/2)
            scr[ilast-2,icenter-shutlab.width-shutstg.width:icenter-shutstg.width]=[shutlab]
            scr[ilast-2,icenter-shutstg.width:icenter]=[shutstg]



            hdrlab=ci.fmtstr(on_blue(bold(yellow('hdrframe ='))))
            hdrstg=ci.fmtstr(on_blue(red(bold(' '+str(hdrframe)))))
            scr[ilast-2,window.width-hdrlab.width-hdrstg.width
                :window.width-hdrstg.width]=[hdrlab]
            scr[ilast-2,window.width-hdrstg.width:window.width]=[hdrstg]

            explab=ci.fmtstr(on_blue(bold(yellow('exprange ='))))
            expstg=ci.fmtstr(on_blue(red(bold(' '+str(exprange)))))
            scr[ilast-2,0:explab.width]=[explab]
            scr[ilast-2,explab.width:explab.width+expstg.width+1]=[expstg]
            

            scanning = False

            if not scanning:
                scr[isr,icw:icw+msgoff.width] = [msgoff]
            else:
                scr[isr,icw:icw+msgon.width] = [msgon]
                
            if forward:
                scr[isd,icw:icw+msgfwd.width] = [msgfwd]
            else:
                scr[isd,icw:icw+msgback.width] = [msgback]

            if energize:
                scr[isc,icw:icw+msgampon.width] = [msgampon]
            else:
                scr[isc,icw:icw+msgampoff.width] = [msgampoff]


#displays initial values
                
            window.render_to_terminal(scr)
            
            for c in inputgen:
                if c == '<ESC>':
                    if scanning:
                        stopscan.set()
                        thscan.join(timeout=None)
                        scanning = False
                    break

                elif c == '<UP>':
                    ispeed = max(ispeed + 1,msgspeed.width+1)
                    ispeed = min(ispeed,window.width-1)
                    scr[iss,ispeed:ispeed+1] = [ci.fmtstr(yellow('|'))]
                    delay = int(mindelay + float(ispeed-msgspeed.width-1)/float(
                        window.width-msgspeed.width-2)*(maxdelay-mindelay))

                elif c == '<DOWN>':
                    scr[iss,ispeed:ispeed+1] = [ci.fmtstr(u' ')]
                    ispeed = max(ispeed - 1,msgspeed.width+1)
                    ispeed = min(ispeed,window.width-1)
                    delay = int(mindelay + float(ispeed-msgspeed.width-1)/float(
                        window.width-msgspeed.width-2)*(maxdelay-mindelay))

                elif c == '<RIGHT>':
                    if not scanning:
                        if not forward:
                            motor.switch('cw')
                            forward = True
                        scr[isd,icw:icw+msgfwd.width] = [msgfwd]

                elif c == '<LEFT>':
                    if not scanning:
                        if forward:
                            motor.switch('cw')
                            forward = False
                        scr[isd,icw:icw+msgback.width] = [msgback]

                elif c == '<SPACE>':
                    scanning = not(scanning)
                    if scanning:
                        stopscan.clear()
                        thscan = th.Thread(name='scan',
                                           target=scan_frames,
                                           args=[camera,motor,delay,
                                                 stopscan])
                        thscan.start()
                        scr[isr,icw:icw+msgon.width] = [msgon]
                    else:                        
                        stopscan.set()
                        thscan.join(timeout=None)
                        scr[isr,icw:icw+msgoff.width] = [msgoff]

                   
                elif c == '<Ctrl-j>':
                    energize = not(energize)
                    if energize:
                        motor.switch('en')
                        scr[isc,icw:icw+msgampon.width] = [msgampon]
                    else:
                        motor.switch('en')
                        scr[isc,icw:icw+msgampoff.width] = [msgampoff]

                else:
                    msghelp = ci.fmtstr(bold(yellow(
                        u'Use enter, arrow keys and space bar for control. Escape to exit')))
                    centerhelp = int((window.width-msghelp.width)/2)
                    scr[ilast-1,centerhelp:centerhelp+msghelp.width] = [msghelp]

#display updated values                    


#                delaylab=ci.fmtstr(on_blue(bold(yellow('delay ='))))
                delaystg=ci.fmtstr(on_blue(red(bold(' '+str(int(delay))))))
                scr[izero,0:delaylab.width]=[delaylab]
                scr[izero,delaylab.width:delaylab.width+delaystg.width+1]=[delaystg]

                imgstg=ci.fmtstr(str(imgcount).zfill(imglgth))
                scr[iim,icw:icw+imgstg.width] = [imgstg]

                
                window.render_to_terminal(scr)

    menu.resume()
    return





if __name__ == "__main__":
    main()
