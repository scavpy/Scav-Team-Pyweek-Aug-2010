"""
 A Panel is a container for some 2D graphics with known
 dimensions.  A flat shape with a border is drawn behind
 the object.

 In its simplest form, it's a rectangle with no border,
 but it can be textured, have rounded corners and so on.

-
Copyright Oct 2009 by Peter Harris
Released under the terms of the GNU General Public License v3 or later

"""
from __future__ import division

from pyglet import image, text

from tdgl.gl import *
from tdgl import part, picking
from tdgl.stylesheet import border_points

__all__ = ('Panel','LabelPanel')

class Panel(part.ScalePart):
    """Base class for things with a bordered panel behind"""
    _default_style = dict(
        bg=None,  # background colour
        bd=None,  # border colour
        border=0, # border width
        bg_radius = 0, # corner radius of background
        bg_round = 0,  # num rounding points at corner
        bd_radius = 0, # corner radius of border
        bd_round = 0,  # rounding points at border corner
        bg_margin = 0, # 0 = (0,0). Spacing from contents to panel edge
        bd_margin = 0, # spacing from contents to border
        texture = None, # texture of panel
        texture_repeat = 'scale', # == (1,1), num repeats across panel
        )
    _style_attributes = tuple(_default_style.keys())
    def __init__(self,*args,**kw):
        super(Panel,self).__init__(*args,**kw)
        dl = glGenLists(2)
        self.bgdl = dl     # for background
        self.bddl = dl + 1 # for border
    def __del__(self):
        glDeleteLists(self.bgdl,2)
    def render(self,mode="OPAQUE"):
        if mode == 'PICK':
            picking.label(self)
        glCallList(self.bgdl)
        glCallList(self.bddl)
        self.render_content(mode)
        if mode == 'PICK':
            picking.nolabel()
    def prepare(self):
        self.prepare_content()
        getstyle = self.getstyle
        bg = getstyle("bg")
        tex = getstyle("texture")
        if bg:
            if isinstance(tex,basestring):
                self.tex = image.load(tex).get_mipmapped_texture()
                self.tex_id = self.tex.id
            elif hasattr(tex,"id"):
                self.tex = tex
                self.tex_id = tex.id
            elif isinstance(tex,int):
                self.tex = tex
                self.tex_id = tex
            else:
                self.tex = None
                self.tex_id = 0
        bd = getstyle("bd")
        border = getstyle("border")
        with gl_compile(self.bgdl):
            if bg:
                self.render_background()
        with gl_compile(self.bddl):
            if bd and border:
                self.render_border()

    def render_background(self):
        w,h = self.content_size()
        getstyle = self.getstyle
        bg = getstyle("bg")
        has_texture = bool(self.tex)
        margin = getstyle("bg_margin",0)
        if type(margin) in (int,float):
            marginx = margin
            marginy = margin
        else:
            marginx,marginy = margin
        radii = getstyle("bg_radius",0)
        round = getstyle("bg_round",0)
        points = border_points(
            w + 2*marginx, h + 2*marginy,
            radii, round)
        if has_texture:
            rep = getstyle("texture_repeat","scale")
            if rep == "scale":
                rep = 1.0
            if type(rep) in (int,float):
                aspect = w/h
                rep = (rep*aspect,rep)
            rx,ry = rep
            tw = rx / (w + 2*marginx)
            th = ry / (h + 2*marginy)
            tpoints = [(x*tw + 0.5, y*th + 0.5)
                       for x,y in points]
            glBindTexture(GL_TEXTURE_2D,self.tex_id)
            glEnable(GL_TEXTURE_2D)
        else:
            glDisable(GL_TEXTURE_2D)
            tpoints = []
        glColor4f(*bg)
        v = glVertex3f
        tc = glTexCoord2f
        z = -0.02
        with gl_begin(GL_TRIANGLE_FAN):
            tc(0.5,0.5); v(0,0,z)
            if tpoints:
                for (x,y),(s,t) in zip(points,tpoints):
                    tc(s,t)
                    v(x,y,z)
            else:
                for (x,y) in points:
                    v(x,y,z)

    def render_border(self):
        w,h = self.content_size()
        getstyle = self.getstyle
        bd = getstyle("bd")
        border = getstyle("border")
        margin = getstyle("bd_margin",0)
        if type(margin) in (int,float):
            marginx = margin
            marginy = margin
        else:
            marginx,marginy = margin
        radii = getstyle("bd_radius",0)
        round = getstyle("bd_round",0)
        points = border_points(
            w + 2*marginx, h + 2*marginy,
            radii, round)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_LINE_SMOOTH)
        glColor4f(*bd)
        v = glVertex3f
        z = -0.01
        glLineWidth(border)
        with gl_begin(GL_LINE_LOOP):
            for (x,y) in points:
                v(x,y,z)

    # Override in sub-classes:
    def prepare_content(self):
        pass
    def render_content(self,mode):
        pass
    def content_size(self):
        return (1,1)

