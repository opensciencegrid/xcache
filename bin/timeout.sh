#!/bin/bash
while getopts "t:" opt; do
  case "$opt" in
      t) timeout=$OPTARG ;;
  esac
done
shift $((OPTIND-1))
 
start_watchdog(){
  timeout="$1"
  (( i = timeout ))
  while (( i > 0 ))
  do
    kill -0 $$ || exit 0
    sleep 1
    (( i -= 1 ))
  done
 
  echo "killing process after timeout of $timeout seconds"
  kill $$
}
 
start_watchdog "$timeout" 2>/dev/null &
exec "$@"