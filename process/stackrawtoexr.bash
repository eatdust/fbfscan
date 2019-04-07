#!/bin/bash

export FLATIMG=BeforeFlat.fits

export DCRAW=/bin/dcraw
#export OPTDCRAW='-r 2.355628 1.000000 1.779836 1.000000 -4 -c'
export OPTDCRAW='-v -w -4 -c -P ./badpixels'

export PAMCUT=/bin/pamcut

export PAMTOFITS=/bin/pamtofits
export OPTPAMTOFITS=

export FITSTOPPM=/bin/fitstopnm
export OPTFITSTOPPM='-omaxval=65535'

export PAMFLIP=/bin/pamflip

export PYTHON=/bin/python
export FLATTEN=./flatten.py
export OPTFLATTEN='--mean'

export PFSINHDR=/bin/pfsinhdrgen
export PFSEXROUT=/bin/pfsout

export PFSIMGOUT=/bin/pfsoutimgmagick
export OPTOUT='--quality 98 --bit-depth 8'

export PFSCAL=/bin/pfshdrcalibrate
export OPTCAL='-r linear -c none -b 12'

export IMGTOHDRGEN=/bin/dcraw2hdrgen
export PFSINEXR=/bin/pfsinexr

export PFSCLAMP=/bin/pfsclamp
export OPTCLAMP=

export PFSTMO=/bin/pfstmo_mantiuk08
export OPTTMO='-d g=2.2:l=5000:b=0.1:k=0:a=0 -f 25'

#basic LDR convertion
#export PFSTMO=/bin/pfsgamma
#export OPTTMO='-g 1.9 -m 0.02'

export IMGSUFFIX='nef'
export FITSSUFFIX='fits'
export PPMSUFFIX='ppm'
export EXRSUFFIX='exr'
export OUTSUFFIX='jpg'

export FLATPREFIX='F_'
export OUTPREFIX='O_'

export IMGPRINTF='%06d'
export HDRPRINTF='%02d'

export IMGMIN=2100
export IMGINF=99999
export HDRMIN=0
export DELETETMP=1
#tone mapping image per image does not allow fps option to work. Will
#generate blinking!
export TONEMAPPING=0


