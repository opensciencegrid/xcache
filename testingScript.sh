#!/bin/bash

source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/bash
module load xrootd/4.1.1 
echo "$(date): Loaded XrootD"
source ./setStashCache.sh
echo "$(date): Got prefix"
arrFiles=$(echo $1 | tr "," "\n") 
for f in $arrFiles; do
    echo $f
    echo "DL start: $(date)"
    bash ./stashcp -d -s $f -l $2 2>&1
    echo "DL end: $(date)"
	stat --printf="%s" $2/$f
done 