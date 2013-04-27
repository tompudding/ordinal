import globals,drawing
from globals.types import Point
import bisect
import ui
import math

twopi = math.pi*2

class Connector(ui.HoverableElement):
    def __init__(self,parent,bl,tr):
        self.dragging = None
        self.colour = drawing.constants.colours.white
        self.highlight_colour = drawing.constants.colours.red
        super(Connector,self).__init__(parent,bl,tr)
        self.circle_segments = 8
        self.circle_lines = [drawing.Line(globals.line_buffer) for i in xrange(self.circle_segments)]
        self.border = [drawing.Line(globals.line_buffer) for i in xrange(4)]
        self.arrow  = [drawing.Line(globals.line_buffer) for i in xrange(3)]
        self.connector_line = drawing.Line(globals.line_buffer)
        self.points = []
        self.connecting = False
        for i in xrange(self.circle_segments):
            angle = (float(i)/self.circle_segments)*twopi
            self.points.append(Point( math.cos(angle)*0.25 + 0.5,math.sin(angle)*0.25 + 0.5))
        self.UpdatePosition()
        self.SetColour(self.colour)

    def UpdatePosition(self):
        super(Connector,self).UpdatePosition()
        for i in xrange(len(self.points)):
            self.circle_lines[i].SetVertices(self.GetAbsolute(self.points[i]),self.GetAbsolute(self.points[(i+1)%len(self.points)]),self.level+0.5)
        bottom_left  = self.absolute.bottom_left 
        top_right    = self.absolute.top_right   
        top_left     = self.absolute.bottom_left + Point(0,self.absolute.size.y)
        bottom_right = self.absolute.bottom_left + Point(self.absolute.size.x,0)
        
        self.border[0].SetVertices(bottom_left,top_left,self.level + 0.5)
        self.border[1].SetVertices(bottom_left,bottom_right,self.level + 0.5)
        self.border[2].SetVertices(bottom_right,top_right,self.level + 0.5)
        self.border[3].SetVertices(top_left,top_right,self.level + 0.5)

        self.arrow[0].SetVertices(self.GetAbsolute(Point(0,0.5) + self.arrow_offset),self.GetAbsolute(Point(0.5,0.5)+ self.arrow_offset),self.level + 0.5)
        self.arrow[1].SetVertices(self.GetAbsolute(Point(0.4,0.4) + self.arrow_offset),self.GetAbsolute(Point(0.5,0.5)+ self.arrow_offset),self.level + 0.5)
        self.arrow[2].SetVertices(self.GetAbsolute(Point(0.4,0.6) + self.arrow_offset),self.GetAbsolute(Point(0.5,0.5)+ self.arrow_offset),self.level + 0.5)
        
    def SetColour(self,colour):
        self.colour = colour
        for line in self.circle_lines:
            line.SetColour(self.colour)
        for line in self.border:
            line.SetColour(self.colour)
        for line in self.arrow:
            line.SetColour(self.colour)

    def Hover(self):
        for line in self.border:
            line.SetColour(self.highlight_colour)

    def EndHover(self):
        for line in self.border:
            line.SetColour(self.colour)

class InputButton(Connector):
    arrow_offset = Point(0,0)

    def OnClick(self,pos,button):
        #if you click on the input it deletes any link connecting to it
        self.parent.BreakBackwardLink()

class OutputButton(Connector):
    arrow_offset = Point(0.45,0)
    def OnClick(self,pos,button):
        if button == 1:
            self.parent.BreakForwardLink()
            self.connecting = True
            self.connector_line.SetVertices(Point(0,0),Point(0,0),0)
            self.connector_line.Enable()
            self.root.active_connector = self

    def Update(self,t):
        if self.connecting:
            self.connector_line.SetVertices(self.GetAbsolute(Point(0.5,0.5)),self.root.mouse_pos,drawing.constants.DrawLevels.ui)
            self.connector_line.SetColour(drawing.constants.colours.red)

    #def Undepress(self):
    #    self.connecting = False
    #    self.connector_line.Disable()

    def MouseButtonDown(self,pos,button):
        pass

    def MouseButtonUp(self,pos,button):
        if self.connecting:
            if button == 3:
                self.connecting = False
                self.connector_line.Disable()
                self.root.active_connector = None
            if button == 1:
                #did they click on something
                hover = self.root.hovered
                if isinstance(hover,InputButton):
                    self.parent.next = hover.parent
                    self.parent.next.prev = self.parent
                    self.connecting = False
                    self.parent.UpdateConnectedLineForward()
                    self.root.active_connector = None
                else:
                    self.connecting = False
                    self.connector_line.Disable()
                    self.root.active_connector = None

    def MouseMotion(self,pos,rel,handled):
        if self.connecting:
            self.connector_line.SetVertices(self.GetAbsolute(Point(0.5,0.5)),pos,drawing.constants.DrawLevels.ui)
            self.connector_line.SetColour(drawing.constants.colours.red)

