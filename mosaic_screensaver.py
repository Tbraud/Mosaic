#!/usr/bin/python

#        DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
#                    Version 2, December 2004 
#
# Copyright (C) 2004 Sam Hocevar <sam@hocevar.net> 
#
# Everyone is permitted to copy and distribute verbatim or modified 
# copies of this license document, and changing it is allowed as long 
# as the name is changed. 
#
#            DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE 
#   TERMS AND CONDITIONS FOR COPYING, DISTRIBUTION AND MODIFICATION 
#
#  0. You just DO WHAT THE FUCK YOU WANT TO.

import pygame
from pygame.locals import *
import sys,os,re
import mimetypes
import random
from subprocess import Popen,PIPE
import threading
#from threading import Queue
from Queue import Queue

# Returns window size and color depth
# In : 
#   windowid : the window in which the screensaver will be executed
# Out : 
#   width : window width
#   height : window height
#   depth : window color depth
def getScreenInfo(windowid):
	ret=Popen(['/usr/bin/xwininfo','-id',windowid],stdout=PIPE).communicate()[0]
	width=int(re.findall(r'Width: (\d+)',ret)[0])
	height=int(re.findall(r'Height: (\d+)',ret)[0])
	depth=int(re.findall('Depth: (\d+)',ret)[0])
	return width,height,depth

# Crawls directories recursively
# In : 
#    path : full path to drectory to crawl
# Out :
#    imglist : a list containing the paths to all images in the directory
def fillimglist(path):
    mimetypes.init()
    imglist=[]
# Crawls directory
    for dirpath, dirnames, files in os.walk(path):
# If it's a directory, recall function with new dir
        for d in dirnames:
            imglist+=fillimglist(d)
# If it's a file, check if it is an image and add to image list
        for f in files:
            fullname=os.path.join(dirpath,f)
            try:
                imagetype=mimetypes.guess_type(fullname)
                if "image" in imagetype[0]:
                    imglist.append(fullname)
            except:
                # It wasn't an image and probably didn't have a type : ignore
                pass
    return imglist


# Gets images from directory specified in xscreensaver configuration file
# In : 
# Out :
#   imglist :
#    imglist : a list containing the paths to all images in the directory
def initlist():
# Parse ~/.xscreensaver configuration file
    filename = os.path.expanduser("~/.xscreensaver")
    f=open(filename,"r")
    path=""
    for line in f:
        line=line.strip()
        line2=line.split()
# Pictures are specified through the imageDirectory parameter.
# Note : procedure may be too restrective
        if len(line2)==2 and line[0]!="#" and line2[0] == "imageDirectory:":
            print(line2[1])
            path=line2[1]
# Check if file exists. Else, use default pictures in home folder 
# Todo : broken if doesn't exist
    if not (os.path.isfile(path) or os.path.isdir(path)):
        path=os.path.expanduser("~/Images")
# Creates image list from path. 
# May be long to process for huge directories
    imglist=fillimglist(path)
    return imglist

# Inits the window
# In :
# Out :
#   screen : pygame display object
#   width : screen width
#   height : screen height
def initscreen():
# Apparently for performance issues (not sure if it actually works)
    flags=pygame.DOUBLEBUF
    flags|=HWSURFACE
    if '--root' in sys.argv or '-root' in sys.argv:
# Magic trick from SDL : get xscreensaver windowid and display on top of it
        windowid=os.environ.get('XSCREENSAVER_WINDOW')
        print windowid
        if windowid is None:
            sys.exit('Need XSCREENSAVER_WINDOW!')
        width,height,depth=getScreenInfo(windowid)
        os.environ['SDL_WINDOWID']=windowid
    else:
# Display in a low resolution window
        width,height=(640,480)
        depth=0
        if '-f' in sys.argv or '--fullscreen' in sys.argv:
           flags|=pygame.FULLSCREEN
# Init pygame variables
    pygame.init()
    screen=pygame.display.set_mode((width,height),flags,depth)
    pygame.display.set_caption('Mosaic')
    pygame.mouse.set_visible(False)
    return screen,width,height

# Utility function that checks if an intersection exists between a container and
# the container list
# In : 
#   (i,j) : coordinates of top left corner
#   (width, height) : width and height of container
#   contlist : list of containers to compare
# Out : 
#   True or False
def isincontainer(((i,j),(width,height)),contlist):
    for cont in contlist:
        if ((i > cont[0][0] and i < cont[0][0]+cont[1][0]) \
            or (i+width > cont[0][0] and i+width<cont[0][0]+cont[1][0])) \
            and( (j > cont[0][1] and j < cont[0][1]+cont[1][1]) \
            or (j+height > cont[0][1] and j+height < cont[0][1]+cont[1][1])):
                return True
        else:
            return False
    return False

# Inits containerlist with small and big containers
# In :
#   coef : square root of the number of small containers contained in a big container
# Out:
#   containers : list of containers
def initcontainers(coef):
    containers=[]
    bigcont=[]

# First, init the big containers. 
    nbig=coef*coef/16
    for i in range(nbig):
        it=random.randint(0,coef-2)
        jt=random.randint(0,coef-2)
