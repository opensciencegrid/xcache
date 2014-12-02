#!/bin/tcsh

set deb=1
if ( $#argv == 1) then
    if ($argv[1] =~ "--quiet" || $argv[1] =~ "-q") then
        set deb=0
    endif
endif

if ( $StashToolsDir =~ "" ) then
    set StashToolsDir = "./"
endif

$StashToolsDir/get-best-StashCache > getBestStashCache

cat getBestStashCache

set r=`grep export getBestStashCache | awk -F "STORAGEPREFIX=" '{print $2}'`
echo "$r"
if ( $r =~ "" ) then
    if ( $deb > 0 ) then
        echo "problem in getting best redirector. Setting it to data.ci-connect.net."
    endif
    setenv STASHPREFIX "root://data.ci-connect.net/"
else
    setenv STASHPREFIX $r
endif

eval "rm -f getBestStashCache"