number_id = 0
          
class Number(ui.UIElement):
    title = 'Number:'
    line_peturb = 0.5
    target_size = Point(240,60).to_float()
    def __init__(self,parent,pos,num):
        global number_id
        tr = pos + (self.target_size/parent.absolute.size)
        super(Number,self).__init__(parent,pos,tr)
        self.id = number_id
        number_id += 1
        self.level_bonus = 800 + self.id*4 #numbers go on top
        self.num = num&0xffff
        self.target = None
        self.start = None
        self.launch_time = None
        self.arrival_time = None
        #we want the title bar to be 22 pixels high
        target_height = 22
        title_bottom = 1-(22.0/self.absolute.size.y)
        self.title_bar = ui.NumberBar(self,Point(0,title_bottom),Point(1,1),self.title,colour = None,buffer=globals.colour_tiles)
        self.content = ui.Box(self,Point(0,0),Point(1,title_bottom),colour = drawing.constants.colours.white,buffer = globals.colour_tiles)
        self.border = [drawing.Line(globals.line_buffer) for i in 0,1,2,3]
        self.hex = ui.TextBox(parent = self,
                              bl = Point(-0.15,0.0),
                              tr = Point(0.95,0.25),
                              text = ' ',
                              scale = 6,
                              colour = drawing.constants.colours.black,
                              textType = drawing.texture.TextTypes.GRID_RELATIVE,
                              alignment = drawing.texture.TextAlignments.RIGHT)
        self.dec = ui.TextBox(parent = self,
                              bl = Point(0,title_bottom),
                              tr = Point(1.05,0.97),
                              text = ' ',
                              scale = 7,
                              colour = drawing.constants.colours.white,
                              textType = drawing.texture.TextTypes.GRID_RELATIVE,
                              alignment = drawing.texture.TextAlignments.RIGHT)
        self.bin = ui.TextBox(parent = self,
                              bl = Point(-0.05,0.25),
                              tr = Point(1.05,0.5),
                              text = ' ',
                              scale = 6,
                              colour = drawing.constants.colours.black,
                              textType = drawing.texture.TextTypes.GRID_RELATIVE,
                              alignment = drawing.texture.TextAlignments.RIGHT)
        for line in self.border:
            line.SetColour(drawing.constants.colours.white)
        self.SetNum(self.num)
        self.UpdatePosition()
        self.readouts = [self.dec,self.hex,self.bin]
        for readout in self.readouts:
            readout.Enable()
        self.SetOpacity(0.8)

    def __hash__(self):
        return self.id

    def Update(self,t):
        if t < self.launch_time:
            #shouldn't even be alive!
            return
        if t >= self.arrival_time:
            #we're done
            if self.target is self.start:
                self.start.ProcessLeaving(self,self.arrival_time)
            else:
                self.target.ProcessArrival(self,self.arrival_time)
        else:
            progress = (t - self.launch_time)/self.duration
            self.bottom_left = self.start_pos + self.vector*progress
            self.top_right = self.bottom_left + self.size
            self.UpdatePosition()

    def Delete(self):
        super(Number,self).Delete()
        for line in self.border:
            line.Delete()
        
    def Disable(self):
        if self.enabled:
            for line in self.border:
                lines.Disable()
        super(Number,self).Disable()

    def Enable(self):
        if not self.enabled:
            for line in self.border:
                line.Enable()
        super(Number,self).Enable()

    def SetTarget(self,start,target,launch_time):
        self.target       = target
        self.start        = start
        
        self.launch_time  = launch_time
        self.arrival_time = launch_time + 1
        self.duration     = float(self.arrival_time - self.launch_time)
        self.UpdateEnds()
        

    def UpdateEnds(self):
        if self.target is self.start:
            #we're progressing across a primitive
            self.start_pos    = self.start.root.GetRelative(self.start.input.GetAbsolute(Point(0.5,0.5)))
            self.end_pos      = self.target.root.GetRelative(self.start.output.GetAbsolute(Point(0.5,0.5)))
        else:
            self.start_pos    = self.start.root.GetRelative(self.start.output.GetAbsolute(Point(0.5,0.5)))
            self.end_pos      = self.target.root.GetRelative(self.target.input.GetAbsolute(Point(0.5,0.5)))
        self.vector       = self.end_pos - self.start_pos

    def SetNum(self,num):
        self.num = num&0xffff
        hexnum = ' '.join(('%4x' % ((self.num>>i)&0xf) for i in (12,8,4,0)))
        binnum = ' '.join(('{:04b}'.format((self.num>>i)&0xf) for i in (12,8,4,0)))
        decnum = '%05d' % self.num
        self.hex.SetText(hexnum)
        self.bin.SetText(binnum)
        self.dec.SetText(decnum)

    def UpdatePosition(self):
        super(Number,self).UpdatePosition()
        bottom_left  = self.absolute.bottom_left + Point(-self.line_peturb,-self.line_peturb)
        top_right    = self.absolute.top_right   + Point(self.line_peturb,self.line_peturb)
        top_left     = self.absolute.bottom_left + Point(-self.line_peturb,self.absolute.size.y + self.line_peturb)
        bottom_right = self.absolute.bottom_left + Point(self.absolute.size.x + self.line_peturb,-self.line_peturb)
        
        self.border[0].SetVertices(bottom_left,top_left,self.level + 0.5)
        self.border[1].SetVertices(bottom_left,bottom_right,self.level + 0.5)
        self.border[2].SetVertices(bottom_right,top_right,self.level + 0.5)
        self.border[3].SetVertices(top_left,top_right,self.level + 0.5)

    def Passable(self):
        return True


