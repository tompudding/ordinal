import globals,drawing
from globals.types import Point
import bisect
import ui
import math
import itertools

twopi = math.pi*2

class Connector(ui.HoverableElement):
    def __init__(self,parent,bl,tr):
        self.dragging = None
        self.prev = None
        self.next = None
        self.numbers = set()
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
        self.prev = self.next = None

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
        for line in itertools.chain(self.border,self.circle_lines,self.arrow):
            line.SetColour(self.colour)

    def Hover(self):
        for line in self.border:
            line.SetColour(self.highlight_colour)

    def EndHover(self):
        for line in self.border:
            line.SetColour(self.colour)

    def Delete(self):
        super(Connector,self).Delete()
        for line in itertools.chain(self.border,self.circle_lines,self.arrow):
            line.Delete()
        self.connector_line.Delete()

    def Reset(self):
        self.numbers = set()
        
    def Disable(self):
        if self.enabled:
            for line in itertools.chain(self.border,self.circle_lines,self.arrow):
                line.Disable()
            self.connector_line.Disable()
        super(Connector,self).Disable()

    def Enable(self):
        if not self.enabled:
            for line in itertools.chain(self.border,self.circle_lines,self.arrow):
                line.Enable()
            self.connector_line.Enable()
        super(Connector,self).Enable()

    def ProcessArrival(self,number,cycle):
        if number.start:
            number.start.numbers.remove(number)
        self.numbers.add(number)

    def UpdateConnectedLineForward(self):
        if self.next:
            #we own the line pointing to the next guy
            self.connector_line.SetVertices(self.GetAbsolute(Point(0.5,0.5)),self.next.GetAbsolute(Point(0.5,0.5)),drawing.constants.DrawLevels.ui)
        for number in self.numbers:
            number.UpdateEnds()
            
    def UpdateConnectedLineBackwards(self):
        if self.prev:
            self.prev.UpdateConnectedLineForward()

    def BreakForwardLink(self):
        pass

    def BreakBackwardLink(self):
        pass

class InputButton(Connector):
    arrow_offset = Point(0,0)

    def OnClick(self,pos,button):
        #if you click on the input it deletes any link connecting to it
        self.BreakBackwardLink()

    def BreakBackwardLink(self):
        if self.prev:
            self.prev.connector_line.Disable()
            self.prev.BreakForwardLink()

    def ProcessArrival(self,number,cycle):
        super(InputButton,self).ProcessArrival(number,cycle)
        self.parent.ProcessArrival(self,number,cycle)


class OutputButton(Connector):
    arrow_offset = Point(0.45,0)
    def OnClick(self,pos,button):
        if button == 1:
            self.BreakForwardLink()
            self.connecting = True
            self.connector_line.SetVertices(Point(0,0),Point(0,0),0)
            self.connector_line.Enable()
            self.root.active_connector = self

    def Update(self,t):
        if self.connecting:
            self.connector_line.SetVertices(self.GetAbsolute(Point(0.5,0.5)),self.root.mouse_pos,drawing.constants.DrawLevels.ui)
            self.connector_line.SetColour(drawing.constants.colours.red)

    def BreakForwardLink(self):
        if self.next:
            self.next.prev = None
            self.next = None
            #kill any numbers that are on our line and haven't reached their target yet
            for number in self.numbers:
                    number.Kill()

            self.numbers = set()

    def ProcessArrival(self,number,cycle):
        super(OutputButton,self).ProcessArrival(number,cycle)
        self.parent.ProcessLeaving(self,number,cycle)


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
                if isinstance(hover,InputButton) and hover.prev == None:
                    self.next = hover
                    self.next.prev = self
                    self.connecting = False
                    self.UpdateConnectedLineForward()
                    self.root.active_connector = None
                else:
                    self.connecting = False
                    self.connector_line.Disable()
                    self.root.active_connector = None

    def MouseMotion(self,pos,rel,handled):
        if self.connecting:
            self.connector_line.SetVertices(self.GetAbsolute(Point(0.5,0.5)),pos,drawing.constants.DrawLevels.ui)
            self.connector_line.SetColour(drawing.constants.colours.red)

    def Delete(self):
        super(OutputButton,self).Delete()

    def Disable(self):
        super(OutputButton,self).Disable()
        

class SourceOutputButton(OutputButton):
    message = "The next numbers from this output will be "
    def Hover(self):
        #This can happen quite a lot, and I think I'm generating a large nested itertools object when that happens
        #oh well
        super(SourceOutputButton,self).Hover()
        comingup = [next(self.parent.gen) for i in xrange(5)]
        self.parent.gen = itertools.chain(comingup, self.parent.gen)
        self.root.SetHelpText(self.message + ' '.join('%d' % v for v in comingup))
        
    def EndHover(self):
        super(SourceOutputButton,self).EndHover()
        self.root.UnshowHelp()

