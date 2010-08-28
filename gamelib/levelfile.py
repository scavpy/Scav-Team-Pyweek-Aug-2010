"""
 Level Representation:

 {"name": level_name,
  "story": [story_text],
  "hexes": { (col,row): cell_code },
  "start": (col,row),
  "exit": (col,row),
  "monsters": { (col,row): monster_code },
  "sound": sfx_name,
  "music": music_name,
  "powerups": { (col,row): ball_code },
  "bg":  background colour for screen frame,
  "bd":  edge colour for screen frame,
  "fg":  foreground colour for screen frame text,
 }

 Cell code
 ---------
 ' ' : a walkable hex of floor
 'Hxxx' : A hexagon that can be destroyed. xxx is the colour. 
 '^','<','>','v','#': Various kinds of indestructible wall.


 Monster Code
 ------------
 Monster class name


 Ball Code
 ----------
 Ball class name

"""
import os
from pyglet import resource
import pickle
import copy
import re

import collision

HEXPOINTS = {
    "Pt":1000,
    "Au":750,
    "Ag":500,
    "Cu":250,
    "H000":150,
    "H000f":150,
    "Hfff":100,
    "Hffff":100,
    }

class Level:
    def __init__(self,leveldict=None):
        self.name = "a level"
        self.story = []
        self.hexes = {}
        self.start = (2,2)
        self.exit = (8,8)
        self.sound = None
        self.music = None
        self.monsters = {}
        self.powerups = {}
        self.bg = (0.6,0.5,0.2,1)
        self.bd = (0.3,0.1,0.1,1)
        self.fg = (1,1,1,1)
        if leveldict:
            self.__dict__.update(copy.deepcopy(leveldict))
        self.hexes[self.start] = "S"
        self.hexes[self.exit] = "X"

    @property
    def celltypes(self):
        return set(self.hexes.values())

    def save(self,fname):
        d = dict(name=self.name, story=self.story,
                 start=self.start, exit=self.exit,
                 hexes=self.hexes, monsters=self.monsters,
                 sound=self.sound, powerups=self.powerups,
                 music=self.music, bg=self.bg, fg=self.fg, bd=self.bd)
        with open(os.path.join("data",fname),"wb") as f:
            pickle.dump(d,f,-1)

    def __setitem__(self,coords,cellcode):
        self.hexes[coords] = cellcode

    def obstacles_near(self,x,y):
        return [(hc,hr,self.hexes[hc,hr])
                for hc,hr in collision.nearest_neighbours(x,y,2)
                if self.hexes.get((hc,hr)," ") not in " SXOP"]
    
    def hexpoints(self,hex):
        p = HEXPOINTS.get(hex)
        if p:
            return p
        if hex.startswith("H"):
            if len(hex) == 4:
                h,r,g,b = hex
                a = "f"
            else:
                h,r,g,b,a = hex
            if r == g == b:
                return 5
            elif re.match("H[f0][f0][f0]",hex):
                return 50
            elif "f" in (r,g,b):
                return 20
            else:
                return 10
        else:
            return False

    def destroy(self,hc,hr):
        """Destroy the hexagon at hc,hr.
        Return false if not possible"""
        c = self.hexes.get((hc,hr)," ")
        points = self.hexpoints(c)
        if c in ["Cu","Ag","Au","Pt"]:
            s = "ring"
        elif c.startswith("H"):
            if len(c) == 5 and c[4] < "f":
                s = "tinkle"
            else:
                s = "crunch"
        if not points:
            return False
        self.hexes[hc,hr] = " "
        return (points,s)

    def collect(self,hc,hr):
        """Collect powerup at hc,hr
        Return None if nothing there"""
        p = self.powerups.get((hc,hr))
        if p:
            self.hexes[hc,hr] = " "
            del self.powerups[hc,hr]
        return p
            

        
def load_level(fname):
    try:
        with resource.file(fname,"rb") as f:
            return Level(pickle.load(f))
    except resource.ResourceNotFoundException:
        try:
            with open(fname,"rb") as f:
                return Level(pickle.load(f))
        except IOError:
            return None
 
 

