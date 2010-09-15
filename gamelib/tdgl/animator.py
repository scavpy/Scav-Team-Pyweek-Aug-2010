#! /usr/bin/env python
"""Generic routines that might be useful for animation by interpolating
   values.

    Copyright Sep 2010 Peter Harris
    Released under the terms of the GNU General Public License, v3 or later
    (see www.gnu.org for details)
"""
from __future__ import division
from copy import deepcopy

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
        self.nowms = max(min(self.endms, self.nowms + ms),0)
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
    def at_start(self):
        return self.nowms == 0

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
    NB: this Interpolator-like thingy has no real start or finishing point,
    so it is NEVER finished.
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
    def at_start(self):
        return False

class Sequencer(object):
    """ interpolate between a series of values """
    def __init__(self,xlist,mslist):
        self.xlist = xlist
        self.mslist = mslist
        self.interp = interpolator(xlist[0],xlist[1],mslist[0])
        self.index = 0
        self.current = xlist[0]

    def step(self,ms):
        interp = self.interp
        interp.step(ms)
        self.current = interp.current
        i = self.index
        if interp.finished() and i < (len(self.mslist) - 1) and ms > 0:
            xlist = self.xlist
            self.index += 1
            i += 1
            self.interp = interpolator(xlist[i],xlist[i+1],self.mslist[i])
        elif interp.at_start() and i > 0 and ms < 0:
            xlist = self.xlist
            self.index -= 1
            i -= 1
            self.interp = interpolator(xlist[i],xlist[i+1],self.mslist[i])
            self.interp.step(self.mslist[i]) # put at end
        return self.current

    def finished(self):
        return self.interp.finished() and self.index == len(self.mslist) - 1

    def at_start(self):
        return self.interp.at_start() and self.index == 0

    
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
        """Return a copy of the Animator's current state."""
        return deepcopy(self)

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
    def oscillate(self,name,xfrom,xto,ms=0,msback=None):
        """Begin oscillating a value
        NB: it will NEVER be finished, until replaced with change() method.
        """
        self.interpolators[name] = Oscillator(xfrom,xto,ms,msback)
    def sequence(self,name,xlist,mslist):
        """Begin a more complex sequence of changes
           If name already in current, start the sequence at its
           current value (and if necessary add an entry to mslist).
        """
        x0 = self.current.get(name)
        if x0 is not None and x0 != xlist[0]:
            if len(mslist) < len(xlist):
                mslist = mslist[:1] + mslist
            xlist = [x0] + xlist
        self.interpolators[name] = Sequencer(xlist,mslist)

class Mutator(Animator):
    """An animator that works on another dict-like object"""
    def __init__(self,mutand):
        self.current = mutand
        self.interpolators = {}
