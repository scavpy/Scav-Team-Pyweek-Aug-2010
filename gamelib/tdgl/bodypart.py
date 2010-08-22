""" bodypart.py  - a Part that draws a body shape,
    with various rotations and translations between the parts of the body.
    These are controlled by a hox list, as implemented in the hox module.

    Copyright 2005 Peter Harris
    Released under the terms of the GNU General Public License
    (see www.gnu.org for details)

"""
import copy
from OpenGL import GLU
from OpenGL.GL import *
from tdlib import part, animator, hox
from tdlib.hox import DRAW,MOVE,ROT,X,Y,Z

class Posable(part.Part):
    """A part whose geometry is controlled by an Animator"""
    _poses = {}
    def __init__(self, *args, **kwd):
        super(Posable,self).__init__(*args,**kwd)
        self.mutator = animator.Mutator(self._geom)
    def step(self,ms):
        self.mutator.step(ms)
    def finished(self):
        return self.mutator.finished()
    def pose(self,posename,steps=0):
        try:
            pose = self._poses[posename]
            for name, value in pose.items():
                self.mutator.change(name,value,steps)
        except KeyError:
            pass

class BodyPart(Posable):
    """ BodyPart has a HoxList, and a dictionary of display-lists it
    uses to draw each piece"""
    def __init__(self,name,hoxlist=None,**kwd):
        super(BodyPart,self).__init__(name,**kwd)
        self.hoxlist = hoxlist
        self.dlists = {}

    # prepare should build display lists for each piece
    
    def __del__(self):
        """Get rid of display lists, quadrics etc."""
        GLU.gluDeleteQuadric(self.quadric)
        for name,dlist in self.dlists.items():
            if glIsList(dlist):
                glDeleteLists(dlist,1)
        super(BodyPart,self).__del__()
    
    def drawpiece(self,name):
        """Will be called from hox.process()"""
        dl = self.dlists.get(name,0)
        if dl:
            glCallList(dl)

    def newpiece(self,name):
        """convenience function"""
        dl = self.dlists.get(name,0)
        if not dl:
            dl = glGenLists(1)
            self.dlists[name] = dl
        return dl

    def render(self,mode):
        hox.process(self.hoxlist,
            self.getgeom,
            self.drawpiece,
            withstyle=(mode != 'PICK'))

    
""" brief note on naming convention of suffixes for body angles and dimensions:
    Z a vertical distance
    Y a distance to the left (by convention bodies face along X axis, at angle 0)
    X a distance forwards
    A an angle
    AX an angle arounf X axis...
    L left
    R right
"""
    
HumanoidHox = [ # drawing begins at point on ground under centre of body
    (MOVE,'hipZ',Z,1.0),
    [#left leg
        (MOVE,'hipY',Y,1.0),
        (ROT, 'legAXL',X,1.0),  # splay leg
        (ROT,'legAL',Y,1.0),    # lift knee
        (MOVE,'thighZ',Z,-1.0), # move down to knee and draw upwards
        (DRAW,'thighL'),
        (ROT,'kneeAL',Y,-1.0),   # bend knee
        (MOVE,'shinZ',Z,1.0),   # move down to ankle and draw upwards
        (DRAW,'shinL'),
        (ROT,'ankleL',Y,1.0),       # lift foot
        (DRAW,'footL'),
        ],
    [#right leg
        (MOVE,'hipY',Y,-1.0),
        (ROT, 'legAXR',X,-1.0),  # splay leg
        (ROT,'legAR',Y,1.0),    # lift knee
        (MOVE,'thighZ',Z,-1.0), # move down to knee and draw upwards
        (DRAW,'thighR'),
        (ROT,'kneeAR',Y,-1.0),  # bend knee
        (MOVE,'shinZ',Z,1.0),   # move down to ankle and draw upwards
        (DRAW,'shinR'),
        (ROT,'ankleR',Y,1.0),       # lift foot
        (DRAW,'footR'),
        ],
    (DRAW,'hips'),
    (MOVE,'waistZ',Z,1.0),  # up to waist height
    (ROT,'waistAZ',Z,1.0),  # twist at waist
    (ROT,'waistAY',Y,-1.0), # bend forward
    (DRAW,'torso'),
    (MOVE,'torsoZ',Z,1.0),  # up to shoulder height
    [# left arm
        (MOVE,'shoulderY',Y,1.0),
        (ROT,'armAXL',X,1.0),   # flap arm
        (ROT,'armAL',Y,1.0),    # rotate arm upwards
        (MOVE,'upperarmZ',Z,-1.0),  # down length of upper arm to elbow
        (DRAW,'upperarmL'), # draw up to shoulder
        (ROT,'elbowAL',Y,1.0),    # bend elbow
        (MOVE,'forearmZ',Z,-1.0),   # down length of forearm
        (DRAW,'forearmL'),  # draw up to elbow
        (ROT,'wristAZL',Z,1.0), # twist wrist outward
        (ROT,'wristAYL',Y,1.0), # lift hand
        (DRAW,'handL'),
        ],
    [# right arm
        (MOVE,'shoulderY',Y,1.0),
        (ROT,'armAXR',X,-1.0),   # flap arm
        (ROT,'armAR',Y,1.0),    # rotate arm upwards
        (MOVE,'upperarmZ',Z,-1.0),  # down length of upper arm
        (DRAW,'upperarmR'),
        (ROT,'elbowAR',Y,1.0),    # bend elbow
        (MOVE,'forearmZ',Z,-1.0),   # down length of forearm
        (DRAW,'forearmR'),
        (ROT,'wristAZR',Z,-1.0), # twist wrist outward
        (ROT,'wristAYR',Y,1.0), # lift hand
        (DRAW,'handR'),
        ],
    (ROT,'headAX',X,1.0),   # lean head to right
    (ROT,'headAY',Y,-1.0),  # tip head forward
    (ROT,'headAZ',Z,1.0),   # turn head left
    (DRAW,'head'),
    ]
    
