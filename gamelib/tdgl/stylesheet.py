#! /usr/bin/env python
"""stylesheet.py - obtain style for tdlib objects in a manner analogous to CSS, only not as good

  Copyright 2007 Peter Harris
  
  Released under the terms of the GNU General Public License v3 or later
"""
from math import pi, sin, cos

def generalisations(seq):
    """generate sequences starting with the one given, and then shorter
    ones made by removing elements, firstly from the end.
    a b c, a b, a c, a, b c, b, c, ()
    """
    if not seq:
        yield seq
    else:
        last = seq[-1:]
        for s in generalisations(seq[:-1]):
            if last: yield s + last
            yield s

DefaultRules = {
    '':{
        'background-colour':(0,0,0,1),
        'colour':(1,1,1,1),
        }
    }
    
class StyleSheet(object):
    """A repository of style information retrieved using a simplified
    form of CSS selectors.
    
    The stylesheet is loaded using load() method, from a dictionary of
    dictionaries. The outer dictionary is indexed by selectors, the inner
    ones are indexed by attribute.
    
    Selector syntax:
        optional id beginning with '#'
        zero or more style classes beginning with '.'
    e.g.
        "#justin.left.leg"
    
    Since it is expensive to break down selectors into lists, sort them,
    make subsets of them and so on, the list of stylesheet selectors matching
    a selector for an object is cached.
    
    """
    def __init__(self,rules=DefaultRules):
        self.clear()
        if rules:
            self.load(rules)
    def selector_list(self,selector):
        """Make a list of valid candidate selectors from a given selector"""
        seq = selector.split('.')
        seq.sort()
        if seq[0] == '#': # invalid, '#' with no id
            del seq[0]
        slist = ['.'.join(sel) for sel in generalisations(seq)]
        return [ key for key in slist if key in self.rules ]
    def canonical_selector(self,selector):
        """To keep the combinations down, assume parts of a selector can
        be sorted without loss of meaning"""
        slist = selector.split('.')
        slist.sort()
        if slist[0] == '#': # invalid, '#' with no id
            del slist[0]
        return '.'.join(slist)
    def load(self,rules,update=True):
        """Load stylesheet rules in the form of a nested dict.
        If update is false, the stylesheet is cleared first"""
        if not update:
            self.clear()
        for sel,adict in rules.items():
            sel = self.canonical_selector(sel)
            self.rules.setdefault(sel,dict()).update(adict)
        # rebuild the cache of selectors for the new rules
        for csel in self.selector_cache:
            slist = self.selector_list(csel)
            self.selector_cache[csel] = slist
    def get(self,selector,*attributes,**renamed):
        """Get an attribute from whatever rule matches most specifically,
        or in the general case return a dictionary of attribute:value
        entries for a list of attributes, possibly renamed.
        
        If called to get one attribute, a value is always returned (None if
        no value found.
        If called to get a dict of attributes, ones not found will have no
        entry in the dict. This is so you can safely update from the dict
        without trashing your default values with Nones.
        """
        try:
            selectors = self.selector_cache[selector]
        except KeyError:
            selectors = self.selector_list(selector)
            self.selector_cache[selector] = selectors
        def getone(attr):
            """get one attribute from the most specific selector that has it"""
            for sel in selectors:
                try:
                    return self.rules[sel][attr]
                except KeyError:
                    continue
            raise KeyError  # to dostinguish between no entry and 'None'
        if len(attributes) == 1 and not renamed:
            try:
                return getone(attributes[0])
            except KeyError:
                return None # have to return some value
        values={}
        for a in attributes:
            try:
                values[a] = getone(a)
            except KeyError:
                pass
        for k,a in renamed.items():
            try:
                values[k] = getone(a)
            except KeyError:
                pass
        return values
    def clear(self):
        self.selector_cache={}
        self.rules={}

# Module level functions are methods of a global default stylesheet
Global = StyleSheet()
load = Global.load
get = Global.get
clear = Global.clear
def reset():
    """Set Global stylesheet to the default"""
    load(DefaultRules,update=False)

def border_points(width=1.0,height=1.0,radii=0,steps=0):
    """Make a list of (x,y) describing the shape of a border
    occupying a box of given width and height.
    
    Radii and steps of each corner can be taken from a stylesheet, e.g:
    border-radius : 1 to 4 float radii for the rounded corners
    border-round : 1 to 4 int. 0 = flat corners, higher numbers
        give a better resolution, in the limit a circular arc.
    """
    if not radii:
        radii = (0.0,0.0,0.0,0.0)
    elif type(radii) in (float,int):
        radii = (radii,radii,radii,radii)
    if not steps:
        steps = (0,0,0,0)
    elif type(steps) in (int,float):
        steps = (int(steps),) * 4
    while len(radii) < 4:
        radii = radii + radii
    while len(steps) < 4:
        steps = steps + steps
    # now definitely at least corner 4 radii and 4 stepcounts
    points = []
    def add(x,y):
        points.append((x,y))
    def arc(cx,cy,r,fromangle,corners):
        theta = fromangle * pi
        turn = (pi * 0.5) / corners
        for i in range(1,corners):
            theta += turn
            add(cx + r * cos(theta), cy + r * sin(theta))
    r0,r1,r2,r3 = radii[:4]
    s0,s1,s2,s3 = steps[:4]
    px,py = -width * 0.5 + r3, -height * 0.5
    add(px,py)
    px += width - (r3 + r2)
    add(px,py)
    py += r2
    if r2 and s2: arc(px,py,r2,-0.5,s2)
    px += r2
    add(px,py)
    py += height - (r2 + r1)
    add(px,py)
    px -= r1
    if r1 and s1: arc(px,py,r1,0.0,s1)
    py += r1
    add(px,py)
    px -= width - (r1 + r0)
    add(px,py)
    py -= r0
    if r0 and s0: arc(px,py,r0,0.5,s0)
    px -= r0
    add(px,py)
    py -= height - (r0 + r3)
    add(px,py)
    px += r3
    if r3 and s3: arc(px,py,r3,1.0,s3)
    points.append(points[0])    # close the loop
    return points
