"""
   Graphics for the Hextrap game
"""
import pickle
from tdgl.gl import *
from tdgl import part

# vertical and horizontal spacing of hexagons
Vspace = 3**0.5
Vhalf = Vspace / 2

hexcorners = [(1,0),(0.5,Vhalf),
              (-0.5,Vhalf),(-1,0),
              (-0.5,-Vhalf),(0.5,-Vhalf)]

def hex_to_world_coords(u,v):
    return u*1.5, v*Vspace + Vhalf * (u%2)

class HexagonField(part.Part):
    """A field of hexagonal tiles on a grid, where the 
    centre of hexagons in even columns are at
    x = 1.5u, y = Vspace * v; center of hexagons in odd
    columns are x = 1.5u, y = Vspace * v + Vhalf"""
    def __init__(self,name="",level={},**kw):
        super(HexagonField,self).__init__(name,**kw)
        self.cells = {} # {(u,v):celltype}
        self.player_start = (0,0)
        self.build_dl(level)

    def __del__(self):
        glDeleteLists(self.dlbase, self.ndl)

    def build_dl(self,level):
        """Parse the somewhat clunky level definition object,
        and make display lists for each distinct kind of
        tile in the level"""
        self.celltypes = {}
        self.celltypes[" "] = 0
        numtypes = 1
        rows = level.get("body",[])
        v = len(rows)
        for row in rows:
            v -= 1
            for u,cell in enumerate(row.split(",")):
                if cell not in self.celltypes:
                    self.celltypes[cell] = numtypes
                    numtypes += 1
                    if cell == "S":
                        self.player_start = (u,v)
                self.cells[u,v] = self.celltypes[cell]
        self.ndl = numtypes
        self.dlbase = glGenLists(self.ndl)
        # Compile display lists
        for k,n in self.celltypes.items():
            with gl_compile(self.dlbase + n):
                if k in (""," ","S"): # space or player start
                    glLineWidth(1)
                    glColor4f(0,0.4,0.3,0.3)
                    with gl_begin(GL_LINE_LOOP):
                        for x,y in hexcorners:
                            glVertex2f(x,y)
                elif k[0] == "H":  # hexagon tile
                    colour = tuple(0.25*int(c) for c in k[1:])
                    glColor3f(*colour)
                    with gl_begin(GL_POLYGON): # STUB
                        for x,y in hexcorners:
                            glVertex2f(x,y)
                elif k[0] == "X":  # exit
                    glColor3f(1,1,1)
                    glLineWidth(3)
                    with gl_begin(GL_LINES): # STUB
                        for x,y in [
                            (-0.5,-0.5), (0.5,0.5),
                            (-0.5,0.5), (0.5,-0.5)]:
                            glVertex2f(x,y)
                else:
                    pass # TODO the rest

    def render(self, mode):
        dlbase = self.dlbase
        h2w = hex_to_world_coords
        for (u,v),d in self.cells.items():
            dx,dy = h2w(u,v)
            glTranslatef(dx,dy,0)
            glCallList(dlbase + d)
            glTranslatef(-dx,-dy,0)

