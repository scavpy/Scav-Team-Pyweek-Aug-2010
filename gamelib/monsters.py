"""
  Monsters!

  "It's all about the monsters."
     -- China Mieville

"""
from math import atan2, degrees, fmod, sin, cos, radians
import random
from tdgl import objpart, animator, lighting
from tdgl.gl import *
from tdgl.vec import Vec
import graphics
import sounds
import collision


class Monster(objpart.ObjPart):
    _has_transparent = True
    _style_attributes = ('obj-pieces','obj-filename',
                         'override-mtl','mtl-override-pieces',
                         'frames','rate')
    _default_style = {"rate":100}
    _default_geom = {"radius":0.49}
    harm_type = "monsterated by a"
    speed = 1.0

    def __init__(self,name='',frame=0,velocity=(0,0,0),level=None,**kw):
        super(Monster,self).__init__(name,**kw)
        self.frame = frame
        self.count = self.getstyle("rate")
        self.velocity = Vec(velocity)

    def prepare(self):
        super(Monster,self).prepare()
        frames = self.getstyle("frames",{})
        self.count = self.getstyle("rate")
        framelist = sorted(frames.items())
        self.framelist = framelist[:self.frame] + framelist[self.frame:]
        if self.framelist:
            self.pieces = self.framelist[0][1]
        else:
            self.pieces = self.obj.pieces()

    def step(self,ms):
        super(Monster,self).step(ms)
        self.count -= ms
        if self.count < 0:
            self.count = self.getstyle("rate")
            if self.framelist:
                f,pieces = self.framelist.pop(0)
                self.framelist.append((f,pieces))
                self.pieces = pieces

    def turn_to(self,v):
        self.angle = degrees(atan2(v.y,v.x))
        self.velocity = v

    def on_collision(self,what,where,direction):
        """Decide what to do after a collision
        (change direction, die etc.)"""
        self.pos = where
        self.turn_to(direction)
        
class Shuttler(Monster):
    """On any collision, just reverse direction"""
    def on_collision(self,what,where,direction):
        self.angle = fmod(self.angle + 180,360)
        self.velocity *= -1
        self.pos = where

class Squashy(Monster):
    _default_geom = {"radius":0.49}
    speed = 0.6
    harm_type = "contaminated by a"
    """ On collision with a ball, die"""
    def on_collision(self,what,where,direction):
        if isinstance(what,graphics.Ball):
            self._expired = True
            sounds.play("squelch")
        else:
            self.turn_to(direction)
            self.pos = where

class Wanderer(Monster):
    _default_geom = {"radius":0.3}
    speed = 0.8
    """ On collision with a ball, pick a random
    direction and speed"""

    def on_collision(self,what,where,direction):
        if isinstance(what,graphics.Ball):
            r = self.velocity.length()
            if r < 0.001 or r > 0.04:
                r = 0.01
            r *= random.gauss(1.0,0.05)
            self.angle = random.random() * 360
            a = radians(self.angle)
            self.velocity = Vec(cos(a),sin(a)) * r
            sounds.play("chime")
        else:
            self.turn_to(direction)
        self.pos = where

class Hunter(Monster):
    """ On collision with a ball, follow the track
    of the ball back towards the player!"""
    def hunt(self,what,where,factor=1.0):
        self.turn_to(what.velocity * -factor)
        self.pos = what.pos
        # Eat the ball!
        what._expired = True

    def eat(self,what,direction):
        self.turn_to(direction)
        self.velocity = Vec(0,0,0)

    def on_collision(self,what,where,direction):
        if isinstance(what,graphics.Ball):
            self.harm_type = "provoked a"
            sounds.play("roar")
            self.hunt(what,where)
        elif isinstance(what,graphics.Player):
            self.eat(what,direction)
            sounds.play("munch")
        else:
            self.turn_to(direction)
            self.pos = where