class CodePrimitive(ui.UIElement):
    line_peturb = 0.5
    def __init__(self,parent,pos,tr,colour):
        self.colour = colour
        self.next = None
        self.prev = None
        #numbers is a list of numbers that are either inside us or on the way to the next number
        self.numbers = set()
        super(CodePrimitive,self).__init__(parent,pos,tr)
        self.title_bar = ui.TitleBar(self,Point(0,0.9),Point(1,1),self.title,colour = self.colour,buffer=globals.colour_tiles)
        self.content = ui.Box(self,Point(0,0),Point(1,0.9),colour = drawing.constants.colours.dark_grey,buffer = globals.colour_tiles)
        self.border = [drawing.Line(globals.line_buffer) for i in 0,1,2,3]
        self.connectors = []
        if self.input:
            self.input = InputButton(self,Point(0,0.4),Point(0.2,0.6)) 
            self.connectors.append( self.input )
        else:
            self.input = ui.UIElement(self,Point(0,0.4),Point(0.2,0.6)) 
        if self.output:
            self.output = OutputButton(self,Point(0.8,0.4),Point(1.0,0.6)) 
            self.connectors.append( self.output )
        else:
            self.output = ui.UIElement(self,Point(0.8,0.4),Point(1.0,0.6))

        self.UpdatePosition()
        self.SetColour(self.colour)
        self.symbol = self.Symbol(self.content,Point(0,0),Point(1,1))

    def Reset(self):
        self.numbers = set()

    def BreakForwardLink(self):
        if self.next:
            self.next.prev = None
            self.next = None

    def BreakBackwardLink(self):
        if self.prev:
            self.prev.next = None
            self.prev.output.connector_line.Disable()
            self.prev = None

    def UpdateConnectedLineForward(self):
        if self.next:
            #we own the line pointing to the next guy
            self.output.connector_line.SetVertices(self.output.GetAbsolute(Point(0.5,0.5)),self.next.input.GetAbsolute(Point(0.5,0.5)),drawing.constants.DrawLevels.ui)
        for number in self.numbers:
            number.UpdateEnds()
            
    def UpdateConnectedLineBackwards(self):
        if self.prev:
            self.prev.UpdateConnectedLineForward()

    def UpdatePosition(self):
        super(CodePrimitive,self).UpdatePosition()
        bottom_left  = self.absolute.bottom_left + Point(-self.line_peturb,-self.line_peturb)
        top_right    = self.absolute.top_right   + Point(self.line_peturb,self.line_peturb)
        top_left     = self.absolute.bottom_left + Point(-self.line_peturb,self.absolute.size.y + self.line_peturb)
        bottom_right = self.absolute.bottom_left + Point(self.absolute.size.x + self.line_peturb,-self.line_peturb)
        
        self.border[0].SetVertices(bottom_left,top_left,self.level + 0.5)
        self.border[1].SetVertices(bottom_left,bottom_right,self.level + 0.5)
        self.border[2].SetVertices(bottom_right,top_right,self.level + 0.5)
        self.border[3].SetVertices(top_left,top_right,self.level + 0.5)

        self.UpdateConnectedLineForward()
        self.UpdateConnectedLineBackwards()

    def Delete(self):
        super(CodePrimitive,self).Delete()
        for line in self.border:
            line.Delete()
        for item in self.symbol:
            item.Delete()
        
    def Disable(self):
        if self.enabled:
            for line in self.border:
                lines.Disable()
        super(CodePrimitive,self).Disable()

    def Enable(self):
        if not self.enabled:
            for line in self.border:
                line.Enable()
        super(CodePrimitive,self).Enable()

    def SetColour(self,colour):
        self.colour = colour
        for line in self.border:
            line.SetColour(self.colour)

    def ProcessArrival(self,number,cycle):
        if number.start and number.start is not self:
            number.start.numbers.remove(number)
        number.SetTarget(self,self,cycle)
        self.numbers.add(number)

    def ProcessLeaving(self,number,cycle):
        self.Process(number,cycle)
        #The number will get removed when it arrives at the next place
        #self.numbers.remove(number)
        if self.next:
            number.SetTarget(self,self.next,cycle)
        else:
            number.Delete()
            self.parent.RemoveNumber(number)

    def Process(self,number,cycle):
        pass