# We check that it doesn't overlap with another big container
        if not isincontainer(((it,jt),(2,2)),bigcont):
            bigcont.append(((it,jt),(2,2)))

# Init the small containers
    for i in range(0,coef): 
        for j in range(0,coef):
# We check that it doesn't overlap with a big container
            if not isincontainer(((i,j),(1,1)),bigcont):
                containers.append(((i,j),(1,1)))

# We add the big containers to container list
    for cont in bigcont:
        containers.append(cont)
    return containers

# Get container, wether random or by index
# In :
#   containers : container list
#   index : index of container to return. if -1 return random container
# Out :
#   a container
def pickcont(containers,index=0):
    if index==-1 or index>=len(containers):
        return random.randint(0,len(containers)-1)
    else:
        return containers[index]

# Select random image and sets it into a given container
def setimage(imglist,cont,width,height,coef):
# Get image width and height
    lenx=cont[1][0]*width/coef
    leny=cont[1][1]*height/coef

# Pick a random image and load it
    imgsizex=0;imgsizey=0;
# Check that image is big enough for being resized
    while imgsizex<lenx or imgsizey<leny:
        it=random.randint(0, len(imglist)-1)
        img = pygame.image.load(imglist[it]).convert()
        imgsizex,imgsizey= img.get_rect().size

# Select how we will crop the image (according to its size ratio)
    coefx=imgsizex/lenx
    coefy=imgsizey/leny
    if coefx>coefy:
        img=img.subsurface(imgsizex/2-imgsizex/coefx/2,0,imgsizex/2+imgsizex/coefx/2,imgsizey)
    else:
        img=img.subsurface(0,imgsizey/2-imgsizey/coefy/2,imgsizex,imgsizey/2+imgsizey/coefy/2)

# Scale the cropped image to the surface
    img = pygame.transform.scale(img,(lenx,leny))
    return img,lenx,leny

# First Mosaic : fills the screen 
# In : 
#   imglist : image list
#   containers : containers list
#   width : window width
#   height : window height
#   coef : square root of the number of small containers contained in a big container
#   q : queue for passing images to other threads
def mosaic_first(imglist,containers,width,height,coef,q):
    for cont in containers:
            posx=cont[0][0]*width/coef
            posy=cont[0][1]*height/coef
            img,lenx,leny=setimage(imglist,cont,width,height,coef)
            q.put((pygame.image.tostring(img,"RGB"),posx,posy,lenx,leny))

# Mosaic Routine : check if main thread has requested an image and creates it
# In : 
#   imglist : image list
#   containers : containers list
#   width : window width
#   height : window height
#   coef : square root of the number of small containers contained in a big container
#   q : queue for passing images to other threads
#   qmsg : message queue for communicating with other threads
def mosaic(imglist,containers,width,height,coef,q,qmsg):
    # Main loop
    while True:
        message=qmsg.get()
        if message=="image":
            it2=pickcont(containers,-1)
            cont=containers[it2]
            posx=cont[0][0]*width/coef
            posy=cont[0][1]*height/coef
            img,lenx,leny=setimage(imglist,cont,width,height,coef)
            q.put((pygame.image.tostring(img,"RGB"),posx,posy,lenx,leny))
        elif message=="quit":
            break
        else:
            raise ValueError

# Draw : picks an image from the image queue and requests a new one in the
# message queue
# In :
#   screen : pygame object
#   q : queue for passing images to other threads
#   qmsg : message queue for communicating with other threads
def draw(screen,q,qmsg):
    imgstr,posx,posy,lenx,leny=q.get()
    img=pygame.image.frombuffer( imgstr, (lenx,leny), 'RGB' )
    qmsg.put("image")
    screen.blit(img, (posx, posy))
    pygame.display.flip()

# Main program
def main():
# The queue used for sharing images among processes
    q = Queue()
    qmsg = Queue()
# Set coef to 4 (best ratio performance/beauty)
    coef=4
# Set counter for container change
    counter=0
    maxcounter=20
# Set time between two images (ms)
    waittime=2000
# Initialize screen, images and containers
    screen,width,height=initscreen()
    imglist=initlist()
    cont=initcontainers(coef)
# Fill screen
    mosaic_first(imglist,cont,width,height,coef,q)
    for c in cont:
        draw(screen,q,qmsg)
# Starts the main routine in a separate thread
    t=threading.Thread(target=mosaic, args=(imglist,cont,width,height,coef,q,qmsg))
    thr=[]
    thr.append(t)
    [thread.start() for thread in thr]
    while True:
# Change containers every maxcounter
        counter+=1
        if counter>maxcounter:
            counter=0
            cont=initcontainers(coef)
# Get processed image
        draw(screen,q,qmsg)
# Wait between two images
        pygame.time.wait(waittime) 
        for event in pygame.event.get():
            if event.type in [pygame.QUIT, pygame.KEYUP]:
                [qmsg.put("quit") for thread in thr]
                print "closed" 
                pygame.quit()
                sys.exit()


if __name__=='__main__':
        main()
