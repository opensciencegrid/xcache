#!/bin/bash

source /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/5.6.2/init/bash
module load xrootd/4.1.1 2>&1
source ./setStashCache.sh
bash ./stashcp -d -s $1 -l $2 