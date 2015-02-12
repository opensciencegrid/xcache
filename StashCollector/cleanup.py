#!/usr/bin/python
from datetime import datetime
import xml.etree.ElementTree as ET

@outputSchema("CLEANED:tuple(SRC:chararray,SITE:chararray,TOS:long,TOD:long,TOE:long,IN:long,OUT:long)")
def XMLtoNTUP(xmlInput):
    ntup = []
    root = ET.fromstring(xmlInput)
    SRC=root.attrib['src']   # server name
    SITE=root.attrib['site'] # sitename as set by the endpoint
    TOS=root.attrib['tos']   # time the service started
    TOD=root.attrib['tod']   # time the statistics gathering started
    
    for child in root:
        print child.tag, child.attrib
        if child.attrib['id']=='link': 
            for c in child:
                if c.tag=='in': IN=long(c.text)
                if c.tag=='out': OUT=long(c.text)
                
        if child.attrib['id']=='sgen':
            for c in child:
                if c.tag=='toe': TOE=long(c.text)
    return (SRC,SITE,TOS,TOD,TOE,IN,OUT)
