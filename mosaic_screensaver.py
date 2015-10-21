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
import signal
import multiprocessing
from multiprocessing import Process, Queue
import fcntl

def getScreenInfo(windowid):
	ret=Popen(['/usr/bin/xwininfo','-id',windowid],stdout=PIPE).communicate()[0]
	width=int(re.findall(r'Width: (\d+)',ret)[0])
	height=int(re.findall(r'Height: (\d+)',ret)[0])
	depth=int(re.findall('Depth: (\d+)',ret)[0])
	return width,height,depth

def initlist():
    filename = os.path.expanduser("~/.xscreensaver")
    f=open(filename,"r")
    path=""
    for line in f:
        if "imageDirectory" in line:
            line2=line.split()
            path=line2[1]
    if not (os.path.isfile(path) or os.path.isdir(path)):
        path="./Pics"
    mimetypes.init()
    imglist=[]
    for dirpath, dirnames, files in os.walk(path):
        for f in files:
            fullname=os.path.join(dirpath,f)
            imagetype=mimetypes.guess_type(fullname)
            if "image" in imagetype[0]:
                imglist.append(fullname)
    return imglist

def initscreen():
    # Here comes the magic
    flags=pygame.DOUBLEBUF
    if '--root' in sys.argv or '-root' in sys.argv:
        print "root"
        windowid=os.environ.get('XSCREENSAVER_WINDOW')
        print windowid
        if windowid is None:
            sys.exit('Need XSCREENSAVER_WINDOW!')
        width,height,depth=getScreenInfo(windowid)
        os.environ['SDL_WINDOWID']=windowid
        flags=0
    else:

	width,height=(640,480)
        depth=0
        if '-f' in sys.argv or '--fullscreen' in sys.argv:
           flags|=pygame.FULLSCREEN

    pygame.init()
    screen=pygame.display.set_mode((width,height),flags,depth)
    pygame.display.set_caption('Mosaic')
    pygame.mouse.set_visible(False)
    return screen,width,height

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

def initcontainers(coef):
    containers=[]
    bigcont=[]

    # First, init the big containers
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

    for cont in bigcont:
        containers.append(cont)
    return containers


def mosaic(imglist,containers,width,height,coef,q,qmsg):
    # It's the worker process, we define the sigterm handler
    signal.signal(signal.SIGTERM , sigterm_handler)
    # Main loop
    while True:
        message=qmsg.get()
        if message=="image":
            print "begin"
            it2=random.randint(0,len(containers)-1)
            cont=containers[it2]
            posx=cont[0][0]*width/coef
            posy=cont[0][1]*height/coef
            lenx=cont[1][0]*width/coef
            leny=cont[1][1]*height/coef

            # pick a random image and load it
            imgsizex=0;imgsizey=0;
            # We check that the image is not too small (which would make it ugly
            # when resizing)
            while imgsizex<lenx or imgsizey<leny:
                it=random.randint(0, len(imglist)-1)
                img = pygame.image.load(imglist[it]).convert()
                imgsizex,imgsizey= img.get_rect().size

            print "middle"
            # Select how we will crop the image (according to its size ratio)
            coefx=imgsizex/lenx
            coefy=imgsizey/leny
            if coefx>coefy:
                img=img.subsurface(imgsizex/2-imgsizex/coefx/2,0,imgsizex/2+imgsizex/coefx/2,imgsizey)
            else:
                img=img.subsurface(0,imgsizey/2-imgsizey/coefy/2,imgsizex,imgsizey/2+imgsizey/coefy/2)

            # Scale the cropped image to the surface
            img = pygame.transform.scale(img,(lenx,leny))
            q.put((pygame.image.tostring(img,"RGB"),posx,posy,lenx,leny))
            print "end"
        elif message=="quit":
            print "closed process"
            q.close()
            q.cancel_join_thread()
            break
        else:
            raise ValueError

def draw(screen,q,qmsg):
    imgstr,posx,posy,lenx,leny=q.get()
    img=pygame.image.frombuffer( imgstr, (lenx,leny), 'RGB' )
    qmsg.put("image")
    pygame.time.wait(1000) 
    screen.blit(img, (posx, posy))
    pygame.display.flip()


def main():
    pid_file = 'program.pid'
    fp = open(pid_file, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        # another instance is running
        sys.exit(0)
    imglist=initlist()
    screen,width,height=initscreen()
    coef=4
    cont=initcontainers(coef)
    counter=0
    # Worker process : loads and resizes images
    p=[Process(target=mosaic, args=(imglist,cont,width,height,coef,q,qmsg)) \
            for i in range(max(multiprocessing.cpu_count()-1,1))]

    [proc.start() for proc in p]
    for i in range(7):
        qmsg.put("image")
    while True:
        # Operations needed for changing containers over time
        counter+=1
        if counter>100:
            counter=0
            cont=initcontainers(coef)
        # Get processed image
        draw(screen,q,qmsg)
        for event in pygame.event.get():
            if event.type in [pygame.QUIT, pygame.KEYUP]:
                [qmsg.put("quit") for proc in p]
                print "closed" 
                pygame.quit()
                sys.exit()



def sigterm_handler(_signo, _stack_frame):
    # Don't wait for the queue to be empty to close process
    q.close()
    q.cancel_join_thread()
    print "kill"
    # Exit gracefully
    sys.exit(0)

if __name__=='__main__':
    # The queue used for sharing images among processes
        q = Queue()
        qmsg = Queue()
        main()
