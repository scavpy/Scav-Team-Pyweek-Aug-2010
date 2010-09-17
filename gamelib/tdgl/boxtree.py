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
    from psyco import compact as _BASE
    _USING_PSYCO = True
except ImportError:
    _USING_PSYCO = False
    _BASE = object

import random
import itertools

__all__ = "Box","BoxTree"


class Counts(object):
    """ container for 3 counts """
    __slots__ = ('inserts', 'compares', 'creates')
    def __init__(self):
        self.inserts = 0
        self.compares = 0
        self.creates = 0
    def clear(self):
        """ reset counts """
        self.inserts = 0
        self.compares = 0
        self.creates = 0
    def __str__(self):
        return "{0} ins, {1} comp, {2} creat".format(
            self.inserts, self.compares, self.creates)

COUNTS = Counts()

class Box(_BASE):
    """ A bounding box defined by 2 opposite corners """
    if not _USING_PSYCO:
        __slots__ = ('ident', 'mincorner', 'maxcorner', 'dimensions')

    def __init__(self, ident, mincorner, maxcorner):
        self.ident = ident
        self.mincorner = mincorner
        self.maxcorner = maxcorner
        assert len(mincorner) == len(maxcorner), "Inconsistent dimensions"
        self.dimensions = len(mincorner)

    def bounds(self, dim):
        """ bounds of a box along one dimension """
        return self.mincorner[dim], self.maxcorner[dim]

    def overlaps(self, other):
        """ whether bounding box overlaps another """
        for d in range(min(self.dimensions, other.dimensions)):
            my_min, my_max = self.bounds(d)
            o_min, o_max = other.bounds(d)
            if my_max < o_min or my_min > o_max:
                return False
        return True

    def __repr__(self):
        return "Box(%r,%r,%r)" % (self.ident, self.mincorner, self.maxcorner)

class BoxTree(_BASE):
    """ A ternary tree of Boxes.
    Each level of the tree subdivides into three subtrees of boxes that
    are greater than, less than or overlapping on one dimension. """
    def __init__(self):
        self.box = None
        self.less = None # subtree of boxes outside and less
        self.ovl = None # subtree of boxes overlapping 
        self.gtr = None # subtree of boxes outside and gtr
        self.min = None
        self.max = None
        self.dim = None
        COUNTS.creates += 1

    def insert(self, box):
        """ insert another bounding box into the tree:
        *  If it's empty, just set the box as self.box
        *  Else put box in one of the subtrees.
        """
        COUNTS.inserts += 1  # instrumented for testing
        if self.box is None:
            self.box = box
            return

        # if self.dim not set yet, have a free choice about it, so
        # try to pick one that puts new box in either less or gtr trees
        if self.dim is None:
            for d in range(self.box.dimensions):
                my_min, my_max = self.box.bounds(d)
                o_min, o_max = box.bounds(d)
                if o_max < my_min or o_min > my_max:
                    self.dim = d
                    self.min = my_min
                    self.max = my_max
                    break
            if self.dim is None:
                self.dim = random.randint(0, self.box.dimensions - 1)
                self.min, self.max = self.box.bounds(self.dim)

        my_min, my_max = self.min, self.max
        o_min, o_max = box.bounds(self.dim)

        COUNTS.compares += 1 # instrumented for testing

        if o_max < my_min:  # goes in less-than tree
            if self.less is None: 
                self.less = BoxTree()
            self.less.insert(box)
        elif o_min > my_max: # goes in greater-than tree
            COUNTS.compares += 1 # instrumented for testing
            if self.gtr is None:
                self.gtr = BoxTree()
            self.gtr.insert(box)
        else:
            if self.ovl is None:
                self.ovl = BoxTree()
            self.ovl.insert(box)

    def walk(self):
        """walk through all the boxes in the tree, prefix order"""
        if self.box:
            yield self.box
        subtrees = []
        if self.less:
            subtrees.append(self.less.walk())
        if self.ovl:
            subtrees.append(self.ovl.walk())
        if self.gtr:
            subtrees.append(self.gtr.walk())
        for box in itertools.chain(*subtrees):
            yield box

    def gen_overlaps(self, box):
        """ walk through all the boxes in the tree that might
        overlap with the given one, and yield all those that do"""
        overlaps = self.box.overlaps(box)
        subtrees = []
        COUNTS.compares += 1
        if overlaps:
            yield self.box
        if self.dim is None:
            raise StopIteration
        my_min, my_max = self.min, self.max
        o_min, o_max = box.bounds(self.dim)
        # must look in less subtree only if o_min <= my_max
        if o_min <= my_min and self.less:
            subtrees.append(self.less.gen_overlaps(box))
        # must look in gtr subtree only if o_max >= my_max
        if o_max >= my_max and self.gtr:
            subtrees.append(self.gtr.gen_overlaps(box))
        # must check 'ovl' subtree always
        if self.ovl:
            subtrees.append(self.ovl.gen_overlaps(box))
        for box in itertools.chain(*subtrees):
            yield box

    def __str__(self):
        return "BoxTree(%r,%r,%r,%r)" % (self.box, self.dim, self.min, self.max)

def test(numboxes):
    """ Run a test to profile number of comparisons, creates and inserts """
    boxes = []
    def rint(n):
        """ random.randint(0, n) """
        return random.randint(0, n)

    def rbox(i):
        """ make a random Box """
        x = rint(1000)
        y = rint(1000)
        z = rint(100)
        return Box(i, (x, y, z), (x+rint(50), y+rint(50), z+rint(10)))

    for i in range(numboxes):
        boxes.append(rbox(i))
    tree = BoxTree()
    COUNTS.clear()
    print "inserting", numboxes, "boxes"
    for b in boxes:
        tree.insert(b)
    print COUNTS
    numchecks = max(min(numboxes // 10, 100), 2)
    print "searching for overlaps with", numchecks, "randomly chosen boxes"
    all_compares = []
    all_overlaps = []
    for bx in random.sample(boxes, numchecks):
        COUNTS.clear()
        overlappers = list(tree.gen_overlaps(bx))
        all_compares.append(COUNTS.compares)
        all_overlaps.append(len(overlappers))
    mean_compares = sum(all_compares) / float(numchecks)
    print "Mean compares", mean_compares
    print "Mean overlaps", sum(all_overlaps) / float(numchecks)
    stddev = (sum((c - mean_compares)**2 
                  for c in all_compares) / numchecks)**0.5
    print "Standard deviation of compares", stddev
    print tree
