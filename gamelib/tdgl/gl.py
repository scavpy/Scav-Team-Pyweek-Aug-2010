#! /usr/bin/env python
"""
Compatibility wrapper to obtain OpenGL bindings from pyglet (preferred) or else PyOpenGL

This file copyright Peter Harris 2009, released under the terms of the
GNU GPL v3. See www.gnu.org for details.
"""
import sys
using_pyglet = "pyglet" in sys.modules
using_pygame = "pygame" in sys.modules

from contextlib import contextmanager 

if not using_pygame and not using_pyglet:
    try:
        import pyglet
        using_pyglet = True
    except ImportError:
        pass

if using_pyglet:
    import pyglet
    from pyglet.gl import *
    from pyglet.gl.glu import *
elif using_pygame:
    import pygame
    from PyOpenGL.GL import *
    from PyOpenGL.GLU import *
else:
    raise ImportError("I don't know whether you are using pygame and PyOpenGL or pyglet")

def tdgl_usual_setup():
    """Set up the sort of things you nearly always need for OpenGL"""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glClearColor(0,0,0,0)
    glEnable(GL_CULL_FACE)

def tdgl_usual_texture_setup():
    """Enable GL_TEXTURE_2D and GL_COLOR_MATERIAL, which you will generally want
    to do when using TNV or .obj models"""
    glEnable(GL_TEXTURE_2D)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)

def tdgl_draw_parts(*parts):
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_EQUAL, 1.0)  # only fully opaque fragments
    glDepthMask(GL_TRUE)        # update depth mask
    for p in parts:
        p.draw("OPAQUE")
    glAlphaFunc(GL_LESS,1.0)    # only partially transparent fragments
    glDepthMask(GL_FALSE)       # no update of depth mask
    for p in parts:
        p.draw("TRANSPARENT")
    glDisable(GL_ALPHA_TEST)
    glDepthMask(GL_TRUE)        # update depth mask


@contextmanager
def gl_compile(dl):
    """context manager for glNewList"""
    glNewList(dl,GL_COMPILE)
    try:
        yield dl
    finally:
        glEndList()

@contextmanager
def gl_begin(prim):
    """context manager for glBegin"""
    glBegin(prim)
    try:
        yield prim
    finally:
        glEnd()