class LabelPanel(Panel):
    """ A Panel containing a pyglet Label"""
    _default_style = Panel._default_style.copy()
    _default_style.update(dict(fg=(1,1,1,1),
                               font=None,
                               font_size=16,
                               italic=False,
                               bold=False))
    _style_attributes = tuple(_default_style.keys())

    def __init__(self,name="",text="",html=False,**kw):
        super(LabelPanel,self).__init__(name,**kw)
        self.text = text
        self.html = html
        self.prepare()
    def content_size(self):
        return self.label.content_width,self.label.content_height
    def render_content(self,mode="OPAQUE"):
        self.label.draw()
    def prepare_content(self):
        getstyle = self.getstyle
        fg = getstyle("fg",(1,1,1,1))
        font = getstyle("font")
        font_size = getstyle("font_size")
        italic = getstyle("italic",False)
        bold = getstyle("bold", False)
        text_width = self.getgeom("text_width")
        multiline = bool(text_width)
        color = [int(c*255) for c in fg]
        if self.html:
            self.label = text.HTMLLabel(
                text=self.text,
                width=text_width,
                multiline=multiline,
                anchor_x='center',anchor_y='center')
            self.label.set_style('color',color)
        else:
            self.label = text.Label(
                text=self.text,
                font_name=font, font_size=font_size,
                color=color,
                italic=italic, bold=bold,
                width=text_width,
                multiline=multiline,
                anchor_x='center',anchor_y='center')

class SelectPanel(Panel):
    """ A Panel containing stacked parts, with one selected.
    The parts have to implement content_size(), so some
    kind of Panel is likely. """
    _default_style = Panel._default_style.copy()
    _default_style["pad"] = 2
    _style_attributes = tuple(_default_style.keys())
    def __init__(self,name="",contents=(),selected=None,vertical=True,**kw):
        super(SelectPanel,self).__init__(name,**kw)
        self.vertical = vertical
        self.selected = selected
        self.contents = list(contents)
        self._content_size = (1,1)
    def prepare_content(self):
        sumw = sumh = 0
        minw = maxw = None
        minh = maxh = None
        pad = self.getstyle("pad",0)
        for i,p in enumerate(self.contents):
            classes = ["choice"]
            if i == self.selected:
                classes.append("selected")
            p.choice_number = i # So we can tell which one it is
            p.add_styles(*classes)
            p.prepare()
            w,h = p.content_size()
            sumw += w
            sumh += h
            minw = w if minw is None else min(minw,w)
            minh = h if minh is None else min(minh,h)
            maxw = w if maxw is None else max(maxw,w)
            maxh = h if maxh is None else max(maxh,h)
        if self.vertical:
            self._content_size = maxw,sumh + (len(self.contents)-1) * pad
            y = sumh / 2.0 # top of contents box, relative to centre
            x = 0
            z = 0.01
            for p in self.contents:
                w,h = p.content_size()
                p.pos = (x,y-h/2.0,z)
                y -= (h + pad)# top of next line
        else:
            self._content_size = sumw + (len(self.contents)-1) * pad,maxh
            y = 0
            x = -sumw / 2.0 # left of contents box, relative to centre
            z = 0.01
            for p in self.contents:
                w,h = p.content_size()
                p.pos = (x + w/2.0,y,z)
                x += w + pad # left of next column
    def render_content(self,mode="OPAQUE"):
        for i,p in enumerate(self.contents):
            if mode=="PICK":
                picking.label(self,selected=i)
            p.draw(mode)
            if mode=="PICK":
                picking.nolabel()
    def content_size(self):
        return self._content_size

    def select_by_number(self,n):
        if n is None or 0 <= n < len(self.contents):
            self.selected = n
            self.prepare()
            
    def select_object(self,obj):
        try:
            self.selected = self.contents.index(obj)
        except ValueError:
            self.selected = None
        self.prepare()
    
    def restyle(self,force=False):
        """Copied from Group.restyle()"""
        super(SelectPanel,self).restyle(force)
        for p in self.contents:
            p.restyle(force)

class SelectTextPanel(SelectPanel):
    """A simple SelectPanel containing LabelPanels"""
    def __init__(self,name="",lines=(),**kw):
        labels = [LabelPanel(name="%s[%d]" % (name,i), text=line) 
                  for i,line in enumerate(lines)]
        super(SelectTextPanel,self).__init__(name, contents=labels, **kw)
