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

class Level:
    def __init__(self,leveldict):
        self.__dict__.update(leveldict)
        # sanity check
        if self.hexes[self.start]:
            del self.hexes[self.start]
        for coords in list(self.monsters) + [self.start, self.exit]:
            if coords in self.hexes:
                del self.hexes[coords]

    @property
    def celltypes(self):
        return set(self.hexes.values())

    def save(self,fname):
        f = open(os.path.join("data",fname))
        pickle.dump(f,-1)

    def __setitem__(self,coords,cellcode):
        self.hexes[coords] = cellcode
        
def load_level(fname):
    try:
        with resource.file(fname,"rb") as f:
            return Level(pickle.load(f))
    except resource.ResourceNotFoundException:
        return None




 
 

