#!/bin/bash

usage="$(basename "$0") [-d] [-r] [-h] -s <source> [-l <location to be copied to>]

	-d: show debugging information
	-r: recursively copy
	-h: show this help text
	
	--closest: return closest cache location

	Exit status 4 indicates that at least one file did not successfully copy over.
	Exit status 1 indicates that the WantsStashCache classad was not present."

function getClose {
	## for now, call Ilija's code, and hope that it is available nearby
    setStashCache=`which setStashCache.sh 2>/dev/null`
    if [ $? -ne '0' ]; then
	>&2 echo "Cannot find setStashCache.sh, setting to defaults"
	echo "root://data.ci-connect.net"
	exit 1
    else 	
	source $setStashCache 2>&1 > /dev/null
	echo $STASHPREFIX
    fi
}

function updateInfo {
    # starts, names, sizes, times, sources
    starts=("${starts[@]}" $1)
    names=("${names[@]}" $2)
    sizes=("${sizes[@]}" $3)
    times=("${times[@]}" $4)
    sources=("${sources[@]}" $5)
}

#http://stackoverflow.com/a/5032641
function strIndex {
    x="${1%%$2*}"
    [[ $x = $1 ]] && echo -1 || echo ${#x}
}

function doStashCpSingle {
    ## address single-file case
    sz=$(xrdfs root://data.ci-connect.net stat $source | grep "Size: " | cut -d':' -f2)
    sz=$(echo -n "${sz//[[:space:]]/}")
    ## if someone has 'Size: ' in their file path, they have bigger problems than this not working.
    mb=$((sz/1000000))
    tm=$((300+mb))
	
    ## use included timeout script (timeout.sh) to timeout on xrdcp
    myFile=$1
    #http://stackoverflow.com/a/16623897
    relPath=${sfile#$prefix}
    st1=$(date +%s%3N)
    timeout $tm xrdcp $xrdargs -f $myPrefix://$myFile $baseDir/$relPath 2>&1
    res=$?
    dl1=$(date +%s%3N)
    if [ $res -eq 0 ]; then
	## pull from local cache succeeded
	dltm=$((dl1-st1))
	if [ $2 ]; then 	# update info only if I want to
	    updateInfo $st1 $myFile $sz $dltm $myPrefix
	fi
	## send info out to flume
	hn=$myPrefix
	timestamp=$(date +%s)
	header="[{ \"headers\" : {\"timestamp\" : \"${timestamp}\", \"host\" : \"${hn}\" },"
	body="\"body\" : \"$((st1/1000)),$myFile,$sz,$dltm,$OSG_SITE_NAME,$hn\"}]"
	echo $header$body > data.json
	timeout 10s curl -X POST -H 'Content-Type: application/json; charset=UTF-8' http://hadoop-dev.mwt2.org:80/ -d @data.json 2>&1 
	rm data.json 2>&1
    else
	## pull from local cache failed; pull from trunk
	if [ $debug -eq 2 ]; then
	    ## print out debug info
	    echo "Pull of $myFile from $myPrefix failed."
	    echo "Command: xrdcp $xrdargs -f $myPrefix://$myFile $baseDir/$relPath 2>&1"
	    echo "Trying to pull from trunk."
	fi
	st2=$(date +%s%3N)
	hn="root://data.ci-connect.net"
	timeout $tm xrdcp $xrdargs -f $hn://$myFile $baseDir/$relPath 2>&1
	res=$?
	dl2=$(date +%s%3N)
	if [ $res -eq 0 ]; then
	    ## pull from trunk succeeded
	    dltm=$((dl2-st2))
	    if [ $2 ]; then
		updateInfo $st2 $myFile $sz $dltm $hn
	    fi
	    failoverfiles=("${failoverfiles[@]}" $myFile)
	    failovertimes=("${failovertimes[@]}" $st1) # time that the failed pull started
	    ## send info out to flume
	    timestamp=$(date +%s)
	    header="[{ \"headers\" : {\"timestamp\" : \"${timestamp}\", \"host\" : \"${hn}\" },"
	    body="\"body\" : \"$((st2/1000)),$myFile,$sz,$dltm,$OSG_SITE_NAME,$hn\"}]"
	    echo $header$body > data.json
	    timeout 10s curl -X POST -H 'Content-Type: application/json; charset=UTF-8' http://hadoop-dev.mwt2.org:80/ -d @data.json 2>&1
	    rm data.json 2>&1
	else
	    failfiles=("${failfiles[@]}" $myFile)	
	    failtimes=("${failtimes[@]}" $st2)	# the last time something failed
	    failcodes=("${failcodes[@]}" $res)
	    echo "Stashcp of $myFile failed."
	    echo "Command: xrdcp $xrdargs -f root://data.ci-connect.net://$myFile $baseDir/$relPath 2>&1"
	    failed=$((failed+1))
	fi
    fi
}

function doStashCpDirectory {
    ## address directory case
    mySource=$1
    sfiles=$(xrdfs root://data.ci-connect.net ls $mySource)
    sz=$(xrdfs root://data.ci-connect.net stat $mySource | grep "Size: " | cut -d':' -f2)
    sz=$(echo -n "${sz//[[:space:]]/}")
    st=$(date +%s%3N)
    echo "Source: $mySource"
    echo "Prefix: $prefix"
    for sfile in $sfiles; do
	isdir=$(xrdfs root://data.ci-connect.net stat $sfile | grep "IsDir" | wc -l)
	if [ $isdir != 0 ] && [ $recursive == 1 ]; then
	    relPath=${sfile#$prefix}
	    echo "My relative path is: $relPath"
	    mkdir -p $baseDir/$relPath
	    doStashCpDirectory $sfile $baseDir/$relPath
	elif [ $isdir == 0 ]; then
	    doStashCpSingle $sfile 	
	fi
    done
    dl=$(date +%s%3N)
    dltm=$((dl-st))
    if [ $2 ]; then
	updateInfo $st $sourceName $sz $dltm $myPrefix
    fi
}

## check if the relevant classad is there
#classad=(`grep ^WantsStashCache $_CONDOR_JOB_AD`)
#if [ ! $classad ]; then # break and return error
#	echo "WantsStashCache classad not present"
#	return 1
#fi

module load xrootd/4.1.1
export PATH=$PATH:$(pwd)

debug=0
file=""
loc="."
source=""
recursive=0
if [ "$#" -eq 0 ]; then
    echo "$usage"
    exit
fi
## http://stackoverflow.com/a/5230306
## http://stackoverflow.com/a/7948533
if ! options=$(getopt -o :drhs:l: -l closest -- "$@"); then
    exit 1
fi
eval set -- "$options"
while [ $# -gt 0 ]; do
    case $1 in 
	-h)
	    echo "$usage"
	    exit
	    ;;
	-d)
	    debug=2
	    ;;
	-s)
	    source=$2
	    shift
	    ;;
	-r)
	    recursive=1
	    ;;
	-l)
	    loc=$2
	    shift
	    ;;
	--closest)
	    getClose
	    exit
	    ;;
	(--)
	    shift
	    break
	    ;;
	(-*)
	    echo "$0: error - unrecognized option $1" 1>&2
	    echo "$usage" >&2
	    exit 1
	    ;;
	(*)
	    break
	    ;;
    esac
	shift
done

#echo "Source: $source"
#echo "Location: $loc"

## find chirp
#which condor_chirp 
#res=$?
#if [ $res -ne 0 ]; then
#	if [ -s /usr/libexec/condor/condor_chirp ]; then
#		PATH=$PATH:/usr/libexec/condor
#	else
#		cd ../../
#		pd=$(find . | grep "condor_chirp")
#		if [ -z $pd ]; then
#			echo "condor_chirp not found" >&2
#		else
#			#echo "Trying non-usr option"
#			p1=$(echo $pd | cut -c 2-)
#			p2=$(echo $p1 | rev | cut -d'/' -f2- | rev)
#			cwd=$(pwd)
#			PATH=$PATH:$cwd/$p2
#		fi
#		cd -
#	fi
#fi

## set prefix to proper format
if [[ $OSG_SITE_NAME == CIT* ]]; then
    STASHPREFIX="root://phiphi.t2.ucsd.edu"
    myPrefix=$STASHPREFIX
elif [ ${#STASHPREFIX} -lt 3 ]; then
    myPrefix="root://data.ci-connect.net"
    echo "Empty prefix"
else
    lcs=$(echo "${STASHPREFIX: -1}")
    if [ $lcs == "/" ]; then
	myPrefix=$(echo $STASHPREFIX | rev | cut -c 2- | rev)
    else
	myPrefix=$STASHPREFIX
    fi
fi

## deal with sites without variable set
if [ ! -n "$OSG_SITE_NAME" ]; then
    OSG_SITE_NAME="UNKNOWN"
fi

## set xrdargs
if [ $debug -eq 2 ]; then
    xrdargs="-d 2 --nopbar"
else
    xrdargs="-s"
fi

failed=0
starts=()
names=()
sizes=()
times=()
sources=()
failoverfiles=()
failovertimes=()
failfiles=()
failtimes=()
failcodes=()

baseDir=$loc
prefix=""

files=($source)

for file in ${files[@]}; do
    ## determine whether the input source is a directory or not
    fisdir=$(xrdfs root://data.ci-connect.net stat $file | grep "IsDir" | wc -l)
    if [ $fisdir -eq 0 ]; then
	export prefix="/$(echo $source | rev | cut -d/ -f1- | rev)"
	doStashCpSingle $file update
    else
	lc=$(echo "${source: -1}")
	if [ "$lc" == "/" ]; then
	    export prefix="/$(echo $source | rev | cut -d/ -f1- | rev)"
	    echo "Prefix for slash case: $prefix"
	    doStashCpDirectory $file update
	else
	    dir=$(echo $source | rev | cut -d/ -f1 | rev)
	    export prefix="/$(echo $source | rev | cut -d/ -f2- | rev)/"
	    echo "Prefix for noslash case: $prefix"
	    mkdir $loc/$dir
	    baseDir=$loc/$dir
	    echo "Base dir: $baseDir"
	    doStashCpDirectory $file update
	fi
    fi
done

## Setting classads as appropriate
#condor_chirp set_job_attr_delayed Chirp_StashCp_Dest $OSG_SITE_NAME
#condor_chirp set_job_attr_delayed Chirp_StashCp_Used true
##http://stackoverflow.com/a/2317171
#startString=$(printf ",%s" "${starts[@]}")
#condor_chirp set_job_attr_delayed Chirp_StashCp_DLStart \"${startString:1:1023}\"
#nameString=$(printf ",%s" "${names[@]}")
#condor_chirp set_job_attr_delayed Chirp_StashCp_FileName \"${nameString:1:1023}\"
#sizeString=$(printf ",%s" "${sizes[@]}")
#condor_chirp set_job_attr_delayed Chirp_StashCp_FileSize \"${sizeString:1:1023}\"
#timeString=$(printf ",%s" "${times[@]}")
#condor_chirp set_job_attr_delayed Chirp_StashCp_DlTimeMs \"${timeString:1:1023}\"
#sourceString=$(printf ",%s" "${sources[@]}")
#condor_chirp set_job_attr_delayed Chirp_StashCp_Source \"${sourceString:1:1023}\"
#if [ $failoverfiles ]; then
#	fofString=$(printf ",%s" "${failoverfiles[@]}")
#	condor_chirp set_job_attr_delayed Chirp_StashCp_FailoverFiles \"${fofString:1:1023}\"
#	fotString=$(printf ",%s" "${failovertimes[@]}")
#	condor_chirp set_job_attr_delayed Chirp_StashCp_FailoverTimes \"${fotString:1:1023}\"
#fi
#if [ $failfiles ]; then
#	ffString=$(printf ",%s" "${failfiles[@]}")
#	condor_chirp set_job_attr_delayed Chirp_StashCp_FailFiles \"${ffString:1:1023}\"
#	ftString=$(printf ",%s" "${failtimes[@]}")
#	condor_chirp set_job_attr_delayed Chirp_StashCp_FailTimes \"${ftString:1:1023}\"
#	fcString=$(printf ",%s" "${failcodes[@]}")
#	condor_chirp set_job_attr_delayed Chirp_StashCp_FailCodes \"${fcString:1:1023}\"
#fi

#Note: if any one file transfer fails, then stashcp fails
if [ $failed -ne 0 ]; then
    exit 4
else	
    exit 0
fi
