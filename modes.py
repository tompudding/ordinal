from OpenGL.GL import *
import random,numpy,cmath,math,pygame

import ui,globals,drawing,os,copy
from globals.types import Point
import sys
import code

class Mode(object):
    """ Abstract base class to represent game modes """
    def __init__(self,parent):
        self.parent = parent
    
    def KeyDown(self,key):
        pass
    
    def KeyUp(self,key):
        pass

    def MouseButtonDown(self,pos,button):
        return False,False

    def Update(self,t):
        pass

class TitleStages(object):
    STARTED  = 0
    COMPLETE = 1
    TEXT     = 2
    SCROLL   = 3
    WAIT     = 4

class Titles(Mode):
    blurb = "ORDINAL"
    number_duration = 2000
    def __init__(self,parent):
        self.parent          = parent
        self.start           = pygame.time.get_ticks()
        self.last = 0
        pygame.mixer.music.load('titles.ogg')
        pygame.mixer.music.play(-1)

        bl = Point(0.30,0.6)
        tr = bl + Point(0.4,0.1)
        self.blurb_text = ui.TextBox(parent = globals.screen_root,
                                     bl     = bl         ,
                                     tr     = tr         ,
                                     text   = self.blurb ,
                                     textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                     alignment = drawing.texture.TextAlignments.CENTRE,
                                     colour = drawing.constants.colours.white,
                                     scale  = 24,
                                     level = drawing.constants.DrawLevels.ui)
        self.play = ui.TextBoxButton(globals.screen_root ,
                                     'Play'               ,
                                     Point(0.4,0.25),
                                     Point(0.6,0.3),
                                     size=12,
                                     callback = self.Complete,
                                     line_width=4)
        self.blurb_text.Enable()
        self.parent.UIDisable()

    def Update(self,t):        
        self.elapsed = t - self.start
        if self.elapsed > self.last + self.number_duration:
            random.choice(globals.sounds.numbers).play()
            #globals.sounds.number_one.play()
            self.last = self.elapsed
        t = self.elapsed/2000.0
        y = 3*math.sin(t)
        x = 4*math.sin(0.666*t)
        z = ((math.sin(t)+1)/4)+0.5
        self.parent.viewpos.Set(Point(x+4,y+3)*globals.screen*0.3)
        self.parent.zoom = z
        #print x,y,z

    def Complete(self,t):
        self.blurb_text.Delete()
        self.play.Delete()
        pygame.mixer.music.stop()
        self.parent.mode = IntroMode(self.parent)
        self.parent.viewpos.Set(Point(2800,2700))
        self.parent.zoom = 0.65

class GameMode(Mode):
    def __init__(self,parent):
        self.parent = parent
        self.parent.EnableGrid()
        self.parent.Reset()
        self.parent.UIEnable()

    def Complete(self):
        pass

class LevelOne(GameMode):
    def __init__(self,parent):
        super(LevelOne,self).__init__(parent)
        self.source = code.OneSource(self.parent,Point(0.38,0.4),drawing.constants.colours.white)
        self.sink   = code.TwoSong(self.parent,Point(0.52,0.39),drawing.constants.colours.white)
        self.parent.AddCode(self.source)
        self.parent.AddCode(self.sink)
        self.parent.Play(None)
        pygame.mixer.music.load('ticks.ogg')
        pygame.mixer.music.play(-1)
        
    def Complete(self,blocks,cycles):
        self.parent.Stop(None)
        self.parent.Reset()
        self.parent.UIDisable()
        pygame.mixer.music.stop()
        self.parent.mode = LevelTwoIntro(self.parent,blocks,cycles)

