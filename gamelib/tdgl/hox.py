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
                    try:    #debug
                        op,name,axis,mult = h
                    except ValueError:  #debug
                        print h #debug
                        raise   #debug
                    t = getgeom(name)
                    if not t: continue  # skip the rest if zero movement
                    v = [0.0,0.0,0.0]
                    v[axis] = t * mult
                    glTranslatef(*v)
                elif op == ROT:
                    try:    #debug
                        op,name,axis,mult = h
                    except ValueError:  #debug
                        print h #debug
                        raise   #debug
                    a = getgeom(name)
                    if not a: continue  # skip the rest if zero rotation
                    v = [0.0,0.0,0.0]
                    v[axis] = 1.0
                    glRotatef(a * mult,*v)
            else:   # recurse into sub-list
                process(h,getgeom,drawpiece,withstyle)
    finally:
        glPopMatrix()   # GOT to do this no matter what!

