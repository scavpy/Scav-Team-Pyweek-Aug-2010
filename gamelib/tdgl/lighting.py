""" Lighting controls


    Copyright 2005 Peter harris
    Released under the terms of the GNU General Public License
    (GPL v3 or later)
    See www.gnu.org for details.
"""
from animator import Animator
from gl import *

switches = {GL_LIGHT0:True}
conditions = {}
options = {GL_LIGHT_MODEL_TWO_SIDE:False,
           GL_LIGHT_MODEL_LOCAL_VIEWER:True}
claimed_lights = []
free_lights = None

def setup():
    """Enable lighting, set up all the lights"""
    glEnable(GL_LIGHTING)
    for light,switch in switches.items():
        if switch:
            glEnable(light)
            anim = conditions.get(light,{})
            for param, value in anim.items():
                try:
                    v = (GLfloat * len(value))(*value)
                    glLightfv(light,param,v)
                except:
                    print "glLightfv",(light,param,value)
                    raise
        else:
            glDisable(light)
    for opt,on in options.items():
        glLightModeliv(opt,GLint(on))

def disable():
    glDisable(GL_LIGHTING)
    
def two_side(on=False):
    options[GL_LIGHT_MODEL_TWO_SIDE] = bool(on)
def local_viewer(on=True):
    options[GL_LIGHT_MODEL_LOCAL_VIEWER] = bool(on)
    
def light_switch(lightnum,on):
    """Turn a light on or off"""
    light = GL_LIGHT0 + lightnum
    switches[light] = on

def update_lights(ms):
    # deprecated
    step(ms)

def step(ms):
    """Make any lighting changes pending"""
    for anim in conditions.values():
        anim.step(ms)

def adjust_light(lightnum,param,value,ms=0):
    """Set up a gradual changes of a lighting parameter"""
    light = GL_LIGHT0 + lightnum
    if light not in conditions:
        conditions[light] = Animator()
    conditions[light].change(param,value,ms)
    
def light_position(lightnum,position,ms=0):
    adjust_light(lightnum,GL_POSITION,position,ms)
    
def light_colour(lightnum,colour,ms=0):
    acolour = tuple(c * 0.1 for c in colour)
    adjust_light(lightnum,GL_AMBIENT,acolour,ms)
    adjust_light(lightnum,GL_DIFFUSE,colour,ms)
    adjust_light(lightnum,GL_SPECULAR,colour,ms)
    
def light_spot_direction(lightnum,direction,ms=0):
    adjust_light(lightnum,GL_SPOT_DIRECTION,direction,ms)
    
def light_spot_cutoff(lightnum,cutoff,ms=0):
    adjust_light(lightnum,GL_SPOT_CUTOFF,cutoff,ms)
    
def light_spot_exponent(lightnum,exponent,ms=0):
    adjust_light(lightnum,GL_SPOT_EXPONENT,exponent,ms)
    
def light_attenuation(lightnum,value=0,ms=0):
    adjust_light(lightnum,GL_QUADRATIC_ATTENUATION,value,ms)

def oscillate_light(lightnum,param,vfrom,vto,ms):
    """Set up an oscillating lighting parameter"""
    light = GL_LIGHT0 + lightnum
    if light not in conditions:
        conditions[light] = Animator()
    conditions[light].oscillate(param,vfrom,vto,ms)

def sequence_light(lightnum,param,vlist,steplist):
    """Set up a sequence of lighting changes"""
    light = GL_LIGHT0 + lightnum
    if light not in conditions:
        conditions[light] = Animator()
    conditions[light].sequence(param,vlist,steplist)

def claim_light():
    """Claim a light for use in lighting effects."""
    global free_lights
    if free_lights is None:
        glint = GLint()
        glGetIntegerv(GL_MAX_LIGHTS,glint)
        num_lights = glint.value
        try:
            free_lights = range(num_lights)
        except TypeError:
            raise TypeError("glGetIntegerv() failed. Maybe OpenGL not initialised")
    if free_lights:
        light = free_lights.pop(0)
        claimed_lights.append(light)
    else:
        light = None    # watch for this return value when no lights left!
    return light

def release_light(light):
    """Release a light so it can be used for other things"""
    if light in claimed_lights:
        light_switch(light,False)
        claimed_lights.remove(light)
        free_lights.append(light)
        if light in conditions:
            del conditions[light]