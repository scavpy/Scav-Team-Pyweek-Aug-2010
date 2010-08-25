'''Game main module.

Contains the entry point used by the run_game.py script.

Feel free to put all your game code here, or in other modules in this "gamelib"
package.
'''
from optparse import OptionParser
import pyglet
from tdgl.gl import tdgl_usual_setup

from pygame import mixer

options = None

import monkey_patches

def main():
    mixer.init()
    
    op = OptionParser("usage: %prog [options]")
    add = op.add_option
    add("--size",default="1024,768",
        help="Size of screen [ %default ]")
    add("-f","--fullscreen",default=False,action="store_true",
        help="full screen")
    add("--fps",default=60,type="int",
        help="Maximum fps [ %default ]")
    add("--time",default=False,action="store_true",
        help="Show timings (inluding actual fps)")
    global options
    options,args = op.parse_args()
    pyglet.clock.set_fps_limit(options.fps)

    if options.fullscreen:
        width = height = None
    else:
        width,height = [int(c) for c in options.size.split(",")]
    
    import tdgl.material
    tdgl.material.load("materials.mtl")

    from gamewindow import GameWindow
    win = GameWindow(width=width,height=height,
                     fullscreen=options.fullscreen)
    tdgl_usual_setup()
    pyglet.app.run()

