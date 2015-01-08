#!/bin/bash

source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/bash
module load xrootd/4.1.1 2>&1
source ./setStashCache.sh
arrFiles=$(echo $1 | tr ",")
for f in $arrFiles; do
	bash ./stashcp -d -s $f -l $2
done 