import bpy
from bpy.types import Operator

from .utils.unit_util import *
from .utils.fc_cloth_util import *

from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
from .widgets . bl_ui_button import *
from .widgets . bl_ui_slider import *
from .widgets . bl_ui_drag_panel import *
from .widgets . bl_ui_draw_op import *

class FC_CircleOperator(BL_UI_OT_draw_operator):
    bl_idname = "object.jnm_circle_op"
    bl_label = "Circle Operator"
    bl_description = "Create circle for selected vertices" 
    bl_options = {'REGISTER', 'UNDO'}
              
    @classmethod
    def poll(cls, context):  

        if context.window_manager.modal_running:
            return False


        if context.active_object == None:
            return False
        
        mode = context.active_object.mode    
        vertex_select = context.tool_settings.mesh_select_mode[0]  
        return len(context.selected_objects) == 1 and mode == "EDIT" and vertex_select

    def __init__(self):

        y_top = 35
        x_left = 100
        self._current = ""

        super().__init__()
        self.panel = BL_UI_Drag_Panel(0, 0, 280, 170)
        self.panel.bg_color = (0.1, 0.1, 0.1, 0.9)

        self.lbl_close = BL_UI_Label(195, y_top - 35, 50, 15)
        self.lbl_close.text = "Escape to Close"
        self.lbl_close.text_size = 10
        self.lbl_close.text_color = (0.9, 0.9, 0.9, 1.0)

        y_top += 15

        self.lbl_resolution = BL_UI_Label(20, y_top, 50, 15)
        self.lbl_resolution.text = "Resolution:"
        self.lbl_resolution.text_size = 14
        self.lbl_resolution.text_color = (0.9, 0.9, 0.9, 1.0)

        self.sl_resolution = BL_UI_Slider(x_left, y_top, 160, 24)
        self.sl_resolution.color = (0.3, 0.56, 0.94, 1.0)
        self.sl_resolution.hover_color = (0.3, 0.56, 0.94, 0.8)
        self.sl_resolution.min = 4
        self.sl_resolution.max = 256
        self.sl_resolution.decimals = 0
        self.sl_resolution.show_min_max = False
        self.sl_resolution.tag = 0
        self.sl_resolution.set_value_change(self.on_resolution_changed)

        self.btn_apply = BL_UI_Button(105, y_top + 45, 80, 25)
        self.btn_apply.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_apply.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_apply.text_size = 14
        self.btn_apply._textoffset = [0, 2]
        self.btn_apply.text = "Apply"

        self.btn_close = BL_UI_Button(190, y_top + 45, 80, 25)
        self.btn_close.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_close.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_close.text_size = 14
        self.btn_close.text = "Close"
        self.btn_close.set_mouse_down(self.on_btn_close_down)

    def modal(self, context, event):
        active = context.view_layer.objects.active

        if active:
            if(self._current != "" and self._current != active.name):
                self.init_widget_values()

            self._current = active.name

        return super().modal(context, event)


    def get_resolution(self):
        return float(self.sl_resolution.get_value())

    def on_btn_close_down(self, widget):
        self.finish()

    def apply_settings(self):
        pass

    def prepare_vertices(self):
        bpy.ops.mesh.bevel(offset_type='OFFSET', offset=0.3, affect='VERTICES')


    def on_resolution_changed(self, slider, value):
      self.apply_settings()

    def on_finish(self, context):
        context.window_manager.modal_running = False
        super().on_finish(context)

    def on_invoke(self, context, event):
      
        # Add new widgets here
        widgets_panel = [self.lbl_resolution, self.sl_resolution, self.lbl_close]
        widgets_panel.append(self.btn_apply)
        widgets_panel.append(self.btn_close)

        widgets = [self.panel]
        widgets += widgets_panel

        self.init_widgets(context, widgets)

        self.panel.add_widgets(widgets_panel)

        # Open the panel at the mouse location
        self.panel.set_location(context.area.height / 2.0, 
                                context.area.height / 2.0)

        self.prepare_vertices()

        self.init_widget_values()

        context.window_manager.modal_running = True

    def init_widget_values(self):
      self.sl_resolution.set_value(32)      