class SinkInputButton(InputButton):
    message = "This sink expects the following numbers "

    def Hover(self):
        super(SinkInputButton,self).Hover()
        self.root.SetHelpText(self.message + ' '.join('%d' % v for v in self.parent.sequence))
        
    def EndHover(self):
        super(SinkInputButton,self).EndHover()
        self.root.UnshowHelp()

class SourceInputButton(InputButton):
    def __init__(self,*args,**kwargs):
        super(SourceInputButton,self).__init__(*args,**kwargs)
        self.Disable()

class SinkOutputButton(OutputButton):
    def __init__(self,*args,**kwargs):
        super(SinkOutputButton,self).__init__(*args,**kwargs)
        self.Disable()


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
            self.start_pos    = self.start.root.GetRelative(self.start.GetAbsolute(Point(0.5,0.5)))
            self.end_pos      = self.target.root.GetRelative(self.start.GetAbsolute(Point(0.5,0.5)))
        else:
            self.start_pos    = self.start.root.GetRelative(self.start.GetAbsolute(Point(0.5,0.5)))
            self.end_pos      = self.target.root.GetRelative(self.target.GetAbsolute(Point(0.5,0.5)))
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

    def Kill(self):
        self.Delete()
        self.root.RemoveNumber(self)


class CodePrimitive(ui.UIElement):
    line_peturb   = 0.5
    input_classes = [InputButton]
    output_classes  = [OutputButton]
    target_size   = Point(300,200).to_float()
    def __init__(self,parent,pos,colour):
        self.colour = colour
        #numbers is a list of numbers that are either inside us or on the way to the next number
        tr = pos + (self.target_size/parent.absolute.size)
        super(CodePrimitive,self).__init__(parent,pos,tr)
        self.title_bar = ui.TitleBar(self,Point(0,0.9),Point(1,1),self.title,colour = self.colour,buffer=globals.colour_tiles)
        self.content = ui.Box(self,Point(0,0),Point(1,0.9),colour = drawing.constants.colours.dark_grey,buffer = globals.colour_tiles)
        self.border = [drawing.Line(globals.line_buffer) for i in 0,1,2,3]
        if self.input:
            self.inputs = [ic(self,Point(0,0.4),Point(0.2,0.6)) for ic in self.input_classes]
        else:
            self.inputs = [SourceInputButton(self,Point(0,0.4),Point(0.2,0.6))]
        if self.output:
            self.outputs = [oc(self,Point(0.8,0.4),Point(1.0,0.6)) for oc in self.output_classes]
        else:
            self.outputs = [SinkOutputButton(self,Point(0.8,0.4),Point(1.0,0.6))]

        self.UpdatePosition()
        self.SetColour(self.colour)
        self.symbol = self.Symbol(self.content,Point(0,0),Point(1,1))

    def Reset(self):
        if self.input:
            for i in self.inputs:
                i.Reset()
        if self.output:
            for o in self.outputs:
                o.Reset()

    def DeleteCallback(self,pos):
        self.Delete()

    def UpdateConnectedLineForward(self):
        if not self.output:
            return
        for o in self.outputs:
            o.UpdateConnectedLineForward()
            
    def UpdateConnectedLineBackwards(self):
        if not self.input:
            return
        for i in self.inputs:
            i.UpdateConnectedLineBackwards()

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
        if self.output:
            for o in self.outputs:
                o.BreakForwardLink()
        if self.input:
            for i in self.inputs:
                i.BreakBackwardLink()
        for line in self.border:
            line.Delete()
        self.symbol.Delete()
        
    def Disable(self):
        if self.enabled:
            for line in self.border:
                line.Disable()
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

    def ProcessArrival(self,input,number,cycle):
        number.SetTarget(self.inputs[0],self.outputs[0],cycle)

    def ProcessLeaving(self,output,number,cycle):
        self.Process(number,cycle)
        if output.next:
            number.SetTarget(output,output.next,cycle)
        else:
            number.Kill()

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
                line.Disable()
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
                line.Disable()
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
    output_classes = [SourceOutputButton]

    def __init__(self,*args,**kwargs):
        self.gen = self.generator()
        super(Source,self).__init__(*args,**kwargs)

    def Squirt(self,cycle):
        n = next(self.gen)
        num = Number(self.root,self.root.GetRelative(self.outputs[0].GetAbsolute(Point(0.5,0.5))),n)
        self.root.AddNumber(num)
        self.inputs[0].ProcessArrival(num,cycle)

    def Reset(self):
        super(Source,self).Reset()
        self.gen = self.generator()

    def DeleteCallback(self,pos):
        #you can't delete sources
        pass