class Mimic(Hunter):
    """ Hides until hit, then goes on a short rampage,
    then goes back into hiding"""
    def __init__(self,name,**kw):
        self.mimic_obj=None
        self.real_obj=None
        self.real_pieces=()
        self.hiding = True
        self.rage = 0
        super(Mimic,self).__init__(name,**kw)
        self.velocity = Vec(0,0,0)

    def prepare(self):
        super(Mimic,self).prepare()
        self.real_obj = self.obj
        self.real_pieces = self.pieces
        fname = self.getstyle("mimic-filename","wall.obj")
        self.mimic_obj = objpart.get_obj(fname)
        if self.hiding:
            self.obj = self.mimic_obj
            self.pieces = self.mimic_obj.pieces()

    def enrage(self):
        self.rage = 10
        self.hiding = False
        self.prepare()

    def on_collision(self,what,where,direction):
        if isinstance(what,graphics.Ball):
            self.hunt(what,where,1.1)
            self.harm_type = "provoked a"
            sounds.play("roar")
            self.enrage()
        elif isinstance(what,graphics.Player):
            self.eat(what,direction)
            sounds.play("munch")
        else:
            self.turn_to(direction)
            self.pos = where
            self.rage -= 1
            if self.rage <= 0:
                self.hiding = True
                x,y,_ = where
                hc,hr = collision.nearest_neighbours(x,y,0).next()
                self.pos = collision.h_centre(hc,hr)
                self.velocity = Vec(0,0,0)
                self.prepare()

    def step(self,ms):
        super(Mimic,self).step(ms)
        if self.hiding:
            self.pieces = self.mimic_obj.pieces()

class Balrog(Hunter):
    _default_geom = {"radius":0.4}
    speed = 0.5
    """ Like a Hunter, but on collision with a wall,
    if the direction is facing roughly towards the
    player, head directly towards the player """

    def __init__(self,name='',**kw):
        super(Balrog,self).__init__(name,**kw)
        self.dark = lighting.claim_light()
        lighting.light_colour(self.dark,(0.1,-0.3,-0.3,1.0))
        x,y,z = self.pos
        lighting.light_position(self.dark,(x,y,1.0,1.0))
        lighting.light_switch(self.dark,True)

    def __del__(self):
        lighting.release_light(self.dark)

    def on_collision(self,what,where,direction):
        if isinstance(what,graphics.Ball):
            self.harm_type = "provoked the"
            sounds.play("rumble")
            self.hunt(what,where,0.9)
        elif isinstance(what,graphics.Player):
            self.eat(what,direction)
            sounds.play("bellow")
        else:
            r = self.velocity.length()
            to_player = Vec(self.player.pos) - self.pos
            if to_player.dot(direction) > 0:
                # facing towards player...
                direction = to_player.normalise() * r
                if random.random < 0.2:
                    sounds.play("rumble")
            self.pos = where
            self.turn_to(direction)

    def step(self,ms):
        super(Balrog,self).step(ms)
        x,y,z = self.pos
        lighting.light_position(self.dark,(x,y,1.0,1.0))


MonsterStyles = {
    "Wanderer": {"obj-filename":"wanderer.obj",
                 "mtl-override-pieces":["Swirly1","Swirly2","Swirly3","Swirly4"],
                 "override-mtl":"Chocolate",
                 "frames":{"1":["Spiky1","Swirly1"],
                           "2":["Spiky2","Swirly2"],
                           "3":["Spiky3","Swirly3"],
                           "4":["Spiky4","Swirly4"]},
                 "rate":100},
    "Hunter": {"obj-filename":"hunter.obj",
               "mtl-override-pieces":["Eye"],
               "override-mtl":"Jade",
               "frames":{"1":["Body","Legs","Eye","Pincers1"],
                         "2":["Body","Legs","Eye","Pincers2"],
                         "3":["Body","Legs","Eye","Pincers3"],
                         "4":["Body","Legs","Eye","Pincers2"]},
               "rate":100,},
    "Mimic": {"obj-filename":"hunter.obj",
              "mtl-override-pieces":["Eye"],
              "override-mtl":"Blood",
              "frames":{"1":["Body","Legs","Eye","Pincers1"],
                        "2":["Body","Legs","Eye","Pincers2"],
                        "3":["Body","Legs","Eye","Pincers3"],
                        "4":["Body","Legs","Eye","Pincers2"]},
              "rate":100,
              "mimic-filename":"wall.obj"},
    "Squashy": {"obj-filename":"squelchy.obj",
                "mtl-override-pieces":[],
                "override-mtl":"White"},
    "Monster": {"obj-filename":"crab.obj",
                "mtl-override-pieces":["Body"],
                "override-mtl":"Steel"},
    "Balrog": {"obj-filename":"balrog.obj",
               "frames":{"1":["Step0"],
                         "2":["Step1"],
                         "3":["Step0"],
                         "4":["Step2"]},
               "rate":300},
    "Shuttler": {"obj-filename":"crab.obj",
                 "mtl-override-pieces":["Body"],
                 "frames":{"1":["Body","LPincer","RPincer","LFlipper","RFlipper","Legs1"],
                           "2":["Body","LPincer","RPincer","LFlipper","RFlipper","Legs2"]},
                 "rate":100,
                 "override-mtl":"Steel"},
    }
