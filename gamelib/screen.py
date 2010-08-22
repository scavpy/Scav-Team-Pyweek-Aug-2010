"""
Screen module.

The game is divided into Screens
"""
from tdgl.gl import *
from tdgl import part, picking

class Screen(part.Group):
    _next = None
    def __init__(self,name="",**kw):
        super(Screen,self).__init__(name,(),**kw)
        self.build_parts(**kw)
        self.restyle(True)

    @staticmethod
    def screen_order():
        while Screen._next:
            yield Screen._next

    @staticmethod
    def set_next(C,*args,**kw):
        Screen._next = (C(*args,**kw) if C else None)

    def exit_to(C, *args, **kw):
        Screen.set_next(C,*args,**kw)
        self._expired = True

    def build_parts(self,**kw): pass
    def keydown(self,sym,mods): pass
    def keyup(self,sym,mods): pass

    def resize(self,width,height):
        self.size = width,height
        for g in self.contents:
            if hasattr(g,'resize'):
                g.resize(width,height)

    def pick_at(self,x,y):
        """Pick topmost object at x,y"""
        picking.start(x,y,1,1)
        self.draw('PICK')
        objects = picking.end()
        if objects:
            minz,maxz,label = objects[0]
            self.pick(label)

    def click(self,x,y,button,mods):
        """ Default behaviour is pick """
        if button != 1:
            return
        self.pick_at(x,y)

    def pick(self,label):
        pass


class GameScreen(Screen):
    pass

class TitleScreen(Screen):
    
    def build_parts(self,**kw):
        # TODO - add a Start button
        pass

    def pick(self,label):
        if label == "Start":
            exit_to(GameScreen)
        elif label == "Quit":
            exit_to(None)

# Initialisation
Screen._next = TitleScreen()
next = Screen.screen_order().next
