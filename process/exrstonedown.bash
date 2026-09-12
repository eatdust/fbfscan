#!/bin/bash

export PFSIMGOUT=/bin/pfsoutimgmagick
export OPTOUT='--quality 98 --bit-depth 8'

export PFSIN=/bin/pfsinexr

#clamp before tonemapping (default none)
export PFSCLAMP=/bin/pfsclamp
export OPTCLAMP='--min 0.0 --max 100.0 -p'

#tone mapping
export PFSTMO=/bin/pfstmo_mantiuk08
export OPTTMO='-d g=2.1:l=5000:b=0.1:k=0:a=0 -f 25'

#or basic LDR convertion
#export PFSTMO=/bin/pfsgamma
#export OPTTMO='-g 1.9 -m 0.02'

#for negative films, set the color inverter (to be commented for
#positive)
#export IMGINVERTER=/bin/magick
export OPTINVERT='-negate -gamma 0.4 -quality 98'
export OPTTMP=
export DELETENEG=0

export EXRSUFFIX='exr'
export OUTSUFFIX='jpg'
export OUTPREFIX='O_'
export TMPSUFFIX='ppm'

export EXRPRINTF='%06d'

export EXRMIN=0
export EXRINF=99999

if [ $# -le 1 ]; then
    echo "usage: imgprefix sequencefile Nprocess"
    exit
fi

export EXRPREFIX=$1

if [ $# -ge 3 ]; then
    export NPJOBS=$3
else
    export NPJOBS=1
fi

echo "NPJOBS= $NPJOBS"


function spawndist()
{
    startframe=$1
    endframe=$2

    pattern=$EXRPREFIX'_'$EXRPRINTF
    
    exrfile=$pattern'.'$EXRSUFFIX
    outfile=$OUTPREFIX$pattern'.'$OUTSUFFIX
    tmpfile=$OUTPREFIX$pattern'.'$TMPSUFFIX

    if [ -z ${IMGINVERTER+x} ]; then

	$PFSIN $exrfile --frames $startframe:$endframe | $PFSCLAMP $OPTCLAMP | $PFSTMO $OPTTMO | $PFSIMGOUT $OPTOUT $outfile --frames $startframe:$endframe

    else

	$PFSIN $exrfile --frames $startframe:$endframe | $PFSCLAMP $OPTCLAMP | $PFSTMO $OPTTMO | $PFSIMGOUT $OPTTMP $tmpfile --frames $startframe:$endframe

	for (( frame=$startframe; frame<=endframe; frame++))
	do
	    FRAMECOUNT=$(printf $EXRPRINTF $frame)
	    negfile=$OUTPREFIX$EXRPREFIX'_'$FRAMECOUNT'.'$TMPSUFFIX
	    posfile=$OUTPREFIX$EXRPREFIX'_'$FRAMECOUNT'.'$OUTSUFFIX
	    echo "Inverting $negfile to $posfile..."
	    $IMGINVERTER $negfile $OPTINVERT $posfile
	    if [ $DELETENEG -eq 1 ]; then
		rm -f $negfile
	    fi
	done

    fi
    
    

	
}



function cleanup()
{
    echo "**** Killing all processes! ****"
    kill $!
    killall $PFSINEXR $PFSTMO $PFSIMGOUT
    kill $$
}


# trap keyboard interrupt (control-c)
trap cleanup SIGINT

########### main ###########

#Search images and guess bracket exposures

EXRCOUNT=$(printf $EXRPRINTF $EXRMIN)

#counts image files
filename=$EXRPREFIX'_'$EXRCOUNT'.'$EXRSUFFIX

count=$EXRMIN
while [ -e $filename -a $count -le $EXRINF ]
do
    count=$[$count + 1]
    exrcount=$(printf $EXRPRINTF $count)
    filename=$EXRPREFIX'_'$exrcount'.'$EXRSUFFIX
done
export EXRNUM=$(($count - $EXRMIN))
export EXRMAX=$(($count - 1))
echo "Found $EXRNUM images!"

echo "Opening sequence file $2"
NCOLS=$(head $2 | awk '{print NF; exit}')
STARTFRAMES=$(cat $2 | awk '{print $1}')
ENDFRAMES=$(cat $2 | awk '{print $2}')

#Main loop
export count=0
export shiftf=0
while read in
do
    startf=$(echo $in | awk '{print $1}')
    endf=$(echo $in | awk '{print $2}')
    echo
    if [ $NCOLS -eq 3 ]; then
#previous shiftf applies to startf
	startf=$[$startf + $shiftf]
#read next shiftf
	shiftf=$(echo $in | awk '{print $3}')
	echo "shift found: $shiftf"
#applies to current enfd
	endf=$[$endf + $shiftf]
    fi				
    echo "sequence: $startf to $endf"
    spawndist $startf $endf &
    echo
    count=$[$count + 1]
    [[ $((count%NPJOBS)) -eq 0 ]] && wait
done < $2
wait


