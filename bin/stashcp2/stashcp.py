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

parser = optparse.OptionParser()
parser.add_option('--debug', dest='debug', action='store_true', help='debug')
parser.add_option('-r', dest='recursive', action='store_true', help='recursively copy')
parser.add_option('--closest', action='store_true')
args,opts=parser.parse_args()

def find_closest():
    closest=subprocess.Popen(['./get_best_stashcache.py', '0'], stdout=subprocess.PIPE)
    cache=closest.communicate()[0].split()[0]
    return cache

if not args.closest:
    try:
        source=opts[0]
        destination=opts[1]
    except:
        parser.error('Source and Destination must be last two arguments')
else:
    print find_closest()
    sys.exit()

#Set debug flag for xrdcp call
if not args.debug:
    xrdargs=0
else:
    xrdargs=1

#set to 5 minutes
TIMEOUT = 300
DIFF = TIMEOUT * 10

#For single file, try xrdcp on optimal cache 2 times, then xrdcp on the origin server
def doStashCpSingle(sourceFile=source, destination=destination):
    xrdfs = subprocess.Popen(["xrdfs", "root://stash.osgconnect.net", "stat", sourceFile], stdout=subprocess.PIPE).communicate()[0]
    fileSize=int(re.findall(r"Size:   \d+",xrdfs)[0].split(":   ")[1])
    cache=find_closest()
    command = "python ./timeout.py -t "+str(TIMEOUT)+ " -f "+sourceFile + " -d "+str(DIFF)+" -s "+str(fileSize)+" -x "+str(xrdargs)+" -c "+cache+" -z "+destination
    date=datetime.datetime.now()
    start1=int(time.mktime(date.timetuple()))*1000
    copy=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
    xrd_exit=copy.communicate()[0].split()[-1]
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
    if xrd_exit=='0': #Worked first try
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
    else: #Copy again using same cache
        print "1st try failed on %s, trying again" % cache
        date=datetime.datetime.now()
        start2=int(time.mktime(date.timetuple()))*1000
        copy=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
        xrd_exit=copy.communicate()[0].split()[-1]
        date=datetime.datetime.now()
        end2=int(time.mktime(date.timetuple()))*1000
        dlSz=os.stat(filename).st_size
        if xrd_exit=='0': #Worked second try
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
        else: #Pull from origin
            print "2nd try failed on %s, pulling from origin" % cache
            cache="root://stash.osgconnect.net"
            command = "python ./timeout.py -t "+str(TIMEOUT)+ " -f "+sourceFile + " -d "+str(DIFF)+" -s "+str(fileSize)+" -x "+str(xrdargs)+" -c "+cache+" -z "+destination
            date=datetime.datetime.now()
            start3=int(time.mktime(date.timetuple()))*1000
            copy=subprocess.Popen([command],stdout=subprocess.PIPE,shell=True)
            xrd_exit=copy.communicate()[0].split()[-1]
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

#Recursive directory copying
def dostashcpdirectory(sourceDir=source, destination=destination):
    sourceItems = subprocess.Popen(["xrdfs", "root://stash.osgconnect.net", "ls", sourceDir], stdout=subprocess.PIPE).communicate()[0].split()
    for file in sourceItems:
        command2 = 'xrdfs root://stash.osgconnect.net stat '+ file + ' | grep "IsDir" | wc -l'
        isdir=subprocess.Popen([command2],stdout=subprocess.PIPE,shell=True).communicate()[0].split()[0]
        if isdir!='0':
            print 'Caching directory'
            dostashcpdirectory(sourceDir=file)
        else:
            print 'Caching file'
            doStashCpSingle(sourceFile=file)

#Send to ES. Will be indexed under "stashcp-*" where "*" is the month
def es_send(payload):
    data=json.dumps(payload)
    try:
        url = "http://uct2-collectd.mwt2.org:9951"
        req = urllib2.Request(url, data=data, headers={'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
    except:
        print "Error posting to ES"


if not args.recursive:
    doStashCpSingle()
else:
    dostashcpdirectory()