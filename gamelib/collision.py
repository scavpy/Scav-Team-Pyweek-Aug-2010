"""
 Calculate collisions between circles and hexagons in 2D

 All the hexagons have side 2, i.e. they fit neatly in a
 circle of radius 1.

 Assume for simplicity we are only dealing with low-speed
 projectiles, so that if there is a collision at all, the
 moving circle will end up overlapping the hexagon, not
 shooting right past it.

 There is a range of increasingly complex tests:

 0. Does bounding box of circle centred at C, radius r,
    overlap bounding box of hexagon?

 1. Does circle overlap bounding circle of hexagon?

 2. Will the circle collide with a nearby hexagon if it 
    tries to move by velocity vector V, and if so, where 
    will its centre be when it stops against the hexagon?

 3. Like 2, but also, how much "left-over" velocity will it
    have to make an elastic collision, and what will its
    reflection vector be?

 We always start with test 0 and work our way onward as
 far as required.  A failed collision at any stage means
 we can just return False.

 Since all the hexagons are identical, the geometry of the
 hexagon can be stored as a list of corner points, a list of
 side vectors, and a list of side normals.

 All tests are begun by transforming the circle's position
 so the centre of the hexagon is at the origin.
"""

from tdgl.vec import Vec

R3 = 3.0**0.5
Sin60 = R3*0.5

H_CORNER = [Vec(1,0),Vec(0.5,Sin60),Vec(-0.5,Sin60),
             Vec(-1,0),Vec(-0.5,-Sin60),Vec(0.5,-Sin60)]
H_SIDE = [H_CORNER[(i+1) % 6] - v for i,v in enumerate(H_CORNER)]
H_NORMAL = [Vec(v.y,-v.x) for v in H_SIDE]

def h_centre(hcol,hrow):
    """position vector of hexagon centre"""
    return Vec(hcol * 1.5, hrow * R3 + Sin60 * (hcol % 2))

def line_segment_cross(P0,v0,P1,v1):
    """ solve:  P0 + m*v0 = P1 + n*v1,
     for m and n.
     return m,n.   return (inf,inf) if vectors parallel

     m(j0) - n(j1) = x1 - x0
     m(k0) - n(k1) = y1 - y0

     if j1 is zero:
         if j0, k0 or k1 are zero at that point,give up.
         m = (x1 - x0) / j0
         n = -(y1 - y0)/(m k0 k1)
     else:
         Try to eliminate n:
         q = k1/j1
         m(k0 - q j0) = (y1 - y0) - q(x1 - x0)
         m = ((y1 - y0) - q(x1 - x0))/(k0 - q j0)
         n = -(x1 -x0)(m j0 j1)

    Or something...
    """
    j0,k0,_ = v0
    j1,k1,_ = v1
    x0,y0,_ = P0
    x1,y1,_ = P1
    def zeroish(x):
        return abs(x) < 0.000001
    try:
        if zeroish(j1):
            m = (x1 - x0) / j0
            n = -(y1 - y0)/(m * k0 * k1)
        else:
            q = k1/j1
            m = ((y1 - y0) - q(x1 - x0)) / (k0 - q * j0)
            n = -(x1 - y0) / (m * j0 * j1)
    except ArithmeticError:
        return float('inf'),float('inf')
    return m,n

COLLIDE_BBOX = 0
COLLIDE_CIRCLE = 1
COLLIDE_POSITION = 2
COLLIDE_REBOUND = 3
 
def collides(hcol,hrow,C,r,v=Vec(0,0),detail=COLLIDE_BBOX):
    """ Collision test:
    hcol,hrow : hexagon grid coordinates
    C : circle centre
    r : circle radius
    v : circle velocity vector
    detail: level of collision detail required (see module doc)
    """
    H = h_centre(hcol,hrow)
    v = Vec(v)
    C0 = Vec(C) - H
    C1 = C0 + v
    left,right = C1.x - r, C1.x + r
    top,bot = C1.y + r, C1.y - r
    bbtest = left < 1 and right > -1 and bot < Sin60 and top > -Sin60
    if not bbtest:
        return False
    if detail == COLLIDE_BBOX:
        return True
    
    circletest = C1.length() < (1 + r)
    if not circletest:
        return False
    if detail == COLLIDE_CIRCLE:
        return True

    # Now the hard maths
    sidetest = False
    for i, n in enumerate(H_NORMAL):
        dot = n.dot(v)
        if (dot >= 0):
            continue  # no colliding from inside the hexagon!
        # projection of v onto normal (points towards hexagon)
        towards_side = (n * dot).normalise()
        # nearest point on circle to the side
        Q0 = C0 + towards_side * r
        # Solve line segment crossing
        mu,nu = line_segment_cross(Q0,v,H_CORNER[i],H_SIDE[i])
        # nu outside [0,1] if nearest point will miss the side
        # mu > 1 if nearest point won't reach the side
        if nu < 0 or nu > 1 or mu > 1:
            continue
        sidetest = True
        Q1 = Q0 + v * mu # collision point
        C2 = Q1 + n * r  # centre of circle at collision point
        break
    if not sidetest:
        return False
    if detail == COLLIDE_POSITION:
        return C2 + H  # transform back to actual coords

    #calculate vector u, same magnitude as v but reflected
    u = n * 2 - v
    ubounce = u.normalise() * (1 - mu)
    return C2 + ubounce + H, u
