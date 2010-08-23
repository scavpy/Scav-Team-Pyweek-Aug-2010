"""
   ObjPart - a part.Part constructed from a (subset of) the
   wavefront .obj format

    Copyright Peter Harris, 2009
    released under conditions of GNU GPL,v3 or later

    NB: In Blender, export to Wavefront OBJ file with high-quality normals
        and NOT Rotate x90
"""

import part, picking
from tdgl.gl import *
from pyglet import resource
from weakref import WeakValueDictionary

import material

obj_pool = WeakValueDictionary()


class WFObj(object):
    """ a set of display lists constructed from a .obj file
    """
    def __init__(self,fname,swapyz=True):
        self.mesh_dls = {}
        self.mat_dls = material.MDLdict()
        self.mesh_trans = {}
        self.load_obj(fname,swapyz)
    def __del__(self):
        if glDeleteLists:
            for dl in self.mesh_dls.values():
                glDeleteLists(dl,1)
            
    def load_obj(self,fname,swapyz=False,on_polygon=None):
        """ Load the .obj file, drawing each sub-object into a display
            list, and setting each material into a display list

            A piece called xxx_Origin has one vertex which marks the origin
            for piece 'xxx', and just adds a glTranslate before and
            after drawing 'xxx'.
        """
        objlines = resource.location(fname).open(fname,"r")
        self.origins = {}
        def int0(s):
            if s:
                return int(s)
            else:
                return 0
        piece = ''
        mesh_dl = None
        npoints = 0
        primitives = {1:GL_POINTS, 2: GL_LINES, 3:GL_TRIANGLES, 4:GL_QUADS}
        vertices = []
        normals = []
        tcoords = []
        for line in objlines:
            tokens = line.split()
            if not tokens or line[0] == '#':
                continue
            key = tokens[0]
            if key == 'mtllib':
                self.mat_dls.load(tokens[1])
            elif key == 'o':
                if piece.endswith("_Origin") and len(vertices):
                    self.origins[piece[:-7]] = vertices[-1]
                elif npoints:
                    glEnd()
                    npoints = 0
                if mesh_dl:
                    glEndList()
                piece = tokens[1]
                if piece.endswith("_Origin"):
                    mesh_dl = None
                else:
                    mesh_dl = self.mesh_dls[piece] = glGenLists(1)
                    self.mesh_trans[piece] = False
                    glNewList(mesh_dl,GL_COMPILE)
            elif key == 'v':
                vx,vy,vz = map(float,tokens[1:4])
                if swapyz:
                    vx,vy,vz = vx,vz,vy
                vertices.append((vx,vy,vz))
            elif key == 'vn':
                normals.append(map(float,tokens[1:4]))
            elif key == 'vt':
                tcoords.append(map(float,tokens[1:3]))
            elif key == 'usemtl':
                if npoints:
                    glEnd()
                    npoints = 0
                mdl = self.mat_dls.get(tokens[1])
                if mdl is not None: # a material we have loaded
                    glCallList(mdl)
                    self.mesh_trans[piece] |= self.mat_dls.is_transparent(tokens[1])
            elif key == 'f':
                points = [map(int0, s.split('/'))
                          for s in tokens[1:]]
                if len(points) != npoints:
                    if npoints:
                        glEnd()
                    npoints = len(points)
                    prim = primitives.get(npoints, GL_POLYGON)
                    glBegin(prim)
                for v, t, n in points:
                    if n: glNormal3f(*normals[n-1])
                    if t: glTexCoord2f(*tcoords[t-1])
                    glVertex3f(*vertices[v-1])
                if on_polygon:
                    on_polygon(piece,[vertices[v-1] for v,t,n in points])
                if npoints > 4: # GL_POLYGON
                    npoints = -1 # can't continue without a glEnd()
        if piece.endswith("_Origin") and len(vertices):
            self.origins[piece[:-7]] = vertices[-1]
        elif npoints:
            glEnd()
            npoints = 0
        if mesh_dl:
            glEndList()
        # Now wrap extra glTranslatef around the pieces with origins
        for piece,(vx,vy,vz) in self.origins.items():
            dl_old = self.mesh_dls.get(piece)
            if not dl_old:
                continue
            dl_new = glGenLists(1)
            self.mesh_dls[piece] = dl_new
            self.mesh_dls[dl_old] = dl_old # stash it so __del__ can release it later
            with gl_compile(dl_new):
                glTranslatef(-vx,-vy,-vz)
                glCallList(dl_old)
                glTranslatef(vx,vy,vz)
            
    def pieces(self):
        return sorted(self.mesh_dls.keys())

    def drawpiece(self,pname):
        try:
            glCallList(self.mesh_dls[pname])
        except KeyError:
            pass
    def is_transparent(self,piece):
        return self.mesh_trans[piece]


def get_obj(fname):
    if fname not in obj_pool:
        obj = WFObj(fname,False)
        obj_pool[fname] = obj
    return obj_pool[fname]

class ObjPart(part.Part):
    _has_transparent = True
    """ A part rendered from a WFObj """
    _style_attributes = ('obj-pieces', 'opaque-pieces',
                         'obj-filename',
                         'override-mtl', 'mtl-override-pieces')
    def __init__(self,name='',geom=None,style=None, **kw):
        super(ObjPart,self).__init__(name,geom=geom, style=style, **kw)
    def prepare(self):
        """ Prepare WFObj from style """
        fname = self.getstyle("obj-filename")
        if fname:
            self.obj = get_obj(fname)
        else:
            self.obj = None
            print "ObjPart ",self._name,"failed to load",fname 
        
        self.pieces = self.getstyle('obj-pieces')
        if self.pieces is None:
            self.pieces = self.obj.pieces()

    def setup_style(self):
        glEnable(GL_LIGHTING)

    def render(self,mode):
        opaque_pieces = self.getstyle('opaque-pieces',())
        override_mtl = self.getstyle('override-mtl',None)
        override_dl = material.get(override_mtl)
        if override_dl:
            override_pieces = set(self.getstyle('mtl-override-pieces',()))
        else:
            override_pieces = ()
        glEnable(GL_CULL_FACE)
        if mode == 'OPAQUE':
            pieces = opaque_pieces
            if not pieces:
                pieces = self.pieces
            glCullFace(GL_BACK)
            for piece in pieces:
                if piece in override_pieces:
                    glCallList(override_dl)
                self.obj.drawpiece(piece)
        elif mode == 'TRANSPARENT':
            glEnable(GL_BLEND)
            pieces = list(set(self.pieces) - set(opaque_pieces))
            glCullFace(GL_FRONT) # draw backfaces first
            for piece in pieces:
                if piece in override_pieces:
                    glCallList(override_dl)        
                self.obj.drawpiece(piece)
            glCullFace(GL_BACK) # draw front faces over back faces
            for piece in pieces:
                if piece in override_pieces:
                    glCallList(override_dl)        
                self.obj.drawpiece(piece)
        elif mode == 'PICK':
            glCullFace(GL_BACK)
            pieces = self.pieces
            for piece in pieces:
                picking.label((self.__class__.__name__, self._name, piece))
                self.obj.drawpiece(piece)
            picking.nolabel()
                
