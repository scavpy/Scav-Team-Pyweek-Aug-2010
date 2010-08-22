"""
Maker for TNV files. These are pickled dicts containing
    {'array': arguments to glInterleavedArrays
     'pieces': dict of { 'name':  arguments to glDrawArrays() }}

At it's simplest, you unpickle a TNV file, call glInterleavedArrays,
bind a 2D texture, set glColor to white, and call glDrawArrays() once for
each of the pieces.  You could also draw each piece separately with different
colour, shininess or even different textures.

Normals can be either flat or rounded (averaged over all faces sharing a vertex).

Texture coords are based on named regions in texture space, encoded as lists of
(s,t) coords.  The coords for a vertex are calculated either by directly mapping
each vertex to one of the corner points of a region, or by doing a calculation
based on the position in space of the vertex relative to other vertices in the
same piece.

Copyright 2005 Peter Harris, released under the terms of the GNU General
Public License. See www.gnu.org for details.

"""
from __future__ import division
import cPickle as pickle
from sets import Set
from itertools import izip, repeat
from math import atan2, degrees, fmod, sqrt
import struct

from OpenGL.GL import GL_T2F_N3F_V3F, GL_TRIANGLES, GL_QUADS, GL_POLYGON
from OpenGL.GL import GL_POINTS, GL_LINES

from tdlib.vec import normalise, plane_normal

class Face(object):
    def __init__(self,keys,vertices,tcoords,rounded=False):
        nvert = len(vertices)
        assert len(vertices[0]) == 3, "Vertices must be 3D"
        assert len(tcoords[0]) == 2, "Texture Coords must be 2D"
        self.keys = keys
        self.vertices = vertices
        tc=[]
        while len(tc) < nvert:
            tc += tcoords
        self.tcoords = tc[:nvert]
        self.rounded = rounded
        if len(vertices) >= 3:
            self.flat_normal = plane_normal(*self.vertices[:3])
        else:
            # not enough coords to calculate normals - so guess arbitrarily.
            self.flat_normal = vertices[0]
        self.normals = [self.flat_normal] * nvert
    def __len__(self):
        return len(self.vertices)
    def unpack(self):
        """Unpack into a list of floats, 2 per texture point + 3 per normal + 3 per vertex"""
        floats = []
        for t,n,v in izip(self.tcoords,self.normals,self.vertices):
            floats.extend(t)
            floats.extend(n)
            floats.extend(v)
        return floats
    def __repr__(self):
        """Show info"""
        return '<Face ' + str(zip(self.keys,self.tcoords,self.normals,self.vertices)) + ' >\n'

def nearest_angle(a1,a2):
    """return a1 or a1+360 depending on which is nearest to a2"""
    diff = abs(a2 - a1)
    if diff > 180:
        return a1 + 360
    else:
        return a1

def cylindrical_face_angles(vertices):
    angles = [fmod(degrees(atan2(y,x))+360,360) for x,y,z in vertices]
    prev = angles[0]
    for i,angle in enumerate(angles):
        a = nearest_angle(angle,prev)
        prev = a
        angles[i] = a
    return angles
    
    
