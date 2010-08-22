"""
   Graphics for the Hextrap game
"""
from tdgl.gl import *
from tdgl import part

# vertical and horizontal spacing of hexagons
Vspace = 3**0.5
Vhalf = Vspace / 2

hexcorners = [(1,0),(0.5,Vhalf),
              (-0.5,Vhalf),(-1,0),
              (-0.5,-Vhalf),(0.5,-Vhalf)]

class HexagonField(part.Part):
    """A field of hexagonal tiles on a grid, where the 
    centre of hexagons in even columns are at
    x = 1.5u, y = Vspace * v; center of hexagons in odd
    columns are x = 1.5u, y = Vspace * v + Vhalf"""
    def __init__(self,name="",hextypes=(),**kw):
        super(HexagonField,self).__init__(name,**kw)
        self.hextypes = list(hextypes)
        self.build_dl()

    def __del__(self):
        glDeleteLists(self.dlbase, self.ndl)

    def build_dl(self):
        self.ndl = max(len(self.hextypes),1)
        self.dlbase = glGenLists(self.ndl)
        # hex type 0 is a blank outlined hexagon
        with gl_compile(self.dlbase):
            glColor3f(0,0.8,0.5)
            with gl_begin(GL_LINE_LOOP):
                for x,y in hexcorners:
                    glVertex2f(x,y)

    def render(self, mode):
        # STUB just one hexagon
        glCallList(self.dlbase)
