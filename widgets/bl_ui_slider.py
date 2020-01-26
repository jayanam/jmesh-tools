from . bl_ui_widget import *

import blf

class BL_UI_Slider(BL_UI_Widget):
    
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self._text_color        = (1.0, 1.0, 1.0, 1.0)
        self._color          = (0.5, 0.5, 0.7, 1.0)
        self._hover_color    = (0.5, 0.5, 0.8, 1.0)
        self._select_color   = (0.7, 0.7, 0.7, 1.0)
        self._bg_color       = (0.8, 0.8, 0.8, 0.6)

        self._min = 0
        self._max = 100
        
        self.x_screen = x
        self.y_screen = y
        
        self._text_size = 14
        self._decimals = 2

        self._show_min_max = True

        self.__state = 0
        self.__is_drag = False
        self.__slider_pos = 0
        self.__slider_value = round(0, self._decimals)
        self.__slider_width = 5
        self.__slider_height = 13
        self.__slider_offset_y = 3


    @property
    def text_color(self):
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value

    @property
    def text_size(self):
        return self._text_size

    @text_size.setter
    def text_size(self, value):
        self._text_size = value

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value

    @property
    def hover_color(self):
        return self._hover_color

    @hover_color.setter
    def hover_color(self, value):
        self._hover_color = value

    @property
    def select_color(self):
        return self._select_color

    @select_color.setter
    def select_color(self, value):
        self._select_color = value

    @property
    def min(self):
        return self._min

    @min.setter
    def min(self, value):
        self._min = value

    @property
    def max(self):
        return self._max

    @max.setter
    def max(self, value):
        self._max = value

    @property
    def decimals(self):
        return self._decimals

    @decimals.setter
    def decimals(self, value):
        self._decimals = value

    @property
    def show_min_max(self):
        return self._show_min_max

    @show_min_max.setter
    def show_min_max(self, value):
        self._show_min_max = value
                
    def draw(self):

        area_height = self.get_area_height()

        self.shader.bind()
        
        color = self._color
        text_color = self._text_color
        
        # pressed
        if self.__state == 1:
            color = self._select_color

        # hover
        elif self.__state == 2:
            color = self._hover_color

        # Draw background
        self.shader.uniform_float("color", self._bg_color)
        bgl.glEnable(bgl.GL_BLEND)
        self.batch_bg.draw(self.shader)

        # Draw slider   
        self.shader.uniform_float("color", color)
        
        self.batch_slider.draw(self.shader) 
        bgl.glDisable(bgl.GL_BLEND)      
        
        # Draw value text
        sFormat = "{:0." + str(self._decimals) + "f}"
        blf.size(0, self._text_size, 72)
        
        sValue = sFormat.format(self.__slider_value)
        size = blf.dimensions(0, sValue)
                      
        blf.position(0, self.__slider_pos + 1 + self.x_screen - size[0] / 2.0, 
                        area_height - self.y_screen + self.__slider_offset_y, 0)
            
        blf.draw(0, sValue)

        # Draw min and max
        if self._show_min_max:
            sMin = sFormat.format(self._min)
            
            size = blf.dimensions(0, sMin)
                        
            blf.position(0, self.x_screen - size[0] / 2.0, 
                            area_height - self.height - self.y_screen, 0)
            blf.draw(0, sMin)

            sMax = sFormat.format(self._max)
            
            size = blf.dimensions(0, sMax)

            r, g, b, a = self._text_color
            blf.color(0, r, g, b, a)
                        
            blf.position(0, self.x_screen + self.width - size[0] / 2.0, 
                            area_height - self.height - self.y_screen, 0)
            blf.draw(0, sMax)


    def update_slider(self):
        # Slider triangles
        # 
        #        0
        #     1 /\ 2
        #      |  |
        #     3---- 4

        # batch for slider
        area_height = self.get_area_height()

        h = self.__slider_height
        w = self.__slider_width
        pos_y = area_height - self.y_screen - self.height / 2.0 + self.__slider_height / 2.0 + self.__slider_offset_y
        pos_x = self.x_screen + self.__slider_pos
        
        indices = ((0, 1, 2), (1, 2, 3), (3, 2, 4))
        
        vertices = (
                    (pos_x    , pos_y    ),
                    (pos_x - w, pos_y - w),
                    (pos_x + w, pos_y - w),
                    (pos_x - w, pos_y - h),
                    (pos_x + w, pos_y - h)
                   )
                    
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        self.batch_slider = batch_for_shader(self.shader, 'TRIS', 
        {"pos" : vertices}, indices=indices)
        
    def update(self, x, y): 

        area_height = self.get_area_height()
        
        # Min                      Max
        #  |---------V--------------|
        
        self.x_screen = x
        self.y_screen = y
        
        self.update_slider()

        # batch for background
        pos_y = area_height - self.y_screen - self.height / 2.0
        pos_x = self.x_screen

        indices = ((0, 1, 2), (0, 2, 3))

        # bottom left, top left, top right, bottom right
        vertices = (
                    (pos_x, pos_y), 
                    (pos_x, pos_y + 4), 
                    (pos_x + self.width, pos_y + 4),
                    (pos_x + self.width, pos_y)
        )


        self.batch_bg = batch_for_shader(self.shader, 'TRIS', {"pos" : vertices}, indices=indices)
 
    def set_value_change(self, value_change_func):
        self.value_change_func = value_change_func
    
    def is_in_rect(self, x, y):
        area_height = self.get_area_height()
        slider_y = area_height - self.y_screen - self.height / 2.0 + self.__slider_height / 2.0 + self.__slider_offset_y

        if (
            (self.x_screen + self.__slider_pos - self.__slider_width <= x <= 
            (self.x_screen + self.__slider_pos + self.__slider_width)) and 
            (slider_y >= y >= slider_y - self.__slider_height)
            ):
            return True
           
        return False

    def __value_to_pos(self, value):
        return self.width * (value - self._min) / (self._max - self._min)

    def __pos_to_value(self, pos):
        return self._min + round(((self._max - self._min) * self.__slider_pos / self.width), self._decimals)

    def set_value(self, value):
        if value < self._min:
            value = self._min
        if value > self._max:
            value = self._max

        if value != self.__slider_value:
            self.__slider_value = round(value, self._decimals)

            try:
                self.value_change_func(self, self.__slider_value)
            except:
                pass

            self.__slider_pos = self.__value_to_pos(self.__slider_value)

            if self.context is not None:
                self.update_slider()


    def __set_slider_pos(self, x):
        if x <= self.x_screen:
            self.__slider_pos = 0
        elif x >= self.x_screen + self.width:
            self.__slider_pos = self.width
        else:
            self.__slider_pos = x - self.x_screen

        newValue = self.__pos_to_value(self.__slider_pos)

        if newValue != self.__slider_value:
            self.__slider_value = newValue

            try:
                self.value_change_func(self, self.__slider_value)
            except:
                pass
                 
    def mouse_down(self, x, y):    
        if self.is_in_rect(x,y):
            self.__state = 1
            self.__is_drag = True
                
            return True
        
        return False
    
    def mouse_move(self, x, y):
        if self.is_in_rect(x,y):
            if(self.__state != 1):
                
                # hover state
                self.__state = 2
        else:
            self.__state = 0
        
        if self.__is_drag:
            self.__set_slider_pos(x)
            self.update(self.x_screen, self.y_screen)
 
    def mouse_up(self, x, y):
        self.__state = 0
        self.__is_drag = False