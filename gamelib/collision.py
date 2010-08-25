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

def nearest_neighbours(x,y,d=1):
    """Yield hexagon grid coords for hexagons near point x,y
    sorted in order of increasing centre distance.
    d is hex grid distance to allow for (0,1,2 likely)"""
    hcol = int((x / 1.5) + 0.5)
    adjust = Sin60 * (hcol % 2)
    hrow = int(((y - adjust) / R3) + 0.5)
    here = Vec(x,y)
    centres = sorted(((h_centre(hcol+i,hrow+j)-here).length(),hcol+i,hrow+j)
               for i in range(-d,d+1)
               for j in range(-d,d+1))
    return ((hc,hr) for (dd,hc,hr) in centres)

def line_segment_cross(P0,v0,P1,v1):
    """ solve:  P0 + m*v0 = P1 + n*v1,
     ( where v0 = (j0,k0), v1 = (j1,k1) )
     for m and n.
     return m,n.   return (inf,inf) if vectors parallel

     Solve the system of equations:
        m   n 
     [ j0 -j1 | x1-x0 ]  (eq1)
     [ k0 -k1 | y1-y0 ]  (eq2)     
    """
    j0,k0,_ = v0
    j1,k1,_ = v1
    x0,y0,_ = P0
    x1,y1,_ = P1
    eq1 = Vec(j0,-j1,x1-x0)
    eq2 = Vec(k0,-k1,y1-y0)
    def zeroish(x):
        return abs(x) < 0.000001
    try:
        if zeroish(k0):
            # try to eliminate m from eq2
            eq3 = eq2 - eq1*(k0/j0)
        else:
            # try to eliminate m from eq1
            eq3 = eq1 - eq2*(j0/k0)
        n = eq3.z/eq3.y
        if zeroish(j0):
            m = (eq2.z - eq2.y*n)/k0
        else:
            m = (eq1.z - eq1.y*n)/j0
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

    # Push the circle away to the edge of the bounding
    # circle of the hexagon.
    n = C1.normalise()
    C2 = n * (1+r)

    if detail == COLLIDE_POSITION:
        return C2 + H

    # Find hexagon normal nearest to the direction of the circle
    nx,ny,_ = n
    dots = sorted((abs(1.0 - v.dot(n)),i)
                   for (i,v) in enumerate(H_NORMAL))
    _,i = dots[0]
    # Real normal at hexagon side...
    n = H_NORMAL[i]

    # Calculate bounce vector...

    # Portion of intended distance still to travel
    speed = v.length()
    v1 = C2 - C0
    remainder = max(0.01,speed - v1.length())
    # Midpoint M is above the collision point 
    M = C2 - v1.proj(n)
    # C3 is opposite C0 through the midpoint M
    C3 = C0 + (M - C0)*2
    # Direction
    v2 = (C3 - C2).normalise()
    C2 += v2 * remainder
    return C2 + H, v2 * speed
    
                  
