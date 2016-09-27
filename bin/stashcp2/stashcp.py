import optparse
import sys
import subprocess
import datetime
import time
import re
import os
import json
import multiprocessing
import urllib2
import threading
import math
import socket


parser = optparse.OptionParser()
parser.add_option('--debug', dest='debug', action='store_true', help='debug')
parser.add_option('-r', dest='recursive', action='store_true', help='recursively copy')
parser.add_option('--closest', action='store_true')
args,opts=parser.parse_args()

if not args.closest:
    try:
        source=opts[0]
        destination=opts[1]
    except:
        parser.error('Source and Destination must be last two arguments')
else:
    print get_best_stashcache()
    sys.exit()

if not args.debug:
    xrdargs=0
else:
    xrdargs=1

TIMEOUT = 300
DIFF = TIMEOUT * 10


def doStashCpSingle(sourceFile, destination=destination):
    xrdfs = subprocess.Popen(["xrdfs", "root://stash.osgconnect.net", "stat", sourceFile], stdout=subprocess.PIPE).communicate()[0]
    fileSize=int(re.findall(r"Size:   \d+",xrdfs)[0].split(":   ")[1])
    cache=get_best_stashcache()
    date=datetime.datetime.now()
    start1=int(time.mktime(date.timetuple()))*1000
    xrd_exit=timed_transfer(timeout=TIMEOUT,filename=sourceFile,diff=DIFF,expSize=fileSize,xrdebug=xrdargs,cache=cache,destination=destination)
    date=datetime.datetime.now()
    end1=int(time.mktime(date.timetuple()))*1000
    filename=destination+'/'+sourceFile.split('/')[-1]
    dlSz=os.stat(filename).st_size
    destSpace=1
    try:
        sitename=os.environ['OSG_SITE_NAME']
    except:
        sitename="siteNotFound"
    xrdcp_version=subprocess.Popen(['echo $(xrdcp -V 2>&1)'],stdout=subprocess.PIPE,shell=True).communicate()[0][:-1]
    start2=0
    start3=0
    end2=0
    xrdexit2=-1
    xrdexit3=-1
    if xrd_exit=='0': #worked first try
        dltime=end1-start1
        status = 'Success'
        tries=1
        payload={}
        payload['timestamp']=end1
        payload['host']=cache
        payload['filename']=sourceFile
        payload['filesize']=fileSize
        payload['download_size']=dlSz
        payload['download_time']=dltime
        payload['sitename']=sitename
        payload['destination_space']=destSpace
        payload['status']=status
        payload['xrdexit1']=xrd_exit
        payload['xrdexit2']=xrdexit2
        payload['xrdexit3']=xrdexit3
        payload['tries']=tries
        payload['xrdcp_version']=xrdcp_version
        payload['start1']=start1
        payload['end1']=end1
        payload['start2']=start2
        payload['end2']=end2
        payload['start3']=start3
        payload['cache']=cache
        try:
            p = multiprocessing.Process(target=es_send, name="es_send", args=(payload,))
            p.start()
            time.sleep(5)
            p.terminate()
        except:
            print "Error curling to ES"
    else: #copy again using same cache
        print "1st try failed on %s, trying again" % cache
        date=datetime.datetime.now()
        start2=int(time.mktime(date.timetuple()))*1000
        xrd_exit=timed_transfer(timeout=TIMEOUT,filename=source,diff=DIFF,expSize=fileSize,xrdebug=xrdargs,cache=cache,destination=destination)
        date=datetime.datetime.now()
        end2=int(time.mktime(date.timetuple()))*1000
        dlSz=os.stat(filename).st_size
        if xrd_exit=='0': #worked second try
            status = 'Success'
            tries=2
            dltime=end2-start2
            payload={}
            payload['timestamp']=end1
            payload['host']=cache
            payload['filename']=sourceFile
            payload['filesize']=fileSize
            payload['download_size']=dlSz
            payload['download_time']=dltime
            payload['sitename']=sitename
            payload['destination_space']=destSpace
            payload['status']=status
            payload['xrdexit1']=xrd_exit
            payload['xrdexit2']=xrdexit2
            payload['xrdexit3']=xrdexit3
            payload['tries']=tries
            payload['xrdcp_version']=xrdcp_version
            payload['start1']=start1
            payload['end1']=end1
            payload['start2']=start2
            payload['end2']=end2
            payload['start3']=start3
            payload['cache']=cache
            try:
                p = multiprocessing.Process(target=es_send, name="es_send", args=(payload,))
                p.start()
                time.sleep(5)
                p.terminate()
            except:
                print "Error curling to ES"
        else: #pull from origin
            print "2nd try failed on %s, pulling from origin" % cache
            cache="root://stash.osgconnect.net"
            date=datetime.datetime.now()
            start3=int(time.mktime(date.timetuple()))*1000
            xrd_exit=timed_transfer(timeout=TIMEOUT,filename=source,diff=DIFF,expSize=fileSize,xrdebug=xrdargs,cache=cache,destination=destination)
            date=datetime.datetime.now()
            end3=int(time.mktime(date.timetuple()))*1000
            dlSz=os.stat(filename).st_size
            dltime=end3-start3
            if xrd_exit=='0':
                print "Trunk Success"
                status = 'Trunk Sucess'
                tries=3
            else:
                print "stashcp failed"
                status = 'Timeout'
                tries = 3
            payload={}
            payload['timestamp']=end1
            payload['host']=cache
            payload['filename']=sourceFile
            payload['filesize']=fileSize
            payload['download_size']=dlSz
            payload['download_time']=dltime
            payload['sitename']=sitename
            payload['destination_space']=destSpace
            payload['status']=status
            payload['xrdexit1']=xrd_exit
            payload['xrdexit2']=xrdexit2
            payload['xrdexit3']=xrdexit3
            payload['tries']=tries
            payload['xrdcp_version']=xrdcp_version
            payload['start1']=start1
            payload['end1']=end1
            payload['start2']=start2
            payload['end2']=end2
            payload['start3']=start3
            payload['cache']=cache
            try:
                p = multiprocessing.Process(target=es_send, name="es_send", args=(payload,))
                p.start()
                time.sleep(5)
                p.terminate()
            except:
                print "Error curling to ES"


