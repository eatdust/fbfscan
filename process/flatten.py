#!/bin/python
import argparse
import numpy as np
from astropy.io import fits


parser = argparse.ArgumentParser()
parser.add_argument("flat",  help="Flat master file")
parser.add_argument("image", help="RGB 3D fits input file")
parser.add_argument("output", help="RGB 3D fits output file")
parser.add_argument("--zero",  help="Zero master file")
parser.add_argument("--median",action="store_true"
                    ,help="Scale output to keep equal medians")
parser.add_argument("--mean",action="store_true"
                    ,help="Scale output to keep equal means")
parser.add_argument("--max",action="store_true"
                    ,help="Scale output to keep equal max")
parser.add_argument("--tanh",action="store_true"
                    ,help="Tanh non-linear compression")
parser.add_argument("--check",action="store_true"
                    ,help="Check for saturation and skip in case of")


pargs = parser.parse_args()

scale = 1
#for 16bits output
maxout = 65535


hduf = fits.open(pargs.flat,ignore_missing_end=True)
hdui = fits.open(pargs.image,ignore_missing_end=True)


if pargs.zero is not None:
    zerocorr = True
    hduz = fits.open(pargs.zero,ignore_missing_end=True)
else:
    zerocorr = False


if zerocorr:
    image = np.true_divide(hdui[0].data - hduz[0].data
                           ,hduf[0].data - hduz[0].data)
    hduz.close()
    hduf.close()
else:
    image = np.true_divide(hdui[0].data,hduf[0].data)
    hduf.close()



if pargs.median:
    befmax = np.median(hdui[0].data)
    aftmax = np.median(image)
    scale = befmax/aftmax

if pargs.mean:
    befmax = np.mean(hdui[0].data)
    aftmax = np.mean(image)
    scale = befmax/aftmax

if pargs.max:
    befmax = np.amax(hdui[0].data)
    aftmax = np.amax(image)
    scale = befmax/aftmax    

    
if pargs.tanh:
    normimage = maxout*np.tanh(image * scale/maxout)
else:
    normimage = image * scale

    
if np.amax(normimage) <= maxout:
    hdui[0].data = normimage
else:
    if pargs.check:
        print('FATAL: flattening skipped due to saturation!')
    else:
        print('WARNING: flattening saturates!')
        hdui[0].data = normimage
        
if scale == 1:
    hdui[0].header['DATAMAX']=np.amax(normimage)
    hdui[0].header['DATAMIN']=np.amin(normimage)

hdui.writeto(pargs.output)

hdui.close()
