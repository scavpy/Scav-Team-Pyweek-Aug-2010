"""
As usual, I find bugs in tdgl...

"""

from tdgl import lighting
from tdgl.gl import glDisable, GL_LIGHT0

def fix_release_light(light):
    """Release a light so it can be used for other things"""
    if light in lighting.claimed_lights:
        lighting.light_switch(light,False)
        print "glDisable(LIGHT0 +", light,")"
        glDisable(GL_LIGHT0 + light)
        lighting.claimed_lights.remove(light)
        lighting.free_lights.append(light)
    if light in lighting.conditions:
        del lighting.conditions[light]

lighting.release_light = fix_release_light