class StickMan(BodyPart):
    _default_geom = dict(pos=(0.0,0.0,0.0), angle=0.0,
        #dimensions
        hipZ=0.5, hipY=0.1, thighZ=0.25, shinZ=0.25, footX=0.1,
        waistZ=0.0, torsoZ=0.5, shoulderY=0.2, headZ=0.2,
        upperarmZ=0.2, forearmZ=0.2, handZ=0.1, stick=0.05,
        #angles
        legAXL=0.0, legAL=0.0, kneeAL=0.0, ankleAL=0.0,
        legAXR=0.0, legAR=0.0, kneeAR=0.0, ankleAR=0.0,
        waistAZ=0.0, waistAY=0.0,
        armAXL=0.0, armAL=0.0, elbowAL=0.0, wristAZL=0.0, wristAYL=0.0,
        armAXR=0.0, armAR=0.0, elbowAR=0.0, wristAZR=0.0, wristAYR=0.0,
        headAX=0.0,
        headAY=0.0,
        headAZ=0.0,
        )
    _default_style = dict(colour=(1,1,1,1), shininess=64)
    _style_attributes = ('colour','shininess')
    
    def __init__(self,name,hoxlist=None,**kw):
        if hoxlist is None:
            hoxlist = copy.deepcopy(HumanoidHox)
        super(StickMan,self).__init__(name,hoxlist,**kw)
        self.quadric = GLU.gluNewQuadric()

    def prepare(self):
        """ Build display lists """
        # for efficiency, allow skipping the TRANSPARENT render if opaque
        self._has_transparent = (self.getstyle('colour')[3] < 1)
        # consts
        v3 = glVertex3f
        r = self.getgeom('stick',0.05)
        # feet
        dl = self.newpiece("footL")
        self.dlists["footR"] = dl   # foot is same on both legs
        glNewList(dl,GL_COMPILE)
        x = self.getgeom('footX',0.1)
        glBegin(GL_TRIANGLES)
        v3(0,0,0)
        v3(x,-x/2.0,0)
        v3(x,x/2.0,0)
        glEnd()
        glEndList()
        # shins
        dl = self.newpiece("shinL")
        self.dlists["shinR"] = dl
        glNewList(dl,GL_COMPILE)
        z = self.getgeom('shinZ',0.25)
        GLU.gluCylinder(self.quadric,r,r,z,3,2)
        glEndList()
        # thighs
        dl = self.newpiece("thighL")
        self.dlists["thighR"] = dl
        glNewList(dl,GL_COMPILE)
        z = self.getgeom('thighZ',0.25)
        GLU.gluCylinder(self.quadric,r,r,z,4,2)
        glEndList()
        #hips
        dl = self.newpiece("hips")
        glNewList(dl,GL_COMPILE)
        w = self.getgeom('hipY',0.1)
        glBegin(GL_LINES)   # simple line across hip joint
        v3(0,-w,0)
        v3(0,w,0)
        glEnd()
        glEndList()
        #torso
        dl = self.newpiece("torso")
        glNewList(dl,GL_COMPILE)
        z = self.getgeom('torsoZ',0.5)
        w = self.getgeom('shoulderY',0.2)
        GLU.gluCylinder(self.quadric,r,r,z,6,2)
        glBegin(GL_LINES)   # line across shoulders
        v3(0,-w,z)
        v3(0,w,z)
        glEnd()
        glEndList()
        # upper arms
        dl = self.newpiece("upperarmL")
        self.dlists['upperarmR'] = dl
        z = self.getgeom('upperarmZ',0.2)
        glNewList(dl,GL_COMPILE)
        GLU.gluCylinder(self.quadric,r,r,z,4,2)
        glEndList()
        # forearms
        dl = self.newpiece("forearmL")
        self.dlists['forearmR'] = dl
        z = self.getgeom('forearmZ',0.2)
        glNewList(dl,GL_COMPILE)
        GLU.gluCylinder(self.quadric,r,r,z,3,2)
        glEndList()
        # hands
        dl = self.newpiece("handL")
        self.dlists["handR"] = dl   # hand is same on both arms
        glNewList(dl,GL_COMPILE)
        z = self.getgeom('handZ',0.1)
        glBegin(GL_TRIANGLES)
        v3(0,0,0)
        v3(0,-z/2.0,-z)
        v3(0,z/2.0,-z)
        glEnd()
        glEndList()
        # head
        dl = self.newpiece("head")
        z = self.getgeom('headZ',0.2)
        glNewList(dl,GL_COMPILE)
        GLU.gluCylinder(self.quadric,r,r,z,4,1) # neck
        glTranslate(0,0,z)  # centre of head
        GLU.gluSphere(self.quadric,2*r,8,6)
        glTranslate(2*r,0,0) # to nose
        glColor(1,0,0,1)    # red nose for testing
        GLU.gluSphere(self.quadric,r*0.5,6,4)
        glEndList()
        
    def __del__(self):
        """Get rid of display lists, quadrics etc."""
        GLU.gluDeleteQuadric(self.quadric)
        super(StickMan,self).__del__()

    def setup_style(self):
        glPushAttrib(GL_LIGHTING_BIT|GL_TEXTURE_BIT)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,(1,1,1,1))
        glMateriali(GL_FRONT_AND_BACK, GL_SHININESS,self.getstyle('shininess'))
        glColor4f(*self.getstyle('colour'))
        glDisable(GL_TEXTURE_2D)

    def setdown_style(self):
        glPopAttrib()
        
