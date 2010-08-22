#! /usr/bin/env python
""" A FloorSet is a set of objects in 3 dimensional space, which may be treated
    as Floors or Obstacles. The region occupied by the object may be one of a few
    kinds of shape that make the maths not too hard.
    
    The region may be an upright cylinder, a cuboid rotated about its vertical axis,
    or an arbitrary convex prism.  A region can be tested to see if it overlaps a
    given upright cylinder. The true return value is a pair (z0,z1) being the
    range of heights over which the overlap occurs.
    
    A Floor provides a method to determine a height at given x,y position which is
    the walking-height of that floor.
    
    An Obstacle is just a Region with a flag set to indicate it is to be treated
    as such.
    
    The Floorset allows a test of whether a cyclinder may be placed unobstructed
    at x,y within a range of heights. The z position is returned.
    
    A Walker placed in a floorset can be moved about within it subject to the
    constraints that if it is at position (x,y,z), it may move to (x',y',z')
    where z' is the walking height of the floorset at x,y plus or minus a vertical
    range (the step height), and the cylinder occupied by the walker is not
    obstructed there.
    

    Copyright Sep 2007 by Peter Harris
    Released under the terms of the GNU General Public License v3 or later
    see www.gnu.org for details.
"""
from __future__ import division
from math import fmod, sin, cos, radians
try:
    set
except NameError:
    from sets import Set as set


from part import Part
from vec import Vec

class AbstractRegion(object):
    """No point in creating one of these, it just has some shared methods"""
    pos = Vec(0,0,0) # generally make the pos a Vec, but allow a tuple
    height = 1
    _a = 0
    _sina = 0
    _cosa = 1
    def z_overlap(self,cz,height):
        if type(self.pos) == tuple:
            rz = self.pos[2]
        else:
            rz = self.pos.z
        rh = self.height
        minrz = min(rz,rz+rh)    # NB heights can be negative
        maxrz = max(rz,rz+rh)
        mincz = min(cz,cz+height)
        maxcz = max(cz,cz+height)
        bottom = max(minrz, mincz)
        top = min(maxrz, maxcz)
        if bottom <= top:
            return bottom,top
        return None
    def _get_angle(self):
        return self._a
    def _set_angle(self,a):
        """Want to cache cos and sin of angle when changed, not calculate
        it every time its needed"""
        self._a = a
        self._sina = sin(radians(a))
        self._cosa = cos(radians(a))
    angle = property(_get_angle,_set_angle)


class CylinderRegion(AbstractRegion):
    def __init__(self,(x,y,z),height=1,radius=1):
        self.pos = Vec(x,y,z)
        self.height = height
        self.radius = radius
    def overlaps(self,(x,y,z),height,radius):
        ztest = self.z_overlap(z,height)
        if ztest:
            if type(self.pos) == tuple:
                self.pos = Vec(self.pos)
            centre = self.pos.projXY()
            v = centre - (x,y)
            d2 = v.dot(v)
            reach = self.radius + radius
            if d2 > (reach * reach):
                return None
        return ztest
    def __and__(self,other):
        """Overload  r1 & r2 operator to mean:
            r2.overlaps(r1.pos,r1.height,r1.radius)
        (by analogy with intersection.  I admit it's not a great analogy)
        """
        return other.overlaps(tuple(self.pos), self.height, self.radius)
    
