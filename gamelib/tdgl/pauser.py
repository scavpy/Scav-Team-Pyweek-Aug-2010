#! /usr/bin/env python
"""
A Pauser is a wrapper group that can "pause" its contents.
While is not paused, it does nothing out of the ordinary.

While it is paused, it intercepts the "step" method.  It draws its contents
and then puts a 50% grey overlay in front of them, but doesn't step them.
It also doesn't draw its contents in "PICK" mode.

This file copyright Peter Harris 2010, released under the terms of the
GNU GPL v2 or later.
See www.gnu.org for details.

"""


import pyglet
from gl import *

import part

class Pauser(part.Group):
    def __init__(self,*args,**kwd):
        super(Pauser,self).__init__(*args,**kwd)
        self.paused = False
    def setup_geom(self): pass  # no positioning
    def setdown_geom(self): pass
    def render(self,mode):
        """Overlay with a grey rect if paused
        """
        if mode == 'PICK' and self.paused:
            return  # no picking of pauser or anything behind it
        for d in self.contents:
            d.draw(mode)
        if self.paused:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)
            glDisable(GL_TEXTURE_2D)
            glPushMatrix()   # MODELVIEW
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()   # PROJECTION
            glLoadIdentity()
            glOrtho(-400,400,-300,300,-1.0,1.0)
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            self.draw_overlay(mode)
            glMatrixMode(GL_PROJECTION)
            glPopMatrix()    # PROJECTION
            glMatrixMode(GL_MODELVIEW)
            glPopMatrix()    # MODELVIEW
    def draw_overlay(self,mode):
        if mode != 'TRANSPARENT':   # overlay is never opaque
            return
        glColor4f(0.1,0.1,0.1,0.5)
        glRectf(-400,-300,400,300)
    def step(self,ms):
        if not self.paused:
            self.step_contents(ms)
    def pause(self):
        self.paused = True
    def unpause(self):
        self.paused = False

class TextPauser(Pauser):
    _default_style = {'fg':(1,1,1,0.8), 'bg':(0.1,0.1,0.1,0.5),
                      'font':None,'font_size':16,'italic':False,'bold':False}
    _style_attributes = tuple(_default_style.keys())
    def __init__(self,*args,**kwd):
        super(TextPauser,self).__init__(*args,**kwd)
        self.text = kwd.get('text','Paused')
        
    def prepare(self):
        getstyle = self.getstyle
        fg = getstyle("fg")
        font = getstyle("font")
        font_size = getstyle("font_size")
        italic = getstyle("italic")
        bold = getstyle("bold")
        color = [int(c*255) for c in fg]
        self.label = pyglet.text.Label(
            text=self.text,
            color=color,
            italic=italic,
            bold=bold,
            font=font,
            font_size=font_size,
            anchor_x='center',anchor_y='center')
        
    def draw_overlay(self,mode):
        glColor4f(*self.getstyle("bg"))
        glRectf(-400,-300,400,300)
        self.label.draw()
