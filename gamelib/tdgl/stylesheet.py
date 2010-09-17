#! /usr/bin/env python
"""stylesheet.py - obtain style for tdlib objects in a manner analogous to CSS,
   only not as good

  Copyright 2010 Peter Harris
  
  Released under the terms of the GNU General Public License v3 or later


  Style selectors are like:

  <style-selector> ::=  <container-selector>* <part-selector>
  <container-selector> ::= <part-selector> ' '
  <part-selector> ::= <type-selector>? <name-selector>? <style-class-selectors>*
  <type-selector> ::= <name>
  <name-selector> ::= '#' <name>
  <style-class-selector> ::= '.' <name>
  <name> ::= [0-9_A-Za-z]+

  In other words, a set of things like "LabelPanel#title.large" separated by 
  spaces.  To match the style-selector, a Part must match the last one (the 
  part-selector), and some of the containers above it must match the container-
  selectors, in reverse order.

  e.g.:
    "Screen#titlescreen LabelPanel#title"
  will match a LabelPanel (or subclass thereof) with name "title", as long as 
  it is contained directly or indirectly by a Screen (or subclass thereof) with 
  name "titlescreen".

  All matching style rules are applied, in increasing order of specificity.

  Specificity is a list of tuples, one for the part-selector and one for each 
  container-selector, in reverse order.  A specificity tuple is:
    (matches_name_exactly, num_style_classes_specified, -subclass_distance)
  where subclass distance is number of levels of inheritance between the class 
  specified in the selector and the class of the Part.

  A Stylesheet keeps a dictionary of style-value dictionaries, keyed by 
  style-selector.  Stylesheet.get(p) returns the union of all styles with a 
  selector that matches the Part p
"""
from inspect import getmro
from math import pi, sin, cos

def nothing(*dummy):
    " a null debug function "
    pass
debug_no_match = nothing
debug_match = nothing

DEFAULT_RULES = {
    '':{'background-colour':(0, 0, 0, 1),
        'colour':(1, 1, 1, 1) }
    }

class Selector(object):
    """hashable struct of ClassName,PartName,StyleClasses"""
    __slots__ = ('pclass', 'name', 'sclasses')
    def __init__(self, selectorstring):
        pclass, hashchar, rest = selectorstring.partition("#")
        if hashchar:
            self.name, _, rest = rest.partition(".")
            self.pclass = pclass
        else:
            self.name = None
            self.pclass, _, rest = pclass.partition(".")
        if rest:
            self.sclasses = frozenset(rest.split("."))
        else:
            self.sclasses = frozenset()
    def __hash__(self):
        return hash((self.name, self.pclass, self.sclasses))
    def __eq__(self, other):
        return (other.pclass == self.pclass and 
                other.name == self.name and 
                other.sclasses == self.sclasses)
    def __repr__(self):
        return "Selector('{0}#{1}.{2}')".format(
            self.pclass, self.name, ".".join(self.sclasses))
    def matches(self, p):
        """specificity of match with a part P"""
        name_specified = self.name is not None
        if name_specified and p._name != self.name:
            debug_no_match("%r doesn't match name '%s'", self, p._name)
            return None
        sclasses = p.style_classes()
        if not self.sclasses.issubset(sclasses):
            debug_no_match(u"%r doesn't match styles of '%s' %s",
                           self, p._name, sclasses)
            return None
        pclassname = p.__class__.__name__
        if self.pclass == '':
            subclass_dist = float('inf') # unspecified class
        elif self.pclass == pclassname:
            subclass_dist = 0 # exact class match
        else: # try superclass match
            mro = [C.__name__ for C in getmro(p.__class__)]
            try:
                subclass_dist = mro.index(self.pclass)
            except ValueError:
                debug_no_match("%r doesn't match class of '%s' %s",
                               self, p._name, pclassname)
                return None
        return (name_specified, len(self.sclasses), -subclass_dist)

def rule_match(selector_tuple, p):
    """Return specificity of match between tuple of Selectors and Part p,
    being None if the match fails"""
    if not selector_tuple:
        return [] # least-specific possible match
    specificity = []
    selectors = list(selector_tuple)
    psel = selectors.pop()
    ok = psel.matches(p)
    if not ok:
        return None
    specificity.append(ok)
    child = p
    while selectors and child._parentref:
        parent = child._parentref()
        if parent is None:
            break # eh? someone got deleted...
        ok = selectors[-1].matches(parent)
        if ok: # match at parent Part
            selectors.pop()
            specificity.append(ok)
        else:
            child = parent
    if selectors: # still something not matched
        return None
    if p._name:
        debug_match("%r matches %s with specificity %r",
                    selector_tuple, p._name, specificity)
    return specificity # part matched 

