""" hox.py

  hox module :  bodies or machines made from a predefined combination of drawing operations
  and transformations.
  
    Terminal Delusion project
    
    Copyright 2009 by Peter Harris
    
    Released under the terms of the GNU General Public License v3 or later.
    (see www.gnu.org for details)
    
    
  The HoxList is a possibly nested list of actions, which are of:
    (DRAW,section_name)
    (STYLE,section_name)
    (MOVE,dimension_name,axis,multiplier) - multiplier usually 1.0
    (ROT,angle_name,axis,multiplier)- multiplier usually 1.0
  
  The list is interpreted with reference to two functions
    getgeom(name) -> return a named angle or dimension
        (can be the getgeom of a Part)
    drawpiece(name) -> perform the drawing action of a named thing
        may well be just glCallList(somedict[name])
    Changes of colour, texture binding etc. can be done as DRAW items or
    STYLE items.  The difference is you might want to omit STYLE items if
    rendering to pick rather than to a buffer.
    
    Note: the top level list and any sublists can be any iterable except
    a tuple, because tuples are the leaf-level structures for now.
"""

from gl import glPushMatrix, glPopMatrix, glTranslatef, glRotatef

DRAW = "draw"
MOVE = "move"
ROT = "rot"
STYLE = "style"
X = 0
Y = 1
Z = 2

def process(hoxlist, getgeom, drawpiece,withstyle=True):
    glPushMatrix()
    try:
        for h in hoxlist:
            if not h: continue  # all nothings are NOOPs
            if type(h) is tuple:
                op = h[0]
                if op == DRAW or (op == STYLE and withstyle):
                    drawpiece(h[1])
                elif op == MOVE:
                    op,name,axis,mult = h
                    t = getgeom(name)
                    if not t: continue  # skip the rest if zero movement
                    v = [0.0,0.0,0.0]
                    v[axis] = t * mult
                    glTranslatef(*v)
                elif op == ROT:
                    op,name,axis,mult = h
                    a = getgeom(name)
                    if not a: continue  # skip the rest if zero rotation
                    v = [0.0,0.0,0.0]
                    v[axis] = 1.0
                    glRotatef(a * mult,*v)
            else:   # recurse into sub-list
                process(h,getgeom,drawpiece,withstyle)
    finally:
        glPopMatrix()   # GOT to do this no matter what!

def compile(hoxlist,justtext=False):
    """Compile a hox list into a function"""
    cmds = ["def compiled_hox(getgeom,drawpiece,withstyle=True):"]
    _compile(hoxlist,cmds)
    fntext = "\n  ".join(cmds)
    if justtext:
        return fntext
    exec fntext
    return compiled_hox


def _compile(hoxlist,cmds):
    cmds.append("glPushMatrix()")
    for h in hoxlist:
        if not h: continue
        if type(h) is tuple:
            op = h[0]
            if op == DRAW:
                cmds.append("drawpiece('{0}')".format(h[1]))
            elif op == STYLE:
                cmds.append("if withstyle: drawpiece('{0}')".format(h[1]))
            elif op == MOVE:
                op,name,axis,mult = h
                cmds.append("t = getgeom('{0}')".format(name))
                args = [0] * 3
                args[axis] = "t * {0}".format(mult)
                cmds.append("if t: glTranslatef({0},{1},{2})".format(*args))
            elif op == ROT:
                op,name,axis,mult = h
                cmds.append("a = getgeom('{0}')".format(name))
                args = [0] * 3
                args[axis] = 1
                cmds.append("if a: glRotatef(a * {0},{1},{2},{3})".format(mult,*args))
        else:
            _compile(h,cmds)
    cmds.append("glPopMatrix()")
