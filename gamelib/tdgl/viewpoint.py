#! /usr/bin/python
"""
    A Viewpoint is a group that sets up a glViewport and
    a projection, and optionally a camera viewpoint.

    It has 3 things that set it apart from a normal group:

    * A resize(w,h) method, to be called from on_resize()
      with the window dimensions.
      The 'vport' entry in its _geom dict specifies how
      to construct its glViewport from these dimensions.
      
    * A with_style_display_list() context manager.
      Put any OpenGL commands in the with statement, and
      they are inserted into a display list that sets
      style info (e.g. glEnable(GL_LIGHTING) for the
      whole group.

    * if created with shared=True, it can share its
      contents with another Group.  It won't update
      positions of the contents with step() if shared=True.
      The other group is responsible for doing that.

    Replaces the old viewgroup module, which was less
    flexible.

    Copyright 2009 Peter Harris
    Released under the terms of the GNU General Public License
    (See www.gnu.org for details)

"""
from __future__ import division

from gl import *

import part, lighting, camera, picking

__all__ = ('OrthoView','SceneView','relative_rect','relative_pos')
        

def vpdim(n,m):
    """Calculate viewport dimension
    based on:
      n - selector of value
      m - maximum value

    if n is a float, return that fraction of m.
    if n < 0 : return  m - n
    otherwise return n
    """
    if isinstance(n,float):
        return int(n * m)
    if n < 0:
        return m + n
    return n

def relative_rect((w,h),(rx,ry,rw,rh)):
    """ A rectangle (x,y,w,h), scaled relative to a viewport size"""
    return (vpdim(rx,w),vpdim(ry,h),vpdim(rw,w),vpdim(rh,h))

def relative_pos((w,h),pos):
    """relative position (pos can have 2 or 3 coords)"""
    x,y = pos[:2]
    return (vpdim(x,w),vpdim(y,h)) + tuple(pos[2:]) 

class Viewpoint(part.Group):
    """View of a collection of parts.
    A top-level container that manages its own 
    viewport, projection and camera.

    As well as its own contents, it can share the
    contents of another group, for a split-screen
    effect.
    """
    _default_geom = {"vport":(0.0, 0.0, 1.0, 1.0)}
    _default_style = {"ClearColor":None}
    def __init__(self, *args, **kwd):
        super(Viewpoint,self).__init__(*args,**kwd)
        self.dl_projection = gl.glGenLists(4)
        self.dl_style = self.dl_projection + 1
        self.dl_vport = self.dl_projection + 2
        self.dl_clear = self.dl_projection + 3
        self.camera = None
        self.shared = kwd.get("shared",())

    def __del__(self):
        if self.dl_projection and glDeleteLists:
            glDeleteLists(self.dl_projection,4)

    def render(self,mode):
        if mode == "OPAQUE":
            glCallList(self.dl_clear)
        for p in self.contents:
            p.draw(mode)
        for p in self.shared:
            p.draw(mode)

    # Resize
    def resize(self,width,height):
        """ Set the viewport and the projection
        Prepares a displaylist for the viewport and
        projection. """
        vport = self.getgeom("vport",(0.0, 0.0, 1.0, 1.0))
        self.vport = relative_rect((width,height),vport)
        with gl_compile(self.dl_vport):
            glViewport(*self.vport)
        with gl_compile(self.dl_projection):
            self.project()
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
        self.prepare()

    def prepare(self):
        clearcolour = self.getstyle("ClearColor",None)
        with gl_compile(self.dl_clear):
            if clearcolour:
                glScissor(*self.vport)
                glEnable(GL_SCISSOR_TEST)
                glClearColor(*clearcolour)
                glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
                glDisable(GL_SCISSOR_TEST)

    def project(self): # abstract
        pass

    # Set up some Open GL commands for setup_style
    def compile_style(self):
        return gl_compile(self.dl_style)

    # Part implementation
    def setup_geom(self):
        glCallList(self.dl_vport) # set up viewport before picking matrix
        picking.project() # identity or picking matrix
        glCallList(self.dl_projection)
        cam = self.camera
        if cam:
            cam.setup()
    def setdown_geom(self):
        pass

    def setup_style(self):
        glCallList(self.dl_style)

    def step(self,ms):
        cam = self.camera
        if cam: cam.step(ms)
        self.step_contents(ms)

class OrthoView(Viewpoint):
    """ Orthographic projection """
    _default_geom = {"vport":(0.0,0.0,1.0,1.0),
                     "left":-1.0, "right":1.0, "top":1.0, "bottom":-1.0,
                     "near":-1.0, "far":1.0}
    def __init__(self,*args,**kwd):
        super(OrthoView,self).__init__(*args,**kwd)
    
    def project(self):
        getgeom = self.getgeom
        near = getgeom("near",-1.0)
        far = getgeom("far",1.0)
        vpx,vpy,vpw,vph = self.vport
        left = getgeom("left",0)
        right = getgeom("right",vpw)
        top = getgeom("top",vph)
        bot = getgeom("bottom",0)
        glOrtho(left,right,bot,top,near,far)

class SceneView(Viewpoint):
    """ Perspective projection """
    _default_geom = {
        "vport":(0.0,0.0,1.0,1.0),
        'perspective_angle':15.0,
        'near':1.0,
        'far':1000.0}
    
    def __init__(self,*args,**kwd):
        super(SceneView,self).__init__(*args,**kwd)
        self.camera = camera.Camera()
        
    def project(self):
        vpx,vpy,vpw,vph = self.vport
        aspect = (vpw/vph if vph else vpw)
        getgeom = self.getgeom
        near = getgeom("near",1.0)
        far = getgeom("far",1000.0)
        angle = getgeom("perspective_angle",15.0)
        gluPerspective(angle,aspect,near,far)
        