class LevelTwo(GameMode):
    def __init__(self,parent):
        super(LevelTwo,self).__init__(parent)
        self.parent.AddCode(code.TwoSource(self.parent,Point(0.38,0.45),drawing.constants.colours.white))
        self.parent.AddCode(code.ThreeSource(self.parent,Point(0.38,0.4),drawing.constants.colours.white))
        self.parent.AddCode(code.FiveSource(self.parent,Point(0.38,0.35),drawing.constants.colours.white))
        self.parent.AddCode(code.AlternateSong(self.parent,Point(0.52,0.39),drawing.constants.colours.white))
        self.parent.Play(None)
        pygame.mixer.music.play(-1)

    def Complete(self,blocks,cycles):
        self.parent.Stop(None)
        self.parent.Reset()
        self.parent.UIDisable()
        self.parent.mode = LevelThreeIntro(self.parent,blocks,cycles)
        pygame.mixer.music.stop()

class LevelThree(GameMode):
    def __init__(self,parent):
        super(LevelThree,self).__init__(parent)
        self.parent.AddCode(code.ArithmeticSource(self.parent,Point(0.38,0.45),drawing.constants.colours.white))
        self.parent.AddCode(code.ArithmeticSource(self.parent,Point(0.38,0.4),drawing.constants.colours.white))
        self.parent.AddCode(code.Two2Song(self.parent,Point(0.52,0.39),drawing.constants.colours.white))
        self.parent.Play(None)
        pygame.mixer.music.play(-1)
        
    def Complete(self,blocks,cycles):
        self.parent.Stop(None)
        self.parent.Reset()
        self.parent.UIDisable()
        self.parent.mode = LevelFourIntro(self.parent,blocks,cycles)
        pygame.mixer.music.stop()


class IntroMode(Mode):
    """ The Intro mode just shows a big text box explaining how to play and has an ok button on it"""
    blurb = """ORDINAL

  In which you must guide numbers from sinks to sources to create beautiful music

    - drag blocks from the bar            - connect inputs to outputs            - watch and listen                    - potato"""
    button_text = 'one'
    target_level = LevelOne
    def __init__(self,parent):
        self.parent = parent
        self.parent.UIDisable()
        self.parent.UnshowHelp()
        if not self.parent.paused:
            self.parent.Play(None) #pause it
        self.level = drawing.constants.DrawLevels.ui + 500
        self.backdrop = ui.Box(globals.screen_root,Point(0.1,0.1),Point(0.9,0.9),colour = drawing.constants.colours.dark_grey,buffer = globals.ui_buffer,level = self.level)
        self.backdrop.Enable()
        self.intro_text = ui.TextBox(self.backdrop,Point(0,0.1),Point(1,0.9),text = self.blurb,scale=12,colour = drawing.constants.colours.white,level = self.level + 1)
        self.play_button = ui.TextBoxButton(parent = self.backdrop,
                                            text = self.button_text,
                                            pos = Point(0.30,0.1),
                                            tr = Point(0.7,0.2),
                                            colour = drawing.constants.colours.white,
                                            size = 24,
                                            callback = self.Play,
                                            level = self.level + 1)

    def Play(self,pos):
        self.backdrop.Delete()
        self.parent.mode = self.target_level(self.parent)

def quit(self,parent):
    raise SystemExit('bye')

class GameOver(IntroMode):
    blurb = 'Congratulations!'
    button_text = 'zero'
    target_level = quit
                                   
class LevelTwoIntro(IntroMode):
    blurb = 'You used {num_symbols} code blocks and took {cycles} cycles. Try to do better on the next level'
    target_level = LevelTwo
    button_text = 'two'

    def __init__(self,parent,blocks,cycles):
        self.blurb = self.blurb.format(num_symbols = blocks,cycles = cycles)
        super(LevelTwoIntro,self).__init__(parent)

class LevelThreeIntro(LevelTwoIntro):
    target_level = LevelThree
    button_text = 'three'
    

class LevelFourIntro(LevelTwoIntro):
    blurb = 'You used {num_symbols} code blocks and took {cycles} cycles.'
    target_level = GameOver
    button_text = 'three'
    
