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

import logging
from urlparse import urlparse



TIMEOUT = 300
DIFF = TIMEOUT * 10


def doStashCpSingle(sourceFile, destination, cache, debug=False):

    logging.debug("Checking size of file.")
    xrdfs = subprocess.Popen(["xrdfs", "root://stash.osgconnect.net", "stat", sourceFile], stdout=subprocess.PIPE).communicate()[0]
    fileSize=int(re.findall(r"Size:   \d+",xrdfs)[0].split(":   ")[1])
    logging.debug("Size of the file %s is %i" % (sourceFile, fileSize))
    #cache=get_best_stashcache()
    logging.debug("Using Cache %s" % cache)

    # Calculate the starting time
    date = datetime.datetime.now()
    start1=int(time.mktime(date.timetuple()))*1000
    xrd_exit=timed_transfer(timeout=TIMEOUT,filename=sourceFile,diff=DIFF,expSize=fileSize,debug=debug,cache=cache,destination=destination)
    
    date = datetime.datetime.now()
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
        logging.debug("Transfer success using %s" % cache)
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
            logging.error("Error curling to ES")
    else: #copy again using same cache
        logging.warning("1st try failed on %s, trying again" % cache)
        date=datetime.datetime.now()
        start2=int(time.mktime(date.timetuple()))*1000
        xrd_exit=timed_transfer(timeout=TIMEOUT,filename=source,diff=DIFF,expSize=fileSize,debug=debug,cache=cache,destination=destination)
        date=datetime.datetime.now()
        end2=int(time.mktime(date.timetuple()))*1000
        dlSz=os.stat(filename).st_size
        if xrd_exit=='0': #worked second try
            logging.info("Transfer successful on second try")
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
                logging.error("Error curling to ES")
        else: #pull from origin
            logging.warning("2nd try failed on %s, pulling from origin" % cache)
            cache="root://stash.osgconnect.net"
            date=datetime.datetime.now()
            start3=int(time.mktime(date.timetuple()))*1000
            xrd_exit=timed_transfer(timeout=TIMEOUT,filename=source,diff=DIFF,expSize=fileSize,debug=debug,cache=cache,destination=destination)
            date=datetime.datetime.now()
            end3=int(time.mktime(date.timetuple()))*1000
            dlSz=os.stat(filename).st_size
            dltime=end3-start3
            if xrd_exit=='0':
                logging.info("Trunk Success")
                status = 'Trunk Sucess'
                tries=3
            else:
                logging.error("stashcp failed after 3 attempts")
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
                logging.error("Error curling to ES")


def dostashcpdirectory(sourceDir, destination, cache, debug=False):
    sourceItems = subprocess.Popen(["xrdfs", "root://stash.osgconnect.net", "ls", sourceDir], stdout=subprocess.PIPE).communicate()[0].split()
    for file in sourceItems:
        command2 = 'xrdfs root://stash.osgconnect.net stat '+ file + ' | grep "IsDir" | wc -l'
        isdir=subprocess.Popen([command2],stdout=subprocess.PIPE,shell=True).communicate()[0].split()[0]
        if isdir!='0':
            dostashcpdirectory(file, destination, cache, debug)
        else:
            doStashCpSingle(file,destination, cache, debug)


def es_send(payload):
    data = payload
    data=json.dumps(data)
    try:
        url = "http://uct2-collectd.mwt2.org:9951"
        req = urllib2.Request(url, data=data, headers={'Content-Type': 'application/json'})
        f = urllib2.urlopen(req)
        response = f.read()
        f.close()
    except:
        print "Error posting to ES"


