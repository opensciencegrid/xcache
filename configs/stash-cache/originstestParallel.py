#!/usr/bin/python3
import subprocess
import os
import traceback
from time import sleep, perf_counter
from threading import Thread
from subprocess import PIPE
import time
from XRootD import client
import numpy as np
from influxdb import InfluxDBClient
from datetime import datetime
from pythonping import ping
from XRootD.client.flags import DirListFlags
from maddash import MaddashClient
import socket
import json
from transfer import TransferTest


file_lorigins = open("/opt/OSDFvis/origins.txt", "r")
lorigins = lines = file_lorigins.read().splitlines()
db_pass = open("/opt/pass", "r")

URL="graph.t2.ucsd.edu"
password=db_pass.readline().strip()
user="cachemon"
db="cachemon_db"

with open('a2a') as g:
    maddash_conf = json.load(g)

key = 'CACHE_FQDN'
cache = 'NONONONO'
for line in open("/etc/xrootd-environment", 'r'):
    if(line.find('CACHE_FQDN') != -1):
        t1 = line.split(" ");
        cache = t1[1].split("=")[1]

if(cache == 'NONONONO'):
    for line in open("/etc/xrootd-environment", 'r'):
        if(line.find('ORIGIN_FQDN') != -1):
            t1 = line.split(" ");
            cache = t1[1].split("=")[1]


clientflux = InfluxDBClient(URL, 8086, user, password, db)

def xrdcpy(origin,n,timeout):
        process = client.CopyProcess()

        sf = origin.split(' ')
        server = sf[0]
        filet = "/"+sf[1]
        print(server)
        print(filet)
        myclient = client.FileSystem(server)
        seconds = time.time()
        status = myclient.copy(server+filet,'/tmp/t'+str(n), force=True)
        el = time.time() - seconds;
        drt[n] = el
        print(status)

def checkSize(ftt,timeout):
     seconds = time.time()
     run = True
     while(run == True):
             try:
                    path = tmppath+"t"+str(ftt);
                    end = time.time()
                    el = end - seconds;
                    if(os.path.exists(path)):
                           file_size = os.path.getsize(path)
                           dr[ftt] = file_size
                    sleep(0.1)
                    if(el > timeout):
                           run = False
             except Exception as e:
                    print(e)
                    traceback.print_exc()


tests = 5
threads = []
threadsTimer = []
dr = np.empty(tests)
drt = np.empty(tests)
timeout = 10;
tmppath = "/tmp/"



for origin in lorigins:
        try:
                oradd = origin.split(" ")[0]
                cache = cache.strip()
                try:
                    hosto = origin.split(" ")[0]
                    hosto = hosto.split("//")[1]
                    hosto = hosto.split(":")[0]
                    media = 0.0;
                    dataping = ping(hosto, count=10)
                    for d in dataping:
                        media = media + d.time_elapsed

                    json_body = [
                        {
                            "measurement": "heatmaplt",
                            "tags": {
                                "origin": oradd+"|"+cache
                            },
                            "time": datetime.utcnow().isoformat() + "Z",
                            "fields": {
                                "value": float(media)
                            }
                        },
                    ]
                    clientflux.write_points(json_body)

                except Exception as e:
                                print(e)
                                traceback.print_exc()

                for n in range(0, tests):
                       if(os.path.exists(tmppath+"t"+str(n))):
                              os.remove(tmppath+"/t"+str(n))
                       t = Thread(target=xrdcpy, args=(origin,n,2))
                       threads.append(t)
                       t.start()
                       t = Thread(target=checkSize, args=(n,timeout))
                       threadsTimer.append(t)
                       t.start()

                for x in threadsTimer:
                       x.join()
                print("join timer")
                for x in threads:
                       x.join()
                print("join copy")

                medias = 0.0
                ct = 0
                for n in dr:
                       print(n)
                       print(drt[ct])
                       if(drt[ct] < timeout):
                             v = n / drt[ct];
                             print("aa")
                       else:
                             v = n / timeout;
                             print("bb")
                       medias = medias + v;
                       ct = ct + 1

                media = medias / len(dr)


                print("MEDIA___________"+str(medias))

                json_body = [
                    {
                        "measurement": "heatmappar",
                        "tags": {
                            "origin": oradd+"|"+cache
                        },
                        "time": datetime.utcnow().isoformat() + "Z",
                        "fields": {
                            "value": float(media)
                        }
                    },
                ]
                print("----------------------"+hosto)
                print(hosto)
                IPAddrorigin=socket.gethostbyname(hosto)
                IPAddrdest=socket.gethostbyname(cache)
                clientflux.write_points(json_body)
                maddash_client = MaddashClient(maddash_conf)
                t = TransferTest(origin,IPAddrdest,hosto,IPAddrorigin,'xrootd',1094,1)
                measure = [];
                measure.insert(0,0)
                measure[0] = media;
                maddash_client.post(t, measure)
                for n in range(0, tests):
                       if(os.path.exists(tmppath+"t"+str(n))):
                              os.remove(tmppath+"t"+str(n))



        except Exception as e:
                print(e)
                traceback.print_exc()                                                                                                                              
