"""
As usual, I find bugs in tdgl...

"""

import pyglet
from tdgl import lighting, gl, panel, picking
from tdgl.gl import *

def fix_release_light(light):
    """Release a light so it can be used for other things"""
    if light in lighting.claimed_lights:
        lighting.light_switch(light,False)
        glDisable(GL_LIGHT0 + light)
        lighting.claimed_lights.remove(light)
        lighting.free_lights.append(light)
    if light in lighting.conditions:
        del lighting.conditions[light]

lighting.release_light = fix_release_light

def fix_panel_del(self):
    if glDeleteLists:
        glDeleteLists(self.bgdl,2)

panel.Panel.__del__ = fix_panel_del

pyglet.image.Texture.transparent = False # don't ask...

def fix_picking_end():  # end --> [(minz,maxz,ob)]
    """End GL_SELECT mode and get a list of objects added by picking.label()
    that overlapped the target rectangle, together with their z-distance range
    """
    picking.active = False
    hits = glRenderMode(GL_RENDER)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    picklist = []
    _buffer = picking._buffer
    j = 0 # index into picking buffer
    for i in range(hits):
        stackdepth = _buffer[j]
        minz = float(_buffer[j+1]) / 0x7fffffff
        maxz = float(_buffer[j+2]) / 0x7fffffff
        hit = picking._labelDict.get(_buffer[j+3])
        if hit:
            hit.minz = minz
            hit.maxz = maxz
            picklist.append((minz,maxz,hit))
        j += 3 + stackdepth
    picklist.sort()
    return picklist

picking.end = fix_picking_end
