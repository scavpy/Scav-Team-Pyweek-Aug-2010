"""
 material.py

  Manage OpenGL materials

   Copyright Peter Harris, Sep 2007

   GPL v3 or later
"""
from gl import *
from pyglet import resource

Mat4Floats = GLfloat*4

NOTEXTURES = False

class MDLdict(object):
    """Materials display lists"""
    def __init__(self):
        self.mat_dls = {}
        self.mat_textures = {}
        self.mat_trans = {}
    def __del__(self):
        if glDeleteLists:
            for dl in self.mat_dls.values():
                glDeleteLists(dl,2)
    def get(self,k):
        return self.mat_dls.get(k)
    def load(self,fname):
        mtllines = resource.location(fname).open(fname,"r")
        mname = None
        mat_dl = None
        mat_params = {'Ka':GL_AMBIENT, 'Kd': GL_DIFFUSE, 'Ks':GL_SPECULAR}
        tname = None
        for line in mtllines:
            tokens = line.split()
            if not tokens or line[0] == '#':
                continue
            if tokens[0] == 'newmtl':
                if mname:
                    if not tname: glDisable(GL_TEXTURE_2D)
                    glEndList()
                tname = None
                mname = tokens[1]
                mat_dl = self.mat_dls.get(mname)
                if mat_dl is None:
                    mat_dl = self.mat_dls[mname] = glGenLists(2)
                glNewList(mat_dl, GL_COMPILE)
            elif tokens[0] == 'Ns':
                glMaterialf(GL_FRONT, GL_SHININESS, float(tokens[1]))
            elif tokens[0] in mat_params:
                params = map(float,tokens[1:])
                floats4 = Mat4Floats(1.0,1.0,1.0,1.0)
                for i,f in enumerate(params):
                    floats4[i] = f
                self.mat_trans[mname] = (floats4[3] < 1.0)
                glMaterialfv(GL_FRONT, mat_params[tokens[0]],floats4)
            elif tokens[0] == 'map_Kd' and not NOTEXTURES:
                # need a texture
                glEnable(GL_TEXTURE_2D)
                glCallList(mat_dl+1) # will bind texture
                glEndList()
                tname = tokens[1]
                tex = resource.texture(tokens[1])
                glNewList(mat_dl+1,GL_COMPILE)
                if tex:
                    self.mat_textures[tname] = tex
                    trans = self.mat_trans.get(mname,False)
                    self.mat_trans[mname] = trans
                    glEnable(GL_TEXTURE_2D)
                    glBindTexture(GL_TEXTURE_2D,tex.id)
                # will end list before starting next one, or at end
        if mname:
            if not tname: glDisable(GL_TEXTURE_2D)
            glEndList()
    def select(self,k):
        dl = self.get(k)
        if dl:
            glCallList(dl)
    def is_transparent(self,k):
        return self.mat_trans.get(k,False)
    
default_mdl_dict = MDLdict()
def load(fname):
    default_mdl_dict.load(fname)
def get(matname):
    return default_mdl_dict.get(matname)
def select(matname):
    default_mdl_dict.select(matname)
def is_transparent(matname):
    return default_mdl_dict.is_transparent(matname)