def dostashcpdirectory(sourceDir=source, destination=destination):
    sourceItems = subprocess.Popen(["xrdfs", "root://stash.osgconnect.net", "ls", sourceDir], stdout=subprocess.PIPE).communicate()[0].split()
    for file in sourceItems:
        print "file is: ",file
        command2 = 'xrdfs root://stash.osgconnect.net stat '+ file + ' | grep "IsDir" | wc -l'
        print command2
        isdir=subprocess.Popen([command2],stdout=subprocess.PIPE,shell=True).communicate()[0].split()[0]
        print type(isdir)
        if isdir!='0':
            print 'Caching directory'
            dostashcpdirectory(sourceDir=file)
        else:
            print 'Caching file ', 
            doStashCpSingle(sourceFile=file,destination=destination)


def es_send(payload):
    data = payload
    print data
    data=json.dumps(data)
    try:
        url = "http://uct2-collectd.mwt2.org:9951"
        req = urllib2.Request(url, data=data, headers={'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
    except:
        print "Error posting to ES"


def timed_transfer(filename,expSize,cache,destination,timeout=TIMEOUT,diff=DIFF,xrdebug=xrdargs):
    def watchdog(xrdcp,filename,expSize,diff,timeout):
        prevSize=0
        newSize=0
        filename="./"+filename.split("/")[-1]
        while (newSize<expSize):
            time.sleep(timeout)
            if os.path.isfile(filename):
                newSize=os.stat(filename).st_size
                nextSize=prevSize+diff
                if nextSize<expSize:
                    wantSize=nextSize
                else:
                    wantSize=expSize
                if newSize < wantSize:
                    xrdcp.kill()
                    newSize=expSize
                else:
                    prevSize=os.stat(filename).st_size
            else:
                xrdcp.kill()
                newSize=expSize

    filepath=cache+":1094//"+ filename
    if xrdebug==1:
        command="xrdcp -d 2 --nopbar -f " + filepath + " " + destination
    else:
        command="xrdcp -s -f " + filepath + " " + destination
    print command
    filename="./"+filename.split("/")[-1]
    if os.path.isfile(filename):
        os.remove(filename)
    xrdcp=subprocess.Popen([command ],shell=True,stdout=subprocess.PIPE)
    time.sleep(1)
    watchdog=multiprocessing.Process(target=watchdog,args=[xrdcp,filename,expSize,DIFF,TIMEOUT,])
    watchdog.start()
    streamdata=xrdcp.communicate()[0]
    xrd_exit=xrdcp.returncode
    watchdog.terminate()
    return str(xrd_exit)


def get_best_stashcache():
    debug=0
    if debug: print "# getting client coordinates..."
    worked=0
    try:
        req = urllib2.Request("http://geoip.mwt2.org:4288/json/", None)
        opener = urllib2.build_opener()
        f = opener.open(req,timeout=5)
        res=json.load(f)
        lon=res['longitude']
        lat=res['latitude']
        ip=res['ip']
        worked=1
    except:
        if debug:
            print "# Can't determine client coordinates using geoip.mwt2.org ", sys.exc_info()[0]

    if not worked:
        try:
            req = urllib2.Request("http://freegeoip.net/json/", None)
            opener = urllib2.build_opener()
            f = opener.open(req,timeout=5)
            res=json.load(f)
            lon=res['longitude']
            lat=res['latitude']
        except:
            print "# Can't determine client coordinates using freegeoip.net ", sys.exc_info()[0]
            sys.exit(1)

    n = datetime.datetime.utcnow()
    one_day = datetime.timedelta(days=1)
    n = n + one_day
    t = n + one_day
    today = datetime.datetime.date(n)
    tomorrow = datetime.datetime.date(t)

    class site:
        def __init__(self,na):
            self.name=na
            self.status=0
            self.longitude=0
            self.latitude=0
        def coo(self, lo, la):
            self.longitude=lo
            self.latitude=la
        def prn(self):
            print "#", self.name, "\tlong:",self.longitude,"\t lat:",self.latitude,"\tstatus:",self.status

    Sites=dict()
    worked=0
    try:
        url="https://raw.githubusercontent.com/opensciencegrid/StashCache/master/bin/caches.json"
        if debug: print "# getting StashCache endpoints coordinates and statuses from GitHub ..."
        response=urllib2.Request(url,None)
        opener = urllib2.build_opener()
        f = opener.open(response, timeout=40)
        data = json.load(f)
        for si in data:
            n=si['name']
            s=site(n)
            s.status=si['status']
            s.coo(si['longitude'],si['latitude'])
            #s.prn()
            Sites[n]=s
        worked=1
    except urllib2.HTTPError:
        if debug: print "# Can't connect to GitHub."
    except:
        if debug: print "# Can't connect to GitHub.", sys.exc_info()[0]

    # calculating distances to "green" endpoints
    mindist=40000
    minsite=''

    for s in Sites:
        if not Sites[s].status==1: continue
        dlon = math.radians(lon - Sites[s].longitude)
        dlat = math.radians(lat - Sites[s].latitude)
        a = pow(math.sin(dlat/2),2) + math.cos(math.radians(Sites[s].latitude)) * math.cos(math.radians(lat)) * pow(math.sin(dlon/2),2)
        c = 2 * math.atan2( math.sqrt(a), math.sqrt(1-a) )
        d = 6373 * c # 6373 is the radius of the Earth in km
        if debug>1:
            Sites[s].prn()
            print "#",d,"km"
        if d<mindist:
            mindist=d
            minsite=Sites[s].name

    if debug:
        print "#",minsite, mindist,"km"

    return minsite[:-1]


### EXECUTE ###
if not args.recursive:
    doStashCpSingle(sourceFile=source)
else:
    print "doing directory"
    dostashcpdirectory()