"""
Screen module.

The game is divided into Screens
"""
import pickle
import random
import pyglet
from pyglet.window import key as pygletkey
from math import atan2,degrees,radians,sin,cos

from tdgl.gl import *
from tdgl import part, picking, panel, stylesheet, lighting, objpart
from tdgl.viewpoint import OrthoView, SceneView
from tdgl.vec import Vec

import graphics
import collision
import levelfile
import monsters
import main # for options
from graphics import ClockPart, Ball, Player, ScreenFrame, StoryPanel, ScreenBorder
from graphics import BlitzBall, BowlingBall, SpikeBall, HappyBall
import sounds

class Screen(part.Group):
    _next = None
    _screen_styles = {
        "LabelPanel.button": {
            "bg":(1,1,1,1), "fg":(0,0,0,1),
            "texture":"data/models/gold.png",
            "font_size":32,
            "border":2, "bd":(1,1,1,1),
            "bg_margin":18,"bg_radius":42, "bg_round:":0,
            "bd_margin":18,"bd_radius":42, "bd_round:":0,
            },
        "LabelPanel": { "font":"ExperiMental" },
        "StoryPanel.storytext": {
            "font_size":30, "font":"ExperiMental",
            "fg":(1,1,1,1),
            "bg_margin":30,
            "border":None,
            "bg":(0,0,0,0.5)},
        }
    music = None
    last_music = None

    def __init__(self,name="",**kw):
        super(Screen,self).__init__(name,(),**kw)
        self.build_parts(**kw)
        stylesheet.load(self._screen_styles)
        self.restyle(True)
        if self.music != Screen.last_music:
            if self.music:
                sounds.music_start(self.music)
            else:
                sounds.music_fade(1000)
            Screen.last_music = self.music

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
    music = "gameplay"
    _screen_styles = {
        "LabelPanel.onframe": {
            "bg":(1,1,1,1), "fg":(1,1,1,1),
            "texture":"data/models/copper.png",
            "texture_repeat":0.2,
            "font_size":14, "font":"Courier",
            "border":3, "bd":(0.4,0.2,0.2,1),
            "bg_margin":10,"bg_radius":20, "bg_round:":0,
            "bd_margin":10,"bd_radius":20, "bd_round:":0,
            },
        "#player":{"obj-filename":"thedetective.obj",
                   "obj-pieces":["Body","Hat","Feet0","Eyes"],
                   "mtl-override-pieces":["Body"],
                   "override-mtl":"Purple"},
        }

    def __init__(self,name="",level=None,levelnum=1,score=0,
                 ammo=0,special=None, **kw):
        if not level:
            level = self.find_level(levelnum)
        self.level = level
        self.levelnum = levelnum
        self.score = score
        self.light = lighting.claim_light()
        stylesheet.load(monsters.MonsterStyles)
        stylesheet.load(graphics.BallStyles)
        if level.music:
            self.music = level.music
        self.special_ammo = ammo
        self.special_ball = special
        super(GameScreen,self).__init__(name,**kw)
        self.set_mode("story" if self.story_page is not None
                      else "playing")
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
        sounds.play(self.level.sound)
            
    def __del__(self):
        lighting.release_light(self.light)

    def set_mode(self,mode):
        self.mode = mode

    def find_level(self,levelnum):
        fname = "level{0:02}.lev".format(levelnum)
        return levelfile.load_level(fname)

    def build_parts(self,**kw):
        level = self.level
        if self.special_ball:
            ammo_name = self.special_ball.__name__
        else:
            ammo_name = None
        border = ScreenBorder(
            "hud",
            title=level.name,
            score=self.score,
            ammo=self.special_ammo,
            ammo_name=ammo_name,
            style=dict(fg=level.fg,bg=level.bg,bd=level.bd))
        ov = ScreenFrame("frame", [border])
        with ov.compile_style():
            glClearColor(0,0,0,0)
            glDisable(GL_LIGHTING)
        if main.options.time:
            ov.append(ClockPart(geom=dict(pos=(50,50,0))))
        if level.story:
            ov.append(StoryPanel("story",level.story[0]))
            self.story_page = 0
        else:
            self.story_page = None
        self.append(ov)
        hf = graphics.HexagonField("hexfield",self.level)
        pu,pv = level.start
        self.player_exit = level.exit
        x,y = graphics.hex_to_world_coords(pu,pv)
        player = Player(name="player",
            geom=dict(pos=(x,y,0),radius=0.49))
        self.player = player
        self.hexfield = hf
        balls = part.Group("balls",[])
        monsters = part.Group("monsters",
                              self.build_monsters(self.level))
        powerups = part.Group("powerups",
                              self.build_powerups(self.level))
        sv = SceneView("scene",[monsters,hf,player,balls,powerups])
        sv.camera.look_at((x,y,1),10)
        sv.camera.look_from_spherical(87,-90,300)
        sv.camera.look_from_spherical(80,-90,100,1000)
        self.camera = sv.camera
        self.camera.step(1)
        with sv.compile_style():
            glEnable(GL_LIGHTING)
        lighting.light_position(self.light,(10,10,10,0))
        lighting.light_colour(self.light,(1,1,1,1))
        lighting.light_switch(self.light,True)
        self.append(sv)
        
    def build_monsters(self,level):
        ms = []
        count = 0
        for coords, classname in level.monsters.items():
            pos = collision.h_centre(*coords)
            M = getattr(monsters,classname,monsters.Monster)
            if classname == "Hunter" or coords == level.exit:
                vel = Vec(0,0)
            else: # random direction and speed
                vel = (random.choice(collision.H_NORMAL) *
                       random.gauss(M.speed,0.02) * 0.01)
            m = M("{0}{1}".format(classname,count),
                  velocity=vel,
                  geom=dict(pos=pos,angle=0))
            if classname == "Balrog":
                # The Balrog knows where you are.
                m.player = self.player
            count += 1
            ms.append(m)
        return ms

    def build_powerups(self,level):
        ps = []
        for coords, classname in level.powerups.items():
            pos = collision.h_centre(*coords)
            P = getattr(graphics,classname,graphics.Ball)
            p = P(repr(coords), geom=dict(pos=pos,angle=0))
            p.duration = float('inf')
            ps.append(p)
        return ps


    def dismiss_story_page(self):
        s = self.story_page + 1
        pn = self["story"]
        if s < len(self.level.story):
            pn.text = self.level.story[s]
            pn.prepare()
            self.story_page = s
        else:
            self["frame"].remove(pn)
            self.set_mode("playing")
        
    def setup_style(self):
        lighting.setup()

    def inc_score(self,points):
        self.score += points
        self["hud"].set_score(self.score)

    def add_ball(self,direction,Kind=Ball):
        ball = Kind(direction=direction)
        r = ball.getgeom("radius")
        player = self.player
        pr = player.getgeom('radius',0.49)
        ball.pos = ball.velocity.normalise() * (r + pr + 0.1) + player.pos
        ball.restyle(True)
        self["balls"].append(ball)
             
    def click(self,x,y,button,mods):
        """ Click to fire """
        if button not in (1,4):
            return
        if self.mode == "dying":
            return
        if self.mode == "story":
            self.dismiss_story_page()
            return
        if self.reload:
            return
        if button == 4:
            if self.special_ammo <= 0:
                return
            self.special_ammo -= 1
            self["hud"].set_ammo(self.special_ammo,
                                 self.special_ball.__name__)
        if self.first_person:
            a = radians(self.player.angle)
            v = Vec(cos(a),sin(a))
        else:
            vx,vy,vw,vh = self.vport
            v = Vec(x - (vx + vw//2), y - (vy + vh//2))
        kind = (self.special_ball if button == 4 else Ball)
        self.add_ball(direction=v,Kind=kind)
        self.reload = 300

    def keydown(self,sym,mods):
        if self.mode == "dying":
            return
        if self.mode == "story":
            self.dismiss_story_page()
            return
        self.keysdown.add(sym)
        if sym == pygletkey.F3:
            if self.first_person:
                self.camera.look_from_spherical(80,270,100,200)
                self.first_person = False
            else:
                self.camera.look_from_spherical(2,self.player.angle + 180,2,200)
                self.first_person = True
        elif sym == pygletkey.ESCAPE:
            self.player_die("boredom")
        elif sym == pygletkey.RETURN:
            a = radians(self.player.angle)
            v = Vec(cos(a),sin(a)) * 0.01 # per ms
            self.add_ball(v)
            self.reload = 300

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
                strafe = 0
                if pygletkey.Q in self.keysdown:
                    strafe = a+90
                elif pygletkey.E in self.keysdown:
                    strafe = a-90
                if pygletkey.A in self.keysdown:
                    a += 5
                if pygletkey.D in self.keysdown:
                    a -= 5
                theta = radians(a)
                if pygletkey.W in self.keysdown:
                    v = Vec(cos(theta),sin(theta)) * ms * 0.01
                elif pygletkey.S in self.keysdown:
                    v = Vec(cos(theta),sin(theta)) * ms * -0.01
                else:
                    v = Vec(0,0)
                if strafe:
                    A = radians(strafe)
                    v += Vec(cos(A),sin(A)) * ms * 0.01
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
                    sounds.play("fanfare")
                    if self.levelnum > 0:
                        levelnum = self.levelnum + 1
                    else:
                        levelnum = self.levelnum - 1
                    level = self.find_level(levelnum)
                    if level:
                        self.exit_to(GameScreen,score=self.score,level=level,
                                     levelnum=levelnum,ammo=self.special_ammo,
                                     special=self.special_ball)
                    else:
                        self.exit_to(VictoryScreen,score=self.score)
                elif phex in self.level.powerups:
                    bname = self.hexfield.collect(*phex)
                    if bname:
                        B = getattr(graphics,bname)
                        if B == self.special_ball:
                            self.special_ammo += B.ammo
                        else:
                            self.special_ball = B
                            self.special_ammo = B.ammo
                        sounds.play("chamber")
                        self["hud"].set_ammo(self.special_ammo, 
                                             self.special_ball.__name__)
                        b = self[repr(phex)]
                        if b:
                            self["powerups"].remove(b)

    def step_balls(self,ms):
        player = self.player
        dying = (self.mode == "dying")
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
                    vel = bv_times_ms * (1/ms)
                    if ball.maxdestroy > 0 and not dying:
                        points = self.hexfield.destroy(hc,hr)
                        if points:
                            sounds.play(points[1])
                            ball.maxdestroy -= 1
                            ball.duration -= 1000
                            self.inc_score(points[0])
                            if not ball.bounces:
                                vel = ball.velocity
                    ball.velocity = vel
                    break
            ball.pos = newpos
            if (ball.lethal
                and not dying 
                and (ball.pos - ppos).length() < (r + pr)):
                self.player_die("ball trauma")

    def step_monsters(self,ms):
        player = self.player
        dying = (self.mode == "dying")
        pr = player.getgeom('radius',0.49)
        ppos = Vec(player.pos)
        for mon in self["monsters"].contents:
            v = mon.velocity * ms
            mx,my,mz = pos = mon.pos
            newpos = v + pos
            r = mon.getgeom('radius',0.49)
            obstacles = self.level.obstacles_near(mx,my)
            collided = False
            for hc,hr,cell in obstacles:
                P = collision.collides(hc,hr,pos,r,v,collision.COLLIDE_REBOUND)
                if P:
                    newpos, mv_times_ms = P
                    velocity = mv_times_ms * (1/ms)
                    mon.on_collision(None,newpos,velocity)
                    collided = True
                    break
            if not dying:
                for ball in self["balls"].contents:
                    br = ball.getgeom("radius")
                    if (ball.pos - newpos).length() < (r + br):
                        mon.on_collision(ball,newpos,mon.velocity)
                        collided = True
                        break
            if mon._expired:
                return
            if not collided:
                mon.pos = newpos
            if not dying and (mon.pos - ppos).length() < (r + pr):
                mon.on_collision(player,newpos,(ppos - mon.pos)*0.01)
                self.player_die("{0} {1}".format(
                        mon.harm_type,
                        mon.__class__.__name__))

    def player_die(self,dying_of=""):
        sounds.play("pain")
        self.set_mode("dying")
        self.dying_of = dying_of
        self.dying_time = 3000
        lighting.light_colour(self.light,(0,0,0,0),self.dying_time)

    def step(self,ms):
        if ms == 0:
            return
        lighting.step(ms)
        if self.mode == "story":
            return
        if self.reload > 0:
            self.reload = max(0,self.reload - ms)
        self.step_monsters(ms)
        self.step_balls(ms)
        self.step_contents(ms)
        if self.mode == "dying":
            if self.dying_time <= 0:
                self.exit_to(ScoreScreen,
                             score=self.score,
                             levelnum=self.levelnum,
                             died_of=self.dying_of)
            else:
                self.dying_time -= ms
        else:
            self.step_player(ms)

class TitleScreen(Screen):
    music = "title"

    def __del__(self):
        lighting.release_light(self.light)

    def build_parts(self,**kw):
        self.light = lighting.claim_light()
        stylesheet.load(monsters.MonsterStyles)
        stylesheet.load(graphics.BallStyles)
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
            geom=dict(left=0,right=1024,top=768,bottom=0,far=1000),
            style={"ClearColor":(0,0,0,0)})
        if main.options.time:
            ov.append(ClockPart(geom=dict(pos=(50,50,0))))
        with ov.compile_style():
            glDisable(GL_LIGHTING)
        self.append(ov)
        sv = SceneView("scene")
        self.level = level = levelfile.load_level("title.lev")
        hf = graphics.HexagonField("hexfield",level)
        sv.append(hf)
        for coords, classname in level.monsters.items():
            pos = collision.h_centre(*coords)
            M = getattr(monsters,classname,monsters.Monster)
            m = M(classname, geom=dict(pos=pos,angle=0))
            sv.append(m)
        for coords, classname in level.powerups.items():
            pos = collision.h_centre(*coords)
            M = getattr(graphics,classname,graphics.Ball)
            m = M(classname, geom=dict(pos=pos,angle=0))
            m.duration = float('inf')
            sv.append(m)
        sv.camera.look_at(pos,10)
        sv.camera.look_from_spherical(45,270,70)
        sv.camera.step(1)
        self.camera = sv.camera
        with sv.compile_style():
            glEnable(GL_LIGHTING)
        lighting.light_position(self.light,(10,10,10,0))
        lighting.light_colour(self.light,(1,1,1,1))
        lighting.light_switch(self.light,True)
        self.append(sv)

    def setup_style(self):
        lighting.setup()

    def step(self,ms):
        self.step_contents(ms)
        lighting.step(ms)
        self.camera.step(ms)
        if self.camera.animator.finished():
            hexlist = [self.level.start, self.level.exit]
            hexlist.extend(self.level.monsters.keys())
            poslist = [tuple(collision.h_centre(*coords))
                       for coords in hexlist]
            poslist.append(poslist[0])
            steplist = [10000 for coords in hexlist]
            steplist.append(1000)
            self.camera.animator.sequence("looking_at",poslist,steplist)

    def pick(self,label):
        name = label.target._name
        if name == "Start":
            lev = main.options.test_level
            if lev is None:
                lev = 1
            self.exit_to(GameScreen,levelnum=lev)
        elif name == "Quit":
            self.exit_to(None)

    def keydown(self,sym,mods):
        if sym == pygletkey.F3:
            self.exit_to(GameScreen,levelnum=0,level=self.level)

class VictoryScreen(Screen):
    victory_text = """After such a terrible ordeal, you creep out
into the sunlight, and make your weary way
home, hoping never again to see another ball
or hexagon in your life...

Or you could hit F3 at the title screen. Enjoy."""
    def __init__(self,score,**kw):
        self.score = score
        super(VictoryScreen,self).__init__(**kw)

    def build_parts(self,**kw):
        pn = StoryPanel("the_end", text=self.victory_text)
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
    def __init__(self,score,died_of="",levelnum=None,**kw):
        self.score = score
        self.died_of = died_of
        self.levelnum = levelnum
        super(ScoreScreen,self).__init__(**kw)
        
    def build_parts(self,**kw):
        pn = panel.LabelPanel(
            "finalscore", text="Your Score: {0}".format(self.score),
            geom=dict(pos=(512,600,0)))
        ov = OrthoView(
            "ortho", [pn],
            geom=dict(left=0,right=1024,top=768,bottom=0))
        if self.levelnum is None:
            quit_btn = panel.LabelPanel(
                "ok", text=" OK ",
                geom=dict(pos=(512,100,0)),
                style_classes=['button'])
            ov.append(quit_btn)
        else:            
            retry_btn = panel.LabelPanel(
                "retry", text=" Try Again ",
                geom=dict(pos=(412,100,0)),
                style_classes=['button'])
            quit_btn = panel.LabelPanel(
                "ok", text=" Give Up ",
                geom=dict(pos=(712,100,0)),
                style_classes=['button'])
            ov.append(retry_btn)
            ov.append(quit_btn)
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
        elif name == "retry":
            self.exit_to(GameScreen,levelnum=self.levelnum)

# Initialisation
Screen.set_next(TitleScreen)
next = Screen.screen_order().next
