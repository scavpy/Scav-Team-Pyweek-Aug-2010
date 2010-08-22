#! /usr/bin/env python
"""Generic routines that might be useful for animation by interpolating
   values.

    Copyright Sep 2007 Peter Harris
    Released under the terms of the GNU General Public License, v3 or later
    (see www.gnu.org for details)
"""
from __future__ import division

def interpolator(xfrom,xto,ms):
    """Interpolate between two values, which should be both a number,
    a tuple of numbers or a dict with numeric values.
    Values are to change linearly over "ms" milliseconds.
    """
    if isinstance(xfrom,dict):
        return DictInterpolator(xfrom,xto,ms)
    elif getattr(xfrom,'__getitem__',None):
        return TupleInterpolator(xfrom,xto,ms)
    else:
        return Interpolator(xfrom,xto,ms)

class Interpolator(object):
    """An object that interpolates from one value to another
    in a given number of milliseconds"""
    __slots__ = ('vfrom','vto','endms','nowms','current')
    def __init__(self,vfrom,vto,ms):
        self.vfrom = vfrom
        self.current = vfrom
        self.vto = vto
        self.endms = ms
        self.nowms = 0
    def step(self,ms):
        self.nowms = min(self.endms, self.nowms + ms)
        self.blend()
        return self.current
    def blend(self):
        nowms = self.nowms
        endms = self.endms
        if nowms >= endms:
            self.current = self.vto
        elif nowms:
            blend1 = nowms / endms
            blend0 = (endms - nowms) / endms
            self.current = self.vfrom*blend0 + self.vto*blend1
        else:
            self.current = self.vfrom
    def finished(self):
        return self.nowms >= self.endms

class TupleInterpolator(Interpolator):
    """An object that interpolates between one tuple of values to another
    in a given number of milliseconds"""
    __slots__ = ('vfrom','vto','endms','nowms','current')    
    def __init__(self,vfrom,vto,ms):
        self.vfrom = list(vfrom)
        self.current = tuple(vfrom)
        self.vto = list(vto)
        self.endms = ms
        self.nowms = 0
    def blend(self):
        nowms = self.nowms
        endms = self.endms
        if nowms >= endms:
            self.current = tuple(self.vto)
        elif nowms:
            blend1 = nowms / endms
            blend0 = (endms - nowms) / endms
            self.current = tuple([a*blend0 + b*blend1 for (a,b) in zip(self.vfrom,self.vto)])
        else:
            self.current = tuple(self.vfrom)
    
class DictInterpolator(Interpolator):
    """An interpolator for dicts instead of tuples"""
    __slots__ = ('vfrom','vto','endms','nowms','current')
    def __init__(self,vfrom,vto,ms):
        self.vfrom = vfrom.copy()
        self.current = vfrom.copy()
        self.vto = vto.copy()
        self.endms = ms
        self.nowms = 0
    def blend(self):
        nowms = self.nowms
        endms = self.endms
        if nowms >= endms:
            self.current = self.vto.copy()
        elif nowms:
            blend1 = nowms / endms
            blend0 = (endms - nowms) / endms
            vto = self.vto
            for k,v0 in self.vfrom.items():
                self.current[k] = v0*blend0 + vto[k]*blend1
        else:
            self.current = self.vfrom.copy()

class Oscillator(object):
    """Go from one value to another and back indefinitely.
    NB: this Interpolator-like thingy is NEVER finished. Be careful.
    """
    def __init__(self,xfrom,xto,ms,msback=None):
        if msback is None:
            msback = ms
        self.forwards = interpolator(xfrom,xto,ms)
        self.backwards = interpolator(xto,xfrom,msback)
        self.step(0)
    def step(self,ms):
        self.forwards.step(ms)
        if self.forwards.finished():
            self.forwards, self.backwards = self.backwards, self.forwards
            self.backwards.nowms = 0
            self.backwards.blend()
        self.current = self.forwards.current
        return self.current
    def finished(self):
        return False

class Sequencer(object):
    """ interpolate between a series of values """
    def __init__(self,xlist,steplist):
        self.xlist = xlist
        self.steplist = steplist
        self.interp = interpolator(xlist[0],xlist[1],steplist[0])
        self.step(0)

    def step(self,ms):
        self.interp.step(ms)
        self.current = self.interp.current
        xlist = self.xlist
        steplist = self.steplist
        if self.interp.finished() and steplist:
            xlist[:1] = []
            steplist[:1] = []
            if len(xlist) > 1:
                self.interp = interpolator(xlist[0],xlist[1],steplist[0])
        return self.current

    def finished(self):
        return not self.steplist

    
class Animator(object):
    """A collection of numeric values which may be static or changing"""
    def __init__(self, **initvalues):
        self.current={}
        self.current.update(initvalues)
        self.interpolators={}
    def step(self,ms):
        """Get next value of each interpolator, change current values"""
        interpolators = self.interpolators
        for k,it in list(interpolators.items()):
            self.current[k] = it.step(ms)
            if it.finished():
                del interpolators[k]
    def finished(self,name=None):
        """Whether a particular value has finished changing,
        or all finished if no name is specified"""
        if name is None:
            return not(self.interpolators)
        else:
            return name not in self.interpolators
    def items(self):
        """current value items"""
        return self.current.items()
    def __getitem__(self,name):
        """Get a current value - defaults to zero - never a KeyError"""
        return self.current.get(name,0.0)
    def get(self,name,default=0.0):
        """Get a current value, with specified default"""
        return self.current.get(name,default)
    def __delitem__(self,name):
        """Delete a value and its interpolator if there is one"""
        try:
            del self.interpolators[name]
        except KeyError:
            pass
        try:
            del self.current[name]
        except KeyError:
            pass
    def __setitem__(self,name,value):
        """Set a value, delete any interpolator that may be present"""
        self.current[name] = value
        try:
            del self.interpolators[name]
        except KeyError:
            pass
    def copy(self):
        """Return a shallow copy of the Animator's current state.
        There's no point in copying the interpolators - you can't
        in general copy a generator."""
        return Animator(**self.current)
    def update(self,other):
        """Update by setting current values from another dict-like object."""
        for k,x in other.items:
            self[k] = x
    def change(self,name,xto,ms=0):
        """Begin changing a value"""
        if ms:
            self.interpolators[name] = interpolator(self.current.get(name,xto),
                                                    xto,ms)
        else:
            self[name] = xto
    def oscillate(self,name,xfrom,xto,steps=1):
        """Begin oscillating a value
        NB: it will NEVER be finished, until replaced with change() method.
        """
        self.interpolators[name] = Oscillator(xfrom,xto,steps)
    def sequence(self,name,xlist,steplist):
        """Begin a more complex sequence of changes"""
        self.interpolators[name] = Sequencer(xlist,steplist)

class Mutator(Animator):
    """An animator that works on another dict-like object"""
    def __init__(self,mutand):
        self.current = mutand
        self.interpolators = {}
