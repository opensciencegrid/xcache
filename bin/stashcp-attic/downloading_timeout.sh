while getopts "t:f:d:s:" opt; do
  case "$opt" in
      t) timeout=$OPTARG ;;
      f) file=$OPTARG ;;
      d) diff=$OPTARG ;;
      s) expSize=$OPTARG ;;
  esac
done
shift $((OPTIND-1))


start_watchdog(){
    timeout=$1
    file=$2
    diff=$3
    expSize=$4
    xrdpid=$5
    prevSize=0
    while (( newSize<expSize ))
    do 
        sleep $timeout #check status after every x seconds
        if [ -e $file ]; then
            newSize=$(du -b $file | cut -f1)
            nextSize=$((prevSize+diff))
            wantSize=$((nextSize<expSize?nextSize:expSize))
            if [ $newSize -lt $wantSize ]; then #if time out
                kill -9 $xrdpid 2>/dev/null
            else #if file increases accordingly
                prevSize=$(du -b $file | cut -f1)
            fi
        else
            kill -9 $xrdpid 2>/dev/null
        fi
    done   
}

#Execute xrdcp
"$@" &
xrdpid=$!

start_watchdog "$timeout" "$file" "$diff" "$expSize" "$xrdpid" &
watchdog_pid=$!

wait $xrdpid
xrd_exit=$?

# If xrdcp command exits, kill the watchdog and exit using xrdcp's exit code
kill $watchdog_pid 2>/dev/null
exit $xrd_exit

## Based on: http://fahdshariff.blogspot.com/2013/08/executing-shell-command-with-timeout.html