class SourceSymbol(ui.UIElement):
    def __init__(self,parent,bl,tr):
        self.colour = drawing.constants.colours.white
        super(SourceSymbol,self).__init__(parent,bl,tr)
        self.lines = [drawing.Line(globals.line_buffer) for i in 0,1,2]
        self.SetColour(self.colour)
        self.UpdatePosition()

    def UpdatePosition(self):
        super(SourceSymbol,self).UpdatePosition()
        self.lines[0].SetVertices(self.GetAbsolute(Point(0.5,0.25)),self.GetAbsolute(Point(0.5,0.75)),self.level+0.5)
        self.lines[1].SetVertices(self.GetAbsolute(Point(0.4,0.65)),self.GetAbsolute(Point(0.5,0.75)),self.level+0.5)
        self.lines[2].SetVertices(self.GetAbsolute(Point(0.6,0.65)),self.GetAbsolute(Point(0.5,0.75)),self.level+0.5)

    def Delete(self):
        super(SourceSymbol,self).Delete()
        for line in self.lines:
            line.Delete()
        
    def Disable(self):
        if self.enabled:
            for line in self.lines:
                lines.Disable()
        super(SourceSymbol,self).Disable()

    def Enable(self):
        if not self.enabled:
            for line in self.lines:
                line.Enable()
        super(SourceSymbol,self).Enable()

    def SetColour(self,colour):
        self.colour = colour
        for line in self.lines:
            line.SetColour(self.colour)

class SourceSymbol(ui.UIElement):
    def __init__(self,parent,bl,tr):
        self.colour = drawing.constants.colours.white
        super(SourceSymbol,self).__init__(parent,bl,tr)
        self.lines = [drawing.Line(globals.line_buffer) for i in 0,1,2]
        self.SetColour(self.colour)
        self.UpdatePosition()

    def UpdatePosition(self):
        super(SourceSymbol,self).UpdatePosition()
        self.lines[0].SetVertices(self.GetAbsolute(Point(0.5,0.25)),self.GetAbsolute(Point(0.5,0.75)),self.level+0.5)
        self.lines[1].SetVertices(self.GetAbsolute(Point(0.4,0.65)),self.GetAbsolute(Point(0.5,0.75)),self.level+0.5)
        self.lines[2].SetVertices(self.GetAbsolute(Point(0.6,0.65)),self.GetAbsolute(Point(0.5,0.75)),self.level+0.5)

    def Delete(self):
        super(SourceSymbol,self).Delete()
        for line in self.lines:
            line.Delete()
        
    def Disable(self):
        if self.enabled:
            for line in self.lines:
                lines.Disable()
        super(SourceSymbol,self).Disable()

    def Enable(self):
        if not self.enabled:
            for line in self.lines:
                line.Enable()
        super(SourceSymbol,self).Enable()

    def SetColour(self,colour):
        self.colour = colour
        for line in self.lines:
            line.SetColour(self.colour)

