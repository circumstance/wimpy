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


import sys,time

class log():
	def timestamp(self):
		return  time.strftime('%a %D %H:%M:%S ')
	def __init__(self,logname):
		self.logname=logname
		self.log("log started")
	def log(self,entry):
		f=open(self.logname,"a")
		f.write(self.timestamp()+entry+'\n')
		f.close()