class TextureRule(object):
    """A rule for converting a list of (x,y,z) vertices into (s,t) texture coords
    The rule may not even look at the vertices, or it may do quite a complex
    calculation to convert them, using the bounding box or centre of the
    piece_vertices passed in."""
    def __init__(self,maptype='untextured',regions={},piece_vertices=[]):
        self.convert = getattr(self,maptype,self.untextured)
        self.regions = regions  # dictionary: named lists of texture coord pairs
        self.piece_vertices=Set(piece_vertices)  # set of (x,y,z) vertices
        self.centre, self.minima, self.maxima = self._piece_box()
        
    def untextured(self,vertices,dummy=None):
        return [(0,0)] * len(vertices)
    
    def direct(self,vertices,region=None):
        n = len(vertices)
        try:
            return self.regions[region][:n] # one set of coords per vertex
        except KeyError:
            return self.untextured(vertices)
        
    def spherical(self,vertices,region=None):
        """Map each vertex to spherical texture coords around centre point"""
        s0,t0,sf,tf = self._tex_rectangle(region)
        cx,cy,cz = self.centre
        tcoords = []
        relative = [(x - cx, y - cy, z - cz) for x,y,z in vertices]
        angles = cylindrical_face_angles(relative)
        for i,(x,y,z) in enumerate(relative):
            theta = angles[i]
            d = (x*x + y*y)**0.5
            phi = degrees(atan2(z,d)) + 90
            s = s0 + sf * (theta / 360.0)
            t = t0 + tf * (phi / 180.0)
            tcoords.append((s,t))
        return tcoords
    
    def cylindrical(self,vertices,region=None):
        """Map each vertex to vertical cylindrical coords around centre point,
        map t-coord based on bounding box of skeleton vertices"""
        s0,t0,sf,tf = self._tex_rectangle(region)
        cx,cy,cz = self.centre
        minz = self.minima[2]
        height = self.maxima[2] - minz
        tcoords = []
        relative = [(x - cx, y - cy, z - minz) for x,y,z in vertices]
        angles = cylindrical_face_angles(relative)
        for i,(x, y, z) in enumerate(relative):
            theta = angles[i]
            s = s0 + sf * (theta / 360.0)
            t = t0 + tf * (z / height)
            tcoords.append((s,t))
        return tcoords

    def _tex_rectangle(self,region):
        if region not in self.regions:
            s0 = t0 = 0
            sf = tf = 1
        else:
            texcoords = self.regions[region]
            scoords = [s for s,t in texcoords]
            tcoords = [t for s,t in texcoords]
            s0 = min(scoords)
            sf = max(scoords) - s0
            t0 = min(tcoords)
            tf = max(tcoords) - t0
        return s0,t0,sf,tf
    
    def _piece_box(self):
        cx = cy = cz = 0.0
        minv = [float('inf')] * 3
        maxv = [float('-inf')] * 3
        N = 0.0
        for x,y,z in self.piece_vertices:
            cx += x
            cy += y
            cz += z
            N += 1
            minv = map(min,minv,(x,y,z))
            maxv = map(max,maxv,(x,y,z))
        if N:
            cx /= N
            cy /= N
            cz /= N
        return (cx,cy,cz),minv,maxv

def triangulator_iterators(seq1,seq2,closed=False):
    """Return a pair of iterators for use by triangulator.
    If closed is true, the last generated value of both iterators will be the same
    as the first element.
    """
    if closed and seq1:
        seq1 = list(seq1) + [seq1[0]]
    if closed and seq2:
        seq2 = list(seq2) + [seq2[0]]
    return iter(seq1),iter(seq2)

def sort_by_angle(skel,contour,coord1=0,coord2=1):
    """Sort a list of vertex names by angle about their centre.
    Angle is by default atan2(y,x) relative to the centre.
    By choosing different coord1,coord2 you can get angle in a different plane"""
    cx =cy = cz = 0.0
    included = []
    for k in contour:
        try:
            x,y,z = skel[k]
            cx += x
            cy += y
            cz += z
            included.append((k,(x,y,z)))
        except KeyError:
            pass
    if included:
        N = len(included)
        centre = cx/N,cy/N,cz/N
        decorated = [ (atan2(vertex[coord2] - centre[coord2],
                             vertex[coord1] - centre[coord1]),k)
                      for k,vertex in included ]
        decorated.sort()
        sorted_contour = [ k for a,k in decorated ]
    else:
        sorted_contour = []
    return sorted_contour
            
