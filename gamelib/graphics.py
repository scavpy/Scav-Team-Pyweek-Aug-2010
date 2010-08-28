"""
   Graphics for the Hextrap game
"""
import pickle
import pyglet
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
    "Au":objpart.get_obj("goldhex.obj"),
    "Ag":objpart.get_obj("silverhex.obj"),
    "Cu":objpart.get_obj("copperhex.obj"),
    "Pt":objpart.get_obj("plathex.obj"),
    "L":objpart.get_obj("lava.obj"),
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
                elif k in ["Au","Ag","Cu","Pt"]:
                    glColor4f(1.0,1.0,1.0,1.0)
                    glCallList(TILE_OBJECTS[k].mesh_dls["hex"])
                elif k[0] in "#^v<>OL": #wall
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
                elif k[0] == "P": #powerup square
                    with gl_begin(GL_TRIANGLE_FAN):
                        glColor4f(1.0,1.0,0.0,1.0)
                        glVertex2f(0,0)
                        glColor4f(0.5,0.0,0.0,0.1)
                        for x,y in hexcorners:
                            glVertex2f(x,y)
                        glVertex2f(*hexcorners[0])

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
            return c

    def collect(self,hc,hr):
        """Collect the powerup at hc,hr
        Return false if not possible"""
        p = self.level.collect(hc,hr)
        if p:
            self.cells[hc,hr] = 0 # blank
            self.prepare()
        return p


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

BallStyles = {
    "Ball":{ "obj-filename":"prismball.obj" },
    "BlitzBall":{ "obj-filename":"blitzball.obj" },
    "BowlingBall":{ "obj-filename":"bowlingball.obj" },
    "SpikeBall":{ "obj-filename":"spikeball.obj" },
    "HappyBall":{ "obj-filename":"faceball.obj" },
}

class Ball(objpart.ObjPart):
    _default_geom = {'radius':0.2}
    lethal = True
    speed = 0.01
    duration = 6000
    maxdestroy = 4
    bounces = True
    ammo = 1

    def __init__(self,name='',direction=None,**kw):
        super(Ball,self).__init__(name,**kw)
        if direction:
            self.velocity = Vec(direction).normalise() * self.speed
        else:
            self.velocity = Vec(0,0,0)

    def step(self,ms):
        self.duration = self.duration - ms
        if self.duration < 0:
            self._expired = True

class BlitzBall(Ball):
    _default_geom = {'radius':0.2}
    duration = 1000
    speed = 0.02
    ammo = 5
    
class BowlingBall(Ball):
    _default_geom = {'radius':0.4}
    speed = 0.005
    duration = 10000
    maxdestroy = 8
    ammo = 3

class HappyBall(Ball):
    _default_geom = {'radius':0.2}
    lethal = False
    maxdestroy = float('inf')
    duration = float('inf')
    ammo = 1

class SpikeBall(Ball):
    _default_geom = {'radius':0.2}
    maxdestroy = 6
    bounces = False
    duration = 8000
    ammo = 4

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

class ScreenBorder(part.Part):
    _default_geom={"width":1024,"height":768}
    _default_style={"texture":"copper.png",
                    "border":3, "bd":(0.4,0.2,0.2,1),
                    "margin":8,"fg":(1,1,1,1),
                    "texture_repeat":0.2,
                    "font_size":14, "font":"Courier"}
    _style_attributes = tuple(_default_style.keys())
    
    def __init__(self,name,title="",score=0,ammo=0,ammo_name=None,**kw):
        super(ScreenBorder,self).__init__(name,**kw)
        self.frame_dl = glGenLists(1)
        self.ammo_obj = None
        self.title_label = None
        self.score_label = None
        self.ammo = ammo
        self.title = title
        self.ammo_name = ammo_name
        self.score = score

    def prepare(self):
        self.prepare_title()
        self.prepare_score()
        self.prepare_ammo()
        self.prepare_frame()

    def set_score(self,score):
        self.score = score
        self.prepare_score()

    def set_title(self,title):
        self.title = title
        self.prepare_title()
        self.prepare_frame()

    def set_ammo(self,ammo,ammo_name):
        self.ammo = ammo
        self.ammo_name = ammo_name
        self.prepare_ammo()
        self.prepare_frame()

    def prepare_title(self):
        getstyle = self.getstyle
        font = getstyle("font")
        font_size = getstyle("font_size")
        self.title_label = pyglet.text.Label(
            text=self.title,
            font_name=font, font_size=font_size,
            color=[int(c*255) for c in getstyle("fg")],
            anchor_x='left',anchor_y='bottom')

    def prepare_score(self):
        getstyle = self.getstyle
        font = getstyle("font")
        font_size = getstyle("font_size")
        self.score_label = pyglet.text.Label(
            text="{0:06}".format(self.score),
            font_name=font, font_size=font_size,
            color=[int(c*255) for c in getstyle("fg")],
            anchor_x='left',anchor_y='top')

    def prepare_frame(self):
        getstyle = self.getstyle
        m = getstyle("margin")
        w = self.getgeom("width")
        h = self.getgeom("height")
        tw = self.title_label.content_width
        th = self.title_label.content_height
        sw = self.score_label.content_width
        sh = self.score_label.content_height
        title_poly = [
            (0,0), (tw+th,0), (tw+th,m), (tw,th+m), (0, th+m)]
        score_poly = [
            (0,h), (0,h-sh-m), (sw,h-sh-m), (sw+sh, h-m), (sw+sh, h)]
        inner_line = [
            (m,th+m),(tw,th+m),(tw+th,m),(w-m,m),(w-m,h-m),
            (sw+sh,h-m), (sw,h-sh-m), (m, h-sh-m) ]
        with gl_compile(self.frame_dl):
            glColor4f(0.6,0.3,0.3,1)
            for p in [title_poly,score_poly]:
                with gl_begin(GL_POLYGON):
                    for (x,y) in p:
                        glVertex2f(x,y)
            glRectf(0,0,m,h)
            glRectf(w-m,0,w,h)
            glRectf(0,0,w,m)
            glRectf(0,h-m,w,h)
            glLineWidth(getstyle("border"))
            glColor4f(*getstyle("bd"))
            with gl_begin(GL_LINE_LOOP):
                for x,y in inner_line:
                    glVertex2f(x,y)
        
    def prepare_ammo(self):
        pass

    def render(self,mode):
        if mode == "PICK":
            return
        h = self.getgeom("height")
        m = self.getstyle("margin")
        glCallList(self.frame_dl)
        glPushMatrix()
        glTranslatef(m//2,m//2,0.05)
        self.title_label.draw()
        glTranslatef(0,h-m,0)
        self.score_label.draw()
        glPopMatrix()
