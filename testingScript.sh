#!/bin/bash

source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/bash
module load xrootd/4.1.1 
echo "$(date): Loaded XrootD"
source ./setStashCache.sh
echo "$(date): Got prefix"
arrFiles=$(echo $1 | tr "," "\n") 
for f in $arrFiles; do
    echo $f
    bash ./stashcp -d -s $f -l $2 2>&1
    file=$(echo $f | rev | cut -d'/' -f1 | rev)
    rm $2/$file
#    f1=$(echo $f | cut -d'/' -f4-)
#    st=$(date +%s%3N)
#    wget http://stash.osgconnect.net/+olsona/$f1 -P $2 2>&1
#    dl=$(date +%s%3N)
#    if [ -s $2/$file ]; then
#	size=$(stat --printf="%s" $2/$file)
#	dltm=$((dl-st))
#	printf "Source: STASH\tFile: %s\tTime: %s ms\tStart: %s\tSize: %s B\n" "$file" "$dltm" "$st" "$size"
#	rm $2/$file
#    else
#	printf "WGET of $file failed."
#    fi
done 
