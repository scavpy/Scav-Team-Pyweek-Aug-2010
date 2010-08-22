"""backdrop.py

A Backdrop is responsible for clearing the colour and depth buffers,
and may also draw something onto the screen as a background.

Best to put a Backdrop inside an viewgroup.OrthoGroup so the projection is
correct.

Copyright May 2005 by Peter Harris

Released under the terms of the GNU General Public License
see www.gnu.org for details.
"""

from tdgl.gl import *
import part, texture, lighting, stylesheet

BUFFERBITS = GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT

class Backdrop(part.Part):
    _default_style={'ClearColor':(0,0,0,1)}
    _style_attributes=('ClearColor',False)    # yuk!
    _active = False # don't keep a group active if just a background in it
    def __init__(self,name='',**kwd):
        super(Backdrop,self).__init__(name,**kwd)
        self.restyle()
    def setup_geom(self):
        pass
    def setdown_geom(self):
        pass
    def setup_style(self):
        glClearColor(*self.getstyle('ClearColor',(0,0,0,1)))
    def render(self,mode):
        if mode == "OPAQUE":   # transparency or picking pass irrelevant
            glClear(BUFFERBITS)

class TextureBackdrop(Backdrop):
    _default_geom = {'distance':100.0}
    _default_style = {'ClearColor':(0,0,0,1), 'colour':(1,1,1,1)}
    _style_attributes = ('ClearColor','colour','texture')
    _active = False
    tex = None
    
    def __init__(self,name='',**kwd):
        super(TextureBackdrop,self).__init__(name,**kwd)

    def prepare(self):
        texname = self._style.get('texture')
        if texname:
            self.tex = texture.get_texture(texname)
            self._has_transparent = self.tex.transparent
        else:
            self.tex = None
            self._has_transparent = False
        self.colour = self._style['colour']
        self._has_transparent = self._has_transparent or  (self.colour[3] < 1.0)

    def setup_style(self):
        """Enable textures and bind self.tex texture object, if it has one."""
        tex = self.tex
        colour = self.colour
        if tex:
            texture.enable()
            tex.bind()
            if self._has_transparent:
                glEnable(GL_BLEND)
                glClearColor(*self._style['ClearColor'])
            else:
                glDisable(GL_BLEND)
        lighting.disable()
        glColor(*colour)
    
    def render(self,mode):
        if mode == "OPAQUE":
            glClear(BUFFERBITS)  # only clear on first pass
        elif mode == "PICK":
            return  # no need to pick
        glDepthMask(GL_FALSE)
        v = glVertex3f
        t = glTexCoord2f
        z = -self._geom['distance']
        glBegin(GL_QUADS)
        t(0,0) ; v(-1,-1,z)
        t(1,0) ; v( 1,-1,z)
        t(1,1) ; v( 1, 1,z)
        t(0,1) ; v(-1, 1,z)
        glEnd()
        if mode != 'TRANSPARENT':
            glDepthMask(GL_TRUE)
