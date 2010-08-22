#! /usr/bin/env python

"""A Part is a thing that can be drawn or respond to events.
   A Group is a Part made of Parts.

   Parts have a certain amount of their configuration calculated
   from a stylesheet. They can be requested to refresh this information
   in the event of a stylesheet change.
   
   They also have a step() method to make changes for the next
   animation frame.

This file copyright Peter Harris 2009, released under the terms of the
GNU GPL v3. See www.gnu.org for details.
"""
import gl
from gl import (
    glPushMatrix, glPopMatrix,
    glTranslatef, glRotatef, glScalef,
    glEnable,GL_NORMALIZE
    )

import stylesheet, picking

def diffkeys(d1,d2):
    """Keys of d2 that are not in d1 or which have different values in d2"""
    s = set()
    for k,v in d2.items():
        if k not in d1 or d1[k] != v:
            s.add(k)
    return s

class Part(object):
    """A component of a scene.  It can draw itself, restyle itself according
    to a stylesheet, respond to an event, step to the next animation frame.
    """
    _default_geom = {}
    _default_style = {}
    _style_attributes = ()
    _expired = False
    _has_transparent = True # by default, assume we need a transparency rendering pass
    _name = ""    # ID for use in stylesheets
    _visible = True
    _active = True  # relevant to whether a Group containing the part expires
    def __init__(self,name="",geom=None,style=None,**kw):
        self._geom = self._default_geom.copy()
        if geom:
            self._geom.update(geom)
        self._style = self._default_style.copy()
        if style:
            self._style.update(style)
        if name:
            self._name = name
        self._style_classes = set(kw.get('style_classes',()))

    def getgeom(self,name,default=None):
        return self._geom.setdefault(name,default)
    def getstyle(self,name,default=None):
        return self._style.setdefault(name,default)
    def setgeom(self,name,val):
        self._geom[name]=val
    def setstyle(self,name,val):
        self._style[name]=val

    def add_styles(self,*style_names):
        self._style_classes |= set(style_names)
        self.restyle()
    def remove_styles(self,*style_names):
        self._style_classes -= set(style_names)
        self.restyle()
    def toggle_styles(self,*style_names):
        self._style_classes ^= set(style_names)
        self.restyle()
    def style_classes(self):
        return self._style_classes

    def style_selector(self):
        """A selector for this object to use for stylesheet lookups"""
        sl = []
        if self._name:
            sl.append("#%s" % self._name)
        sl.append(self.__class__.__name__)
        sl.extend(self._style_classes)
        return '.'.join(sl)
        
    def restyle(self,force=False):
        """Re-calculate style information, and if anything has changed,
        prepare whatever expensive calculations, display lists or
        cached objects are needed for drawing with the new style.
        """
        style = stylesheet.get(self.style_selector(),*self._style_attributes)
        if style:
            d = diffkeys(self._style,style)
            self._style.update(style)
        else:
            d = set()
        if d or force:
            self.prepare()
            
    def prepare(self):
        """Perform expensive calculations, load textures or fonts etc.
        Anything that you want to do only once after init or after each restyle()"""
        pass
        
    def draw(self,mode="OPAQUE"):
        """Draw, in one of three ways used in different contexts:
          OPAQUE      : draw the opaque bits, with styling
          TRANSPARENT : draw the transparent bits, with styling
          PICK        : draw both but with no styling, and set picking labels
          
          A rendering loop will generally call draw("OPAQUE") for all objects,
          then draw("TRANSPARENT").  When picking is underway, it will call
          draw("PICK").
          
          NB: if you can be sure no pixels will be drawn with alpha < 1.0, you can
          skip the TRANSPARENT pass. Set _has_transparent to False. 
        """
        if not self._visible: return    # turning off _visible turns off draw()
        self.setup_geom()   # position, scaling, rotation etc.
        if mode != "PICK":  self.setup_style()
        if self._has_transparent or mode != 'TRANSPARENT':
            self.render(mode)
        if mode != "PICK":  self.setdown_style()
        self.setdown_geom()
        
    def setup_geom(self):
        """Default setup_geom is translation to pos, rotation by angle"""
        pos = self.pos
        angle = self.angle
        glPushMatrix()
        glTranslatef(*pos)
        if angle:
            glRotatef(angle,0,0,1.0)
        
    def setup_style(self): pass
    
    def render(self,mode): pass
    
    def setdown_style(self): pass
    
    def setdown_geom(self):
        """Default setdown_geom pops modelview matrix"""
        glPopMatrix()
        
    def event(self,event): pass
    
    def step(self,ms=20): pass
    
    def expired(self):
        """Return a true value if there is nothing to draw any more"""
        return self._expired
        
    # pos and angle properties
    @property
    def pos(self):
        return self._geom.get('pos',(0,0,0))
    @pos.setter
    def pos(self,value):
        self._geom['pos'] = value
    
    @property
    def angle(self):
        return self._geom.get('angle',0.0)
    @angle.setter
    def angle(self,a):
        self._geom['angle'] = a

