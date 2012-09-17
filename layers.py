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

from PIL import Image
from latLng import latLng

class layer:
	"""template for a GPS image layer"""
	tl=latLng()
	br=latLng()
	pixel=(0,0)
	def __init__(self,file,ll1,ll2):
		try:
			self.image=Image.open(file)
		except:
			print "gps layer: failed to open", file
		try:
			l1=latLng()
			l2=latLng()
			l1.parse(ll1)
			l2.parse(ll2)
			self.tl.lat=max(l1.lat,l2.lat)
			self.tl.lng=min(l1.lng,l2.lng)
			self.br.lat=min(l1.lat,l2.lat)
			self.br.lng=max(l1.lng,l2.lng)
			self.pixsize=latLng(abs(self.tl.lat-self.br.lat)/self.image.size[1],abs(self.tl.lng-self.br.lng)/self.image.size[0])
		except:
			print "gps layer: failed to parse", file
	def checkcoord(self,pos):
		p=self.findpixel(pos)
		#print "pixel:",p[0],p[1]
		if p!=self.pixel:
			self.pixel=p
			return self.setcoord(p)
		else:
			return None
	def findpixel(self,pos):
		return (int((pos.lng-self.tl.lng)/self.pixsize.lng),int((self.tl.lat-pos.lat)/self.pixsize.lat))
	def setcoord(self,pos):
		"""to be overwritten:
		gets a messages when values change"
		returns None otherwise"""
		return None
		
class trigger():
	"""a generic trigger - 
	id can be anything - 
	i.e. a string or an integer"""
	def __init__(self,id,command,param):
		self.id=id
		self.command=(command,param)
	def check(self,id):
		if id==self.id:
			return command
		else:
			return None
		
class indexlayer(layer):
	"""generates gps triggers from an index colour image
	triggers when colour changes"""
	triggers=[]
	colour=-1
	def setcoord(self,pos):
		result=None
		p=(min(max(int(pos[0]),0),self.image.size[0]-2),min(max(int(pos[1]),0),self.image.size[1]-2))
		c=self.image.getpixel(p)			
		if c!=self.colour:
			self.colour=c
			print "indexlayer: new colour",c
			for t in self.triggers:
				if c==t.id:
					result=t.command
		return result
		
class scalelayer(layer):
	"""generates a varying signal based on interpolating a greyscale image
	uses sub pixel position"""
	def findpixel(self,pos):
		#float version
		return ((pos.lng-self.tl.lng)/self.pixsize.lng,(self.tl.lat-pos.lat)/self.pixsize.lat)
	def setcommand(self,command):
		self.command=command
	def setcoord(self,pos):
		px=min(max(int(pos[0]),0),self.image.size[0]-2)
		py=min(max(int(pos[1]),0),self.image.size[1]-2)
		c=float(self.image.getpixel((px,py)))/255.0
		c1=float(self.image.getpixel((px+1,py)))/255.0
		c2=float(self.image.getpixel((px,py+1)))/255.0
		c3=float(self.image.getpixel((px+1,py+1)))/255.0
		xf=pos[0]-px
		yf=pos[1]-py
		#lerp sub-pixel value
		return (self.command,(((c*(1.0-xf))+(c1*xf))*(1.0-yf))+(((c2*(1.0-xf))+(c3*xf))*yf))
		