#!/bin/bash

source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/current/init/bash
module load stashcp
stashcp --closest
arrFiles=$(echo $1 | tr "," "\n") 
for f in $arrFiles; do
    echo $f
    stashcp -d -s $f -l $2 2>&1
    file=$(echo $f | rev | cut -d'/' -f1 | rev)
#    rm $2/$file
    f1=$(echo $f | cut -d'/' -f4-)
    st=$(date +%s%3N)
    #wget http://stash.osgconnect.net/+olsona/$f1 -P $2 2>&1
    wget -qO- http://stash.osgconnect.net/+olsona/$f1 &> /dev/null
    res=$?
    dl=$(date +%s%3N)
    #if [ -s $2/$file ]; then
    if [ $res -eq 0 ]; then
	#size=$(stat --printf="%s" $2/$file)
	size=10
	dltm=$((dl-st))
	printf "Source: STASH\tDestination: %s\tFile: %s\tTime: %s ms\tStart: %s\tSize: %s B\n" "$OSG_SITE_NAME" "$file" "$dltm" "$st" "$size"
	#rm $2/$file
    else
	printf "WGET of $file failed.\n"
    fi
done 

#Pulls a file using stashcp first, then pulls the same file using WGET.  Results from WGET are printed out; results from STASHCP are available on Hadoop node.
