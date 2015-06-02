#!/bin/bash
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
	timeout="$1"
	file="$2"
	diff="$3"
	expSize="$4"
	(( i = timeout ))
	prevSize=0
	while (( i > 0 ))
	do
		if [ -e $file ]; then
			newSize=$(du -b $file | cut -f1)
			nextSize=$((prevSize+diff))
			wantSize=$((nextSize<expSize?nextSize:expSize))
			echo -e "$prevSize\t$newSize\t$nextSize\t$wantSize" >> sizes.track.txt
			if [ $newSize -lt $((wantSize)) ]; then
				kill -0 $$ || exit 0
				sleep 1
				(( i -= 1 ))
			else
				prevSize=$(du -b $file | cut -f1)
				(( i = timeout ))
			fi
		fi
	done
	
	echo "killing process after timeout of $timeout seconds"
	kill $$
}


start_watchdog "$timeout" "$file" "$diff" "$expSize" 2>/dev/null &
exec "$@"
return $?

#http://fahdshariff.blogspot.com/2013/08/executing-shell-command-with-timeout.html
