"""
Screen module.

The game is divided into Screens
"""
import pickle
import pyglet
from pyglet.window import key as pygletkey
from math import atan2,degrees

from tdgl.gl import *
from tdgl import part, picking, panel, stylesheet, lighting, objpart
from tdgl.viewpoint import OrthoView, SceneView
from tdgl.vec import Vec

import graphics
import collision
import main # for options

class Screen(part.Group):
    _next = None
    _screen_styles = {
        "LabelPanel.button": {
            "bg":(0,0.8,0.5,1), "fg":(0,0,0,1),
            "font_size":32,
            "border":2, "bd":(1,1,1,1),
            "bg_margin":18,"bg_radius":42, "bg_round:":0,
            "bd_margin":18,"bd_radius":42, "bd_round:":0,
            },
        "LabelPanel": { "font":"ExperiMental" },
        }

    def __init__(self,name="",**kw):
        super(Screen,self).__init__(name,(),**kw)
        self.build_parts(**kw)
        stylesheet.load(self._screen_styles)
        self.restyle(True)

    @staticmethod
    def screen_order():
        while Screen._next:
            yield Screen._next

    @staticmethod
    def set_next(C ,*args, **kw):
        del Screen._next
        Screen._next = (C(*args,**kw) if C else None)

    def exit_to(self, C, *args, **kw):
        Screen.set_next(C,*args,**kw)
        self._expired = True
        self.cleanup()

    def setup_geom(self): pass
    def setdown_geom(self): pass
    def build_parts(self,**kw): pass
    def keydown(self,sym,mods): pass
    def keyup(self,sym,mods): pass

    def resize(self,width,height):
        self.size = width,height
        for g in self.contents:
            if hasattr(g,'resize'):
                g.resize(width,height)

    def pick_at(self,x,y):
        """Pick topmost object at x,y"""
        picking.start(x,y,1,1)
        self.draw('PICK')
        objects = picking.end()
        if objects:
            minz,maxz,label = objects[0]
            self.pick(label)

    def click(self,x,y,button,mods):
        """ Default behaviour is pick """
        if button != 1:
            return
        self.pick_at(x,y)

    def pick(self,label):
        pass

    def cleanup(self):
        pass

class ClockPart(part.Part):
    clock = pyglet.clock.ClockDisplay()
    def __init__(self,name="clock",**kw):
        super(ClockPart,self).__init__(name,**kw)
    def render(self,mode):
        if mode != "PICK":
            self.clock.draw()

class Player(objpart.ObjPart):
    pass

