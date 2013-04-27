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
        print self.points
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

class OutputButton(Connector):
    arrow_offset = Point(0.45,0)
    def OnClick(self,pos,button):
        if button == 1:
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
          

class CodePrimitive(ui.UIElement):
    line_peturb = 0.5
    def __init__(self,parent,pos,tr,colour):
        self.colour = colour
        self.next = None
        self.prev = None
        super(CodePrimitive,self).__init__(parent,pos,tr)
        self.title_bar = ui.TitleBar(self,Point(0,0.9),Point(1,1),self.title,colour = self.colour,buffer=globals.colour_tiles)
        self.content = ui.Box(self,Point(0,0),Point(1,0.9),colour = drawing.constants.colours.dark_grey,buffer = globals.colour_tiles)
        self.border = [drawing.Line(globals.line_buffer) for i in 0,1,2,3]
        self.connectors = []
        if self.input:
            self.input = InputButton(self,Point(0,0.4),Point(0.2,0.6)) 
            self.connectors.append( self.input )
        if self.output:
            self.output = OutputButton(self,Point(0.8,0.4),Point(1.0,0.6)) 
            self.connectors.append( self.output )

        self.UpdatePosition()
        self.SetColour(self.colour)
        self.symbol = self.Symbol(self.content,Point(0,0),Point(1,1))

    def UpdateConnectedLineForward(self):
        if self.next:
            #we own the line pointing to the next guy
            self.output.connector_line.SetVertices(self.output.GetAbsolute(Point(0.5,0.5)),self.next.input.GetAbsolute(Point(0.5,0.5)),drawing.constants.DrawLevels.ui)
            
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

class Increment(CodePrimitive):
    title  = "Increment"
    Symbol = TextSymbolCreator("+1")
    input  = True
    output = True
