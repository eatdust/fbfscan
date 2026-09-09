#!/bin/python
import argparse
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clip


parser = argparse.ArgumentParser()
parser.add_argument("flat",  help="Flat master file")
parser.add_argument("image", help="RGB 3D fits input file")
parser.add_argument("output", help="RGB 3D fits output file")
parser.add_argument("--zero",  help="Zero master file (optional)")
parser.add_argument("--median",action="store_true"
                    ,help="Flattening keeps equal medians")
parser.add_argument("--mean",action="store_true"
                    ,help="Flattening keeps equal means")
parser.add_argument("--max",action="store_true"
                    ,help="Flattening keeps equal max")
parser.add_argument("--check",action="store_true"
                    ,help="Check for saturation and skip in case of")
parser.add_argument("--dataheader",action="store_true"
                    ,help="Update header with DATAMIN/DATAMAX")
parser.add_argument("--colorheader",action="store_true"
                    ,help="Update header with COLMIN/COLMAX")

pargs = parser.parse_args()

scale = 1
#for 16bits output
maxout = 65535


hduf = fits.open(pargs.flat)
hdui = fits.open(pargs.image)

#sanity check
naxis = hdui[0].header['NAXIS']
if hduf[0].header['NAXIS'] != naxis:
    exit()

if pargs.zero is not None:
    zerocorr = True
    hduz = fits.open(pargs.zero)
else:
    zerocorr = False

#flattening with zero corrections or not
if zerocorr:
    image = np.true_divide(hdui[0].data - hduz[0].data
                           ,hduf[0].data - hduz[0].data)
    hduz.close()
    hduf.close()
else:
    image = np.true_divide(hdui[0].data,hduf[0].data)
    hduf.close()


#Determine factors for image rescaling, if any
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

normimage = scale * image
    
#Warn or skip flattening in case of saturation       
if np.amax(normimage) <= maxout and np.amax(normimage) >=0:
    hdui[0].data = normimage
else:
    if pargs.check:
        print('FATAL: image skipped due to saturation and/or negative values')
    else:
        print('WARNING: saturation and/or negative values detected!')
        hdui[0].data = normimage
    

#fill header and output file
if pargs.dataheader:
    hdui[0].header['DATAMAX']=np.amax(normimage)
    hdui[0].header['DATAMIN']=np.amin(normimage)

if pargs.colorheader and naxis == 3:
    ncolors = hdui[0].header['NAXIS3']
    for i in range(ncolors):
        hdui[0].header['COLMAX'+str(i+1)]=np.amax(normimage[i,:,:])
        hdui[0].header['COLMIN'+str(i+1)]=np.amin(normimage[i,:,:])
        

hdui.writeto(pargs.output)

hdui.close()
