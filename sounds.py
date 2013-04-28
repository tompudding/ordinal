import sys, pygame, glob, os

from pygame.locals import *
import pygame.mixer

pygame.mixer.init()

class Sounds(object):
    def __init__(self):
        self.numbers = []
        for filename in glob.glob('*.wav'):
            #print filename
            sound = pygame.mixer.Sound(filename)
            sound.set_volume(0.6)
            name = os.path.splitext(filename)[0]
            if 'number' in name:
                sound.set_volume(0.1)
                self.numbers.append(sound)
            if name.startswith('saw'):
                sound.set_volume(0.4)
            setattr(self,name,sound)
        self.sawsong  = [self.sawe,self.sawg,self.sawb]*2 + [self.sawd,self.sawg,self.sawb]*2 
        self.sawsong1 = [self.sawb,self.sawa,self.sawe]*2 + [self.sawa,self.sawf,self.sawd]*2

        
