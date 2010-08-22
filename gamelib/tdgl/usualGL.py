""" usualGL - convenience functions for OpenGL

    Copyright 2009 Peter Harris
    Released under the terms of the GNU General Public License
"""
from gl import *

def usual_setup():
    """Set up the sort of things you nearly always need for OpenGL"""
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glClearColor(0,0,0,0)
    glEnable(GL_CULL_FACE)

def usual_for_textures():
    """Enable GL_TEXTURE_2D and GL_COLOR_MATERIAL, which you will generally want
    to do when using TNV or .obj models"""
    glEnable(GL_TEXTURE_2D)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)

def usual_for_opaque():
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_EQUAL, 1.0)  # only fully opaque fragments
    glDepthMask(GL_TRUE)        # update depth mask
    
def usual_for_transparent():
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_LESS,1.0)    # only partially transparent fragments
    glDepthMask(GL_FALSE)       # no update of depth mask
