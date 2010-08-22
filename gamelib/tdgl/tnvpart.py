"""
TNVpart is a Part made from a TNV file with chosen texturing and colouring.

Copyright 2007 Peter Harris, released under the terms of the GNU General Public License
(GPL v3 or later)

"""
import cPickle as pickle
import array
from weakref import WeakValueDictionary

from OpenGL.GL import glPushMatrix, glPopMatrix, glTranslate, glRotate
from OpenGL.GL import glEnable, GL_NORMALIZE, GL_TEXTURE_2D, glColor4f
from OpenGL.GL import GL_COLOR_MATERIAL, glColorMaterial, GL_FRONT_AND_BACK, GL_BLEND
from OpenGL.GL import GL_AMBIENT_AND_DIFFUSE, GL_CULL_FACE, GL_FRONT, GL_BACK
from OpenGL.GL import glInterleavedArrays, glDrawArrays, glCullFace, glDisable

from OpenGL.GL import GL_POINTS, GL_LINES, GL_TRIANGLES, GL_QUADS, GL_POLYGON, GL_TRIANGLE_FAN

import part, texture, usualGL, picking, resource

tnv_pool = WeakValueDictionary()

try:
    set()
except NameError:
    from sets import Set as set

import struct

I_AM_BIGENDIAN = (struct.pack('f',1.0) == struct.pack('>f',1.0))

def bigendianise(tnv):
    format, stride, little_endian = tnv['array']
    num=len(little_endian)/4
    floats = struct.unpack('<%df' % num, little_endian)
    big_endian = struct.pack('>%df' % num, *floats)
    tnv['array'] = format, stride, big_endian

class TNV:
    """Get around the problem that you can't get a weak reference to a dict, and
    also simplify drawing the pieces"""
    def __init__(self,tnv):
        self.tnv = tnv
    def __getitem__(self,i):
        return self.tnv[i]
    def prepare(self):
        glInterleavedArrays(*self.tnv['array'])
    def drawpiece(self,piece):
        try:
            glDrawArrays(*self.tnv['pieces'][piece])
        except IndexError:
            pass    # that piece isn't there!
    def pieces(self):
        return self.tnv['pieces'].keys()

    def face_data(self,piece):
        """yield vertices and first normal for each facet of a piece"""
        mode,first,num = self.tnv['pieces'][piece]
        firstvertex = []
        offset = 0
        if mode == GL_POLYGON:
            perface = num
        elif mode == GL_TRIANGLE_FAN:
            perface = 2
            firstvertex = [self.get_vertex_pos(piece,0)]
            offset = 1
        else:
            perface = {
                GL_POINTS: 1,
                GL_LINES: 2,
                GL_TRIANGLES: 3,
                GL_QUADS: 4}.get(mode)
        length = (num - offset) // perface
        for j in xrange(length):
            vertices = firstvertex[:]
            vidx = perface * j + offset
            for i in xrange(perface):
                vertices.append(self.get_vertex_pos(piece,vidx+i))
            norm = self.get_vertex_normal(piece,vidx)
            yield norm, vertices

    def get_vertex_pos(self,piece,idx=0):
        """get coords of n'th vertex in a piece"""
        if not hasattr(self,'array'):
            # only do this once, on demand
            self.array = array.array('f')
            self.array.fromstring(self.tnv['array'][2])
        mode,first,num = self.tnv['pieces'][piece]
        if idx < 0: idx += num
        if idx >= num or idx < 0:
            raise IndexError("Piece has only %d vertices" % num)
        offset = (idx + first) * 8
        return tuple(self.array[offset+5:offset+8])   # x,y,z coords as floats
        
    def get_vertex_normal(self,piece,idx=0):
        """Get normal at n'th vertex of a piece"""
        if not hasattr(self,'array'):
            # only do this once, on demand
            self.array = array.array('f')
            self.array.fromstring(self.tnv['array'][2])
        mode,first,num = self.tnv['pieces'][piece]
        if idx < 0: idx += num
        if idx >= num or idx < 0:
            raise IndexError("Piece has only %d vertices" % num)
        offset = (idx + first) * 8
        return tuple(self.array[offset+2:offset+5])   # i,j,k components as floats

def load_tnv(filename):
    tnv = pickle.load(file(filename))
    if I_AM_BIGENDIAN:
        bigendianise(tnv)
    return TNV(tnv)

def get_tnv(filename):
    """Load a TNV file, but re-use the same data if the file is already loaded"""
    filename = resource.find(filename)
    if filename not in tnv_pool:
        tnv = load_tnv(filename)    # create a ref so weak reference stays
        tnv_pool[filename] = tnv    # otherwise it will be gone before return!
    return tnv_pool[filename]

def enable_usual():
    """Enable GL_TEXTURE_2D and GL_COLOR_MATERIAL, which you will generally want
    to do when using TNV models"""
    usualGL.usual_for_textures()

class TNVpart(part.ScalePart):
    _default_geom = {'pos':(0,0,0), 'angle':0.0, 'scale':1.0 }
    _default_style = {'colour':(1,1,1,1), 'opaque-pieces':() }
    _style_attributes = ('colour','opaque-pieces','tnv-pieces','texture','tnv-filename')
    def __init__(self,name,**kwd):
        super(TNVpart,self).__init__(name,**kwd)
    def prepare(self):
        """Prepare TNV object and Texture object, and list of pieces to draw"""
        tnvname = self._style.get('tnv-filename')
        if tnvname:
            self.tnv = get_tnv(tnvname)
        else:
            self.tnv = None
        assert self.tnv is not None, self.__class__.__name__ + " has no tnv-filename"
        texname = self._style.get('texture')
        if texname:
            self.tex = texture.get_texture(texname)
            self._has_transparent = self.tex.transparent
        else:
            self.tex = None
            self._has_transparent = False
        pieces = self._style.get('tnv-pieces',None)
        if pieces is None:
            self.pieces = self.tnv.pieces()
            self.pieces.sort()
        else:
            self.pieces = pieces
        colour = self._style.get('colour',(1,1,1,1))
        if colour[3] != 1.0:
            self._has_transparent = True
    def setup_style(self):
        colour = self._style.get('colour',(1,1,1,1))
        glColor4f(*colour)
        if self.tex:
            enable_usual()
            self.tex.bind()

    def render(self,mode='OPAQUE'):
        opaque_pieces = self._style.get('opaque-pieces',())
        if opaque_pieces == True or not self._has_transparent:
            opaque_pieces = self.pieces
        glEnable(GL_CULL_FACE)
        if mode == 'OPAQUE':
            if self._has_transparent:
                return  # can't guarantee opaque render
            pieces = opaque_pieces
            glCullFace(GL_BACK)
            self.tnv.prepare()
            for piece in pieces:
                self.tnv.drawpiece(piece)
        elif mode == 'TRANSPARENT':
            glEnable(GL_BLEND)  # just make sure
            pieces = list(set(self.pieces) - set(opaque_pieces))
            glCullFace(GL_FRONT) # draw backfaces first
            self.tnv.prepare()
            for piece in pieces:
                self.tnv.drawpiece(piece)
            glCullFace(GL_BACK) # draw front faces over back faces
            for piece in pieces:
                self.tnv.drawpiece(piece)
        elif mode == 'PICK': #PICK
            glCullFace(GL_BACK)
            pieces = self.pieces
            self.tnv.prepare()
            for piece in pieces:
                picking.label((self.__class__.__name__, self._name, piece))
                self.tnv.drawpiece(piece)
            picking.nolabel()
        else:
            raise ValueError("render mode %s?" % mode)
