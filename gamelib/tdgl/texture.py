#! /usr/bin/env python
"""A Texture is a manager of an OpenGL tecture object, constructed from
    a pygame surface.

    Best way to get a texture is to call get_texture(filename), which will re-use
    the same Texture object if it is called again while the object is still in use.
    
This file copyright Peter Harris 2007, released under the terms of the
GNU GPL v3 or later.
See www.gnu.org for details.

"""
__all__ = ('is_a_power_of_2','Texture','get_texture')

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.error import Error
from pygame import image
from weakref import WeakValueDictionary

import resource

texture_pool = WeakValueDictionary()

def enable():
    """Convenience function to glEnable(GL_TEXTURE_2D)"""
    glEnable(GL_TEXTURE_2D)

def disable():
    """Convenience function to glDisable(GL_TEXTURE_2D)"""
    glDisable(GL_TEXTURE_2D)

def is_a_power_of_2(x):
    """Binary trick: x & -x yields lowest set bit in x.
    For powers of 2 it's the only bit"""
    return x == (x & -x)
    
class Texture:
    def __init__(self,filename):
        """Create texture from image file"""
        self.tname = glGenTextures(1)
        img = image.load(filename)
        width,height = img.get_size()
        if not (is_a_power_of_2(width) and is_a_power_of_2(height)):
            print "Warning: size of texture image %s is (%d,%d)", (filename,width,height)
        img_data = image.tostring(img,"RGBA",True)
        glBindTexture(GL_TEXTURE_2D,self.tname)
        try:
            gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA8,
                        width, height, GL_RGBA, GL_UNSIGNED_BYTE,
                        img_data)
        except Error:
            # give up - something unknown went wrong
            glDeleteTextures([self.tname])
            self.tname = 0
        alphabytes = img_data[3::4]
        if alphabytes != '\xff' * len(alphabytes):  # some transparency
            self.transparent = True
        else:
            self.transparent = False

    def bind(self):
        glBindTexture(GL_TEXTURE_2D,self.tname)

    def __del__(self):
        if glDeleteTextures:
            glDeleteTextures([self.tname])
        
def get_texture(filename):
    """Get a texture object or re-use one already loaded"""
    filename = resource.find(filename)
    if filename not in texture_pool:
        tex = Texture(filename)
        texture_pool[filename] = tex
    return texture_pool[filename]
