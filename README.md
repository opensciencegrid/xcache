# StashCache

[![Build Status](https://travis-ci.org/opensciencegrid/StashCache.svg?branch=master)](https://travis-ci.org/opensciencegrid/StashCache)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.377033.svg)](https://doi.org/10.5281/zenodo.377033)


This repo holds json file with addresses, statuses and geographical coordinates of all of the StashCache caches.
Status is given as a number: 1 - Active, 0 - Not Active.

## Using Stashcp

XrootD client is required to be installed in order to use stashcp.  You can use it with:

    ./bin/stashcp <source> <destination>
    
See the help message for full usage of the command.

## Operation of stashcp

Stashcp uses geo located nearby caches in order to copy from the OSG Connect's stash storage service
to a job's workspace on a cluster.

Stashcp uses an ordered list of methods to access the file:

1. Copy the file from CVMFS, under the directory /cvmfs/stash.osgstorage.org/...
2. Copy the file with `xrdcp` from the nearest cache.
3. Copy the file with `xrdcp` from the source, stash.osgconnect.net.

While using `xrdcp`, it uses XrootD's internal timers to act as a strict watchdog.
