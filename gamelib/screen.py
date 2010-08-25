"""
Screen module.

The game is divided into Screens
"""
import pickle
import pyglet
from pyglet.window import key as pygletkey
from math import atan2,degrees,radians,sin,cos

from pygame import mixer

from tdgl.gl import *
from tdgl import part, picking, panel, stylesheet, lighting, objpart
from tdgl.viewpoint import OrthoView, SceneView
from tdgl.vec import Vec

import graphics
import collision
import levelfile
import main # for options
from graphics import ClockPart, Ball, Player, ScreenFrame

MUSIC = {
    "title":"data/sound/subterranean.ogg",
    "gameplay":None,
    }

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
        "LabelPanel.storytext": {"font_size":30},
        }

    def __init__(self,name="",**kw):
        super(Screen,self).__init__(name,(),**kw)
        self.build_parts(**kw)
        stylesheet.load(self._screen_styles)
        self.restyle(True)
        self.music = None

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


class GameScreen(Screen):
    _screen_styles = {
        "LabelPanel.onframe": {
            "bg":(0.6,0.5,0.1,1), "fg":(1,1,1,1),
            "font_size":14, "font":"Courier",
            "border":2, "bd":(1,1,1,1),
            "bg_margin":10,"bg_radius":20, "bg_round:":0,
            "bd_margin":10,"bd_radius":20, "bd_round:":0,
            },
        "#player":{ "obj-filename":"crab.obj" },
        "Ball":{"obj-filename":"faceball.obj"},
        }

    def __init__(self,name="",level=None,levelnum=1,score=0,**kw):
        if not level:
            level = self.find_level(levelnum)
        self.level = level
        self.levelnum = levelnum

        self.score = score
        self.light = lighting.claim_light()
        super(GameScreen,self).__init__(name,**kw)
        self.set_mode("playing")
        Sin60 = collision.Sin60
        self.movekeys = {
            # Gamer keys
            pygletkey.A: Vec(-1,0),
            pygletkey.D: Vec(1,0),
            pygletkey.W: Vec(0,1),
            pygletkey.S: Vec(0,-1),

            # Hexagon around J
            pygletkey.H: Vec(-1,0),
            pygletkey.U: Vec(-0.5,Sin60),
            pygletkey.I: Vec(0.5,Sin60),
            pygletkey.K: Vec(1,0),
            pygletkey.M: Vec(0.5,-Sin60),
            pygletkey.N: Vec(-0.5,-Sin60),
            }
        self.keysdown = set()
        self.first_person = False
        vport = (GLint*4)()
        glGetIntegerv(GL_VIEWPORT, vport)
        self.vport = tuple(vport)
        self.reload = 0

            
    def __del__(self):
        lighting.release_light(self.light)

    def set_mode(self,mode):
        self.mode = mode

    def find_level(self,levelnum):
        fname = "level{0:02}.lev".format(levelnum)
        return levelfile.load_level(fname)

    def build_parts(self,**kw):
        ov = ScreenFrame()
        ov.add_label(
            "level_indicator",
            "{0} ({1})".format(self.level.name,self.levelnum))
        ov.add_label("score",
                     "{0:05}".format(self.score),
                     top=False,left=False)
        with ov.compile_style():
            glClearColor(0,0,0,0)
            glDisable(GL_LIGHTING)
        if main.options.time:
            ov.append(ClockPart(geom=dict(pos=(50,50,0))))
        self.append(ov)
        hf = graphics.HexagonField("hexfield",self.level)
        pu,pv = self.level.start
        self.player_exit = self.level.exit
        x,y = graphics.hex_to_world_coords(pu,pv)
        player = Player(name="player",
            geom=dict(pos=(x,y,0),radius=0.49))
        self.player = player
        self.hexfield = hf
        balls = part.Group("balls",[])
        sv = SceneView("scene",[hf,player,balls])
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

    def inc_score(self,points):
        self.score += points
        self["frame"].update_label("score","{0:05}",self.score)

    def add_ball(self,velocity,maxdestroy=4):
        r = 0.2
        ball = Ball(velocity=velocity,
                    maxdestroy=maxdestroy,
                    geom=dict(radius=r))
        player = self.player
        pr = player.getgeom('radius',0.49)
        ball.pos = velocity.normalise() * (r + pr + 0.1) + player.pos
        ball.restyle(True)
        self["balls"].append(ball)
             
    def click(self,x,y,button,mods):
        """ Click to fire """
        if button != 1:
            return
        if self.reload:
            return
        if self.first_person:
            a = radians(self.player.angle)
            v = Vec(cos(a),sin(a)) * 0.01 # per ms
        else:
            vx,vy,vw,vh = self.vport
            v = Vec(x - (vx + vw//2), y - (vy + vh//2)).normalise() * 0.01
        self.add_ball(v)
        self.reload = 500

    def keydown(self,sym,mods):
        self.keysdown.add(sym)
        if sym == pygletkey.F3:
            if self.first_person:
                self.camera.look_from_spherical(87,-90,100,200)
                self.first_person = False
            else:
                self.camera.look_from_spherical(30,self.player.angle + 180,20,200)
                self.first_person = True
        elif sym == pygletkey.ESCAPE:
            self.player_die("boredom")
        elif sym == pygletkey.RETURN:
            a = radians(self.player.angle)
            v = Vec(cos(a),sin(a)) * 0.01 # per ms
            self.add_ball(v)

    def keyup(self,sym,mods):
        try:
            self.keysdown.remove(sym)
        except KeyError:
            pass # never mind

    def step_player(self,ms):
        player = self.player
        if self.keysdown:
            if self.first_person:
                a = self.player.angle
                if pygletkey.LEFT in self.keysdown:
                    a += 10
                if pygletkey.RIGHT in self.keysdown:
                    a -= 10
                theta = radians(a)
                if pygletkey.UP in self.keysdown:
                    v = Vec(cos(theta),sin(theta)) * ms * 0.01
                else:
                    v = Vec(0,0)
                dx,dy,dz = v
                player.angle = a
                self.camera.look_from_spherical(30,a + 180,20,200)
            else:
                z = Vec(0,0)
                v = sum((self.movekeys.get(k,z) for k in self.keysdown),z).normalise() * ms * 0.01
                dx,dy,dz = v
                if dx or dy:
                    a = degrees(atan2(dy,dx))
                    player.angle = a
            if dx or dy:
                # See if player will collide with any hexagons
                px,py,pz = player.pos
                obstacles = self.level.obstacles_near(px,py)
                newpos = v + player.pos
                r = player.getgeom('radius',0.49)
                for hc,hr,cell in obstacles:
                    P = collision.collides(hc,hr,player.pos,r,v,collision.COLLIDE_POSITION)
                    if P:
                        newpos = P
                        break
                player.pos = newpos
                self.camera.look_at(tuple(player.pos))
                # See if player has escaped
                phex = collision.nearest_neighbours(newpos.x,newpos.y,0).next()
                if phex == self.player_exit:
                    level = self.find_level(self.levelnum+1)
                    if level:
                        self.exit_to(GameScreen,score=self.score,level=level,levelnum=self.levelnum+1)
                    else:
                        self.exit_to(VictoryScreen,score=self.score)

    def step_balls(self,ms):
        player = self.player
        pr = player.getgeom('radius',0.49)
        ppos = player.pos
        for ball in self["balls"].contents:
            v = ball.velocity * ms
            bx,by,bz = pos = ball.pos
            newpos = v + pos
            r = ball.getgeom('radius',0.2)
            obstacles = self.level.obstacles_near(bx,by)
            for hc,hr,cell in obstacles:
                P = collision.collides(hc,hr,pos,r,v,collision.COLLIDE_REBOUND)
                if P:
                    newpos, bv_times_ms = P
                    ball.velocity = bv_times_ms * (1/ms)
                    if ball.maxdestroy > 0:
                        points = self.hexfield.destroy(hc,hr)
                        if points:
                            ball.maxdestroy -= 1
                            ball.duration -= 1000
                            self.inc_score(points)
                    break
            ball.pos = newpos
            if (ball.pos - ppos).length() < (r + pr):
                self.player_die("ball trauma")

    def player_die(self,died_of=""):
        self.exit_to(ScoreScreen,score=self.score,died_of=died_of)

    def step(self,ms):
        if self.reload > 0:
            self.reload = max(0,self.reload - ms)
        self.step_player(ms)
        self.step_balls(ms)
        self.step_contents(ms)

class TitleScreen(Screen):

    def build_parts(self,**kw):
        # Playing music in a common function between screens
        mixer.music.load(MUSIC.get("title"))
        mixer.music.play(-1)
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
            self.exit_to(GameScreen)
        elif name == "Quit":
            self.exit_to(None)

class VictoryScreen(Screen):
    victory_text = """After such a terrible ordeal, you creep out
into the sunlight, and make your weary way
home, hoping never again to see another ball
or hexagon in your life..."""
    def __init__(self,score,**kw):
        self.score = score
        super(VictoryScreen,self).__init__(**kw)

    def build_parts(self,**kw):
        mixer.music.stop()
        pn = panel.LabelPanel(
            "the_end", text=self.victory_text,
            geom=dict(pos=(512,400,0),
                      text_width=800),
            style_classes=['storytext'])
        ok_btn = panel.LabelPanel(
            "ok", text=" Finally! ",
            geom=dict(pos=(512,100,0)),
            style_classes=['button'])
        ov = OrthoView(
            "ortho", [pn,ok_btn],
            geom=dict(left=0,right=1024,top=768,bottom=0))
        with ov.compile_style():
            glClearColor(0.1,0.6,0.1,0)
            glDisable(GL_LIGHTING)
        self.append(ov)
        
    def pick(self,label):
        name = label.target._name
        if name == "ok":
            self.exit_to(ScoreScreen,score=self.score)

class ScoreScreen(Screen):
    _screen_styles = {
        "LabelPanel.#finalscore": {
            "bg":None, "fg":(1,1,1,1),
            "font_size":64,
            },
        "LabelPanel.#coroners_report": {
            "bg":(0.9,0.9,0.8,1),"fg":(0,0,0,1),
            "bg_margin":20,
            "font":"Courier",
            "font_size":20 },
        }
    def __init__(self,score,died_of="",**kw):
        self.score = score
        self.died_of = died_of
        super(ScoreScreen,self).__init__(**kw)
        
    def build_parts(self,**kw):
        mixer.music.stop()
        pn = panel.LabelPanel(
            "finalscore", text="Your Score: {0}".format(self.score),
            geom=dict(pos=(512,600,0)))
        ok_btn = panel.LabelPanel(
            "ok", text=" OK ",
            geom=dict(pos=(512,100,0)),
            style_classes=['button'])
        ov = OrthoView(
            "ortho", [pn,ok_btn],
            geom=dict(left=0,right=1024,top=768,bottom=0))
        if self.died_of:
            text = ("CORONER'S REPORT\n"
                    "----------------\n"
                    "Cause of death: {0}").format(self.died_of)
            CoD = panel.LabelPanel(
                "coroners_report",
                text=text,
                geom=dict(pos=(512,300,0),
                          text_width=280))
            ov.append(CoD)
        with ov.compile_style():
            glClearColor(0.1,0,0.1,0)
            glDisable(GL_LIGHTING)
        self.append(ov)
        
    def pick(self,label):
        name = label.target._name
        if name == "ok":
            self.exit_to(TitleScreen)

# Initialisation
Screen.set_next(TitleScreen)
next = Screen.screen_order().next
