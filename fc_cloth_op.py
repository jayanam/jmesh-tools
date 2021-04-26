import bpy
from bpy.types import Operator

from .utils.unit_util import *
from .utils.fc_cloth_util import *

from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
from .widgets . bl_ui_button import *
from .widgets . bl_ui_slider import *
from .widgets . bl_ui_textbox import *
from .widgets . bl_ui_drag_panel import *
from .widgets . bl_ui_draw_op import *

class FC_ClothOperator(BL_UI_OT_draw_operator):
    bl_idname = "object.cloth_op"
    bl_label = "Clothify"
    bl_description = "Add cloth modifier to an object" 
    bl_options = {'REGISTER', 'UNDO'}
              
    @classmethod
    def poll(cls, context):  

        if context.window_manager.modal_running:
            return False

        return len(context.selected_objects) > 0

    def __init__(self):

        y_top = 35
        x_left = 90

        super().__init__()
        self.panel = BL_UI_Drag_Panel(0, 0, 280, 120)
        self.panel.bg_color = (0.1, 0.1, 0.1, 0.9)

        self.lbl_Pressure = BL_UI_Label(20, y_top, 50, 15)
        self.lbl_Pressure.text = "Pressure:"
        self.lbl_Pressure.text_size = 14
        self.lbl_Pressure.text_color = (0.9, 0.9, 0.9, 1.0)

        unitinfo = get_current_units()
        self.txt_pressure = BL_UI_Textbox(x_left, y_top - 2, 50, 24)
        self.txt_pressure.is_numeric = True
        input_keys = self.txt_pressure.get_input_keys()
        input_keys.remove('RET')
        input_keys.remove('ESC')
        self.txt_pressure.set_text_changed(self.on_pressure_changed)

        self.lbl_close = BL_UI_Label(195, y_top - 35, 50, 15)
        self.lbl_close.text = "Escape to Close"
        self.lbl_close.text_size = 10
        self.lbl_close.text_color = (0.9, 0.9, 0.9, 1.0)

        self.btn_start_stop = BL_UI_Button(20, y_top + 45, 80, 25)
        self.btn_start_stop.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_start_stop.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_start_stop.text_size = 14
        self.btn_start_stop.text = "Start"
        self.btn_start_stop.set_mouse_down(self.on_btn_start_stop_down)

        self.btn_apply = BL_UI_Button(105, y_top + 45, 80, 25)
        self.btn_apply.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_apply.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_apply.text_size = 14
        self.btn_apply._textoffset = [0, 2]
        self.btn_apply.text = "Apply"
        self.btn_apply.set_mouse_down(self.on_btn_apply_down)

        self.btn_close = BL_UI_Button(190, y_top + 45, 80, 25)
        self.btn_close.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_close.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_close.text_size = 14
        self.btn_close.text = "Close"
        self.btn_close.set_mouse_down(self.on_btn_close_down)

    def get_pressure(self):
        return float(self.txt_pressure.text)

    def on_btn_close_down(self, widget):
        self.finish()

    def set_start_stop_text(self):
        
        btn = self.btn_start_stop
        btn._textoffset = [0,0]
        
        if bpy.context.screen.is_animation_playing:
            btn.text = "Stop"
            btn._textoffset = [0,2]
        else:
            btn.text = "Start"


    def on_btn_start_stop_down(self, widget):

        scn = bpy.context.scene
        if bpy.context.screen.is_animation_playing:
            frame = scn.frame_current
            bpy.ops.screen.animation_cancel()
            scn.frame_set(frame)
        else:
            scn.frame_set(0)
            bpy.ops.screen.animation_play()

        self.set_start_stop_text()
        
    def on_btn_apply_down(self, widget):
        mod_cloth = self.get_cloth_modifier()

        if(mod_cloth):
            bpy.ops.object.modifier_apply(modifier=mod_cloth.name)

        self.finish()

    def on_pressure_changed(self, textbox, context, event):
      pressure = self.get_pressure()
      mod_cloth = self.get_cloth_modifier()
      if mod_cloth is not None:
         mod_cloth.settings.uniform_pressure_force = pressure

    def on_finish(self, context):
        context.window_manager.modal_running = False
        super().on_finish(context)

    def on_invoke(self, context, event):

        bpy.ops.object.mode_set(mode="OBJECT")
        
        self.add_cloth(context)

        # Add new widgets here
        widgets_panel = [self.lbl_Pressure, self.txt_pressure, self.lbl_close]
        widgets_panel.append(self.btn_start_stop)
        widgets_panel.append(self.btn_apply)
        widgets_panel.append(self.btn_close)

        widgets = [self.panel]
        widgets += widgets_panel

        self.init_widgets(context, widgets)

        self.panel.add_widgets(widgets_panel)

        # Open the panel at the mouse location
        self.panel.set_location(context.area.height / 2.0, 
                                context.area.height / 2.0)

        self.init_widget_values()

        context.window_manager.modal_running = True

    def get_cloth_modifier(self):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            return active_obj.modifiers.get("Cloth")
        return None

    def init_widget_values(self):
        mod_cloth = self.get_cloth_modifier()
        if mod_cloth is not None: 
            pressure = mod_cloth.settings.uniform_pressure_force
            self.txt_pressure.text  = "{:.2f}".format(pressure)

    def add_cloth(self, context):
        
        active_object = bpy.context.view_layer.objects.active

        mod_cloth = self.get_cloth_modifier()
        if mod_cloth is None:
          execute_cloth(context.active_object)         
