from . bl_ui_widget import *

import blf
import bpy


class BL_UI_Textbox(BL_UI_Widget):

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self._text_color = (1.0, 1.0, 1.0, 1.0)

        self._label_color = (1.0, 1.0, 1.0, 1.0)

        self._label_text_color = (0.1, 0.1, 0.1, 1.0)

        self._bg_color = (0.2, 0.2, 0.2, 1.0)

        self._carret_color = (0.0, 0.2, 1.0, 1.0)

        self._offset_letters = 0

        self._carret_pos = 0

        self._input_keys = ['ESC', 'RET', 'BACK_SPACE', 'HOME', 'END', 'LEFT_ARROW', 'RIGHT_ARROW', 'DEL']

        self.text = ""
        self._label = ""
        self._text_size = 12
        self._textpos = [x, y]
        self._max_input_chars = 100
        self._label_width = 0
        self._is_numeric = False

    @property
    def carret_color(self):
        return self._carret_color

    @carret_color.setter
    def carret_color(self, value):
        self._carret_color = value

    @property
    def text_color(self):
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value

    @property
    def max_input_chars(self):
        return self._max_input_chars

    @max_input_chars.setter
    def max_input_chars(self, value):
        self._max_input_chars = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self._carret_pos = len(value)

        if self.context is not None:
            self.update_carret()

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label = value
        if self.context is not None:
            self.update_label()

    @property
    def text_size(self):
        return self._text_size

    @text_size.setter
    def text_size(self, value):
        self._text_size = value

    @property
    def has_label(self):
        return self._label != ""

    @property
    def is_numeric(self):
        return self._is_numeric

    @is_numeric.setter
    def is_numeric(self, value):
        self._is_numeric = value   

    def update(self, x, y):
        super().update(x, y)

        if self.has_label:       
            self.update_label()

        self._textpos = [x, y]
        self.update_carret()

    def update_label(self):
        y_screen_flip = self.get_area_height() - self.y_screen

        size = blf.dimensions(0, self._label)

        self._label_width = size[0] + 12

        # bottom left, top left, top right, bottom right
        vertices_outline = (
                    (self.x_screen, y_screen_flip), 
                    (self.x_screen + self.width + self._label_width, y_screen_flip), 
                    (self.x_screen + self.width + self._label_width, y_screen_flip - self.height),
                    (self.x_screen, y_screen_flip - self.height))
                    
        self.batch_outline = batch_for_shader(self.shader, 'LINE_LOOP', {"pos" : vertices_outline})

        indices = ((0, 1, 2), (2, 3, 1))

        lb_x = self.x_screen + self.width

        # bottom left, top left, top right, bottom right
        vertices_label_bg = (
                    (lb_x, y_screen_flip), 
                    (lb_x + self._label_width, y_screen_flip), 
                    (lb_x, y_screen_flip - self.height),
                    (lb_x + self._label_width, y_screen_flip - self.height))
                    
        self.batch_label_bg = batch_for_shader(self.shader, 'TRIS', {"pos" : vertices_label_bg}, indices=indices)

    def get_carret_pos_px(self):
        size_all = blf.dimensions(0, self._text)
        size_to_carret = blf.dimensions(0, self._text[:self._carret_pos])
        return self.x_screen + (self.width / 2.0) - (size_all[0] / 2.0) + size_to_carret[0]

    def update_carret(self):

        y_screen_flip = self.get_area_height() - self.y_screen

        x = self.get_carret_pos_px()

        # bottom left, top left, top right, bottom right
        vertices = (
            (x, y_screen_flip - 6),
            (x, y_screen_flip - self.height + 6)
        )

        self.batch_carret = batch_for_shader(
            self.shader, 'LINES', {"pos": vertices})

    def draw(self):

        if not self.visible:
            return
            
        super().draw()

        area_height = self.get_area_height()

        # Draw text
        self.draw_text(area_height)

        self.shader.bind()
        self.shader.uniform_float("color", self._carret_color)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        bgl.glLineWidth(2)
        self.batch_carret.draw(self.shader)

        if self.has_label:
            self.shader.uniform_float("color", self._label_color)
            bgl.glLineWidth(1)
            self.batch_outline.draw(self.shader)

            self.batch_label_bg.draw(self.shader)

            size = blf.dimensions(0, self._label)

            textpos_y = area_height - self.y_screen - (self.height + size[1]) / 2.0
            blf.position(0, self.x_screen + self.width + (self._label_width / 2.0) - (size[0]  / 2.0), textpos_y + 1, 0)

            r, g, b, a = self._label_text_color
            blf.color(0, r, g, b, a)

            blf.draw(0, self._label)

    def set_colors(self):
        color = self._bg_color
        text_color = self._text_color

        self.shader.uniform_float("color", color)

    def draw_text(self, area_height):
        blf.size(0, self._text_size, 72)
        size = blf.dimensions(0, self._text)

        textpos_y = area_height - self._textpos[1] - (self.height + size[1]) / 2.0
        blf.position(0, self._textpos[0] + (self.width - size[0]) / 2.0, textpos_y + 1, 0)

        r, g, b, a = self._text_color
        blf.color(0, r, g, b, a)

        blf.draw(0, self._text)

    def get_input_keys(self):
        return self._input_keys

    def text_input(self, event):

        index = self._carret_pos

        if event.ascii != '' and len(self._text) < self.max_input_chars:
            value = self._text[:index] + event.ascii + self._text[index:]
            if self._is_numeric and not (event.ascii.isnumeric() or event.ascii in ['.', ',', '-']):
                return False
                
            self._text = value
            self._carret_pos += 1
        elif event.type == 'BACK_SPACE':
            if event.ctrl:
                self._text = ""
                self._carret_pos = 0
            elif self._carret_pos > 0:
                self._text = self._text[:index-1] + self._text[index:]
                self._carret_pos -= 1

        elif event.type == 'DEL':
            if self._carret_pos < len(self._text):
                self._text = self._text[:index] + self._text[index+1:]

        elif event.type == 'LEFT_ARROW':
            if self._carret_pos > 0:
                self._carret_pos -= 1

        elif event.type == 'RIGHT_ARROW':
            if self._carret_pos < len(self._text):
                self._carret_pos += 1

        elif event.type == 'HOME':
            self._carret_pos = 0

        elif event.type == 'END':
            self._carret_pos = len(self._text)

        self.update_carret()
        try:
            self.text_changed_func(self, self.context, event)
        except:
            pass

        return True

    def set_text_changed(self, text_changed_func):
        self.text_changed_func = text_changed_func

    def mouse_down(self, x, y):
        if self.is_in_rect(x, y):
            return True

        return False

    def mouse_move(self, x, y):
        pass

    def mouse_up(self, x, y):
        pass
