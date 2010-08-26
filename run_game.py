#! /usr/bin/env python
import sys
import os
def p(s="."):
    print s,
    sys.stdout.flush()

try:
    here = os.path.abspath(os.path.dirname(__file__))
    os.chdir(here)
    libdir = os.path.join(here, 'gamelib')
    sys.path.insert(0, os.path.join(libdir,'tdgl.zip'))
    sys.path.insert(0, libdir)
    p("Doing pyglet things. . .")
    sys.stdout.flush()
    import pyglet.resource
    p()
    import pyglet.font
    p()
    pyglet.resource.path = ["data", "data/models"]
    pyglet.resource.reindex()
    p()
    pyglet.font.add_directory(os.path.join(here,"data/fonts"))
    print "\nOK."
except NameError:
    # probably running inside py2exe which doesn't set __file__
    pass

import main
main.main()