class ScalePart(Part):
    def setup_geom(self):
        """Move to pos, turn by angle and scale by scale"""
        super(ScalePart,self).setup_geom()
        scale=self._geom.get('scale',1)
        if scale and scale != 1:
            glEnable(GL_NORMALIZE)
            glScalef(scale,scale,scale)

class Group(Part):
    """A collection of parts, bundled together for convenience.
    The group's setup_*() and setdown_*() methods bracket the drawing
    of all drawable parts.
    All parts that can respond to events are passed each event passed
    into the event() method.
    All parts that have a name are kept in a dictionary so they can be
    found easily."""
    _transient = False
    _has_transparent = True # contents might need a transparency rendering pass

    def __init__(self,name="",contents=(),**kwd):
        super(Group,self).__init__(name,**kwd)
        self._transient = kwd.get('transient',False)
        self.named_parts = {}
        self.contents = []
        for p in contents:
            self.append(p)

    # public interface
    def __iter__(self):
        return iter(self.contents)

    def append(self,newpart):
        """Add another part to the contents of the group"""
        self.contents.append(newpart)
        if newpart._name:
            self.named_parts[newpart._name] = newpart

    def remove(self,delpart):
        """Remove a part if it is in the contents of a group"""
        try:
            self.contents.remove(delpart)
        except ValueError:
            pass
        name = delpart._name
        if (name in self.named_parts and
           self.named_parts[name] == delpart):
            del self.named_parts[name]

    def __getitem__(self,name):
        """Get a named part from contents of group, or from any group
        within it"""
        try:
            return self.named_parts[name]
        except KeyError:
            for g in self.contents:
                if isinstance(g,Group):
                    p = g[name]
                    if p:
                        return p
            return None

    # internal workings
    def render(self,mode):
        for p in self.contents:
            p.draw(mode)
    def restyle(self,force=False):
        super(Group,self).restyle(force)
        for p in self.contents:
            p.restyle(force)
    def event(self,event):
        return self.event_to_contents(event)
    def event_to_contents(self,event):
        """Call the event() method of every Part in the contents
        return first non-None return value (indicating some Part
        has consumed the event)
        """
        for p in self.contents:
            r = p.event(event)
            if r is not None:
                return r
    def step(self,ms=20):
        self.step_contents(ms)
    def step_contents(self,ms=20):
        """Next animation frame of each visible part, then remove
        any that have expired"""
        any_active = False
        for p in tuple(self.contents):
            if p.expired():
                self.remove(p)
            else:
                p.step(ms)
                any_active = any_active or p._active
        if self._transient and not any_active:
            self._expired = True

class VisibleSetsGroup(Group):
    """A group which only makes some of its contents visible
    depending on its state"""
    def __init__(self,name="",contents=(),visible_sets=None,state=None,**kw):
        super(VisibleSetsGroup,self).__init__(name,contents,**kw)
        self.visible_sets={}
        self.state = state
        if visible_sets:
            self.visible_sets.update(visible_sets)
    def render(self,mode):
        visibles = set(self.visible_sets.get(self.state,()))
        for p in self.contents:
            if p._name == "" or p._name in visibles:
                p.draw(mode)

            
