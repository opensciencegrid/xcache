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
        echo "problem in getting best redirector. Setting it to atlas-xrd-us.usatlas.org."
    endif
    setenv STORAGEPREFIX "root://data.ci-connect.net/"
else
    setenv STORAGEPREFIX $r/
endif

eval "rm -f getBestStashCache"