class PrismRegion(AbstractRegion):
    """A Polygonal prism uses some vector algebra to decide whether
    a point lies within it, and if not then whether it lies within
    a given distance of any part of it.
    
    Some conjectures (no proof offered)
      A if you follow the boundary of a convex polygon anticlockwise,
        any point outside the polygon will at some point be on your right.
        
      B if a disc whose centre is outside the polygon intersects any sides
        of it, it must intersect at least one of the sides for which the
        centre of the disc is "on the right" as above. The others are on the
        side of the polygon facing away.
        
      C if the centre of the disc is on the right of a side and it is further
        away from the line passing through that side than the disc's radius, it
        cannot intersect the polygon anywhere. (All other sides are "on the left"
        so no part of the disc can reach them.)
    """

    def __init__(self,(x,y,z),boundary,height=1,angle=0):
        self.pos = Vec(x,y,z)
        self.height = height
        self.angle = angle
        self.vertices = boundary[:] # list of 2d or 3d coord tuples
    def overlaps(self,(x,y,z),height,radius):
        ztest = self.z_overlap(z,height)
        if ztest:
            if type(self.pos) == tuple:
                self.pos = Vec(self.pos)
            # see if circle overlaps polygon
            centre = self.pos.projXY()
            v = Vec(x,y) - centre  # vector from polygon centre to circle centre
            r2 = radius * radius
            # rotate v around centre so it's in same coord system as polygon
            P = Vec(v.x * self._cosa + v.y * self._sina, v.y * self._cosa - v.x * self._sina)
            # follow boundary anti-clockwise
            v0 = Vec(self.vertices[-1]).projXY()
            any_outside = False
            for vtuple in self.vertices:
                v1 = Vec(vtuple).projXY()
                u = v1 - v0 # vector along side of polygon
                uperp = Vec(u.y, -u.x) # perpendicular to u, away from polygon
                w = P - v0  # vector from v0 to P
                outside = (w.dot(uperp) > 0) # w in "same direction" as uperp 
                if outside: # Conjectures A, B
                    if not r2:
                        return None    # outside and of zero size
                    any_outside = True
                    wproj = (w.proj(uperp)) # length is dist from side
                    d2 = wproj.dot(wproj)
                    if d2 > r2:
                        return None    # Conjecture C
                    behind_v0 = (u.dot(w) < 0)
                    if behind_v0: # v0 is nearest point to P
                        if w.dot(w) < r2:  # and within radius
                            return ztest # must overlap
                    else:
                        v = P - v1
                        behind_v1 = (v.dot(-u) < 0)
                        if behind_v1:  #  v1 is nearest point to P
                            if v.dot(v) < r2:  # and within radius
                                return ztest
                        else: # P between v0 and v1, and we know it's near enough
                            return ztest
                v0 = v1 # proceeding anti-clockwise
            # all the way round without finding a crossing
            if any_outside:  # centre not within polygon
                return None
        return ztest

class CuboidRegion(PrismRegion):
    def __init__(self,(x,y,z),width=1,length=1,height=1,angle=0):
        hw = width / 2
        hl = length / 2
        boundary = [(-hw,-hl),(hw,-hl),(hw,hl),(-hw,hl)]
        super(CuboidRegion,self).__init__((x,y,z),boundary,height,angle)

class Floor(object):
    """A floor decides what height its upper surface is at for a given (x,y)
    Whether a point is within the floor is delegated to the floor's region."""
    _normal = (0,0,1)   # normal of top surface
    _offset = (0,0,0)   # any point on the surface
    def __init__(self,name,region,normal=(0,0,1)):
        self.name = name
        self.region = region
        self._normal = normal
    def overlaps(self,pos,height,radius):
        return self.region.overlaps(pos,height,radius)
    def z_at(self,(x,y,z),step):
        """Z coordinate of floor at point x,y. None if x,y outside the floor, or
        z - step .. z + step outside vertical range of region"""
        test = self.overlaps((x,y,z-step),z*2,0)
        if test:
            origin = (self.region.pos + self._offset)
            v = Vec(x,y,0) - origin.projXY()
            a,b,c = self._normal
            z = origin.z + (-a * v.x - b * v.y)/c
            return z
        else:
            return None

def walkable_normal((x,y,z)):
    return z > max(abs(x),abs(y))
    
class FacetedFloor(Floor):
    """A floor made of multiple polygonal regions"""
    def __init__(self,name,pos,facets=[],angle=0):
        self.name = name
        self._offset = Vec(pos)
        self.floors = []
        self.angle = angle
        for norm, vertices in facets:
            if walkable_normal(norm):
                self.add_facet(norm,vertices)
    def overlaps(self,pos,height,radius):
        for f in self.floors:
            ztest = f.overlaps(pos,height,radius)
            if ztest:
                break
        return ztest
    def z_at(self,pos,step):
        for f in self.floors:
            z = f.z_at(pos,step)
            if z is not None:
                break
        return z
    def _get_angle(self):
        return self._angle
    def _set_angle(self,a):
        for f in self.floors:
            f.region.angle = a
        self._angle = a
    def add_facet(self,normal,vertices):
        zs = [z for (x,y,z) in vertices]
        minz = min(min(zs),self._offset.z)
        maxz = max(max(zs),self._offset.z)
        bottom = self._offset.projXY() + (0,0,minz)
        height = maxz - minz
        region = PrismRegion(bottom,vertices,height=height,angle=self.angle)
        f = Floor(self.name, region, normal=normal)
        self.floors.append(f)

