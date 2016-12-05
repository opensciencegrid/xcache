#!/bin/bash

deb=1
if [ "$#" -eq 1 ]; then
    if [ $1 = "--quiet" -o $argv[1] = "-q" ]; then
        deb=0
    fi
fi

if [ "$StashToolsDir" = "" ]; then
    StashToolsDir="./"
fi

red=$($StashToolsDir/get-best-StashCache)
sc=$?

if [ $deb -eq 1 ]; then
    echo "$red"
fi

if [ $sc -eq 0 ]; then
    eval "$red"
else
    if [ $deb -eq 1 ]; then
    	echo "problem in getting best redirector. Setting it to data.ci-connect.net."
    fi
    export STASHPREFIX="root://data.ci-connect.net/"
fi