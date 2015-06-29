#!/usr/bin/python
import pygame
from pygame.constants import *
import sys,os,re
import time
import mimetypes
import random
from subprocess import Popen,PIPE


def getScreenInfo(windowid):
	ret=Popen(['/usr/bin/xwininfo','-id',windowid],stdout=PIPE).communicate()[0]
	width=int(re.findall(r'Width: (\d+)',ret)[0])
	height=int(re.findall(r'Height: (\d+)',ret)[0])
	depth=int(re.findall('Depth: (\d+)',ret)[0])
	return width,height,depth

def initlist():
    path="/home/tristan/dev/dev_perso/crawlur/Pics/"
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
    flags=pygame.DOUBLEBUF
    #flags=0
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

def initcontainers(width,height):
    containers=[]

    for i in range(0,width,width/4): 
        for j in range(0,height,height/4):
            if i<width and j<height:
                containers.append(((i,j),(i+width/4,j+height/4)))
    return containers


def mosaic(imglist,containers):
    it=random.randint(0, len(imglist)-1)
    img = pygame.image.load(imglist[it]).convert()
    imgsizex,imgsizey= img.get_rect().size
    it2=random.randint(0,len(containers)-1)
    cont=containers[it2]
    posx=cont[0][0]
    posy=cont[0][1]
    lenx=cont[1][0]-cont[0][0]
    leny=cont[1][1]-cont[0][1]
    img = pygame.transform.scale(img,(lenx,leny))
    return img,posx,posy

def draw(screen,img,posx,posy):
    screen.blit(img, (posx,posy))
    pygame.display.flip()

def main():
    imglist=initlist()
    screen,width,height=initscreen()
    cont=initcontainers(width,height)
    while True:
        img,posx,posy=mosaic(imglist,cont)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type ==KEYUP:
                print "Keyup"
                pygame.quit()
                sys.exit()
        pygame.time.wait(1000) 
        draw(screen,img,posx,posy)



if __name__=='__main__':
	main()
