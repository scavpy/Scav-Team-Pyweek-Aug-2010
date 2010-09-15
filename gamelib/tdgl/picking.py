""" picking.py
    OpenGL selection helper functions
    
    Copyright May 2007 by Peter Harris
    
    Released under the terms of the GNU General Public License
    (GPL v3 or later)
    
"""

from gl import *

# API attributes
active = False          # whether picking is underway
pickRect = None
DEFAULT_BUFFER_SIZE = 1024
# Private attributes
_labelDict  = {}
_lastLabelNum = 0
_buffer = (GLuint * DEFAULT_BUFFER_SIZE)()

def start(vpx,vpy,vpdx,vpdy,backwards=False):
    """Set up picking matrix for a region of the viewport, clear dictionary
    of objects associated with picking names (which are GL_INTs)
    
    Usage:
      Before setting up the projection call picking.start(x,y,dx,dy)
      where (x,y) is the centre of the target rectangle of the viewport.
      
    If you have already set up projection, need to call with backwards=True,
    which will get a copy of the projection matrix and multiply it back in
    after setting up the picking matrix.

    Otherwise you should call picking.project() before setting up the
    projection.
    """
    global active, pickRect, _lastLabelNum
    if active:
        raise ValueError("picking already active")
    _labelDict.clear()
    _lastLabelNum = 0
    active = True
    pickRect = (vpx, vpy, vpdx, vpdy)
    glSelectBuffer(DEFAULT_BUFFER_SIZE,_buffer)
    glRenderMode(GL_SELECT)
    glInitNames()
    glPushName(0)
    if backwards:
        projection_matrix = glGetFloatv(GL_PROJECTION_MATRIX)
        project()
        glMultMatrixf(projection_matrix)
    
def project():
    """Set up picking projection if picking is active. This can be used
    from other modules to make sure the picking projection is set, in case
    something else may have messed up the projection matrix
    (e.g. a scene with parts in both Ortho and Perspective projections,
    all of which may need to be picked)
    Can be used when picking is not active, as a glLoadIdentity.
    *** Leaves matrix mode in GL_PROJECTION. ***
    """
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    if active:
        x,y,dx,dy = pickRect
        vport = (GLint*4)()
        glGetIntegerv(GL_VIEWPORT,vport)
        gluPickMatrix(x,y,dx,dy,vport)

class Hit(object):
    """Picking labels are stored as Hit objects, containing a main picking target
     and any other keyword values that are added as attributes"""
    def __init__(self,target,**kw):
        self.target = target
        self.__dict__.update(kw)

def label(ob,**kw):
    """Set a label for the object. Anything drawn up to the next label()
    or nolabel() that is picked will cause end() to include the object in
    its return value"""
    global _lastLabelNum
    _lastLabelNum += 1
    _labelDict[_lastLabelNum] = Hit(ob,**kw)
    glLoadName(_lastLabelNum)
    return _lastLabelNum
    
def nolabel():
    """End of drawing a labelled object, as far as picking is concerned"""
    glLoadName(0)

def end():  # end --> [(minz,maxz,ob)]
    """End GL_SELECT mode and get a list of objects added by picking.label()
    that overlapped the target rectangle, together with their z-distance range
    """
    global active
    active = False
    hits = glRenderMode(GL_RENDER)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    picklist = []
    j = 0 # index into picking buffer
    for i in range(hits):
        stackdepth = _buffer[j]
        minz = float(_buffer[j+1]) / 0x7fffffff
        maxz = float(_buffer[j+2]) / 0x7fffffff
        hit = _labelDict.get(_buffer[j+3])
        if hit:
            hit.minz = minz
            hit.maxz = maxz
            picklist.append((minz,maxz,hit))
        j += 3 + stackdepth
    picklist.sort()
    return picklist

    
