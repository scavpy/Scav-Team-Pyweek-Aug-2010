#! /usr/bin/env python
"""
   Simple level editor

"""
import os
import monkey_patches
from inspect import isclass
import pyglet
import pyglet.resource
pyglet.resource.path = ["../data", "../data/models"]
pyglet.resource.reindex()
import pyglet.window.key as pygkey

from tdgl.gl import *
from tdgl import viewpoint, lighting, part, picking, panel, stylesheet

import levelfile, collision, graphics, monsters

basic_hexes = {pygkey.SPACE:" ",
               pygkey._3:"#",
               pygkey.X:"X",
               pygkey.S:"S",
               pygkey.DELETE:None,
               pygkey.O:"O",
               }

TOOLW = 1024-768
HEIGHT = 768
WIDTH = 768

class EditorWindow(pyglet.window.Window):
    def __init__(self,fname=None,**kw):
        super(EditorWindow,self).__init__(**kw)
        self.level = None
        if fname:
            self.level = levelfile.load_level(fname)
        else:
            fname = "untitled.lev"
        self.fname = fname
        if not self.level:
            self.level = levelfile.Level()
        if options.name:
            self.level.name = options.name
        self.set_caption("{0} - {1}".format(fname,self.level.name))
        if options.story:
            with open(options.story,"ru") as f:
                self.level.story = f.read().split("\n\n")
        if options.sound:
            self.level.sound = options.sound
        self.cellcode = "#"
        self.rgb = [1,1,1]
        stylesheet.load(monsters.MonsterStyles)
        stylesheet.load(graphics.BallStyles)
        self.get_monster_list()
        self.get_balls_list()
        self.build_parts()

    def get_monster_list(self):
        self.monster_list = []
        for name in dir(monsters):
            k = getattr(monsters,name)
            if not isclass(k): continue
            if name == "Monster": continue
            if issubclass(k,monsters.Monster):
                self.monster_list.append(name)

    def get_balls_list(self):
        self.balls_list = []
        for name in dir(graphics):
            k = getattr(graphics,name)
            if not isclass(k): continue
            if name == "Ball": continue
            if issubclass(k,graphics.Ball):
                self.balls_list.append(name)
                           
    def build_parts(self):
        view = viewpoint.OrthoView(
            "view",[],
            geom=dict(left=0, right=40, top=40, bottom=0,
                      near=-1.6,
                      vport=(0,0,WIDTH,HEIGHT)),
            style={"ClearColor":(0.2,0.2,0.2,0)})
        self.hexfield = graphics.HexagonField(
            "field",self.level)
        view.append(self.hexfield)
        with view.compile_style():
            glEnable(GL_LIGHTING)
        self.light = lighting.claim_light()
        lighting.light_position(self.light,(10,10,10,0))
        lighting.light_colour(self.light,(1,1,1,1))
        lighting.light_switch(self.light,True)
        lighting.setup()
        tools = viewpoint.OrthoView(
            "tools",[],
            geom=dict(left=0,right=100,top=300,bottom=0,
                      vport=(WIDTH,0,TOOLW,HEIGHT)),
            style={"ClearColor":(0,0,0,0)})

        tools.append(
            ColourBar("red",0,
                      geom=dict(scale=10,pos=(10,10,0))))
        tools.append(
            ColourBar("green",1,
                      geom=dict(scale=10,pos=(25,10,0))))
        tools.append(
            ColourBar("blue",2,
                      geom=dict(scale=10,pos=(40,10,0))))

        tools.append(
            panel.LabelPanel("cellcode",
                             text=self.cellcode,
                             style={"font_size":10},
                             geom={"pos":(50,250,0)}))
                             
        self.parts = part.Group("parts",[view,tools])
        for coords,mname in self.level.monsters.items():
            self.add_thing_to_view(coords,monsters,mname)
        for coords,pname in self.level.powerups.items():
            self.add_thing_to_view(coords,graphics,pname)

        self.parts.restyle(True)


    def set_cell_code(self,cellcode):
        self.cellcode = cellcode
        label = self.parts["cellcode"]
        label.text = str(cellcode)
        label.prepare()

    def set_hex_colour(self):
        hexdigits = "".join(hex(c)[-1] for c in self.rgb)
        self.set_cell_code("H" + hexdigits)

    def on_key_press(self,sym,mods):
        if sym == pygkey.S and mods & pygkey.MOD_CTRL:
            self.level.save(self.fname)
        elif sym == pygkey.ESCAPE:
            self.close()
        elif sym in basic_hexes:
            self.set_cell_code(basic_hexes[sym])
        elif sym == pygkey.H:
            self.set_hex_colour()
        elif sym == pygkey.M:
            self.toggle_monster()
        elif sym == pygkey.P:
            self.toggle_powerup()
            
    def on_mouse_press(self,x,y,button,mods):
        if x < 768:
            self.click_in_grid(x,y,button,mods)
        else:
            self.click_in_tools(x,y,button,mods)

    def toggle_monster(self):
        if self.cellcode in self.monster_list:
            self.monster_list = self.monster_list[1:] + self.monster_list[:1]
        self.set_cell_code(self.monster_list[0])

    def toggle_powerup(self):
        if self.cellcode in self.balls_list:
            self.balls_list = self.balls_list[1:] + self.balls_list[:1]
        self.set_cell_code(self.balls_list[0])

    def add_thing_to_view(self,coords,module,classname):
        M = getattr(module,classname)
        mname = repr(coords)
        m = M(mname)
        m.pos = collision.h_centre(*coords)
        m.restyle(True)
        self.parts["view"].append(m)

    def place_monster(self,coords,monstername):
        lev = self.level
        self.unplace(coords)
        lev.monsters[coords] = monstername
        self.add_thing_to_view(coords,monsters,monstername)

    def unplace(self,coords):
        if coords in self.level.monsters:
            del self.level.monsters[coords]
        if coords in self.level.powerups:
            del self.level.powerups[coords]
        mname = repr(coords)
        view = self.parts["view"]
        m = view[mname]
        if m:
            view.remove(m)

    def place_powerup(self,coords,ballname):
        lev = self.level
        self.unplace(coords)
        lev.powerups[coords] = ballname
        self.add_thing_to_view(coords,graphics,ballname)
        
    def click_in_grid(self,x,y,button,mods):
        if button != 1: return
        fx = x/768.0 * 40
        fy = y/768.0 * 40
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
        elif self.cellcode is None:
            if (coords not in [level.start,level.exit]
                and coords in level.hexes):
                del level.hexes[coords]
            self.unplace(coords)
        elif self.cellcode in self.monster_list:
            self.place_monster(coords,self.cellcode)
        elif self.cellcode in self.balls_list:
            self.place_powerup(coords,self.cellcode)
            level.hexes[coords] = "P"
        else:
            level.hexes[coords] = self.cellcode
        self.hexfield.build_dl()
        self.hexfield.prepare()

    def click_in_tools(self,x,y,button,mods):
        picking.start(x,y,1,1)
        self.parts["tools"].draw('PICK')
        objects = picking.end()
        if objects:
            minz,maxz,label = objects[0]
            self.pick(label)

    def pick(self,label):
        ob = label.target
        if ob._name in ["red","green","blue"]:
            ob.intensity = label.intensity
            self.rgb[ob.component] = label.intensity
            self.set_hex_colour()

    def on_draw(self):
        tdgl_draw_parts(self.parts)

    def on_resize(self,w,h):
        self.parts["view"].resize(w,h)
        self.parts["tools"].resize(w,h)
        self.parts.restyle()
        return True

