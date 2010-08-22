"""
   GameWindow is a pyglet window that runs a series of game screens

"""
import pyglet
from tdgl.gl import tdgl_draw_parts
import screen

class GameWindow(pyglet.window.Window):
    """A pyglet Window that displays a series of Screen
    in turn, exiting when there are no more to show"""
    def __init__(self,**kw):
        super(GameWindow,self).__init__(**kw)
        pyglet.clock.schedule(self.on_tick)
        self.this_screen = screen.next()
        
    def on_tick(self,secs):
        ms = secs * 1000
        s = self.this_screen
        if not s:
            self.close()
        s.step(ms)
        if s.expired():
            try:
                s = screen.next()
                s.resize(*self.get_size())
                self.this_screen = s
            except StopIteration:
                self.close()

    def on_draw(self):
        self.clear()
        s = self.this_screen
        if s:
            tdgl_draw_parts(s)

    def on_resize(self,w,h):
        s = self.this_screen
        if s:
            s.resize(w,h)
            s.restyle()
        return True

    def on_key_press(self,sym,mods):
        s = self.this_screen
        if s:
            s.keydown(sym,mods)

    def on_key_release(self,sym,mods):
        s = self.this_screen
        if s:
            s.keyup(sym,mods)

    def on_mouse_press(self,x,y,button,mods):
        s = self.this_screen
        if s:
            s.click(x,y,button,mods)
