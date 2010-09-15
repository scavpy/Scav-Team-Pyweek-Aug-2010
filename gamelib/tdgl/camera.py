""" camera module - control the position of the camera and where it is looking.

    Previously this was under the control of a CameraGroup object, but it was
    not very convenient, so I have made it a module. That way, control of the
    camera is globally available.

    It is assumed that some Group object or other calls camera.setup()
    before drawing its contents.

    Copyright 2009 Peter Harris
    Released under the terms of the GNU General Public License
    see www.gnu.org for details.
"""

from gl import *
from animator import Animator

from math import cos,sin,radians,degrees,sqrt,atan2

class Camera(object):
    """An object to control the camera"""
    def __init__(self):
        self.animator = Animator(looking_at=(0,0,0),
                                 looking_from=(0,-50,-50),
                                 up_vector=(0,0,1),
                                 latitude=45.0,
                                 longitude=45.0,
                                 distance=(50*sqrt(2.0)))
        self.spherical = False
        self.prepare_args()
    def prepare_args(self):
        anim = self.animator
        if self.spherical:
            d = anim['distance']
            theta = radians(anim['longitude'])
            phi = radians(anim['latitude'])
            r = d * cos(phi)
            dz = d * sin(phi)
            dx = r * cos(theta)
            dy = r * sin(theta)
            x0,y0,z0 = anim['looking_at']
            up_r = - sin(phi)
            up = (up_r * cos(theta), up_r * sin(theta), cos(phi))
            anim['looking_from'] = (x0+dx, y0+dy, z0+dz)
            anim['up_vector'] = up
        self.lookat_args = (tuple(anim['looking_from']) +
                            tuple(anim['looking_at']) +
                            tuple(anim['up_vector']))
    def setup(self):
        glLoadIdentity()
        gluLookAt(*self.lookat_args)
    def look_at(self, pos, steps=0):
        """Point the camera.
           If a number of steps specified, step() will turn the camera
           in that many steps.
        """
        self.animator.change('looking_at',pos,steps)
        self.prepare_args()
    def look_from(self, pos, steps=0):
        """Move the camera.
        If a number of steps specified, step() will move the camera in that
        many steps.
        """
        self.animator.change('looking_from',pos,steps)
        self.spherical = False
        self.prepare_args()
    def look_from_spherical(self,lat,long,dist,steps=0):
        """Move the camera, using spherical coordinates"""
        if not self.spherical:
            x,y,z = self.animator['looking_from']
            x0,y0,z0 = self.animator['looking_at']
            dx,dy,dz = x-x0, y-y0, z-z0
            distance = sqrt(dx*dx + dy*dy + dz*dz)
            self.animator['distance'] = distance
            longitude = degrees(atan2(y0,x0))
            latitude = degrees(atan2(z0,sqrt(x0*x0+y0*y0)))
            self.animator['latitude'] = latitude
            self.animator['longitude'] = longitude
        self.animator.change('latitude',lat,steps)
        self.animator.change('longitude',long,steps)
        self.animator.change('distance',dist,steps)
        self.spherical = True
    def choose_up(self,vec,steps=0):
        """Choose the subjective 'up' vector"""
        self.animator.change('up_vector',vec,steps)
        self.prepare_args()
    def step(self,ms):
        """Move and point the camera"""
        changed = not(self.animator.finished())
        self.animator.step(ms)
        if changed:
            self.prepare_args()
    def ready(self):
        return self.animator.finished()

# Create a default camera object, and use its methods as module-level functions
_TheCam = Camera()
setup = _TheCam.setup
step = _TheCam.step
look_at = _TheCam.look_at
look_from = _TheCam.look_from
look_from_spherical = _TheCam.look_from_spherical
choose_up = _TheCam.choose_up
ready = _TheCam.ready





