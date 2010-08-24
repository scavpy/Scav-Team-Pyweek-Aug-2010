import os
import pyglet
import pyglet.resource
pyglet.resource.path = ["../data", "../data/models"]
pyglet.resource.reindex()
import pyglet.window.key as pygkey

from tdgl.gl import *
from tdgl import viewpoint, lighting

import levelfile, collision, graphics

basic_hexes = {pygkey.R:"Hf00",
               pygkey.G:"H0f0",
               pygkey.B:"H00f",
               pygkey.SPACE:" ",
               pygkey._3:"#",
               pygkey.X:"X",
               pygkey.S:"S"
               }

class EditorWindow(pyglet.window.Window):
    def __init__(self,fname=None,**kw):
        super(EditorWindow,self).__init__(**kw)
        self.view = viewpoint.OrthoView(
            "view",[],
            geom=dict(left=0, right=40, top=30, bottom=0),
            style={"ClearColor":(0.2,0.2,0.2,0)})
        self.level = None
        self.fname = fname
        if fname:
            self.level = levelfile.load_level(fname)
        if not self.level:
            self.level = levelfile.Level()
        if options.name:
            self.level.name = options.name
        if options.story:
            with open(options.story,"ru") as f:
                self.level.story = f.read.split("\n\n")
        self.hexfield = graphics.HexagonField(
            "field",self.level)
        self.view.append(self.hexfield)
        with self.view.compile_style():
            glEnable(GL_LIGHTING)
        self.light = lighting.claim_light()
        lighting.light_position(self.light,(10,10,10,0))
        lighting.light_colour(self.light,(1,1,1,1))
        lighting.light_switch(self.light,True)
        lighting.step(1)
        self.cellcode = "#"
        self.view.restyle(True)

    def on_key_press(self,sym,mods):
        if sym == pygkey.S and mods & pygkey.MOD_CTRL:
            self.level.save(self.fname)
        elif sym == pygkey.ESCAPE:
            self.close()
        elif sym in basic_hexes:
            self.cellcode = basic_hexes[sym]
            
    def on_mouse_press(self,x,y,button,mods):
        if button != 1: return
        fx = x/1024.0 * 40
        fy = y/768.0 * 30
        coords = collision.nearest_neighbours(fx,fy,0).next()
        level = self.level
        if self.cellcode == "S":
            level.hexes[level.start] = " "
            level.start = coords
            level.hexes[coords] = "S"
        elif self.cellcode == "X":
            level.hexes[level.exit] = " "
            level.exit = coords
            level.hexes[coords] = "X"
        else:
            self.level.hexes[coords] = self.cellcode
        self.hexfield.build_dl()
        self.hexfield.prepare()

    def on_draw(self):
        self.clear()
        tdgl_draw_parts(self.view)

    def on_resize(self,w,h):
        s = self.view
        s.resize(w,h)
        s.restyle()
        return True

if __name__ == '__main__':
    from optparse import OptionParser
    op = OptionParser("usage: %prog [options] fname")
    add = op.add_option
    add("--story",default=None,help="Story file to use for level")
    add("--name",default=None,help="Level name")
    options,args = op.parse_args()
    if len(args) != 1:
        op.error("Must give exactly one filename")
    win = EditorWindow(fname=args[0],width=1024,height=768)
    pyglet.clock.set_fps_limit(20)
    tdgl_usual_setup()
    pyglet.app.run()
