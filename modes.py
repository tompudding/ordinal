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
    def __init__(self,parent):
        self.parent          = parent
        self.start           = pygame.time.get_ticks()
        self.stage           = TitleStages.STARTED
        self.handlers        = {TitleStages.STARTED  : self.Startup,
                                TitleStages.COMPLETE : self.Complete}
        bl = self.parent.GetRelative(Point(0,0))
        tr = bl + self.parent.GetRelative(globals.screen)
        self.blurb_text = ui.TextBox(parent = self.parent,
                                     bl     = bl         ,
                                     tr     = tr         ,
                                     text   = self.blurb ,
                                     textType = drawing.texture.TextTypes.GRID_RELATIVE,
                                     colour = (1,1,1,1),
                                     scale  = 4)
        self.backdrop        = ui.Box(parent = globals.screen_root,
                                      pos    = Point(0,0),
                                      tr     = Point(1,1),
                                      colour = (0,0,0,0))
        self.backdrop.Enable()

    def KeyDown(self,key):
        self.stage = TitleStages.COMPLETE

    def Update(self,t):        
        self.elapsed = t - self.start
        self.stage = self.handlers[self.stage](t)

    def Complete(self,t):
        self.backdrop.Delete()
        self.blurb_text.Delete()
        self.parent.mode = GameOver(self.parent)

    def Startup(self,t):
        return TitleStages.STARTED

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
        
    def Complete(self,blocks,cycles):
        self.parent.Stop(None)
        self.parent.Reset()
        self.parent.UIDisable()
        self.parent.mode = LevelTwoIntro(self.parent,blocks,cycles)

class LevelTwo(GameMode):
    def __init__(self,parent):
        super(LevelTwo,self).__init__(parent)
        self.parent.AddCode(code.TwoSource(self.parent,Point(0.38,0.45),drawing.constants.colours.white))
        self.parent.AddCode(code.ThreeSource(self.parent,Point(0.38,0.4),drawing.constants.colours.white))
        self.parent.AddCode(code.FiveSource(self.parent,Point(0.38,0.35),drawing.constants.colours.white))
        self.parent.AddCode(code.AlternateSong(self.parent,Point(0.52,0.39),drawing.constants.colours.white))
        self.parent.Play(None)

    def Complete(self,blocks,cycles):
        self.parent.Stop(None)
        self.parent.Reset()
        self.parent.UIDisable()
        self.parent.mode = LevelThreeIntro(self.parent,blocks,cycles)

class LevelThree(GameMode):
    def __init__(self,parent):
        super(LevelThree,self).__init__(parent)
        self.parent.AddCode(code.ArithmeticSource(self.parent,Point(0.38,0.45),drawing.constants.colours.white))
        self.parent.AddCode(code.ArithmeticSource(self.parent,Point(0.38,0.4),drawing.constants.colours.white))
        self.parent.AddCode(code.TwoSong(self.parent,Point(0.52,0.39),drawing.constants.colours.white))
        self.parent.Play(None)
        
    def Complete(self,blocks,cycles):
        self.parent.Stop(None)
        self.parent.Reset()
        self.parent.UIDisable()
        self.parent.mode = LevelFourIntro(self.parent,blocks,cycles)


class IntroMode(Mode):
    """ The Intro mode just shows a big text box explaining how to play and has an ok button on it"""
    blurb = """Ordinal

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
                                            pos = Point(0.39,0.1),
                                            tr = Point(0.61,0.2),
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
    
