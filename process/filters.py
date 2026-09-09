#!/bin/python
import argparse
import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clip


parser = argparse.ArgumentParser()
parser.add_argument("image", help="RGB 3D fits input file")
parser.add_argument("output", help="RGB 3D fits output file")
parser.add_argument("--scale",type=float
                    ,help="Multiply all channels by this number")
parser.add_argument("--tanh",action="store_true"
                    ,help="Tanh non-linear compression")
parser.add_argument("--invert",action="store_true"
                    ,help="Invert values in each channel")
parser.add_argument("--normalize_min",action="store_true"
                    ,help="Normalize color channels to common minimal dynamical range")
parser.add_argument("--normalize_max",action="store_true"
                    ,help="Normalize color channels to common maximal dynamical range")
parser.add_argument("--vanish",action="store_true"
                    ,help="Set each color channel minimum at zero")
parser.add_argument("--equalize",action="store_true"
                    ,help="Perform histogram equalization in each color channel")
parser.add_argument("--sigclipmax",type=float
                    ,help="Sigma for clipping max values")
parser.add_argument("--sigclipmin",type=float
                    ,help="Sigma for clipping min values")
parser.add_argument("--shift",type=float
                    ,help="Shift all channels by this value")
parser.add_argument("--dataheader",action="store_true"
                    ,help="Update header with DATAMIN/DATAMAX")
parser.add_argument("--colorheader",action="store_true"
                    ,help="Update header with COLMIN/COLMAX")

pargs = parser.parse_args()

scale = 1
#for 16bits output
maxout = 65535

hdui = fits.open(pargs.image)
naxis = hdui[0].header['NAXIS']


#Rescale all fluxes
if pargs.scale is not None:
    normimage = hdui[0].data * pargs.scale
else:
    normimage = hdui[0].data


#Compress the image with a tanh    
if pargs.tanh:
    normimage = maxout*np.tanh(normimage/maxout)


#Apply sigma clipping if requested
if pargs.sigclipmax is not None:
    clipped = sigma_clip(normimage,
                         sigma_lower=np.inf,sigma_upper=pargs.sigclipmax)
    befmax = normimage.max()
    clipmax = clipped.max()
    print('Sigma clipped newmax= oldmax=',clipmax,befmax)
    normimage = clipped.filled(clipmax)

if pargs.sigclipmin is not None:
    clipped = sigma_clip(normimage,
                         sigma_lower=pargs.sigclipmin,sigma_upper=np.inf)
    befmin = normimage.min()
    clipmin = clipped.min()
    print('Sigma clipped newmin= oldmin=',clipmin,befmin)
    normimage = clipped.filled(clipmin)



#Invert the channels in the normalised image
if pargs.invert:    
    if naxis == 3:
        ncolors = hdui[0].header['NAXIS3']
        for i in range(ncolors):
            normimage[i,:,:] = maxout - normimage[i,:,:]
    elif naxis == 2:       
        normimage = maxout - normimage
    else:
        print('FATAL: naxis number unsupported in inverting')
        exit()

                  
#Equalize color channels within their range
if pargs.equalize:
    if naxis == 3:
        ncolors = hdui[0].header['NAXIS3']
        naxis1 = hdui[0].header['NAXIS1']
        naxis2 = hdui[0].header['NAXIS2']

        for i in range(ncolors):
            channel = np.int32(normimage[i,:,:].flatten())
            minval = np.amin(channel)
            maxval = np.amax(channel)
            df,bins = np.histogram(channel,maxout+1,[0.0,maxout])
            rawcdf = df.cumsum()
            unitcdf =  rawcdf * np.amax(df)/np.amax(rawcdf)
            cdf = minval + (unitcdf - np.min(unitcdf)) * (maxval-minval)/(np.max(unitcdf) - np.min(unitcdf))

            normimage[i,:,:] = cdf[channel].reshape((naxis2,naxis1))
            
    elif naxis == 2:

        channel = np.int16(normimage.flatten())
        minval = np.amin(channel)
        maxval = np.amax(channel)
        df,bins = np.histogram(channel,maxout+1,[0.0,maxout])
        rawcdf = df.cumsum()
        unitcdf =  rawcdf * np.amax(df)/np.amax(rawcdf)
        cdf = minval + (unitcdf - np.min(unitcdf)) * (maxval-minval)/(np.max(unitcdf) - np.min(unitcdf))

        normimage = cdf[channel].reshape((naxis2,naxis1))
        
    else:
        print('FATAL: naxis number unsupported in equalizing')
        exit()


        
#set black at 0, mostly relevant for negative films after inversion
if pargs.vanish:
    if naxis == 3:
        ncolors = hdui[0].header['NAXIS3']
        for i in range(ncolors):
            mincolor = np.amin(normimage[i,:,:])
            normimage[i,:,:] = normimage[i,:,:]- mincolor
    elif naxis == 2:
        normimage = normimage - np.amin(normimage)
        print('FATAL: naxis number unsupported in transate filter')
        exit()

        
#normalize colors to the minimal dynamical range of all channels
if pargs.normalize_min or pargs.normalize_max:
    if naxis == 3:
        ncolors = hdui[0].header['NAXIS3']
        maxcolor = []
        mincolor = []
        for i in range(ncolors):
            maxcolor.append(np.amax(normimage[i,:,:]))
            mincolor.append(np.amin(normimage[i,:,:]))

        if pargs.normalize_min:
            maxval = np.amin(maxcolor)
            minval = np.amax(mincolor)
        else:
            maxval = np.amax(maxcolor)
            minval = np.amin(maxcolor)
            
        for i in range(ncolors):            
            normimage[i,:,:] = minval + (normimage[i,:,:]- mincolor[i]) * (maxval-minval)/(maxcolor[i]-mincolor[i])
            
    elif naxis != 2:
        print('FATAL: naxis number unsupported in normalizing')
        exit()

if pargs.shift is not None:
    normimage = normimage + pargs.shift
    
    
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
