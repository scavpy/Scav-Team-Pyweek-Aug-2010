"""
As usual, I find bugs in tdgl...

"""

import pyglet
from tdgl import lighting, gl, panel
from tdgl.gl import glDisable, GL_LIGHT0, glDeleteLists

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