def triangulator(skel,contourA,contourB,closed=False):
    """Generate triangles from two contours, which should be lists of skeleton
    vertex names ie. (section,num).  They should be sorted consistently according
    to some geometrical property (e.g. sort_by_angle for closed horizontal contours)
    The generator returns 3-tuples of vertex names, which represent the triangles.

    Algorithm adapted from "An Introductory Course in Computer Graphics" by
    Dr Richard Kingslake (Chartwell-Bratt)
    """
    iterA, iterB = triangulator_iterators(contourA, contourB, closed)
    def dist(k1,k2):
        """Distance between vertices"""
        x1,y1,z1 = skel[k1]
        x2,y2,z2 = skel[k2]
        x = x2 - x1
        y = y2 - y1
        z = z2 - z1
        return sqrt(x*x + y*y + z*z)

    try:
        curA = iterA.next()
        curB = iterB.next()
    except StopIteration:
        raise ValueError("Both contours must have 1 or more vertices")

    Aleft = True    # there are vertices left in contour A
    Bleft = True    # there are vertices left in contour B

    try:
        nexA = iterA.next()
    except StopIteration:
        nexA = curA
        Aleft = False

    try:
        nexB = iterB.next()
    except StopIteration:
        nexB = curB
        Bleft = False

    while Aleft or Bleft:
        # for this loop to terminate: each time it must consume
        # one unused vertex from either contour A or contour B
        B_closer = dist(curA,nexB) <= dist(curB,nexA)
        choose_B = (B_closer and Bleft) or (not Aleft)
        if choose_B:
            yield (curA,nexB,curB)
            curB = nexB
            try:
                nexB = iterB.next()
            except StopIteration:   # run out of vertices on contour B
                Bleft = False
        else:
            yield (curA,nexA,curB)
            curA = nexA
            try:
                nexA = iterA.next()
            except StopIteration:   # run out of vertices on contour A
                Aleft = False
    
class VertexSkeleton(dict):
    """A dictionary of vertices, keyed by (section,num)"""
    def add(self,section,vertex):
        """Add a vertex, taking the next number from the specified section"""
        try:
            num = max([num for sect,num in self if sect == section]) + 1
        except:
            num = 0
        self[section,num] = tuple(vertex)
        return section,num
    def save(self,filename):
        """Save self as a pickled plain dict"""
        d = {}
        d.update(self)
        pickle.dump(d,file(filename,'wb'),True)
    def load(self,filename,merge=False):
        if not merge:
            self.clear()
        d = pickle.load(file(filename))
        self.merge(d)
    def merge(self,other):
        for k,v in other.items():
            if k in self:
                self.add(k[0],v)
            else:
                self[k] = v

default_primitives = {1:GL_POINTS, 2:GL_LINES, 3:GL_TRIANGLES, 4:GL_QUADS}