if [ $# -le 1 ]; then
    echo "usage: imgprefix cropsize Nprocess"
    exit
fi

export IMGPREFIX=$1
export cropsize=$2

if [ $# -ge 3 ]; then
    export NPJOBS=$3
else
    export NPJOBS=1
fi

echo "NPJOBS= $NPJOBS"


function spawndist()
{
    imgcount=$(printf $IMGPRINTF $1)
    hdrmin=$2
    hdrnum=$3
    hdrmax=$[$hdrnum - 1]

    prefix=$IMGPREFIX'_'$imgcount
    
    if [ $# -eq 4 ];then
	export crop="$4"
	width=`echo $crop | awk 'BEGIN { FS = "x|+" } ; { print $1 }'`
	height=`echo $crop | awk 'BEGIN { FS = "x|+" } ; { print $2 }'`
	left=`echo $crop | awk 'BEGIN { FS = "x|+" } ; { print $3 }'`
	top=`echo $crop | awk 'BEGIN { FS = "x|+" } ; { print $4 }'`
    fi

    for (( ihdr=$hdrmin; ihdr<hdrnum; ihdr++))
    do

	hdrcount=$(printf $HDRPRINTF $ihdr)

	imgname=$prefix'_'$hdrcount'.'$IMGSUFFIX
	fitsname=`echo $imgname | sed 's|.'$IMGSUFFIX'|.'$FITSSUFFIX'|g'`
	outfits=$FLATPREFIX$fitsname
	outppm=`echo $outfits | sed 's|.'$FITSSUFFIX'|.'$PPMSUFFIX'|g'`
	
	echo
	echo '********************************************************************'
	echo 'converting: '$imgname 'with' $crop

	$DCRAW $OPTDCRAW $imgname | $PAMCUT -left $left -top $top -width $width -height $height | $PAMTOFITS $OPTPAMTOFITS > $fitsname

	if [ -e $FLATIMG ]; then
	    echo 'flattening: '$fitsname 'to' $outfits
	    $PYTHON $FLATTEN $FLATIMG $fitsname $outfits $OPTFLATTEN
	else
	    echo 'no flattening performed!'
	    ln -s $fitsname $outfits
	fi
	    
	echo 'converting: '$outfits 'to' $outppm	
	$FITSTOPPM $OPTFITSTOPPM $outfits | $PAMFLIP -topbottom > $outppm

	if [ $DELETETMP -eq 1 ]; then
	    rm -f $outfits $fitsname
	fi
	    
	
	echo '********************************************************************'

    done

    hdrgenfile=$prefix.hdrgen
    
    $IMGTOHDRGEN $prefix'_'*.$IMGSUFFIX > $hdrgenfile

    sed -i 's|.'$IMGSUFFIX'|.'$PPMSUFFIX'|g' $hdrgenfile
    sed -i 's|'$IMGPREFIX'|'$FLATPREFIX$IMGPREFIX'|g' $hdrgenfile
        
    echo
    echo '--------------------------------------------------------------------'
    echo 'creating HDR image from '$hdrgenfile

    exrfile=$prefix'.'$EXRSUFFIX
    
    $PFSINHDR $hdrgenfile | $PFSCAL $OPTCAL | $PFSEXROUT $exrfile

    if [ $DELETETMP -eq 1 ]; then
	rm -f $FLATPREFIX$prefix'_'*.$PPMSUFFIX
    fi

    outfile=$OUTPREFIX$prefix'.'$OUTSUFFIX

    if [ $TONEMAPPING -eq 1 ]; then
	$PFSINEXR $exrfile | $PFSCLAMP $OPTCLAMP | $PFSTMO $OPTTMO | $PFSIMGOUT $OPTOUT $outfile
    fi
	
}



function cleanup()
{
    echo "**** Killing all processes! ****"
    kill $!
    killall $DJPEG $PAMTOFITS $PFSIN $FITSTOPPM $PYTHON
    kill $$
}


# trap keyboard interrupt (control-c)
trap cleanup SIGINT

########### main ###########

#Search images and guess bracket exposures
HDRCOUNT=$(printf $HDRPRINTF $HDRMIN)
IMGCOUNT=$(printf $IMGPRINTF $IMGMIN)

filename=$IMGPREFIX'_'$IMGCOUNT'_'$HDRCOUNT'.'$IMGSUFFIX
echo "Searching images as $filename"


#counts hdr brackets
count=$HDRMIN
while [ -e $filename ]
do
    count=$[$count + 1]
    hdrcount=$(printf $HDRPRINTF $count)
    filename=$IMGPREFIX'_'$IMGCOUNT'_'$hdrcount'.'$IMGSUFFIX
done
export HDRNUM=$[$count - $HDRMIN]
export HDRMAX=$[$count - 1]

#counts image files
filename=$IMGPREFIX'_'$IMGCOUNT'_'$HDRCOUNT'.'$IMGSUFFIX

count=$IMGMIN
while [ -e $filename -a $count -le $IMGINF ]
do
    count=$[$count + 1]
    imgcount=$(printf $IMGPRINTF $count)
    filename=$IMGPREFIX'_'$imgcount'_'$HDRCOUNT'.'$IMGSUFFIX
done
export IMGNUM=$[$count - $IMGMIN]
export IMGMAX=$[$count - 1]
echo "Found $IMGNUM images with $HDRNUM bracket exposures!"



#Main loop
for (( count=$IMGMIN; count<=$IMGMAX; count++ ))
do
    spawndist $count $HDRMIN $HDRNUM $cropsize &
    [[ $((count%NPJOBS)) -eq 0 ]] && wait
done
wait


