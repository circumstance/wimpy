#!/usr/bin/python

# Copyright (C) 2007 by Jaroslaw Zachwieja
# Modified (C) 2012 by Tim Redfern
# Published under the terms of GNU General Public License v2 or later.
# License text available at http://www.gnu.org/licenses/licenses.html#GPL

import serial,string,threading,time,sys,random

class GpsPoller(threading.Thread):
	
	latitude = 0
	longitude = 0
	changed = False
	fix=0
	satellites=0
	gps =""
	
	def __init__(self,port,test=False):
		self.test=test
		self.port=port
		if not self.test:
			self.gps = serial.Serial(port, 9600, timeout=1)
		threading.Thread.__init__(self)
		self.fixname=("no fix","no fix","2D fix","3D fix")
		
	def check(self):
		if self.changed:
			self.changed=False
			return (self.latitude,self.longitude)
		else:
			return False

	def run(self):
		if self.test:
			print "GpsPoller: serving random data"
		else:	
			print "GpsPoller: serving data from",self.port
		try:
			while True:
				if self.test:
					self.satellites=12
					self.fix=3
					self.latitude=random.random()*90
					self.longitude=random.random()*90
					self.changed=True
					time.sleep(0.5)
				else:
					line=""
					try:
						line = self.gps.read(1)
						line = line+self.gps.readline()
						datablock = line.split(',') 
						#print line
					except:
						print "caught serial error"
					try:
						if line[0:6] =='$GPGSV':
							try:
								self.satellites=string.atoi(datablock[3])
							except:
								self.satellites=0
						if line[0:6] =='$GPGSA':
							self.fix=string.atoi(datablock[2])
						if line[0:6] == '$GPGGA':
							
						
							latitude_in = string.atof(datablock[2])
							longitude_in = string.atof(datablock[4])
							
							#altitude = string.atof(datablock[8])
							#speed_in = string.atof(datablock[7])
							#heading = string.atof(datablock[8])

							if datablock[3] == 'S':
								 latitude_in = -latitude_in
							if datablock[5] == 'W':
								 longitude_in = -longitude_in

							latitude_degrees = int(latitude_in/100)
							latitude_minutes = latitude_in - latitude_degrees*100

							longitude_degrees = int(longitude_in/100)
							longitude_minutes = longitude_in - longitude_degrees*100

							latitude = latitude_degrees + (latitude_minutes/60)
							longitude = longitude_degrees + (longitude_minutes/60)
							
							if latitude!=self.latitude or longitude!=self.longitude:
								self.latitude=latitude
								self.longitude=longitude
								self.changed=True
					except:
						print "caught corrupt NMEA sentence"
			
			
		except StopIteration:
			pass

	def __del__(self):
		if self.gps!="":
			self.gps.close()

if __name__ == '__main__':
	
	gpsp = GpsPoller(sys.argv[1])
	gpsp.start()
	while 1:
		# In the main thread, every 5 seconds print the current value
		time.sleep(1.0)
		check=gpsp.check()
		print time.ctime(),gpsp.fixname[gpsp.fix],":satellites in view", gpsp.satellites
		if check!=False:
			print "changed:",check[0],check[1]
