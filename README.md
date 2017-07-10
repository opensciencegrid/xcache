# StashCache-Daemon meta package

## Dependencies

* condor-python
* xrootd-python

## StashCache Description

The script `/usr/sbin/stashcache` is used as an intermediary between a condor_master and a StashCache
cache server. Its two main functions are to accept signals from the
`condor_master` and to advertise the cache stats back to the master. It is not
intended to be run standalone but rather by the condor_master. It calls
`xrootd_cache_stats.py` to query the XRootD cache.

## Invoking xrootd_cache_stats.py
This is a script for collecting information about the files in a Stash cache and formatting them as an HTCondor classad.

If run as:

`xrootd_cache_stats.py <base xrootd URL> <top level cache directory> [max cache fraction]`

It will print the classad to stdout, for example:

`xrootd_cache_stats.py root://fermicloud126.fnal.gov /stash 0.9`

The max cache fraction is needed to correctly calculate the remaining cache size.
It should match the value in the xrootd config file.
