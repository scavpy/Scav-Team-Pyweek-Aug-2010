"""
Screen module.

The game is divided into Screens
"""
from tdgl.gl import *
from tdgl import part, picking, panel, stylesheet
from tdgl.viewpoint import OrthoView

class Screen(part.Group):
    _next = None
    _screen_styles = {
        "LabelPanel.button": {
            "bg":(0,0.8,0.5,1), "fg":(0,0,0,1),
            "font_size":32,
            "border":2, "bd":(1,1,1,1),
            "bg_margin":18,"bg_radius":42, "bg_round:":0,
            "bd_margin":18,"bd_radius":42, "bd_round:":0,
            },
        "LabelPanel": { "font":"ExperiMental" },
        }

    def __init__(self,name="",**kw):
        super(Screen,self).__init__(name,(),**kw)
        self.build_parts(**kw)
        stylesheet.load(self._screen_styles)
        self.restyle(True)

    @staticmethod
    def screen_order():
        while Screen._next:
            yield Screen._next

    @staticmethod
    def set_next(C ,*args, **kw):
        Screen._next = (C(*args,**kw) if C else None)

    def exit_to(self, C, *args, **kw):
        Screen.set_next(C,*args,**kw)
        self._expired = True

    def setup_geom(self): pass
    def setdown_geom(self): pass
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

    def click(self,x,y,button,mods):
        """ Click to fire """
        if button != 1:
            return
        #STUB exit on click
        self.exit_to(TitleScreen)

class TitleScreen(Screen):

    def build_parts(self,**kw):
        start_btn = panel.LabelPanel("Start", text=" Start ",
                                     geom=dict(pos=(512,200,0)),
                                     style_classes=['button'])
        quit_btn = panel.LabelPanel("Quit", text=" Quit ",
                                     geom=dict(pos=(512,100,0)),
                                     style_classes=['button'])
        container = OrthoView("ortho", [start_btn, quit_btn],
                              geom=dict(left=0,right=1024,top=768,bottom=0))
        self.append(container)

    def pick(self,label):
        name = label.target._name
        if name == "Start":
            print label.target._style
            self.exit_to(GameScreen)
        elif name == "Quit":
            self.exit_to(None)
        else:
            print label

# Initialisation
Screen.set_next(TitleScreen)
next = Screen.screen_order().next
