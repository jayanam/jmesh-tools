import gpu
import bgl

from gpu_extras.batch import batch_for_shader

class BL_UI_Widget:
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.x_screen = x
        self.y_screen = y
        self.width = width
        self.height = height
        self._bg_color = (0.8, 0.8, 0.8, 1.0)
        self._tag = None
        self.context = None
        self.__inrect = False
        self._mouse_down = False

    def set_location(self, x, y):
        self.x = x
        self.y = y
        self.x_screen = x
        self.y_screen = y
        self.update(x,y)

    @property
    def bg_color(self):
        return self._bg_color

    @bg_color.setter
    def bg_color(self, value):
        self._bg_color = value

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        self._tag = value
                		    
    def draw(self):
        self.shader.bind()
        self.shader.uniform_float("color", self._bg_color)
        
        bgl.glEnable(bgl.GL_BLEND)
        self.batch_panel.draw(self.shader) 
        bgl.glDisable(bgl.GL_BLEND)

    def init(self, context):
        self.context = context
        self.update(self.x, self.y)
    
    def update(self, x, y):
        
        area_height = self.get_area_height()
        
        self.x_screen = x
        self.y_screen = y
                
        indices = ((0, 1, 2), (0, 2, 3))

        y_screen_flip = area_height - self.y_screen

        # bottom left, top left, top right, bottom right
        vertices = (
                    (self.x_screen, y_screen_flip), 
                    (self.x_screen, y_screen_flip - self.height), 
                    (self.x_screen + self.width, y_screen_flip - self.height),
                    (self.x_screen + self.width, y_screen_flip))
                    
        self.shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        self.batch_panel = batch_for_shader(self.shader, 'TRIS', {"pos" : vertices}, indices=indices)
    
    def handle_event(self, event):
        x = event.mouse_region_x
        y = event.mouse_region_y

        if(event.type == 'LEFTMOUSE'):
            if(event.value == 'PRESS'):
                self._mouse_down = True
                return self.mouse_down(x, y)
            else:
                self._mouse_down = False
                self.mouse_up(x, y)
                
        
        elif(event.type == 'MOUSEMOVE'):
            self.mouse_move(x, y)

            inrect = self.is_in_rect(x, y)

            # we enter the rect
            if not self.__inrect and inrect:
                self.__inrect = True
                self.mouse_enter(event, x, y)

            # we are leaving the rect
            elif self.__inrect and not inrect:
                self.__inrect = False
                self.mouse_exit(event, x, y)

            return False
                        
        return False                 

    def get_area_height(self):
        return self.context.area.height    

    def is_in_rect(self, x, y):
        area_height = self.get_area_height()

        widget_y = area_height - self.y_screen
        if (
            (self.x_screen <= x <= (self.x_screen + self.width)) and 
            (widget_y >= y >= (widget_y - self.height))
            ):
            return True
           
        return False      

    def mouse_down(self, x, y):       
        return self.is_in_rect(x,y)

    def mouse_up(self, x, y):
        pass

    def mouse_enter(self, event, x, y):
        pass

    def mouse_exit(self, event, x, y):
        pass

    def mouse_move(self, x, y):
        pass