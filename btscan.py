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


import bluetooth
import select,  socket, struct, os, time, random, shelve
from threading import Thread
import socket
outsock = socket.socket( socket.AF_INET,socket.SOCK_DGRAM )

import bluetooth._bluetooth as _bt
#import the .so

def debug(m):
	print m
	
def _gethcisock (device_id = -1):
    try:
        sock = _bt.hci_open_dev (device_id)
	return sock
    except:
	debug("error accessing bluetooth device")
	exit(0)
	

class Devicemanager:
	def __init__(s,log=False,host='127.0.0.1',port=9000):
		s.devices={}
		s.logi=0
		s.now=time.time()
		s.logging=log
		s.host=host
		s.port=port
		s.triggers={}
	def msg(s,message):
		outsock.sendto(str(message[0])+' '+str(message[1])+'\n', (s.host, s.port))
		
	def dolog(s,o):
		log=shelve.open('s_btlog')
		log[str(s.logi)]=o
		log[str(s.logi)+'int']=time.time()-s.now
		s.now=time.time()
		log.close()
		s.logi+=1
	def play(s,e):
		if e[0]=='discovered':
			s.discovered(e[1],e[2],e[3])
		elif e[0]=='name':
			s.name_found(e[1],e[2])
		elif e[0]=='complete':
			s.inquiry_complete()
	def discovered(s, address, device_class='',rssi=0):
		#if not address in s.devices: - first trigger/ debounce?
		s.devices[address]=True
		if (debug):
			print "wim: found:",address
		if address in s.triggers:
			s.msg(s.triggers[address])
			if (debug):
				print "wim: sending",str(s.triggers[address][0]),str(s.triggers[address][1])
	def name_found(s,address,name):
		#catch for log
		if address not in s.devices:
			s.discovered(address)
		#s.devices[address].foundname(name)
		#if s.logging:
		#	s.dolog(['name',address, name])
	def inquiry_complete(s):
		num=0
		devs="";
		#for i in s.devices:
		#	if s.devices[i].checklost():
		#		num +=1
		#		if num>1:
		#			devs+=","
		#		devs+=s.devices[i].name
		#if s.logging:
		#	s.dolog(['complete'])
		
		#print num,"bluetooth devices (",devs,")"
		#s.msg("bt",[num])
		

