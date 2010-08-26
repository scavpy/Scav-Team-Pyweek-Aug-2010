"""
   Graphics for the Hextrap game
"""
import pickle
from tdgl.gl import *
from tdgl import part, objpart, viewpoint, panel
from tdgl.vec import Vec

import collision, levelfile

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
    "O":objpart.get_obj("trickwall.obj"),
}

def cellcolour(cellcode):
    c = cellcode[:1]
    if c == " ":
        return (0,0.5,0.5,0.5)
    elif c in "#<>^vO":
        return (0.5,0.5,0.5,1)
    elif c == "H":
        rgba = [int(x,16) / 15.0 for x in cellcode[1:4]] + [1]
        return tuple(rgba)
    else:
        return (1,1,1,1)


class CellType(object):
    def __init__(self,n,walkable=False):
        self.n = n
        self.walkable = walkable

class HexagonField(part.Part):
    """A field of hexagonal tiles on a grid, where the 
    centre of hexagons in even columns are at
    x = 1.5u, y = Vspace * v; center of hexagons in odd
    columns are x = 1.5u, y = Vspace * v + Vhalf"""
    def __init__(self,name,level,**kw):
        super(HexagonField,self).__init__(name,**kw)
        self.level = level
        self.ndl = 0
        self.dlbase = None
        self.build_dl()

    def __del__(self):
        glDeleteLists(self.dlbase, self.ndl)

    def build_dl(self):
        """Parse the somewhat clunky level definition object,
        and make display lists for each distinct kind of
        tile in the level"""
        level = self.level
        self.cells = {} # {(u,v):dl_offset}
        if self.ndl:
            glDeleteLists(self.dlbase, self.ndl)
        # first display list is a blank cell
        self.celltypes = {' ':CellType(0,True)}
        for i,ct in enumerate(sorted(level.celltypes)):
            self.celltypes[ct] = CellType(i+1,ct in " SXO")
        numtypes = len(level.celltypes)
        for coords,cellcode in level.hexes.items():
            ct = self.celltypes[cellcode]
            self.cells[coords] = ct.n
        self.ndl = numtypes
        self.dlbase = glGenLists(self.ndl)
        # Compile display lists
        for k,ct in self.celltypes.items():
            with gl_compile(self.dlbase + ct.n):
                # space or player start
                if k[0] in " S":
                    glLineWidth(1 if k[0] == " " else 3)
                    glColor4f(*cellcolour(k))
                    with gl_begin(GL_LINE_LOOP):
                        for x,y in hexcorners:
                            glVertex2f(x,y)
                elif k[0] == "H":  # hexagon tile
                    glColor4f(*cellcolour(k))
                    glCallList(TILE_OBJECTS["H"].mesh_dls["hex"])
                elif k[0] in "#^v<>O": #wall
                    glColor4f(*cellcolour(k))
                    glCallList(TILE_OBJECTS[k[0]].mesh_dls["hex"])
                elif k[0] == "X":  # exit
                    glColor4f(*cellcolour(k))
                    glLineWidth(3)
                    with gl_begin(GL_LINES): # STUB
                        for x,y in [
                            (-0.5,-0.5), (0.5,0.5),
                            (-0.5,0.5), (0.5,-0.5)]:
                            glVertex2f(x,y)
                else:
                    pass # TODO the rest
        self.all_dl = glGenLists(1)

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
        c = self.level.destroy(hc,hr)
        if c:
            self.cells[hc,hr] = 0 # blank
            self.prepare()
            return 10

class StoryPanel(panel.LabelPanel):
    _default_geom = {"pos":(512,400,0),
                     "text_width":800 }
    def __init__(self,name,text,**kw):
        init = super(StoryPanel,self).__init__
        init(name,text=text,
             style_classes=["storytext"],**kw)
    def content_size(self):
        return 800, self.label.content_height


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
    lethal = True
    speed = 0.01
    duration = 6000
    maxdestroy = 3
    bounces = True

    def __init__(self,direction,**kw):
        super(Ball,self).__init__('',**kw)
        self.velocity = Vec(direction).normalise() * self.speed

    def step(self,ms):
        self.duration = self.duration - ms
        if self.duration < 0:
            self._expired = True

class BlitzBall(Ball):
    _default_geom = {'radius':0.2}
    duration = 1000
    speed = 0.02
    
class BowlingBall(Ball):
    _default_geom = {'radius':0.4}
    speed = 0.005
    duration = 10000
    maxdestroy = 8

class HappyBall(Ball):
    _default_geom = {'radius':0.2}
    lethal = False
    maxdestroy = float('inf')
    duration = float('inf')

class SpikeBall(Ball):
    _default_geom = {'radius':0.2}
    maxdestroy = 6
    bounces = False
    duration = 8000

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
