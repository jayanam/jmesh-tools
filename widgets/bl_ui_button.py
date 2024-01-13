from . bl_ui_widget import *

import blf
import bpy

from .. utils.textutils import *
from .. utils.shader_utils import *

class BL_UI_Button(BL_UI_Widget):
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self._text_color        = (1.0, 1.0, 1.0, 1.0)
        self._hover_bg_color    = (0.5, 0.5, 0.5, 1.0)
        self._select_bg_color   = (0.7, 0.7, 0.7, 1.0)
        
        self._text = "Button"
        self._text_size = 16
        self._textpos = (x, y)
        self._textoffset = [0, 0]

        self.__state = 0
        self.__image = None
        self.__image_size = (24, 24)
        self.__image_position = (4, 2)

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
    def hover_bg_color(self):
        return self._hover_bg_color

    @hover_bg_color.setter
    def hover_bg_color(self, value):
        self._hover_bg_color = value

    @property
    def select_bg_color(self):
        return self._select_bg_color

    @select_bg_color.setter
    def select_bg_color(self, value):
        self._select_bg_color = value 

    def set_text_offset(self, x,y):
        self._textoffset = [x,y]
        
    def set_image_size(self, imgage_size):
        self.__image_size = imgage_size

    def set_image_position(self, image_position):
        self.__image_position = image_position

    def set_image(self, rel_filepath):
        try:
            self.__image = bpy.data.images.load(rel_filepath, check_existing=True)   
            self.__image.gl_load()
        except:
            pass

    def update(self, x, y):        
        super().update(x, y)
        self._textpos = [x, y]
        
    def draw(self):
        if not self.visible:
            return
            
        area_height = self.get_area_height()

        self.shader.bind()
        
        self.set_colors()
        
        gpu.state.blend_set('ALPHA')

        self.batch_panel.draw(self.shader) 

        self.draw_image()   

        gpu.state.blend_set('NONE')

        # Draw text
        self.draw_text(area_height)

    def set_colors(self):
        color = self._bg_color
        text_color = self._text_color

        # pressed
        if self.__state == 1:
            color = self._select_bg_color

        # hover
        elif self.__state == 2:
            color = self._hover_bg_color

        self.shader.uniform_float("color", color)

    def draw_text(self, area_height):
        blf_set_size(0, self._text_size)
        size = blf.dimensions(0, self._text)

        textpos_y = area_height - self._textpos[1] - (self.height + size[1]) / 2.0
        textpos_y += self._textoffset[1]

        blf.position(0, self._textoffset[0] + self._textpos[0] + (self.width - size[0]) / 2.0, textpos_y + 1, 0)

        r, g, b, a = self._text_color
        blf.color(0, r, g, b, a)

        blf.draw(0, self._text)

    def draw_image(self):
        if self.__image is not None:
            try:
                y_screen_flip = self.get_area_height() - self.y_screen
        
                off_x, off_y =  self.__image_position
                sx, sy = self.__image_size
                
                # bottom left, top left, top right, bottom right
                vertices = (
                            (self.x_screen + off_x, y_screen_flip - off_y), 
                            (self.x_screen + off_x, y_screen_flip - sy - off_y), 
                            (self.x_screen + off_x + sx, y_screen_flip - sy - off_y),
                            (self.x_screen + off_x + sx, y_screen_flip - off_y))
                
                self.shader_img = get_builtin_shader('IMAGE', '2D')
                self.batch_img = batch_for_shader(self.shader_img, 'TRI_FAN', 
                { "pos" : vertices, 
                "texCoord": ((0, 1), (0, 0), (1, 0), (1, 1)) 
                },)

                texture = gpu.texture.from_image(self.__image)

                self.shader_img.bind()
                self.shader.uniform_sampler("image", texture)

                self.batch_img.draw(self.shader_img) 
                return True
            except:
                pass

        return False     
        
    def set_mouse_down(self, mouse_down_func):
        self.mouse_down_func = mouse_down_func   
                 
    def mouse_down(self, x, y):    
        if self.is_in_rect(x,y):
            self._mouse_down = True
            self.__state = 1
            try:
                self.mouse_down_func(self)
            except:
                pass
                
            return True
        
        return False
    
    def mouse_move(self, x, y):
        if self.is_in_rect(x,y):
            if(self.__state != 1):
                
                # hover state
                self.__state = 2
        else:
            self.__state = 0
 
    def mouse_up(self, x, y):
        self._mouse_down = False
        if self.is_in_rect(x,y):
            self.__state = 2
        else:
            self.__state = 0