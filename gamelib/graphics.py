"""
   Graphics for the Hextrap game
"""
import pickle
from tdgl.gl import *
from tdgl import part, objpart

import collision

# vertical and horizontal spacing of hexagons
Vspace = 3**0.5
Vhalf = Vspace / 2

hexcorners = [ (v.x, v.y) for v in collision.H_CORNER ]
def hex_to_world_coords(col,row):
    x,y,_ = collision.h_centre(col,row)
    return x,y

TILE_OBJECTS = {
    "#":objpart.get_obj("hex.obj"),
    "H":objpart.get_obj("hex.obj"),
}

class CellType(object):
    def __init__(self,n,walkable=False):
        self.n = n
        self.walkable = walkable

class HexagonField(part.Part):
    """A field of hexagonal tiles on a grid, where the 
    centre of hexagons in even columns are at
    x = 1.5u, y = Vspace * v; center of hexagons in odd
    columns are x = 1.5u, y = Vspace * v + Vhalf"""
    def __init__(self,name="",level={},**kw):
        super(HexagonField,self).__init__(name,**kw)
        self.cells = {} # {(u,v):celltype}
        self.obstacles = {}
        self.player_start = (0,0)
        self.build_dl(level)

    def __del__(self):
        glDeleteLists(self.dlbase, self.ndl)

    def build_dl(self,level):
        """Parse the somewhat clunky level definition object,
        and make display lists for each distinct kind of
        tile in the level"""
        self.celltypes = {}
        self.celltypes[" "] = CellType(0,True)
        numtypes = 1
        rows = level.get("body",[])
        v = len(rows)
        for row in rows:
            v -= 1
            for u,cell in enumerate(row.split(",")):
                ct = self.celltypes.get(cell)
                if not ct:
                    n = numtypes
                    walk = cell[:1] in ("","E"," ","S")
                    ct = self.celltypes[cell] = CellType(n,walk)
                    numtypes += 1
                    if cell == "S":
                        self.player_start = (u,v)
                self.cells[u,v] = self.celltypes[cell].n
                if not ct.walkable:
                    self.obstacles[u,v] = cell
        self.ndl = numtypes
        self.dlbase = glGenLists(self.ndl)
        # Compile display lists
        for k,ct in self.celltypes.items():
            with gl_compile(self.dlbase + ct.n):
                # space or player start or enemy
                if k[:1] in ("","E"," ","S"):
                    glLineWidth(1)
                    glColor4f(0,0.4,0.3,0.3)
                    with gl_begin(GL_LINE_LOOP):
                        for x,y in hexcorners:
                            glVertex2f(x,y)
                elif k[0] == "H":  # hexagon tile
                    colour = tuple(0.25*int(c) for c in k[1:])
                    glColor3f(*colour)
                    glCallList(TILE_OBJECTS["H"].mesh_dls["hex"])
                elif k == "#": #wall
                    glColor3f(0.3,0.3,0.3)
                    glCallList(TILE_OBJECTS["#"].mesh_dls["hex"])
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

    def obstacles_near(self,u,v):
        blank = CellType(0,True)
        return [(u+i,v+j,self.obstacles[u+i,v+j])
                for i in range(-2,+3)
                for j in range(-2,+3)
                if (u+i,v+j) in self.obstacles]

    def setup_style(self):
        glEnable(GL_COLOR_MATERIAL)

    def setdown_style(self):
        glDisable(GL_COLOR_MATERIAL)

    def render(self, mode):
        dlbase = self.dlbase
        h2w = hex_to_world_coords
        for (u,v),d in self.cells.items():
            dx,dy = h2w(u,v)
            glTranslatef(dx,dy,0)
            glCallList(dlbase + d)
            glTranslatef(-dx,-dy,0)

