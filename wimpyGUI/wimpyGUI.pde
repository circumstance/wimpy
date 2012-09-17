import hypermedia.net.*;

/*

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU Lesser General Public License
 as published by the Free Software Foundation; either version 2.1
 of the License, or (at your option) any later version.

 wimpyGUI - gui for wim.py - gps / bluetooth listener communicates via UDP packets
 designed to interface with pure data
  (C) 2012 Tim Redfern

 wimpyGUI is a processing program - http://processing.org

 wimpyGUI uses the same bitmaps and overlays as wim.py - copy them into the data folder

 wimpyGUI requires the hypermiedia.net UDP library from here: http://ubaa.net/shared/processing/udp/

 to use- open wimpyGUI.pde with processing
 press 0,1 or 2 to switch between bitmap overlays
 move the mouse to simulate gps input
 
 developed exclusively for circumstance - Tomorrow the ground forgets you were here
 
 http://productofcircumstance.com/portfoliocpt/tomorrow-the-ground-forgets-you-were-here/

 Bugs, issues, suggestions: tim@eclectronics.org
 
*/

PImage[] bgmaps;
int usemap;
UDP udp;
int x,y;
float lat1,lng1,lat2,lng2,fw,fh;
String sendIP;


void setup() 
{
  bgmaps=new PImage[3];
  sendIP="127.0.0.1";
  int map=1;
  switch (map) {
    case 1:
      bgmaps[0] = loadImage("gentmap.png");
      bgmaps[1] = loadImage("indexV4.gif");
      bgmaps[2] = loadImage("scalar01.png");
      lat1=51.050608;
      lng1=3.724698;
      lat2=51.046878;
      lng2=3.732852;
      break;
    case 2:
      bgmaps[0] = loadImage("TimelabTestAreaGUI.jpg");
      bgmaps[1] = loadImage("TimelabTestAreaGRADIENT.png");
      lat1=51.043293;
      lng1=3.737025;
      lat2=51.042154;
      lng2=3.739584;
      break;
    case 3:
      bgmaps[0] = loadImage("domst.png");
      bgmaps[1] = loadImage("domst_grad.png");
      bgmaps[2] = loadImage("domst_index.png");
      lat1=53.353241;
      lng1=-6.268789;
      lat2=53.35171;
      lng2=-6.266284;
      break;
  }
  usemap=0;
  size(bgmaps[0].width,bgmaps[0].height);
  frameRate(5);
  udp = new UDP(this);
  x=width/2;
  y=height/2;
  
  fw=lng2-lng1;
  fh=lat1-lat2;
}

void draw() 
{
  background(bgmaps[usemap]);
  fill(255);
  stroke(255,0,0);
  ellipse(x,y,5,5);
}

void mouseDragged() 
{
  if (mousePressed) {
    x=mouseX;
    y=mouseY;
    float fx=((float)mouseX)/width;
    float fy=((float)mouseY)/height;
    udp.send(lat1-((fy*fh))+","+((fx*fw)+lng1)+"\n",sendIP,5400);
    //println(lat1-((fy*fh))+","+((fx*fw)+lng1));
  }
}

void keyPressed() {
  switch(key) {
    case '0':
      usemap=0;
      break;
    case '1':
      usemap=1;
      break;
    case '2':
      usemap=2;
      break;
  }
}

