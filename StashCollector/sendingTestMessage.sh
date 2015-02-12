# order of things to be sent:
# filename
# filesize [bytes]
# time it took to copy [seconds] (float)
# computing site
# stashCache address used
#

fname='asdf/asdf/asdf/asdf/asdf/'
fsize=123123123
tcopy=123.1234
cs=MWT2
sc="stashCache1.org"

hn=$(hostname)
timestamp=$(date +%s)
header='[{ "headers" : {"timestamp" : "'${timestamp}'", "host" : "'${hn}'" },'
body='"body" : "'${timestamp}','${fname}','${fsize}','${tcopy}','${cs}','${sc}'" }]'

curl -X POST -H 'Content-Type: application/json; charset=UTF-8' -d $header$body http://hadoop-dev.mwt2.org:80/