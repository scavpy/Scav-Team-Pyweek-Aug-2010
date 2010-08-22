"""
BoxTree is a data structure for storing bounding
boxes, that can be searched for overlap with
a given box more efficiently than linear search.

I hope, anyway.

Works better if you have psyco

This file copyright Peter Harris Feb 2008, released
under the terms of the GNU GPL v3 or later. 
See www.gnu.org for details.

"""

try:
    from psyco import compact as __baseclass
    using_psyco = True
except ImportError:
    using_psyco = False
    __baseclass = object

import itertools

__all__ = "Box","BoxTree"


count_of_inserts = 0
count_of_compares = 0
count_of_creates = 0

def reset_counts():
    global count_of_inserts
    global count_of_compares
    global count_of_creates
    count_of_inserts = 0
    count_of_creates = 0
    count_of_compares = 0

def show_counts():
    print count_of_inserts,"inserts, ",
    print count_of_compares,"compares, ",
    print count_of_creates,"creates"

class Box(__baseclass):
  def __init__(self,ident,mincorner,maxcorner):
      self.identifier = ident
      self.mincorner = mincorner
      self.maxcorner = maxcorner
      assert len(mincorner) == len(maxcorner), "Box with inconsistent dimensions"
      self.dimensions = len(mincorner)

  def extent(self,dim):
      return self.mincorner[dim], self.maxcorner[dim]

  def overlaps(self,other):
      for d in range(min(self.dimensions,other.dimensions)):
          my_min, my_max = self.extent(d)
          o_min, o_max = other.extent(d)
          if my_max < o_min or my_min > o_max:
              return False
      return True

  def __repr__(self):
      return "Box(%r,%r,%r)" % (self.identifier, self.mincorner, self.maxcorner)


class BoxTree(__baseclass):
  def __init__(self):
      self.box = None
      self.less = None # subtree of boxes outside and less
      self.on = None # subtree of boxes overlapping 
      self.gtr = None # subtree of boxes outside and gtr
      self.min = None
      self.max = None
      self.dim = None
      global count_of_creates
      count_of_creates += 1

  def insert(self,box):
      """ insert another bounding box into the tree:
      *  If it's empty, just set box and dimension.
      *  Else put box in one of the subtrees.
      """
      global count_of_inserts
      count_of_inserts += 1  # instrumented for testing
      if self.box is None:
          self.box = box
          extents = [box.extent(d) for d in range(box.dimensions)]
          sizes = sorted((e[1]-e[0],d) for d,e in enumerate(extents))
          size,self.dim = sizes[0] # choose smallest dimension
          self.min, self.max = extents[self.dim]
          return

      my_min, my_max = self.min, self.max
      o_min, o_max = box.extent(self.dim)

      global count_of_compares
      count_of_compares += 1 # instrumented for testing

      if o_max < my_min:  # goes in less-than tree
          if self.less is None: self.less = BoxTree()
          self.less.insert(box)
      elif o_min > my_max: # goes in greater-than tree
          count_of_compares += 1 # instrumented for testing
          if self.gtr is None: self.gtr = BoxTree()
          self.gtr.insert(box)
      else:
          if self.on is None: self.on = BoxTree()
          self.on.insert(box)

  def walk(self):
      """walk through all the boxes in the tree, prefix order"""
      if self.box: yield self.box
      subtrees = []
      if self.less: subtrees.append(self.less.walk())
      if self.on:subtrees.append(self.on.walk())
      if self.gtr: subtrees.append(self.gtr.walk())
      for box in itertools.chain(*subtrees):
          yield box

  def gen_overlaps(self,box):
      """ walk through all the boxes in the tree that might
      overlap with the given one, and yield all those that do"""
      overlaps = self.box.overlaps(box)
      subtrees = []
      global count_of_compares
      count_of_compares += 1
      if overlaps:
          yield self.box
      my_min, my_max = self.min, self.max
      o_min, o_max = box.extent(self.dim)
      # must look in less subtree only if o_min <= my_max
      if o_min <= my_min:
          if self.less: subtrees.append(self.less.gen_overlaps(box))
      # must look in gtr subtree only if o_max >= my_max
      if o_max >= my_max:
          if self.gtr: subtrees.append(self.gtr.gen_overlaps(box))
      # must check 'on' subtree always
      if self.on: subtrees.append(self.on.gen_overlaps(box))
      for box in itertools.chain(*subtrees):
          yield box

  def __str__(self):
      return "BoxTree(%r,%r,%r,%r)" % (self.box, self.dim, self.min, self.max)

def test(N):
    import random
    boxes = []
    for i in range(N):
        x = random.randint(0,500)
        y = random.randint(0,500)
        z = random.randint(0,100)
        w = random.randint(0,50)
        h = random.randint(0,20)
        l = random.randint(0,50)
        boxes.append(Box(i,(x,y,z),(x+w,y+l,z+h)))
    tree = BoxTree()
    reset_counts()
    print "inserting",N,"boxes"
    for b in boxes:
        tree.insert(b)
    show_counts()
    M = max(min(N // 10,100),2)
    print "searching for overlaps with",M,"randomly chosen boxes"
    all_compares = []
    all_overlaps = []
    for bx in random.sample(boxes,M):
        reset_counts()
        overlappers = list(tree.gen_overlaps(bx))
        all_compares.append(count_of_compares)
        all_overlaps.append(len(overlappers))
    mean_compares = sum(all_compares) / float(M)
    print "Mean compares", mean_compares
    print "Mean overlaps", sum(all_overlaps) / float(M)
    stddev = (sum((c - mean_compares)**2 for c in all_compares) / M)**0.5
    print "Standard deviation of compares", stddev