class OneSource(Source):
    def generator(self):
        while True:
            yield 1

class Sink(CodePrimitive):
    title  = "Sink"
    Symbol = SinkSymbol
    input  = True
    output = False
    input_classes = [SinkInputButton]

    def __init__(self,*args,**kwargs):
        self.matched = 0
        super(Sink,self).__init__(*args,**kwargs)

    def Process(self,number,cycle):
        if number.num == self.sequence[self.matched]:
            self.matched += 1
            if self.matched == len(self.sequence):
                #play correct noise
                globals.current_view.mode.Complete()
                self.matched = 0
        else:
            #play bad noise
            print 'bad note!',number.num
            self.matched = 0

    def Reset(self):
        super(Sink,self).Reset()
        self.matched = 0

    def DeleteCallback(self,pos):
        #you can't delete sinks
        pass


class TwoSong(Sink):
    sequence = [2,2,2,2]

class Increment(CodePrimitive):
    title  = "Increment"
    short_form = 'INC'
    help = """Increment increases the value of the input number by one"""
    Symbol = TextSymbolCreator("+1")
    input  = True
    output = True

    def Process(self,number,cycle):
        number.SetNum(number.num + 1)

class CodeCreator(ui.HoverableElement):
    def __init__(self,parent,pos,tr,code_class):
        super(CodeCreator,self).__init__(parent,pos,tr)
        self.code_class = code_class
        self.backdrop = ui.Box(self,Point(0,0.3),Point(1,1),colour = drawing.constants.colours.dark_grey,buffer=globals.ui_buffer,level = drawing.constants.DrawLevels.ui)
        self.title = ui.TextBox(parent = self,
                                bl = Point(0,0),
                                tr = Point(1,0.3),
                                text = code_class.short_form,
                                scale = 6,
                                colour = drawing.constants.colours.black,
                                textType = drawing.texture.TextTypes.SCREEN_RELATIVE,
                                alignment = drawing.texture.TextAlignments.CENTRE,
                                level = drawing.constants.DrawLevels.ui+1000)
        self.dragging = None
        self.last_opacity = 1

    def Depress(self,pos):
        create_pos = globals.current_view.GetScreen(pos)
        new_code = self.code_class(globals.current_view,globals.current_view.GetRelative(create_pos),drawing.constants.colours.white)
        new_code.level_bonus = 100
        self.last_opacity = 1
        self.dragging = (create_pos,new_code)
        return self

    def Undepress(self):
        if self.dragging:
            pos,new_code = self.dragging
            if globals.current_view.CollidesAny(new_code,include_parent = False):
                new_code.Delete()
            else:
                new_code.level_bonus = 0
                new_code.UpdatePosition()
                globals.current_view.AddCode(new_code)
        self.dragging = None

    def MouseMotion(self,pos,rel,handled):
        if self.dragging != None:
            dragging,new_code = self.dragging
            if globals.current_view.CollidesAny(new_code,include_parent = False):
                if self.last_opacity != 0:
                    new_code.SetOpacity(0.6)
                    self.last_opacity = 0
            else:
                if self.last_opacity != 1:
                    new_code.SetOpacity(1)
                    self.last_opacity = 1
            pos = globals.current_view.GetScreen(pos)
            
            new_code.SetPosAbsolute(new_code.absolute.bottom_left + (pos - dragging))
            self.dragging = (pos,new_code)

    def Hover(self):
        super(CodeCreator,self).Hover()
        globals.current_view.SetHelpText(self.code_class.help)
        
    def EndHover(self):
        super(CodeCreator,self).EndHover()
        globals.current_view.UnshowHelp()

class CodeBar(ui.UIElement):
    def __init__(self,parent,bl,tr):
        super(CodeBar,self).__init__(parent,bl,tr)
        self.backdrop = ui.Box(self,Point(0,0),Point(1,1),colour = drawing.constants.colours.white,buffer=globals.ui_buffer,level = drawing.constants.DrawLevels.ui)
        self.max_num = 12
        self.button_width = 0.08
        self.spacing = (1.0-self.button_width)/(self.max_num+1)
        self.buttons = []

    def AddButton(self,code_class):
        startx = ((self.spacing+self.button_width)*len(self.buttons)) + self.spacing
        endx   = startx + self.button_width
        new_button = CodeCreator(self,Point(startx,0),Point(endx,0.75),code_class)
        self.buttons.append(code_class)
        
        
