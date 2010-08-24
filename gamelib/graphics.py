"""
   Graphics for the Hextrap game
"""
import pickle
from tdgl.gl import *
from tdgl import part, objpart, viewpoint, panel
from tdgl.vec import Vec

import collision

# vertical and horizontal spacing of hexagons
Vspace = 3**0.5
Vhalf = Vspace / 2

hexcorners = [ (v.x, v.y) for v in collision.H_CORNER ]
def hex_to_world_coords(col,row):
    x,y,_ = collision.h_centre(col,row)
    return x,y

TILE_OBJECTS = {
    "#":objpart.get_obj("wall.obj"),
    "H":objpart.get_obj("hex.obj"),
    "^":objpart.get_obj("nwall.obj"),
    "v":objpart.get_obj("swall.obj"),
    ">":objpart.get_obj("ewall.obj"),
    "<":objpart.get_obj("wwall.obj"),
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
        self.player_exit = (1,1)
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
                    walk = cell[:1] in ("","E"," ","S","X")
                    ct = self.celltypes[cell] = CellType(n,walk)
                    numtypes += 1
                    if cell == "S":
                        self.player_start = (u,v)
                    elif cell == "X":
                        self.player_exit = (u,v)
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
                elif k[0] in "#^v<>": #wall
                    glColor3f(0.7,0.7,0.7)
                    glCallList(TILE_OBJECTS[k[0]].mesh_dls["hex"])
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
        self.all_dl = glGenLists(1)

    def obstacles_near(self,x,y):
        return [(hc,hr,self.obstacles[hc,hr])
                for hc,hr in collision.nearest_neighbours(x,y,2)
                if (hc,hr) in self.obstacles]

    def setup_style(self):
        glEnable(GL_COLOR_MATERIAL)

    def setdown_style(self):
        glDisable(GL_COLOR_MATERIAL)

    def render(self, mode):
        glCallList(self.all_dl)

    def prepare(self):
        with gl_compile(self.all_dl):
            dlbase = self.dlbase
            h2w = hex_to_world_coords
            for (u,v),d in self.cells.items():
                dx,dy = h2w(u,v)
                glTranslatef(dx,dy,0)
                glCallList(dlbase + d)
                glTranslatef(-dx,-dy,0)

    def destroy(self,hc,hr):
        """Destroy the hexagon at hc,hr.
        Return false if not possible"""
        c = self.obstacles.get((hc,hr))
        if not c or c[0] != "H":
            return False
        del self.obstacles[hc,hr]
        self.cells[hc,hr] = 0 # blank
        self.prepare()
        return 10 # points?

class ClockPart(part.Part):
    clock = pyglet.clock.ClockDisplay()
    def __init__(self,name="clock",**kw):
        super(ClockPart,self).__init__(name,**kw)
    def render(self,mode):
        if mode != "PICK":
            self.clock.draw()

class Player(objpart.ObjPart):
    _default_geom = {'radius':0.49}
    pass

class Ball(objpart.ObjPart):
    _default_geom = {'radius':0.2}

    def __init__(self,velocity=(0,0),duration=6000,maxdestroy=3,**kw):
        super(Ball,self).__init__('',**kw)
        self.velocity = Vec(velocity)
        self.duration = duration
        self.maxdestroy = maxdestroy

    def step(self,ms):
        self.duration -= ms
        if self.duration < 0:
            self._expired = True


class ScreenFrame(viewpoint.OrthoView):
    def __init__(self,name="frame",contents=(),**kw):
        super(ScreenFrame,self).__init__(name,contents,**kw)

    def add_label(self,name,text,top=True,left=True,**kw):
        lab = panel.LabelPanel(
            name, text=text, 
            style_classes = ['onframe'])
        w,h = lab.content_size()
        x = w // 2 + 16
        y = h // 2 + 16
        if top:
            y = 768 - y
        if not left:
            x = 1024 - x
        lab.pos = (x,y,0.1)
        self.append(lab)

    def update_label(self,name,text,*args):
        lab = self[name]
        lab.text = text.format(*args)
        lab.prepare()
