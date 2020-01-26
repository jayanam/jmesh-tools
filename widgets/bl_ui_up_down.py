from . bl_ui_widget import *

import blf

class BL_UI_Up_Down(BL_UI_Widget):
    
    def __init__(self, x, y):

        self.__up_down_width = 16
        self.__up_down_height = 16

        super().__init__(x, y, self.__up_down_width * 2, self.__up_down_height)

        # Text of the numbers
        self._text_color        = (1.0, 1.0, 1.0, 1.0)

        # Color of the up/down graphics
        self._color          = (0.5, 0.5, 0.7, 1.0)

        # Hover % select colors of the up/down graphics
        self._hover_color    = (0.5, 0.5, 0.8, 1.0)
        self._select_color   = (0.7, 0.7, 0.7, 1.0)

        self._min = 0
        self._max = 100

        self.x_screen = x
        self.y_screen = y
        
        self._text_size = 14
        self._decimals = 2

        self.__state = 0
        self.__up_down_value = round(0, self._decimals)

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

        self.shader.uniform_float("color", color)
        
        self.batch_up.draw(self.shader)

        color = self._color

        # pressed (down button)
        if self.__state == 3:
            color = self._select_color

        # hover (down button)
        elif self.__state == 4:
            color = self._hover_color

        self.shader.uniform_float("color", color)
        self.batch_down.draw(self.shader)        
        
        # Draw value text
        sFormat = "{:0." + str(self._decimals) + "f}"
        blf.size(0, self._text_size, 72)
        
        sValue = sFormat.format(self.__up_down_value)
        size = blf.dimensions(0, sValue)

        y_pos = area_height - self.y_screen - size[1] - 2
        x_pos = self.x_screen + 2 * self.__up_down_width + 10
                      
        blf.position(0, x_pos, y_pos, 0)

        r, g, b, a = self._text_color
        blf.color(0, r, g, b, a)
            
        blf.draw(0, sValue)

    def create_up_down_buttons(self):
        # Up / down triangle
        # 
        #        0
        #     1 /\ 2
        #       --

        area_height = self.get_area_height()

        h = self.__up_down_height
        w = self.__up_down_width / 2.0
        
        pos_y = area_height - self.y_screen
        pos_x = self.x_screen
               
        vertices_up = (
                    (pos_x + w  , pos_y    ),
                    (pos_x      , pos_y - h),
                    (pos_x + 2*w, pos_y - h)
                   )

        pos_x += 18

        vertices_down = (
                    (pos_x      , pos_y    ),
                    (pos_x + w  , pos_y - h),
                    (pos_x + 2*w, pos_y    )
                    
                   )
                    
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        self.batch_up = batch_for_shader(self.shader, 'TRIS', {"pos" : vertices_up})
        self.batch_down = batch_for_shader(self.shader, 'TRIS', {"pos" : vertices_down})
        
    def update(self, x, y): 

        self.x_screen = x
        self.y_screen = y
       
        self.create_up_down_buttons()

 
    def set_value_change(self, value_change_func):
        self.value_change_func = value_change_func

    def is_in_up(self, x, y):

        area_height = self.get_area_height()
        pos_y = area_height - self.y_screen

        if (
            (self.x_screen <= x <= self.x_screen + self.__up_down_width) and 
            (pos_y >= y >= pos_y - self.__up_down_height)
            ): 
            return True

        return False

    def is_in_down(self, x, y):

        area_height = self.get_area_height()
        pos_y = area_height - self.y_screen
        pos_x = self.x_screen + self.__up_down_width + 2

        if (
            (pos_x <= x <= pos_x + self.__up_down_width) and 
            (pos_y >= y >= pos_y - self.__up_down_height)
            ): 
            return True

        return False
    
    def is_in_rect(self, x, y):
        return self.is_in_up(x,y) or self.is_in_down(x,y)

    def set_value(self, value):
        if value < self._min:
            value = self._min
        if value > self._max:
            value = self._max

        if value != self.__up_down_value:
            self.__up_down_value = round(value, self._decimals)

            try:
                self.value_change_func(self, self.__up_down_value)
            except:
                pass
                 
    def mouse_down(self, x, y):    
        if self.is_in_up(x,y):
            self.__state = 1
            self.inc_value()
            return True

        if self.is_in_down(x,y):
            self.__state = 3
            self.dec_value()
            return True
        
        return False

    def inc_value(self):
        self.set_value(self.__up_down_value + 1)

    def dec_value(self):
        self.set_value(self.__up_down_value - 1)
    
    def mouse_move(self, x, y):
        if self.is_in_up(x,y):
            if(self.__state != 1):
                
                # hover state
                self.__state = 2

        elif self.is_in_down(x,y):
            if(self.__state != 3):
                
                # hover state
                self.__state = 4

        else:
            self.__state = 0
 
    def mouse_up(self, x, y):
        self.__state = 0