class TNVmaker:
    def __init__(self,skel,tmap):
        self.length = 0
        self.skel = skel
        self.tmap = tmap
        self.face_lists = {}
        self.numvert = {}
        self.primitive={}
        
    def add_piece(self,name,faces,maptype='direct',primitive=None):
        """Add a piece, as a list of (vertices,rounded,texture_region)
        It guesses the kind of primitive based on number of vertices
        per face. You can specify GL_TRIANGLE_FAN or whatever if you
        want something other than the default. In particular, it will
        only ever guess GL_POLYGON for > 4 vertices.
        """
        if faces:
            fsizes = [len(face[0]) for face in faces]
            minv = min(fsizes)
            maxv = max(fsizes)            
            if minv != maxv:
                raise ValueError('Not all faces have same number of vertices')
        else:
            minv = 1    # no actual faces
        self.numvert[name] = minv
        if primitive:
            self.primitive[name] = primitive
        else:
            self.primitive[name] = default_primitives.get(minv,GL_POLYGON)
            
        skelset = Set()
        for v,r,t in faces:
            skelset |= Set(v)      # union of all vertices in all faces of the piece
        piece_vertices = [self.skel[v] for v in skelset if v in self.skel]
        rule = TextureRule(maptype,self.tmap,piece_vertices)
        facelist = []
        self.face_lists[name] = facelist
        for keys,r,t in faces:
            vertices = [self.skel[k] for k in keys if k in self.skel]
            if len(vertices) == minv:   # a complete face with no missing bits
                tcoords = rule.convert(vertices,t)
                facelist.append(Face(keys,vertices,tcoords,r))
        
    def calculate_rounded(self):
        """Calculate rounded normals for all faces which are rounded.
        The rounded normal at a vertex is the normalised sum of the flat normals of all
        rounded faces that include it.
        """
        all_rounded = []
        for piece in self.face_lists:
            all_rounded.extend([f for f in self.face_lists[piece] if f.rounded])
        for face in all_rounded:
            # calculate normals for the face
            for i,key in enumerate(face.keys):
                # i is 0 to N-1 for N vertices, key is vertex name
                adjacent = [f for f in all_rounded if key in f.keys] # faces that use vertex
                norm = [0.0,0.0,0.0]
                for j in 0,1,2: # x,y,z component of normal
                    norm[j] = sum([f.flat_normal[j] for f in adjacent]) # sum flat normals
                norm = normalise(*norm) # and normalise them
                face.normals[i] = norm

    def extract(self):
        """Extract the TNV object"""
        floats = []
        first = 0
        pieces = {}
        for name in self.face_lists:
            flist = self.face_lists[name]
            nvert = self.numvert[name]
            mode = self.primitive[name]
            count = nvert * len(flist)
            for face in flist:
                floats.extend(face.unpack())
            pieces[name] = (mode, first, count)
            first += count
        # TNV files use little-endian order for string
        floatstrings = [struct.pack("<f",f) for f in floats]
        tnv = {'array':(GL_T2F_N3F_V3F,0,''.join(floatstrings)),
                'pieces':pieces }
        return tnv
    
    def dump(self,filename):
        """Save as pickled dictionary"""
        tnv = self.extract()
        pickle.dump(tnv,file(filename,'wb'),True)
        

if __name__ == '__main__':
    cube_skel = {
        ('top',0):(0,0,1),
        ('top',1):(1,0,1),
        ('top',2):(1,1,1),
        ('top',3):(0,1,1),
        ('bot',0):(0,0,0),
        ('bot',1):(1,0,0),
        ('bot',2):(1,1,0),
        ('bot',3):(0,1,0),
        ('top',4):(0.5,0.5,1.0),
        }

    texture_skel = {
        'S':[(0,0),(1,0),(1,1),(0,1)],
        'T':[(0,0),(1,0),(0.5,1.0)]
        }
            
    cube_faces = [
        ([('top',2), ('bot',2), ('bot',3), ('top', 3)],False,'S'), #north
        ([('top',0), ('top',1), ('top',2), ('top', 3)],False,'S'), #top
        ([('bot',1), ('bot',2), ('top',2), ('top', 1)],False,'S'), #east
        ([('bot',0), ('bot',1), ('top',1), ('top', 0)],False,'S'), #south
        ([('bot',3), ('bot',0), ('top',0), ('top', 3)],False,'S'), #west
        ([('bot',0), ('bot',3), ('bot',2), ('bot', 1)],False,'S'), #bot
        ]

    rcube_faces = [(v,True,t) for (v,r,t) in cube_faces]

    pyramid_faces = [
        ([('bot',2), ('bot',3), ('top',4)],True,'T'), #north
        ([('bot',1), ('bot',2), ('top',4)],True,'T'), #east
        ([('bot',0), ('bot',1), ('top',4)],True,'T'), #south
        ([('bot',3), ('bot',0), ('top',4)],True,'T'), #west
        ]

    tile_faces = [
        ([('bot',0), ('bot',1), ('bot',2), ('bot', 3)],False,'S')
        ]

    t1 = TNVmaker(cube_skel, texture_skel)
    t1.add_piece('cube',cube_faces)
    t1.add_piece('rcube',rcube_faces,maptype='spherical')
    t1.add_piece('pyramid',pyramid_faces, maptype='cylindrical')
    t1.add_piece('tile',tile_faces)
    t1.calculate_rounded()
    t1.dump('t1.tnv')