class MyDiscoverer(bluetooth.DeviceDiscoverer):
	
	def __init__ (s,host='127.0.0.1',port=9000):
		s.sock = None
		s.is_inquiring = False
		s.lookup_names = False
		s.names_to_find = {}
		s.names_found = {}
		s.dm=Devicemanager(False,host,port)
    
	def pre_inquiry(s):
		s.done = False

	def device_discovered(s, address, device_class,rssi=0):
		s.dm.discovered(address, device_class,rssi=0)

	def name_found(s,address,name):
		s.dm.name_found(address,name)
		
	def inquiry_complete(s):
		s.dm.inquiry_complete()
		s.done = True
		
	def find_devices (s, lookup_names=True, duration=8, flush_cache=True):
		if s.is_inquiring:
			raise BluetoothError ("Already inquiring!")

		s.lookup_names = lookup_names

		s.sock = _gethcisock ()
		flt = _bt.hci_filter_new ()
		_bt.hci_filter_all_events (flt)
		_bt.hci_filter_set_ptype (flt, _bt.HCI_EVENT_PKT)

		try:
			s.sock.setsockopt (_bt.SOL_HCI, _bt.HCI_FILTER, flt)
		except:
			raise BluetoothError ("problem with local bluetooth device.")

		# send the inquiry command
		max_responses = 255
		cmd_pkt = struct.pack ("BBBBB", 0x33, 0x8b, 0x9e, \
			duration, max_responses)

		s.pre_inquiry ()
		
		try:
			_bt.hci_send_cmd (s.sock, _bt.OGF_LINK_CTL, \
			    _bt.OCF_INQUIRY, cmd_pkt)
		except:
			raise BluetoothError ("problem with local bluetooth device.")

		s.is_inquiring = True

		s.names_to_find = {}
		#s.names_found = {}

	def _process_hci_event (s):

		if s.sock is None: return
		# voodoo magic!!!
		pkt = s.sock.recv (255)
		ptype, event, plen = struct.unpack ("BBB", pkt[:3])
		pkt = pkt[3:]
		if event == _bt.EVT_INQUIRY_RESULT:
		    nrsp = struct.unpack ("B", pkt[0])[0]
		    for i in range (nrsp):
			addr = _bt.ba2str (pkt[1+6*i:1+6*i+6])
			psrm = pkt[ 1+6*nrsp+i ]
			pspm = pkt[ 1+7*nrsp+i ]
			devclass_raw = struct.unpack ("BBB", 
				pkt[1+9*nrsp+3*i:1+9*nrsp+3*i+3])
			devclass = (devclass_raw[2] << 16) | \
				(devclass_raw[1] << 8) | \
				devclass_raw[0]
			clockoff = pkt[1+12*nrsp+2*i:1+12*nrsp+2*i+2]

			if addr not in s.names_found and addr not in s.names_to_find:
				s.names_to_find[addr] = (devclass, psrm, pspm, clockoff)
			s.device_discovered (addr, devclass)
		elif event == _bt.EVT_INQUIRY_RESULT_WITH_RSSI:
		    nrsp = struct.unpack ("B", pkt[0])[0]
		    for i in range (nrsp):
			addr = _bt.ba2str (pkt[1+6*i:1+6*i+6])
			psrm = pkt[ 1+6*nrsp+i ]
			pspm = pkt[ 1+7*nrsp+i ]
	#                devclass_raw = pkt[1+8*nrsp+3*i:1+8*nrsp+3*i+3]
	#                devclass = struct.unpack ("I", "%s\0" % devclass_raw)[0]
			devclass_raw = struct.unpack ("BBB", 
				pkt[1+8*nrsp+3*i:1+8*nrsp+3*i+3])
			devclass = (devclass_raw[2] << 16) | \
				(devclass_raw[1] << 8) | \
				devclass_raw[0]
			clockoff = pkt[1+11*nrsp+2*i:1+11*nrsp+2*i+2]
			rssi = struct.unpack ("b", pkt[1+13*nrsp+i])[0]
			#print "%s rssi: %i" % (addr, rssi)
			if addr not in s.names_found and addr not in s.names_to_find:
				s.names_to_find[addr] = (devclass, psrm, pspm, clockoff)
			s.device_discovered (addr, devclass,rssi)
			#s.signalstrength(addr,rssi)
		elif event == _bt.EVT_INQUIRY_COMPLETE:
		    s.is_inquiring = False
		    if len (s.names_to_find) == 0:
	#                print "inquiry complete (evt_inquiry_complete)"
			s.sock.close ()
			s.inquiry_complete ()
		    else:
			s._send_next_name_req ()

		elif event == _bt.EVT_CMD_STATUS:
		    # XXX shold this be "<BBH"
		    status, ncmd, opcode = struct.unpack ("BBH", pkt[:4])
		    if status != 0:
			s.is_inquiring = False
			s.sock.close ()
			
	#                print "inquiry complete (bad status 0x%X 0x%X 0x%X)" % \
	#                        (status, ncmd, opcode)
			s.names_to_find = {}
			s.inquiry_complete ()
		elif event == _bt.EVT_REMOTE_NAME_REQ_COMPLETE:
		    status = struct.unpack ("B", pkt[0])[0]
		    addr = _bt.ba2str (pkt[1:7])
		    if status == 0:
			try:
			    name = pkt[7:].split ('\0')[0]
			except IndexError:
			    name = '' 
			if addr in s.names_to_find:
				device_class = s.names_to_find[addr][0]
				s.names_found[addr] = ( device_class, name)
				#s.device_discovered (addr, device_class, name)
				del s.names_to_find[addr]
				s.name_found(addr,name)
			else:
			    pass
		    else:
			if addr in s.names_to_find: del s.names_to_find[addr]
			# XXX should we do something when a name lookup fails?
	#                print "name req unsuccessful %s - %s" % (addr, status)

		    if len (s.names_to_find) == 0:
			s.is_inquiring = False
			s.sock.close ()
			s.inquiry_complete ()
	#                print "inquiry complete (name req complete)"
		    else:
			s._send_next_name_req ()
		else:
		    pass
	#            print "unrecognized packet type 0x%02x" % ptype
		
class scanner(Thread):
	def __init__ (s,host="127.0.0.1",port=9000,log=False):
		s.host=host
		s.port=port
		s.d = MyDiscoverer(s.host,s.port)
		s.simulate=False
		Thread.__init__(s)
		s.active=True
		s.kill=False
	
	def control(s,*msg):
		x,y=msg
		if x[2]=="sim":
			s.devices={}
			s.simulate=(x[3]==1)
		if x[2]=="active":
			s.active=(x[3]==1)
	def run(s):
		sock = _gethcisock ()
		if sock is None: 
			print "bt scanner: no bluetooth"
			exit(0)
		else:
			s.d.find_devices(lookup_names = False)
			readfiles = [ s.d, ]

			while not s.kill:
				if s.active:
					if s.simulate:
						print "simulating bluetooth.."
						try:
							f=shelve.open('btlog')
						except:
							print "bt log not found."
							break
						while s.active and s.simulate:
							i=1
							n=len(f.dict.keys())
							while i<n and s.active and s.simulate:
								event=f[str(i)]
								s.d.dm.play(event)
								i+=1
								time.sleep(f[str(i)+'int'])
						f.close()
						
					else:
						rfds = select.select( readfiles, [], [] )[0]
						if s.d in rfds:
							s.d.process_event()
						if s.d.done:
							s.d.find_devices(lookup_names = False)
				else:
					time.sleep(1)

def main():
	sock = _gethcisock ()
	if sock is None: 
		print "no bluetooth"
		exit(0)
	else:
		scan=scanner("127.0.0.1",5401,False)
		scan.start()
		while True:
			pass

if __name__ == '__main__': main()
