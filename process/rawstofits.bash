#!/bin/bash

export IMGSUFFIX='nef'
export FITSSUFFIX='fits'

export OPTDCRAW='-v -4 -w -c -P ./badpixels'

if [ $# -eq 0 ];then
    echo 'usage is: filelist cropsize Nprocess'
    exit
fi

if [ $# -ge 2 ]; then
    export cropsize=$2
fi

if [ $# -ge 3 ]; then
    export NPJOBS=$3
else
    export NPJOBS=1
fi

echo "NPJOBS= $NPJOBS"


function spawndist()
{
    image=$1

    if [ $# -eq 2 ];then
	export crop="$2"
	width=`echo $crop | awk 'BEGIN { FS = "x|+" } ; { print $1 }'`
	height=`echo $crop | awk 'BEGIN { FS = "x|+" } ; { print $2 }'`
	left=`echo $crop | awk 'BEGIN { FS = "x|+" } ; { print $3 }'`
	top=`echo $crop | awk 'BEGIN { FS = "x|+" } ; { print $4 }'`
    fi

    
    name=`echo $image | sed 's|.'$IMGSUFFIX'||g'`
    echo
    echo '********************************************************************'
    echo 'converting: '$image 'with' $crop
    echo '********************************************************************'
    echo
    
    dcraw $OPTDCRAW $image | pamcut -left $left -top $top -width $width -height $height | pamtofits > $name.$FITSSUFFIX
}

function cleanup()
{
    echo "**** Killing all processes! ****"
    kill $!
    killall dcraw pamcut pamtofits
    kill $$
}

# trap keyboard interrupt (control-c)
trap cleanup SIGINT

########### main loop ###########

filename=$1

imagelist=`cat $filename`
echo 'reading image list:' $filename

count=0
for image in $imagelist
do
    spawndist $image $cropsize &
    count=$[$count + 1]
    [[ $((count%NPJOBS)) -eq 0 ]] && wait
done
wait



