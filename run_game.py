#! /usr/bin/env python
import sys
import os
try:
    here = os.path.abspath(os.path.dirname(__file__))
    libdir = os.path.join(here, 'gamelib')
    sys.path.insert(0, os.path.join(libdir,'tdgl.zip'))
    sys.path.insert(0, libdir)
    import pyglet.resource, pyglet.font
    pyglet.resource.path=[".","data"]
    pyglet.resource.reindex()
    pyglet.font.add_directory(os.path.join(here,"data/fonts"))
    assert pyglet.font.base.Font.have_font("IM FELL English Roman")
except NameError:
    # probably running inside py2exe which doesn't set __file__
    pass

import main
main.main()