def timed_transfer(filename,expSize,cache,destination,timeout=TIMEOUT,diff=DIFF,debug=False):
    
    # To set environment varibles if they don't already exist (set by user)
    def set_if_none(var, value):
        if var not in os.environ:
            os.environ[var] = str(value)
    
    
    # All these values can be found on the xrdcp man page
    set_if_none("XRD_REQUESTTIMEOUT", 30)   # How long to wait for a read request (s)
    set_if_none("XRD_CPCHUNKSIZE", 8388608) # Size of each read request (8MB)
    set_if_none("XRD_TIMEOUTRESOLUTION", 5) # How often to check the timeouts
    set_if_none("XRD_CONNECTIONWINDOW", 30) # How long to wait for the initial TCP connection
    set_if_none("XRD_CONNECTIONRETRY", 2)   # How many time should we retry the TCP connection
    set_if_none("XRD_STREAMTIMEOUT", 30)    # How long to wait for TCP activity
    
    filepath=cache+":1094//"+ filename
    if debug:
        command="xrdcp -d 2 --nopbar -f " + filepath + " " + destination
    else:
        command="xrdcp -s -f " + filepath + " " + destination
        
    filename="./"+filename.split("/")[-1]
    if os.path.isfile(filename):
        os.remove(filename)
    xrdcp=subprocess.Popen([command ],shell=True,stdout=subprocess.PIPE)
    
    streamdata=xrdcp.communicate()[0]
    xrd_exit=xrdcp.returncode

    return str(xrd_exit)


def get_best_stashcache():
    
    # First, check for caches.json file in this file's directory:
    dir_path = os.path.dirname(os.path.realpath(__file__))
    cache_file = os.path.join(dir_path, 'caches.json')
    if not os.path.isfile(cache_file):
        logging.error("Unable to find caches.json in %s" % dir_path)
        return None
    
    # Get all the caches from the json file
    f = open(cache_file, 'r')
    caches_list = json.loads(f.read())
    f.close()
    
    # Get the possible GeoIP sites
    
    # Format the caches for the CVMFS query
    caches_string = ""
    for cache in caches_list:
        if cache['status'] == 0:
            continue
        parsed_url = urlparse(cache['name'])
        caches_string = "%s,%s" % (caches_string, parsed_url.hostname)
    # Remove the first comma
    caches_string = caches_string[1:]
    
    # Query the GeoIP sites:
    final_url = "http://hcc-cvmfs.unl.edu:8000/cvmfs/config-osg.opensciencegrid.org/api/v1.0/geo/@proxy@/%s" % caches_string
    logging.debug("Querying for closest cache: %s" % final_url)
    response = urllib2.urlopen("http://hcc-cvmfs.unl.edu:8000/cvmfs/config-osg.opensciencegrid.org/api/v1.0/geo/@proxy@/%s" % caches_string)
    
    # From the response, should respond with something like:
    # 3,1,2
    ordered_list = response.read().strip().split(",")
    logging.debug("Got response %s" % str(ordered_list))
    minsite = caches_list[int(ordered_list[0])-1]['name']
    
    logging.debug("Returning closest cache: %s" % minsite)
    return minsite


def main():
    parser = optparse.OptionParser()
    parser.add_option('-d', '--debug', dest='debug', action='store_true', help='debug')
    parser.add_option('-r', dest='recursive', action='store_true', help='recursively copy')
    parser.add_option('--closest', action='store_true')
    parser.add_option('-c', '--cache', dest='cache', help="Cache to use")
    args,opts=parser.parse_args()

    logger = logging.getLogger()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARNING)

    if not args.closest:
        try:
            source=opts[0]
            destination=opts[1]
        except:
            parser.error('Source and Destination must be last two arguments')
    else:
        print get_best_stashcache()
        sys.exit()

    # Check for manually entered cache to use
    if args.cache and len(args.cache) > 0:
        cache = args.cache
    else:
        cache = get_best_stashcache()
    
    if not args.recursive:
        doStashCpSingle(sourceFile=source, destination=destination, cache=cache, debug=args.debug)
    else:
        dostashcpdirectory(sourceDir = source, destination = destination, cache=cache, debug=args.debug)


if __name__ == "__main__":
    main()
