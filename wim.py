#!/usr/bin/python

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2.1
# of the License, or (at your option) any later version.

# wim.py - gps / bluetooth listener communicates via UDP packets
# designed to interface with pure data
#  (C) 2012 Tim Redfern
# 
# developed exclusively for circumstance - Tomorrow the ground forgets you were here
# 
# http://productofcircumstance.com/portfoliocpt/tomorrow-the-ground-forgets-you-were-here/
#
# Bugs, issues, suggestions: tim@eclectronics.org

# wim.py requires an xml config file - see example
# this details 3 types of triggers which are translated into UDP packets
# trigger types: gps scalar, gps index, bluetooth

# GPS TRIGGERS require a serial gps device sending NMEA sentences
# the gps device address is in the xml config file

# gps scalar and index triggers reference geo-located bitmap overlays
# index triggers send a pre-deteremined message when an area is entered
# scalar triggers send a continually varying signal by interpolating greyscale values

# BLUETOOTH TRIGGERS are similar to index triggers but send a message when a
# known bluetooth device is encountered

import signal,sys

def signal_handler(signal, frame):
        insock.close()
        print "wim: interrupted"
        sys.exit(0)
        
signal.signal(signal.SIGINT, signal_handler)

from latLng import *
from layers import *
from xml2obj import *
from logger import *

if len(sys.argv)<2:
	print "usage: wim.py configfile [-D debug] [-L log] [-T test]"
	sys.exit(0)

Debug=False
test=False
Log=False
if len(sys.argv)>2:
	if sys.argv[2]=="-D" or sys.argv[2]=="-d":
		Debug=True
		print "wim: DEBUG mode"
if len(sys.argv)>3:
	if sys.argv[3]=="-L" or sys.argv[3]=="-l":
		Log=True
		print "wim: gps LOG mode"
if len(sys.argv)>4:
	if sys.argv[4]=="-T" or sys.argv[4]=="-t":
		test=True
		print "wim: gps TEST mode"
	
doc=xml2obj(open(sys.argv[1]))
gpslayers=[]

#catch invalid xml
try:
	for i in doc.gps.index:
		#catch invalid xml
		try:
			g=indexlayer(i.file,i.ll1,i.ll2)
			for t in i.trigger:
				g.triggers.append(trigger(int(t.id),t.command,t.param))
			gpslayers.append(g)
		except:
			print "wim: error parsing xml index entry"
except:
	print "wim: no index layers found"

#catch invalid xml
try:		
	for i in doc.gps.scale:
		#catch invalid xml
		try:
			g=scalelayer(i.file,i.ll1,i.ll2)
			g.setcommand(i.command)
			gpslayers.append(g)
		except:
			print "wim: error parsing xml index entry"
except:
	print "wim: no scale layers found"
		
from gpspoller import *
gpsp=""

try:
	gpsp = GpsPoller(doc.gpsdevice,test)
	gpsp.start()
except:
	print "wim: gps device not found"
	
from btscan import *

scan=scanner("127.0.0.1",5401,False)

try:
	for t in doc.bt.trigger:
		scan.d.dm.triggers[t.id]=(t.command,t.param)
except:
	print "wim: no bluetooth triggers found"
	
if len(scan.d.dm.triggers) >0:
	scan.start()
		
logger=None

if Log:
	logger=log("gpslog")

import socket

GUI_IP="0.0.0.0"
GUI_PORT=5400
insock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) 
insock.bind( (GUI_IP,GUI_PORT) )
insock.settimeout(0.01) #non blocking, this sets the frame rate of checking
PD_IP="127.0.0.1"
PD_PORT=5401
outsock = socket.socket( socket.AF_INET,socket.SOCK_DGRAM )

pos=latLng()
posChanged=False

gpsfix=False

while True:
	data=""
	try:
		data, addr = insock.recvfrom(128)
		if Debug:
			print "wim: received:",data
		pos.parse(data)
		posChanged=True
	except:
		nothing=None
	
	if gpsp!="": #gps available
		if gpsp.fix>1:
				gpsfix=True
				outsock.sendto( "gps status 1\n", (PD_IP, PD_PORT) )
		if gpsp.fix<2:
				gpsfix=False
				outsock.sendto( "gps status 0\n", (PD_IP, PD_PORT) )
		check=gpsp.check()
		if check!=False:
			if Debug:
				print "wim: received from gps",check[0],check[1]
			outsock.sendto("gps data "+str(check[0])+" "+str(check[1])+"\n",(PD_IP, PD_PORT) )
			pos=latLng(check[0],check[1])
			posChanged=True
	if Log:
		logger.log(str(pos.lng)+","+str(pos.lat))
	if posChanged:
		posChanged=False
		for layer in gpslayers:
			r=layer.checkcoord(pos) #returns a message or None
			if r!=None:
				if Debug:
					print "wim: sending:",str(r[0]),str(r[1])
				#pd needs \n at end of message
				outsock.sendto( str(r[0])+' '+str(r[1])+'\n', (PD_IP, PD_PORT) )
	time.sleep(0.1)
				