class StyleSheet(object):
    """A repository of style information retrieved using a simplified
    form of CSS selectors.
    
    The stylesheet is loaded using load() method, from a dictionary of
    dictionaries. The outer dictionary is indexed by selectors, the inner
    ones are indexed by attribute.
    """
    def __init__(self, rules=None):
        self.clear()
        if rules is not None:
            self.load(rules)
        else:
            self.load(DEFAULT_RULES)

    def load(self, rules, update=True):
        """Load stylesheet rules in the form of a nested dict.
        If update is false, the stylesheet is cleared first"""
        if not update:
            self.clear()
        for selstring, adict in rules.items():
            seltuple = tuple(Selector(s) for s in selstring.split())
            if seltuple:
                name = seltuple[-1].name
            else:
                name = None
            rules = self.rules_by_name.setdefault(name, dict())
            rules.setdefault(seltuple, dict()).update(adict)

    def get(self, p):
        """Get a dictionary of style attributes composed by
        updating an empty dict with all style values whose
        selector matches the part
        """
        values = {}
        # Always check rules that aren't specific by part name
        values.update(self.get_matching_rules_by_name(None, p))
        if p._name:
            # Only check additional rules where name is same as part name.
            # Others must inevitably fail to match.
            values.update(self.get_matching_rules_by_name(p._name, p))
        return values

    def get_matching_rules_by_name(self, name, p):
        """stylesheet rules specifying a name in their innermost
        selector are separated out by name, so the number of matches
        to attempt is reduced somewhat"""
        ruleset = self.rules_by_name.get(name, {})
        matching_rules = [(rule_match(selectors, p), styles) 
                          for (selectors,styles) in ruleset.items()]
        ordered_rules = sorted((m, s) for (m, s) in matching_rules 
                               if m is not None)
        values = {}
        for _, s in ordered_rules:
            values.update(s)
        return values

    def clear(self):
        """ clear stylesheet rules """
        self.rules_by_name = {}

# Module level functions are methods of a global default stylesheet
Global = StyleSheet()
load = Global.load
get = Global.get
clear = Global.clear
def reset():
    """Set Global stylesheet to the default"""
    load(DEFAULT_RULES, update=False)

def border_points(width=1.0, height=1.0, radii=0, steps=0):
    """Make a list of (x,y) describing the shape of a border
    occupying a box of given width and height.
    
    Radii and steps of each corner can be taken from a stylesheet, e.g:
    border-radius : 1 to 4 float radii for the rounded corners
    border-round : 1 to 4 int. 0 = flat corners, higher numbers
        give a better resolution, in the limit a circular arc.
    """
    if not radii:
        radii = (0.0, 0.0, 0.0, 0.0)
    elif type(radii) in (float, int):
        radii = (radii, radii, radii, radii)
    if not steps:
        steps = (0, 0, 0, 0)
    elif type(steps) in (int, float):
        steps = (int(steps),) * 4
    while len(radii) < 4:
        radii = radii + radii
    while len(steps) < 4:
        steps = steps + steps
    # now definitely at least corner 4 radii and 4 stepcounts
    points = []
    def add(x, y):
        """ add a point to points list """
        points.append((x, y))
    def arc(cx, cy, r, fromangle, corners):
        """ add points in an arc """
        theta = fromangle * pi
        turn = (pi * 0.5) / corners
        for _ in range(1, corners):
            theta += turn
            add(cx + r * cos(theta), cy + r * sin(theta))
    r0, r1, r2, r3 = radii[:4]
    s0, s1, s2, s3 = steps[:4]
    px, py = -width * 0.5 + r3, -height * 0.5
    add(px, py)
    px += width - (r3 + r2)
    add(px, py)
    py += r2
    if r2 and s2:
        arc(px, py, r2, -0.5, s2)
    px += r2
    add(px, py)
    py += height - (r2 + r1)
    add(px, py)
    px -= r1
    if r1 and s1:
        arc(px, py, r1, 0.0, s1)
    py += r1
    add(px, py)
    px -= width - (r1 + r0)
    add(px, py)
    py -= r0
    if r0 and s0:
        arc(px, py, r0, 0.5, s0)
    px -= r0
    add(px, py)
    py -= height - (r0 + r3)
    add(px, py)
    px += r3
    if r3 and s3:
        arc(px, py, r3, 1.0, s3)
    points.append(points[0])    # close the loop
    return points
