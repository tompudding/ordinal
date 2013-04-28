from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import modes
import random
import code

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
        self.pos = point
        #self.NoTarget()

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
    timer_update_duration = 0.1
    def __init__(self):
        self.atlas = globals.atlas = drawing.texture.TextureAtlas('tiles_atlas_0.png','tiles_atlas.txt')
        self.game_over = False
        #pygame.mixer.music.load('music.ogg')
        #self.music_playing = False
        super(GameView,self).__init__(Point(0,0),Point(8000,8000))
        self.grid = ui.Grid(self,Point(0,0),Point(1,1),Point(80,80))
        self.grid.Disable()

        self.ui = ui.UIElement(globals.screen_root,Point(0,0),Point(1,1)) 
        self.timer = ui.Box(self.ui,Point(0.75,0.95),Point(1,1),colour = drawing.constants.colours.white,buffer = globals.ui_buffer,level = drawing.constants.DrawLevels.ui)
        self.timer.text = ui.TextBox(parent = self.timer,
                                     bl     = Point(0,0),
                                     tr     = Point(1,0.90),
                                     text   = ' ',
                                     scale  = 12,
                                     colour = drawing.constants.colours.black,
                                     textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                     alignment = drawing.texture.TextAlignments.RIGHT,
                                     level = drawing.constants.DrawLevels.ui)
        self.time_controls = ui.Box(self.ui,Point(0.76,0.035),Point(0.98,0.2),colour = drawing.constants.colours.white,buffer = globals.ui_buffer,level = drawing.constants.DrawLevels.ui)
        self.speed_points = [(v/1000.0,i) for i,v in enumerate((0,0.25,1,2,4,8))]
        self.speed = 0.25/1000.0
        self.mouse_text           = ui.TextBox(parent   = self.ui,
                                               bl       = Point(0.005,0.005)  ,
                                               tr       = None                ,
                                               text     = ' '                 ,
                                               scale    = 8                   ,
                                               textType = drawing.texture.TextTypes.MOUSE_RELATIVE)

        self.mouse_text_colour    = (1,1,1,1)
        self.help = ui.Box(self.ui,Point(0.05,0.6),Point(0.40,0.95),colour = drawing.constants.colours.dark_grey,buffer = globals.ui_buffer)
        self.help.titlebar = ui.HelpBar(self.help,Point(0,0.9),Point(1,1),'Help (h to close)',colour = None,buffer=globals.ui_buffer)
        self.help.text = ui.TextBox(parent = self.help,
                                    bl     = Point(0,0),
                                    tr     = Point(1,0.8),
                                    text   = ' '*10,
                                    scale  = 6,
                                    colour = drawing.constants.colours.white,
                                    textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                    alignment = drawing.texture.TextAlignments.LEFT)
        self.help.Disable()

        self.time_controls.slider = ui.Slider(self.time_controls,
                                              bl = Point(0.05,0.5),
                                              tr = Point(0.95,0.95),
                                              points = self.speed_points,
                                              callback = self.set_speed_index,
                                              initial_index = 1,
                                              level = drawing.constants.DrawLevels.ui)

        self.time_controls.title = ui.TextBox(parent = self.time_controls,
                                              bl     = Point(0,0.8),
                                              tr     = Point(1,0.97),
                                              text   = 'Speed : %4.2f' % (self.speed*1000),
                                              scale  = 8,
                                              colour = drawing.constants.colours.black,
                                              textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                              alignment = drawing.texture.TextAlignments.CENTRE,
                                              level = drawing.constants.DrawLevels.ui)
        button_width = 0.15
        space = (1 - 2*button_width)/3
        button_height = (self.time_controls.absolute.size.x / self.time_controls.absolute.size.y) *button_width
        self.time_controls.stop = ui.TextBoxButton(parent = self.time_controls,
                                                   text   = 'S',
                                                   pos = Point(space,space*0.6),
                                                   tr = Point(space + button_width,space*0.6+button_height),
                                                   colour = drawing.constants.colours.black,
                                                   size = 19,
                                                   callback = self.Stop,
                                                   level = drawing.constants.DrawLevels.ui
                                                   )
        self.time_controls.play = ui.TextBoxButton(parent = self.time_controls,
                                                   text   = 'P',
                                                   pos = Point(space*2+button_width,space*0.6),
                                                   tr = Point(space*2 + button_width*2,space*0.6+button_height),
                                                   colour = drawing.constants.colours.black,
                                                   size = 19,
                                                   callback = self.Play,
                                                   level = drawing.constants.DrawLevels.ui
                                                   )
        self.time_controls.paused_text = ui.TextBox(parent = self.time_controls,
                                                    bl     = Point(0,0.0),
                                                    tr     = Point(1,0.2),
                                                    text   = 'Paused',
                                                    scale  = 6,
                                                    colour = drawing.constants.colours.black,
                                                    textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                                    alignment = drawing.texture.TextAlignments.CENTRE,
                                                    level = drawing.constants.DrawLevels.ui)

        self.time_controls.Enable()
        self.time_controls.paused_text.Disable()

        self.code_bar = code.CodeBar(self.ui,Point(0.03,0.035),Point(0.7,0.2))
        self.code_bar.AddButton(code.Increment)
        self.code_bar.AddButton(code.Add)
        self.code_bar.AddButton(code.Sub)
        self.code_bar.AddButton(code.Multiply)
        self.code_bar.AddButton(code.Divide)
        self.code_bar.AddButton(code.XOR)
        self.code_bar.AddButton(code.OR)

        self.code_bar.Enable()
        
        #skip titles for development of the main game
        #self.mode = modes.Titles(self)
        
        self.viewpos = Viewpos(Point(2800,2700))
        self.dragging = None
        self.zoom = 0.65
        self.zooming = None
        self.active_connector = False
        self.wall = pygame.time.get_ticks()
        self.last_cycle = 0
        self.t = 0
        self.numbers = set()
        self.StartMusic()
        self.last_timer_update = 0
        self.paused  = False
        self.stopped = False
        self.mouse_pos = Point(0,0)
        self.help_enabled = True
        self.help_showing = False
        self.sources = []
        self.blocks = []
        self.mode = modes.IntroMode(self)

    def UIEnable(self):
        self.ui.Enable()
        if not self.help_enabled or not self.help_showing:
            self.help.Disable()

    def UIDisable(self):
        self.ui.Disable()

    def Reset(self):
        self.Stop(None)
        for code in self.blocks:
            code.Delete()
        self.sources = []
        self.blocks = []

    def AddCode(self,new_code):
        self.blocks.append(new_code)
        if isinstance(new_code,code.Source):
            self.sources.append(new_code)
        new_code.Enable()

    def Stop(self,pos):
        """Reset the cycle count to zero, reset the sinks and the sources, and delete all the numbers on the board"""
        self.set_speed(0)
        self.t = 0
        self.wall = 0
        for number in self.numbers:
            number.Delete()
        self.numbers = set()
        for code in self.blocks:
            code.Reset()
        self.set_speed(0)
        self.timer.text.SetText('cycle:%8f' % self.t,colour = drawing.constants.colours.black)
        self.last_timer_update = self.t
        self.last_cycle = 0
        self.stopped = True
        self.paused  = False
        

    def Play(self,pos):
        if self.stopped:
            self.stopped = False
            self.set_speed(0.25/1000.0)
        elif self.paused:
            self.paused = False
            self.time_controls.paused_text.Disable()
        else:
            self.paused = True
            self.time_controls.paused_text.Enable()

    def set_speed_index(self,index):
        self.speed = self.speed_points[index][0]
        self.time_controls.title.SetText(('Speed : %4.2f' % (self.speed*1000)),colour = drawing.constants.colours.black)

    def set_speed(self,speed):
        self.speed = speed
        if self.speed > self.speed_points[-1][0]:
            self.speed = self.speed_points[-1][0]
        if self.speed < self.speed_points[0][0]:
            self.speed = self.speed_points[0][0]
        self.time_controls.slider.SetPointerValue(self.speed)
        self.time_controls.title.SetText(('Speed : %4.2f' % (self.speed*1000)),colour = drawing.constants.colours.black)

    def StartMusic(self):
        pass
        #pygame.mixer.music.play(-1)
        #self.music_playing = True

    def SetHelpText(self,text):
        self.help.text.SetText(text,colour = drawing.constants.colours.white)
        self.help_showing = True
        if self.help_enabled:
            self.help.Enable()
        else:
            self.help.Disable()

    def UnshowHelp(self):
        self.help.Disable()
        self.help_showing = False

    def IsDragging(self):
        return True if self.dragging else False

    def NewCycle(self,cycle):
        for source in self.sources:
            source.Squirt(cycle)

    def AddNumber(self,number):
        self.numbers.add(number)

    def RemoveNumber(self,number):
        try:
            self.numbers.remove(number)
        except KeyError:
            #it's already been deleted, probably by a global reset. Whatever!
            pass

    def Draw(self):
        drawing.ResetState()
        drawing.Scale(self.zoom,self.zoom,1)
        drawing.Translate(-self.viewpos.pos.x,-self.viewpos.pos.y,0)
        drawing.LineWidth(2)
        drawing.DrawNoTexture(globals.line_buffer)
        drawing.DrawNoTexture(globals.colour_tiles)
        drawing.DrawAll(globals.nonstatic_text_buffer,globals.text_manager.atlas.texture.texture)
        drawing.ResetState()
        drawing.Translate(self.mouse_pos.x,self.mouse_pos.y,10)
        drawing.DrawAll(globals.mouse_relative_buffer,globals.text_manager.atlas.texture.texture)

    def EnableGrid(self):
        self.grid.Enable()

    def DisableGrid(self):
        self.grid.Disable()
        
    def Update(self,t):
        if self.mode:
            self.mode.Update(t)

        if self.game_over:
            return
            
        elapsed = (t - self.wall)
        if self.speed != 0 and not self.paused:
            self.t += elapsed*self.speed
            for cycle in xrange(self.last_cycle,int(self.t)):
                self.NewCycle(cycle+1)
                self.last_cycle = int(self.t)
            if self.t > self.last_timer_update + self.timer_update_duration:
                self.timer.text.SetText('cycle:%8f' % self.t,colour = drawing.constants.colours.black)
                self.last_timer_update = self.t
            

        self.wall = t
        for num in set(self.numbers):
            num.Update(self.t)
        
        self.viewpos.Update(self.wall)
        self.ClampViewpos()

    def GameOver(self):
        self.game_over = True
        self.mode = modes.GameOver(self)
        
    def KeyDown(self,key):
        self.mode.KeyDown(key)

    def KeyUp(self,key):
        if key == pygame.K_KP_PLUS:
            self.set_speed(self.speed * 1.5)
        elif key == pygame.K_KP_MINUS:
            self.set_speed(self.speed / 1.5)
        if key == pygame.K_DELETE:
            if self.music_playing:
                self.music_playing = False
                pygame.mixer.music.set_volume(0)
            else:
                self.music_playing = True
                pygame.mixer.music.set_volume(1)
        if key == pygame.K_SPACE:
            self.Play(None)
        if key == pygame.K_h:
            if self.help_enabled:
                self.help_enabled = False
                if self.help_showing:
                    self.help.Disable()
            else:
                self.help_enabled = True
                if self.help_showing:
                    self.help.Enable()
        self.mode.KeyUp(key)

    def GetScreen(self,pos):
        return self.viewpos.Get() + (pos/self.zoom)

    def MouseButtonDown(self,pos,button):
        screen_pos = self.viewpos.Get() + (pos/self.zoom)
        if self.active_connector:
            self.active_connector.MouseButtonDown(screen_pos,button)
            return False,None
        handled,dragging = super(GameView,self).MouseButtonDown(screen_pos,button)
        
        if handled:
            return handled,dragging
        if button == 1:
            self.zooming = None
            self.dragging = screen_pos
            return True,self
        if button == 2:
            self.dragging = None
            self.zooming = screen_pos
            return True,self
            
        return False,None

    def MouseButtonUp(self,pos,button):
        screen_pos = self.viewpos.Get() + (pos/self.zoom)
        if self.active_connector:
            self.active_connector.MouseButtonUp(screen_pos,button)
            return False,None
        handled,dragging = super(GameView,self).MouseButtonUp(screen_pos,button)
        if handled:
            return handled,dragging

        if button == 1:
            self.dragging = None
            return True,False
        if button == 2:
            self.zooming = None
            return True,False
        if not self.zooming and not globals.dragging:
            if button == 4:
                self.AdjustZoom(-0.5,pos)
            elif button == 5:
                self.AdjustZoom(+0.5,pos)
        
        return False,self.IsDragging()

    def MouseMotion(self,pos,rel,handled):
        screen_pos = self.viewpos.Get() + (pos/self.zoom)
        screen_rel = rel/self.zoom
        self.mouse_pos = pos
        if self.active_connector:
            self.active_connector.MouseMotion(screen_pos,screen_rel,handled)
        handled = super(GameView,self).MouseMotion(screen_pos,screen_rel,handled)
        if handled:
            return handled
        #always do dragging
        if self.dragging:
            self.viewpos.Set(self.dragging - (pos/self.zoom))
            self.ClampViewpos()
            self.dragging = self.viewpos.Get() + (pos/self.zoom)
        elif self.zooming:
            self.AdjustZoom(-rel.y/100.0,globals.screen/2)

    def DispatchMouseMotion(self,target,pos,rel,handled):
        screen_pos = self.viewpos.Get() + (pos/self.zoom)
        screen_rel = rel/self.zoom
        return target.MouseMotion(screen_pos,screen_rel,handled)

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

        new_viewpos = self.viewpos.Get()
        if new_viewpos.y < 0:
            new_viewpos.y = 0

        if new_viewpos.x < 0:
            new_viewpos.x = 0
        
        #now the top left
        new_top_right = new_viewpos+top_right
        if new_top_right.y  > self.absolute.size.y:
            new_viewpos.y -= (new_top_right.y - self.absolute.size.y)

        if new_top_right.x > self.absolute.size.x:
            new_viewpos.x -= (new_top_right.x - self.absolute.size.x)
        
        try:
            if new_viewpos.y < 0:
                raise ValueError

            if new_viewpos.x < 0:
                raise ValueError

            #now the top left
            new_top_right = new_viewpos+top_right
            if new_top_right.y  > self.absolute.size.y:
                raise ValueError

            if new_top_right.x > self.absolute.size.x:
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
