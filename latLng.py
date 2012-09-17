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


class latLng:
	def __init__(self,lat=0.0,lng=0.0):
		self.lat=lat
		self.lng=lng
	def parse(self,string):
		n=string.split(",")
		try:
			self.lat=float(n[0])
		except:
			self.lat=0.0
		try:
			self.lng=float(n[1])
		except:
			self.lng=0.0
	def __eq__(self,pos):
		ret=False
		if isinstance(pos,latLng):
			if self.lat==pos.lat:
				if self.lng==pos.lng:
					ret=True
		return ret
	def __ne__(self,pos):
		return not self==pos