class ColourBar(part.ScalePart):

    def __init__(self,name,component=0,**kw):
        super(ColourBar,self).__init__(name,**kw)
        self.intensity = 1
        self.component = component
        self._has_transparent = (component == 3)

    def setup_style(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)
        glLineWidth(2)
        
    def render(self,mode):
        """Render as a colour bar with a white border"""
        v = glVertex2f
        colour = [0,0,0,1]
        for i in range(16):
            if mode == 'PICK':
                picking.label(self,intensity=i)
            else:
                colour[self.component] = i * (1.0/15)
                glColor4f(*colour)
            with gl_begin(GL_QUADS):
                v(0,i)
                v(1,i)
                v(1,i+1)
                v(0,i+1)
        if mode == 'PICK':
            picking.nolabel
        else:
            glColor3f(1,1,1)
            with gl_begin(GL_LINE_LOOP):
                v(0,0)
                v(1,0)
                v(1,16)
                v(0,16)
            i = self.intensity
            with gl_begin(GL_LINE_LOOP):
                v(0.1,i+0.1)
                v(0.9,i+0.1)
                v(0.9,i+0.9)
                v(0.1,i+0.9)

if __name__ == '__main__':
    from optparse import OptionParser
    op = OptionParser("usage: %prog [options] fname")
    add = op.add_option
    add("--story",default=None,help="Story file to use for level")
    add("--sound",default=None,help="Sound effect to announce level")
    add("--name",default=None,help="Level name")
    options,args = op.parse_args()
    if len(args) != 1:
        op.error("Must give exactly one filename")
    win = EditorWindow(fname=args[0],width=1024,height=768)
    pyglet.clock.set_fps_limit(20)
    tdgl_usual_setup()
    pyglet.app.run()
