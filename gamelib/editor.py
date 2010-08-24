import os
import pyglet
import pyglet.resource
pyglet.resource.path = ["../data", "../data/models"]
pyglet.resource.reindex()
import pyglet.window.key as pygkey

from tdgl.gl import *
from tdgl import viewpoint

import levelfile, collision, graphics

class EditorWindow(pyglet.window.Window):
    def __init__(self,fname=None,**kw):
        super(EditorWindow,self).__init__(**kw)
        self.view = viewpoint.OrthoView(
            "view",[],
            geom=dict(vport=(0,0,40,30)))
        self.level = None
        if fname:
            self.level = levelfile.load_level(fname)
        if not self.level:
            self.level = levelfile.Level()
        
    def on_key_press(self,sym,mods):
        pass

    def on_mouse_press(self,x,y,button,mods):
        if button != 1: return
        

    def on_draw(self):
        self.clear()
        tdgl_draw_parts(self.view)

    def on_resize(self,w,h):
        s = self.view
        s.resize(w,h)
        s.restyle()
        return True

if __name__ == '__main__':
    import sys
    if len(sys.argv) >= 2:
        fname = sys.argv[1]
    else:
        fname = None
    win = EditorWindow(fname=fname,width=1024,height=768)
    pyglet.clock.set_fps_limit(20)
    tdgl_usual_setup()
    pyglet.app.run()
