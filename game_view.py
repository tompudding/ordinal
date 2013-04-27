from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import modes
import random

class Viewpos(object):
    follow_threshold = 0
    max_away = 250
    def __init__(self,point):
        self.pos = point
        self.NoTarget()
        self.follow = None
        self.follow_locked = False
        self.t = 0

    def NoTarget(self):
        self.target        = None
        self.target_change = None
        self.start_point   = None
        self.target_time   = None
        self.start_time    = None

    def Set(self,point):
        self.pos = point.to_int()
        self.NoTarget()

    def SetTarget(self,point,t,rate=2,callback = None):
        #Don't fuck with the view if the player is trying to control it
        rate /= 4.0
        self.follow        = None
        self.follow_start  = 0
        self.follow_locked = False
        self.target        = point
        self.target_change = self.target - self.pos
        self.start_point   = self.pos
        self.start_time    = t
        self.duration      = self.target_change.length()/rate
        self.callback      = callback
        if self.duration < 200:
            self.duration  = 200
        self.target_time   = self.start_time + self.duration

    def Follow(self,t,actor):
        """
        Follow the given actor around.
        """
        self.follow        = actor
        self.follow_start  = t
        self.follow_locked = False

    def HasTarget(self):
        return self.target != None

    def Get(self):
        return self.pos

    def Skip(self):
        self.pos = self.target
        self.NoTarget()
        if self.callback:
            self.callback(self.t)
            self.callback = None

    def Update(self,t):
        try:
            return self.update(t)
        finally:
            self.pos = self.pos.to_int()

    def update(self,t):
        self.t = t
        if self.follow:
            if self.follow_locked:
                self.pos = self.follow.GetPos() - globals.screen*0.5
            else:
                #We haven't locked onto it yet, so move closer, and lock on if it's below the threshold
                fpos = self.follow.GetPos()*globals.tile_dimensions
                if not fpos:
                    return
                target = fpos - globals.screen*0.5
                diff = target - self.pos
                if diff.SquareLength() < self.follow_threshold:
                    self.pos = target
                    self.follow_locked = True
                else:
                    distance = diff.length()
                    if distance > self.max_away:
                        self.pos += diff.unit_vector()*(distance*1.02-self.max_away)
                        newdiff = target - self.pos
                    else:
                        self.pos += diff*0.02
                
        elif self.target:
            if t >= self.target_time:
                self.pos = self.target
                self.NoTarget()
                if self.callback:
                    self.callback(t)
                    self.callback = None
            elif t < self.start_time: #I don't think we should get this
                return
            else:
                partial = float(t-self.start_time)/self.duration
                partial = partial*partial*(3 - 2*partial) #smoothstep
                self.pos = (self.start_point + (self.target_change*partial)).to_int()


class GameView(ui.RootElement):
    def __init__(self):
        self.atlas = globals.atlas = drawing.texture.TextureAtlas('tiles_atlas_0.png','tiles_atlas.txt')
        self.game_over = False
        #pygame.mixer.music.load('music.ogg')
        #self.music_playing = False
        super(GameView,self).__init__(Point(0,0),Point(2000,2000))
        self.grid = ui.Grid(self,Point(0,0),Point(1,1),Point(0.04,0.04))
        self.grid.Disable()
        #skip titles for development of the main game
        #self.mode = modes.Titles(self)
        self.mode = modes.GameMode(self)
        self.viewpos = Viewpos(Point(0,0))
        self.dragging = None
        self.zoom = 1
        self.StartMusic()

    def StartMusic(self):
        pass
        #pygame.mixer.music.play(-1)
        #self.music_playing = True

    def IsDragging(self):
        return True if self.dragging else False

    def Draw(self):
        drawing.ResetState()
        drawing.Scale(self.zoom,self.zoom,1)
        drawing.Translate(-self.viewpos.pos.x,-self.viewpos.pos.y,0)
        drawing.DrawNoTexture(globals.line_buffer)
        drawing.DrawNoTexture(globals.colour_tiles)
        drawing.DrawAll(globals.nonstatic_text_buffer,globals.text_manager.atlas.texture.texture)

    def EnableGrid(self):
        self.grid.Enable()

    def DisableGrid(self):
        self.grid.Disable()
        
    def Update(self,t):
        if self.mode:
            self.mode.Update(t)

        if self.game_over:
            return
            
        self.t = t
        self.viewpos.Update(t)
        self.ClampViewpos()

    def GameOver(self):
        self.game_over = True
        self.mode = modes.GameOver(self)
        
    def KeyDown(self,key):
        self.mode.KeyDown(key)

    def KeyUp(self,key):
        if key == pygame.K_DELETE:
            if self.music_playing:
                self.music_playing = False
                pygame.mixer.music.set_volume(0)
            else:
                self.music_playing = True
                pygame.mixer.music.set_volume(1)
        self.mode.KeyUp(key)

    def MouseButtonDown(self,pos,button):
        if button == 3:
            self.dragging = self.viewpos.Get() + (pos/self.zoom)
            return True,self
        return False,None

    def MouseButtonUp(self,pos,button):
        if button == 3:
            self.dragging = None
            return True,False
        if button == 4:
            self.AdjustZoom(-0.2,pos)
        elif button == 5:
            self.AdjustZoom(+0.2,pos)
        
        return False,self.IsDragging()

    def MouseMotion(self,pos,rel,handled):
        self.mouse_pos = pos
        #always do dragging
        if self.dragging:
            self.viewpos.Set(self.dragging - (pos/self.zoom))
            self.ClampViewpos()
            self.dragging = self.viewpos.Get() + (pos/self.zoom)
            print self.viewpos.Get()
        if handled:
            return handled

    def AdjustZoom(self,amount,pos):
        pos_coords = self.viewpos.Get() + (pos/self.zoom)
        oldzoom = self.zoom
        self.zoom -= (amount/10.0)
        if self.zoom > 4:
            self.zoom = 4
        
        #if we've zoomed so far out that we can see an edge of the screen, fix that
        top_left= Point(0,globals.screen.y/self.zoom)
        top_right = globals.screen/self.zoom
        bottom_right = Point(globals.screen.x/self.zoom,0)
        
        try:
            viewpos = self.viewpos.Get()
            if viewpos.y < 0:
                raise ValueError

            if viewpos.x < 0:
                raise ValueError

            #now the top left
            viewpos = self.viewpos.Get()+top_right
            if viewpos.y  > self.absolute.size.y:
                raise ValueError

            if viewpos.x > self.absolute.size.y:
                raise ValueError

        except ValueError:
            #abort! This is a bit shit but whatever
            self.zoom = oldzoom
            return

        new_pos_coords = self.viewpos.Get() + pos/self.zoom
        self.viewpos.Set(self.viewpos.Get() + (pos_coords - new_pos_coords))

    def ClampViewpos(self):
        if self.viewpos.pos.x < 0:
            self.viewpos.pos.x = 0
        if self.viewpos.pos.y < 0:
            self.viewpos.pos.y = 0
        if self.viewpos.pos.x > (self.absolute.size.x - (globals.screen.x/self.zoom)):
            self.viewpos.pos.x = (self.absolute.size.x - (globals.screen.x/self.zoom))
        if self.viewpos.pos.y > (self.absolute.size.y - (globals.screen.y/self.zoom)):
            self.viewpos.pos.y = (self.absolute.size.y - (globals.screen.y/self.zoom))
