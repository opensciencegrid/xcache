#!/bin/bash

source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/bash
module load xrootd/4.1.1 2>&1
source ./setStashCache.sh
arrFiles=$(echo $1 | tr "," "\n") 
for f in $arrFiles; do
    echo $f
    echo "DL start: $(date)"
#    bash ./stashcp -d -s $f -l $2
    echo "DL end: $(date)"
done 