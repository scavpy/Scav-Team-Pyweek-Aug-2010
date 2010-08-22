#! /usr/bin/env python
"""Defines a standard main loop which polls pygame events and draws a scene
   consisting of a Part (which may be a Group with various other parts in it)

   The loop exits when the Part expires.

    Copyright 2005 Peter Harris
    Released under the terms of the GNU General Public License
"""
    
import pygame

from pygame.locals import *     # useful constants
import usualGL

def open_window(size,fullscreen=False):
    """Open a window of given size, optionally in full-screen mode"""
    pygame.init()
    flags = OPENGL|DOUBLEBUF
    if fullscreen: flags |= FULLSCREEN
    return pygame.display.set_mode(size,flags)

def until_condition(the_part,framerate=60,idle=True,showrate=False,condition=None):
    """An event loop to be carried out on a part.Part object, ending only
    when a condition becomes true"""
    if not callable(condition):
        condition = the_part.expired
    clock = pygame.time.Clock()
    the_part.restyle(force=True)  # prepare style info
    if showrate:
        countframes = 0
    while True:
        usualGL.usual_for_opaque()
        the_part.draw("OPAQUE")  # View to be redrawn
        usualGL.usual_for_transparent()
        the_part.draw("TRANSPARENT")
        pygame.display.flip()
        ms = clock.tick(framerate)
        if showrate:
            countframes += 1
            if not(countframes % 100):
                print clock.get_fps(), "fps"
        if idle:
            event = pygame.event.Event(NOEVENT) # an idle event
        else:
            event = pygame.event.wait()     # wait for an event
        events = [event] + pygame.event.get() # do all the events in the queue
        for event in events:
            the_part.event(event)  # pass event to handler
        the_part.step(ms) # get ready for next animation frame
        if condition():
            break
            
def until_expired(the_part,framerate=60,idle=True,showrate=False):
    """An event loop to be carried out on a part.Part object, ending only
    when the object expires.
    If using this, it's a good idea for the event method of the part
    to watch for QUIT events and explicitly expire itself."""
    until_condition(the_part,framerate=framerate,idle=idle,showrate=showrate,
                    condition=the_part.expired)

if __name__ == '__main__':
    import part
    class FakePart(part.Part):
        """A Part that doesn't draw anything. All it does is expire
        itself when it gets a pygame QUIT event"""
        def __init__(self,name,**kw):
            super(FakePart,self).__init__(name,**kw)
        def event(self,event):
            if event.type == QUIT:
                self._expired = True
    open_window((640,480))
    until_expired(FakePart('nothing'),showrate=True)
    
