"""
  Monsters!

  "It's all about the monsters."
     -- China Mieville

"""
from math import atan2, degrees, fmod, sin, cos, radians
import random
from tdgl import objpart
from tdgl.gl import *
from tdgl.vec import Vec
import graphics


class Monster(objpart.ObjPart):
    _has_transparent = True
    _style_attributes = ('obj-pieces','obj-filename',
                         'override-mtl','mtl-override-pieces',
                         'frames','rate')
    _default_style = {"rate":100}
    _default_geom = {"radius":0.49}
    harm_type = "monsterated by a"

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
    _default_geom = {"radius":0.7}
    harm_type = "contaminated by a"
    """ On collision with a ball, die"""
    def on_collision(self,what,where,direction):
        if isinstance(what,graphics.Ball):
            self._expired = True
        else:
            self.turn_to(direction)
            self.pos = where

class Wanderer(Monster):
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
        else:
            self.turn_to(direction)
        self.pos = where

class Hunter(Monster):
    """ On collision with a ball, follow the track
    of the ball back towards the player!"""
    def on_collision(self,what,where,direction):
        if isinstance(what,graphics.Ball):
            self.turn_to(what.velocity * -1)
            self.harm_type = "provoked a"
            self.pos = what.pos
        else:
            self.turn_to(direction)
            self.pos = where

MonsterStyles = {
    "Wanderer": {"obj-filename":"crab.obj",
                 "mtl-override-pieces":["Body"],
                 "override-mtl":"Blood"},
    "Hunter": {"obj-filename":"crab.obj",
               "mtl-override-pieces":["Body"],
               "override-mtl":"Chocolate"},
    "Squashy": {"obj-filename":"squelchy.obj",
               "mtl-override-pieces":[],
               "override-mtl":"White"},
    "Monster": {"obj-filename":"crab.obj",
               "mtl-override-pieces":["Body"],
               "override-mtl":"Steel"},
    "Shuttler": {"obj-filename":"crab.obj",
               "mtl-override-pieces":["Body"],
               "override-mtl":"Steel"},
    }
