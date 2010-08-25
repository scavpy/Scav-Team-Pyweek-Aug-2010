"""
 Level Representation:

 {"name": level_name,
  "story": [story_text],
  "hexes": { (col,row): cell_code },
  "start": (col,row),
  "exit": (col,row),
  "monsters": { (col,row): monster_code },
 }

 Cell code
 ---------
 ' ' : a walkable hex of floor
 'Hxxx' : A hexagon that can be destroyed. xxx is the colour. 
 '^','<','>','v','#': Various kinds of indestructible wall.

 Monster Code
 ------------
 Monster class name

"""
import os
from pyglet import resource
import pickle
import copy

import collision

class Level:
    _defaults = {
        "name":"a level",
        "story":[],
        "hexes":{},
        "start":(0,0),
        "exit":(2,0),
        "monsters":{}}
    def __init__(self,leveldict=_defaults):
        self.__dict__.update(copy.deepcopy(leveldict))
        # sanity check
        for coords in list(self.monsters):
            if coords in self.hexes:
                del self.hexes[coords]
        self.hexes[self.start] = "S"
        self.hexes[self.exit] = "X"

    @property
    def celltypes(self):
        return set(self.hexes.values())

    def save(self,fname):
        d = dict(name=self.name, story=self.story,
                 start=self.start, exit=self.exit,
                 hexes=self.hexes, monsters=self.monsters)
        with open(os.path.join("data",fname),"wb") as f:
            pickle.dump(d,f,-1)

    def __setitem__(self,coords,cellcode):
        self.hexes[coords] = cellcode

    def obstacles_near(self,x,y):
        return [(hc,hr,self.hexes[hc,hr])
                for hc,hr in collision.nearest_neighbours(x,y,2)
                if self.hexes.get((hc,hr)," ") not in " SX"]

    def destroy(self,hc,hr):
        """Destroy the hexagon at hc,hr.
        Return false if not possible"""
        c = self.hexes.get((hc,hr)," ")
        if c[0] != "H":
            return False
        self.hexes[hc,hr] = " "
        return c

        
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
 
 