class SinkSymbol(ui.UIElement):
    def __init__(self,parent,bl,tr):
        self.colour = drawing.constants.colours.white
        super(SinkSymbol,self).__init__(parent,bl,tr)
        self.lines = [drawing.Line(globals.line_buffer) for i in 0,1,2]
        self.SetColour(self.colour)
        self.UpdatePosition()

    def UpdatePosition(self):
        super(SinkSymbol,self).UpdatePosition()
        self.lines[0].SetVertices(self.GetAbsolute(Point(0.5,0.25)),self.GetAbsolute(Point(0.5,0.75)),self.level+0.5)
        self.lines[1].SetVertices(self.GetAbsolute(Point(0.4,0.35)),self.GetAbsolute(Point(0.5,0.25)),self.level+0.5)
        self.lines[2].SetVertices(self.GetAbsolute(Point(0.6,0.35)),self.GetAbsolute(Point(0.5,0.25)),self.level+0.5)

    def Delete(self):
        super(SinkSymbol,self).Delete()
        for line in self.lines:
            line.Delete()
        
    def Disable(self):
        if self.enabled:
            for line in self.lines:
                lines.Disable()
        super(SinkSymbol,self).Disable()

    def Enable(self):
        if not self.enabled:
            for line in self.lines:
                line.Enable()
        super(SinkSymbol,self).Enable()

    def SetColour(self,colour):
        self.colour = colour
        for line in self.lines:
            line.SetColour(self.colour)


def TextSymbolCreator(text):
    def CreateTextObject(self,parent,bl,tr):
        return ui.TextBox(parent = parent,
                          bl     = bl,
                          tr     = Point(tr.x,tr.y-0.4),
                          text   = text,
                          scale  = 24,
                          colour = drawing.constants.colours.white,
                          textType = drawing.texture.TextTypes.GRID_RELATIVE,
                          alignment = drawing.texture.TextAlignments.CENTRE)
    return CreateTextObject

class Source(CodePrimitive):
    title  = "Source"
    Symbol = SourceSymbol
    input  = False
    output = True

    def __init__(self,*args,**kwargs):
        self.gen = self.generator()
        super(Source,self).__init__(*args,**kwargs)

    def Squirt(self,cycle):
        n = next(self.gen)
        num = Number(self.root,self.root.GetRelative(self.output.GetAbsolute(Point(0.5,0.5))),n)
        self.root.AddNumber(num)
        self.ProcessArrival(num,cycle)

    def Reset(self):
        super(Source,self).Reset()
        self.gen = self.generator()

class OneSource(Source):
    def generator(self):
        while True:
            yield 1

class Sink(CodePrimitive):
    title  = "Sink"
    Symbol = SinkSymbol
    input  = True
    output = False

    def __init__(self,*args,**kwargs):
        self.matched = 0
        super(Sink,self).__init__(*args,**kwargs)

    def Process(self,number,cycle):
        if number.num == self.sequence[self.matched]:
            self.matched += 1
            print 'matched',self.matched
            if self.matched == len(self.sequence):
                #play correct noise
                print 'finished level!'
                self.matched = 0
        else:
            #play bad noise
            print 'bad note!',number.num
            self.matched = 0

    def Reset(self):
        super(Sink,self).Reset()
        self.matched = 0

class TwoSong(Sink):
    sequence = [2,2,2,2]

class Increment(CodePrimitive):
    title  = "Increment"
    Symbol = TextSymbolCreator("+1")
    input  = True
    output = True

    def Process(self,number,cycle):
        number.SetNum(number.num + 1)
