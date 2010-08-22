#! /usr/bin/env python
"""
A Pauser is a wrapper group around some objects that intercepts events.
While is not paused it passes all events except the P key, which makes it
be paused. It draws nothing except its contents.

While it is paused, it intercepts all events. The P key makes it unpause.
While paused, it draws its contents and then puts a 50% grey overlay in front
of them.

This file copyright Peter Harris 2005, released under the terms of the
GNU GPL. See www.gnu.org for details.

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
            glOrtho(-1.0,1.0,-1.0,1.0,-1.0,1.0)
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
        glRectf(-1.0,-1.0,1.0,1.0)
    def event(self,event):
        """Pause/Continue if P pressed. Intercept all events while paused"""
        if event.type == KEYDOWN and event.key == K_p:
            self.paused = not self.paused
            return None
        elif not self.paused:
            return self.event_to_contents(event)
    def step(self,ms):
        if not self.paused:
            self.step_contents(ms)

class TextPauser(Pauser):
    _default_style = {'colour':(1,1,1,0.8),'pitch':10, 'font':None}
    _style_attributes = ('colour','pitch','font')
    def __init__(self,*args,**kwd):
        super(TextPauser,self).__init__(*args,**kwd)
        self.text = kwd.get('text','Paused')
        
    def prepare(self):
        style = self._style
        font = style.get('font')
        if font is None:
            self.font = texturefont.TextureFont()
        else:
            self.font = font
        self.width = self.font.width(self.text)
        self.scale = 1.0 / style['pitch']
        self.colour = style['colour']
        
    def draw_overlay(self,mode):
        glColor4f(0.1,0.1,0.1,0.5)
        glRectf(-1.0,-1.0,1.0,1.0)
        glColor4f(*self.colour)
        glScalef(self.scale,self.scale,1.0)
        glTranslatef(-(self.width / 2.0), -0.5, 0.0)
        self.font.render(self.text)
