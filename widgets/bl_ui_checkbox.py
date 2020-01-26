from . bl_ui_widget import *

import blf
import bpy

class BL_UI_Checkbox(BL_UI_Widget):
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self._text_color        = (1.0, 1.0, 1.0, 1.0)
        self._box_color         = (1.0, 1.0, 1.0, 1.0)
        self._cross_color       = (0.2, 0.9, 0.9, 1.0)
        
        self._text = "Checkbox"
        self._text_size = 16
        self._textpos = [x, y]
        self.__boxsize = (16,16)

        self.__state = False

    @property
    def text_color(self):
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
                
    @property
    def text_size(self):
        return self._text_size

    @text_size.setter
    def text_size(self, value):
        self._text_size = value

    @property
    def is_checked(self):
        return self.__state

    @is_checked.setter
    def is_checked(self, value):
        if value != self.__state:
            self.__state = value

            self.call_state_changed()

    def update(self, x, y):        
        super().update(x, y)

        self._textpos = [x + 26, y]

        area_height = self.get_area_height()
        
        y_screen_flip = area_height - self.y_screen

        off_x = 0
        off_y = 0
        sx, sy = self.__boxsize 

        self.shader_chb = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        
        # top left, top right, ...
        vertices_box = (
                    (self.x_screen + off_x,      y_screen_flip - off_y - sy), 
                    (self.x_screen + off_x + sx, y_screen_flip - off_y - sy), 
                    (self.x_screen + off_x + sx, y_screen_flip - off_y),
                    (self.x_screen + off_x,      y_screen_flip - off_y))

        self.batch_box = batch_for_shader(self.shader_chb, 'LINE_LOOP', {"pos": vertices_box})

        inset = 4

        # cross top-left, bottom-right | top-right, bottom-left
        vertices_cross = (
            (self.x_screen + off_x + inset,      y_screen_flip - off_y -  inset), 
            (self.x_screen + off_x + sx - inset, y_screen_flip - off_y - sy + inset),
            (self.x_screen + off_x + sx - inset, y_screen_flip - off_y -  inset), 
            (self.x_screen + off_x + inset, y_screen_flip - off_y - sy + inset))

        self.batch_cross = batch_for_shader(self.shader_chb, 'LINES', {"pos": vertices_cross})

   
    def draw(self):

        area_height = self.get_area_height()
        self.shader_chb.bind()

        if self.is_checked:
            bgl.glLineWidth(3)
            self.shader_chb.uniform_float("color", self._cross_color)

            self.batch_cross.draw(self.shader_chb) 

        bgl.glLineWidth(2)
        self.shader_chb.uniform_float("color", self._box_color)

        self.batch_box.draw(self.shader_chb) 

        # Draw text
        self.draw_text(area_height)


    def draw_text(self, area_height):
        blf.size(0, self._text_size, 72)
        size = blf.dimensions(0, self._text)

        textpos_y = area_height - self._textpos[1] - (self.height + size[1]) / 2.0
        blf.position(0, self._textpos[0], textpos_y, 0)

        r, g, b, a = self._text_color
        blf.color(0, r, g, b, a)

        blf.draw(0, self._text)

    def is_in_rect(self, x, y):
        area_height = self.get_area_height()

        widget_y = area_height - self.y_screen
        if (
            (self.x_screen <= x <= (self.x_screen + self.__boxsize[0])) and 
            (widget_y >= y >= (widget_y - self.__boxsize[1]))
            ):
            return True
           
        return False    

    def set_state_changed(self, state_changed_func):
        self.state_changed_func = state_changed_func  
 
    def call_state_changed(self):
        try:
            self.state_changed_func(self, self.__state)
        except:
            pass

    def toggle_state(self):
        self.__state = not self.__state

    def mouse_enter(self, event, x, y):
        if self._mouse_down:
            self.toggle_state()
            self.call_state_changed()

    def mouse_down(self, x, y):
        if self.is_in_rect(x,y):
            self.toggle_state()

            self.call_state_changed()

            return True

        return False