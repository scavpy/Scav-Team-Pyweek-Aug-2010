#! /usr/bin/env python
"""Higher order functions and operations on callables
   
   partial(fn,*args,**kw) - callable resulting from partial application of fn

    Peter Harris    March 2004
"""

class partial(object):
    """Callable with arguments partially applied from the left."""
    def __init__(*args, **kw):
        self = args[0]
        self.fn, self.args, self.kw = (args[1], args[2:], kw)

    def __call__(self, *args, **kw):
        if kw and self.kw:
            d = self.kw.copy()
            d.update(kw)
        else:
            d = kw or self.kw
        return self.fn(*(self.args + args), **d)