class FloorSet(object):
    """A Floorset contains floors and other things with a region attribute.
    A thing is a floor if it has a z_at attribute, and an obstacle if it
    has an obstacle attribute (which will usually be statically True but
    could be a calculated property.
    """
    def __init__(self):
        self.floors = []
        self.obstacles = []
        self.other = []
        
    def add(self,thing):
        if not hasattr(thing,'region'):
            raise TypeError,"Floorset will only accept things with a region"
        if hasattr(thing,'z_at'):
            self.floors.append(thing)
        elif hasattr(thing,'obstacle'):
            self.obstacles.append(thing)
        else:
            self.other.append(thing)

    def remove(self,thing):
        for subset in self.floors, self.obstacles, self.other:
            try:
                subset.remove(thing)
                break
            except ValueError:
                pass

    def can_stand_at(self,thing,(x,y,z),step=0.1):
        """A thing with a cylindrical region can stand at (x,y,z) plus or
        minus z step, if there is at least one floor there, and when standing
        on highest floor in the z range, there are no obstacles blocking it.
        Returns None or (z',name) where z' is the height of highest floor and
        name is the name of that floor.
        """
        radius = thing.radius
        height = thing.height
        bottom = (x,y,z-step)
        floors = [(f.z_at(bottom,step*2,radius), f) for f in self.floors]
        floors.sort()   # highest at end
        if floors:
            z,f = floors[-1]
            if z is not None:
                obstacles = [ o.overlaps((x,y,z),height,radius)
                              for o in self.obstacles
                              if o is not thing # can't obstruct self!
                              if o.obstacle
                            ]
                if not obstacles:
                    return z,f.name
        return None
        
    def what_is_at(self,(x,y,z)):
        """Get a set of object names of things that overlap the given point"""
        return set([ob.name
                    for ob in (self.floors + self.obstacles + self.other)
                    if ob.overlaps((x,y,z),0,0)
                    ])

    def clear(self):
        self.floors = []
        self.obstacles = []
        self.other = []

# Make a default one at module level for most simple purposes
DEFAULT_FLOORSET = FloorSet()
add = DEFAULT_FLOORSET.add
clear = DEFAULT_FLOORSET.clear
can_stand_at = DEFAULT_FLOORSET.can_stand_at
what_is_at = DEFAULT_FLOORSET.what_is_at

def ball_collide_tri(tri, P, velocity,radius=0.0):
    """Calculate whether nearest point on a sphere
    centred at P will cross the plane defined by tri
    (3 points) if you add vector v to it, and whether
    the point where it crosses lies within the triangle.
    
    If so, returns (sphere centre at collision point,
     normalised reflection vector of v),
    else returns (None, distance from plane after move).

    No collision is deemed to occur if the nearest point
    on the sphere is already on the "inside" of the triangle.

    Doesn't handle collision of any other part of the
    sphere with edges of the triangle.

    """

    # need everything to be vectors
    T0,T1,T2 = [Vec(t) for t in tri]
    n = ((T1-T0).cross(T2-T1)).normalise() # normal to plane
    pcentre = Vec(P)
    p0 = pcentre - (n*radius) # point of sphere nearest to plane
    v = Vec(velocity)
    p1 = p0 + v
    h0 = (p0 - T0).dot(n)
    h1 = (p1 - T0).dot(n)
    if h0 < 0 or h1 > 0:
        return None,h1

    # p0p1 crosses plane. Where?
    k = h0 / (h0 - h1) # proportion of v to reach plane exactly
    C = p0 + v*k # where point reaches plane

    u0 = T1 - T0
    u1 = T2 - T1
    u2 = T0 - T2
    
    Q0 = T0 + (T2-T0).proj(u0) # point on T0_T1 opposite T2
    if (Q0 - T2).dot(C - Q0) > 0: # C 'outside' T0_T1
        return None, h1

    Q1 = T1 + (T0-T1).proj(u1) # point along T1_T2 opposite T0
    if (Q1 - T0).dot(C - Q1) > 0: # C 'outside' T1_T2
        return None, h1

    Q2 = T2 + (T1-T2).proj(u2) # point along T2_T0 opposite T1
    if (Q2 - T1).dot(C - Q2) > 0: # C 'outside' T2_T0
        return None, h1

    # reflected point is other side of M, above C by h0
    M = C + n * h0
    R = p0 + (M - p0) * 2
    rv = (R - C).normalise()
    return C + (n*radius), rv
    