class GameScreen(Screen):
    _screen_styles = {
        "#level_indicator": {
            "bg":(0.6,0.5,0.1,1), "fg":(1,1,1,1),
            "font_size":14, "font":"Courier",
            "border":2, "bd":(1,1,1,1),
            "bg_margin":10,"bg_radius":20, "bg_round:":0,
            "bd_margin":10,"bd_radius":20, "bd_round:":0,
            },
        "#player" : {
            "obj-filename":"crab.obj"
            },
        }

    def __init__(self,name="",level=None,**kw):
        self.level = level
        self.light = lighting.claim_light()
        super(GameScreen,self).__init__(name,**kw)
        self.set_mode("playing")
        self.movekeys = {
            pygletkey.A: Vec(-1,0),
            pygletkey.D: Vec(1,0),
            pygletkey.W: Vec(0,1),
            pygletkey.S: Vec(0,-1),
            }
        self.keysdown = set()
        self.first_person = False
            
    def __del__(self):
        lighting.release_light(self.light)

    def cleanup(self):
        """ remove attributes that may have circular references
        to self (e.g. bound methods of same instance) """
        try:
            del self.click
            del self.keyup
            del self.step
            del self.keydown
        except NameError:
            pass

    def set_mode(self,mode):
        for handler in ["keydown","keyup","click","step"]:
            f = getattr(self,handler + "_" + mode)
            if f:
                setattr(self,handler,f)

    def build_parts(self,**kw):
        lev = panel.LabelPanel(
            "level_indicator",
            text="Level 01",multiline="True",
            geom=dict(pos=(60,730,0)))                
        ov = OrthoView("frame",[lev])
        with ov.compile_style():
            glClearColor(0,0,0,0)
            glDisable(GL_LIGHTING)
        if main.options.time:
            ov.append(ClockPart(geom=dict(pos=(50,50,0))))
        self.append(ov)
        hf = graphics.HexagonField("hexfield",self.level)
        pu,pv = hf.player_start
        x,y = graphics.hex_to_world_coords(pu,pv)
        player = Player(name="player",
            geom=dict(pos=(x,y,0)))
        self.player = player
        self.hexfield = hf
        sv = SceneView("scene",[hf,player])
        sv.camera.look_at((x,y,0),10)
        sv.camera.look_from_spherical(87,-90,300)
        sv.camera.look_from_spherical(87,-90,100,1000)
        self.camera = sv.camera
        with sv.compile_style():
            glEnable(GL_LIGHTING)
        lighting.light_position(self.light,(10,10,10,0))
        lighting.light_colour(self.light,(1,1,1,1))
        lighting.light_switch(self.light,True)
        self.append(sv)
        
    def setup_style(self):
        lighting.setup()

    def click_playing(self,x,y,button,mods):
        """ Click to fire """
        if button != 1:
            return
        #STUB exit on click
        self.exit_to(TitleScreen)

    def keydown_playing(self,sym,mods):
        self.keysdown.add(sym)
        if sym == pygletkey.F3:
            if self.first_person:
                self.camera.look_from_spherical(87,-90,100,200)
                self.first_person = False
            else:
                self.camera.look_from_spherical(30,self.player.angle + 180,20,200)
                self.first_person = True

    def keyup_playing(self,sym,mods):
        try:
            self.keysdown.remove(sym)
        except KeyError:
            pass # never mind

    def step_playing(self,ms):
        player = self.player
        if self.keysdown:
            z = Vec(0,0)
            v = sum((self.movekeys.get(k,z) for k in self.keysdown),z) * ms * 0.01
            dx,dy,dz = v
            if dx or dy:
                a = degrees(atan2(dy,dx))
                player.angle = a
                if self.first_person:
                    self.camera.look_from_spherical(30,a + 180,20,200)
                # See if player will collide with any hexagons
                px,py,pz = player.pos
                obstacles = self.hexfield.obstacles_near(px,py)
                newpos = v + player.pos
                for hc,hr,cell in obstacles:
                    P = collision.collides(hc,hr,player.pos,0.8,v,collision.COLLIDE_POSITION)
                    if P:
                        newpos = P
                        break
                player.pos = newpos
                self.camera.look_at(tuple(player.pos))

        self.step_contents(ms)

class TitleScreen(Screen):

    def build_parts(self,**kw):
        start_btn = panel.LabelPanel(
            "Start", text=" Start ",
            geom=dict(pos=(512,200,0)),
            style_classes=['button'])
        quit_btn = panel.LabelPanel(
            "Quit", text=" Quit ",
            geom=dict(pos=(512,100,0)),
            style_classes=['button'])
        ov = OrthoView(
            "ortho", [start_btn, quit_btn],
            geom=dict(left=0,right=1024,top=768,bottom=0))
        if main.options.time:
            ov.append(ClockPart(geom=dict(pos=(50,50,0))))
        with ov.compile_style():
            glClearColor(0.2,0,0,0)
            glDisable(GL_LIGHTING)
        self.append(ov)

    def pick(self,label):
        name = label.target._name
        if name == "Start":
            with pyglet.resource.file("level01.lev") as lf:
                level = pickle.load(lf)
            self.exit_to(GameScreen, level=level)
        elif name == "Quit":
            self.exit_to(None)
        else:
            print label

# Initialisation
Screen.set_next(TitleScreen)
next = Screen.screen_order().next
