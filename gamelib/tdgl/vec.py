# vector normals module
"""Utilities for calculating face normals on a triangle mesh, plus Vec class
for simple 3D vectors.

Works better if you have psyco

This file copyright Peter Harris Sep 2007, released under the terms of the
GNU GPL v3 or later. See www.gnu.org for details.

"""

try:
    import psyco
    from psyco import compact as __baseclass
    using_psyco = True
except ImportError:
    using_psyco = False
    __baseclass = object
    
from math import sqrt

def normalise(x,y,z):
    d = sqrt(x*x + y*y + z*z)
    if d:
        return (x/d,y/d,z/d)
    else:
        return 0.0,0.0,0.0

def plane_normal(vertex1,vertex2,vertex3):
    """Vector normal to the triangle given by 3 vertices"""
    v = Vec(vertex1)
    v2 = Vec(vertex2) - v
    v3 = Vec(vertex3) - v
    return v2.cross(v3).normalise()

def away_from(vertex,centre):
    """Unit vector in direction of line segment from 'centre' to 'vertex'"""
    v = [0.0] * 3
    for i in 0,1,2:
        v[i] = vertex[i] - centre[i]
    return normalise(v[0],v[1],v[2])
    
class Vec(__baseclass):
    """3d vector"""
    if not using_psyco:
        __slots__ = ('x','y','z')

    def __init__(self,x,y=None,z=0.0):
        if y is None:
            if type(x) is tuple:
                self.x = float(x[0])
                self.y = float(x[1])
                if len(x) == 3:
                    self.z = float(x[2])
                else:
                    self.z = 0.0
            else:
                try:
                    self.x = x.x
                    self.y = x.y
                    self.z = x.z
                except AttributeError:
                    try:
                        self.x = x.i
                        self.y = x.j
                        self.z = x.k
                    except:
                        raise ValueError("Can't make a Vec from a %s" % type(x))
        else:
            self.x = float(x)
            self.y = float(y)
            self.z = float(z)
        
    def dot(self,other):
        """ inner product """
        if type(other) is not Vec:
            other = Vec(other)
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def length(self):
        """ length of vector """
        return sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)
    
    def __mul__(self, k):
        """ multiply by scalar """
        return Vec(self.x * k, self.y * k, self.z * k)
    __rmul__ = __mul__
        
    def __add__(self, other):
        """ vector addition """
        if type(other) is not Vec:
            other = Vec(other)
        return Vec(self.x + other.x, self.y + other.y, self.z + other.z)
    __radd__ = __add__
        
    def __sub__(self, other):
        """ vector subtraction """
        if type(other) is not Vec:
            other = Vec(other)
        return Vec(self.x - other.x, self.y - other.y, self.z - other.z)
    __rsub__ = __sub__

    def __div__(self,k):
        """ multiply by reciprocal of scalar """
        d = 1.0/k
        return self * d
    __rdiv__ = __div__
        
    def __neg__(self):
        """ Reverse direction of vector """
        return Vec(-self.x, -self.y, -self.z)

    def __nonzero__(self):
        return self.x != 0.0 or self.y != 0.0 or self.z != 0.0
        
    def projXY(self):
        """project onto XY"""
        return Vec(self.x, self.y)
        
    def orthoXY(self):
        """orthogonal to projection onto XY"""
        return Vec(-self.y, self.x)
        
    def proj(self,other):
        """Projection of self onto another vector"""
        if type(other) is not Vec:
            other = Vec(other)
        if not other:
            return Vec(0.0,0.0,0.0)
        else:
            return other * (self.dot(other) / other.dot(other))
    
    def normalise(self):
        d = self.length()
        if d == 0.0:
            return Vec(0.0,0.0,0.0)
        return Vec(self.x / d, self.y / d, self.z / d)

    def __repr__(self):
        return "Vec(%f,%f,%f)" % (self.x,self.y,self.z)
        
    def __str__(self):
        return "Vec(%s,%s,%s)" % (str(self.x),str(self.y),str(self.z))
        
    def cross(self,other):
        """cross product"""
        if type(other) is not Vec:
            other = Vec(other)
        return Vec(self.y * other.z - self.z * other.y,
                   self.z * other.x - self.x * other.z,
                   self.x * other.y - self.y * other.x)
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

if using_psyco:
    psyco.bind(Vec)
    psyco.bind(normalise)
    psyco.bind(plane_normal)
    psyco.bind(away_from)
