import bpy
from bpy.types import Operator

from .utils.unit_util import *
from .utils.fc_solidify_util import *

from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
from .widgets . bl_ui_button import *
from .widgets . bl_ui_slider import *
from .widgets . bl_ui_textbox import *
from .widgets . bl_ui_drag_panel import *
from .widgets . bl_ui_draw_op import *

class FC_SolidifyOperator(BL_UI_OT_draw_operator):
    bl_idname = "object.solid_op"
    bl_label = "Solidify an object"
    bl_description = "Solidify an object" 
    bl_options = {'REGISTER', 'UNDO'}
              
    @classmethod
    def poll(cls, context):  

        if context.window_manager.modal_running:
            return False

        return len(context.selected_objects) > 0

    def __init__(self):

        y_top = 35
        x_left = 100

        super().__init__()
        self.panel = BL_UI_Drag_Panel(0, 0, 280, 120)
        self.panel.bg_color = (0.1, 0.1, 0.1, 0.9)

        self.lbl_width = BL_UI_Label(20, y_top, 50, 15)
        self.lbl_width.text = "Thickness:"
        self.lbl_width.text_size = 14
        self.lbl_width.text_color = (0.9, 0.9, 0.9, 1.0)

        unitinfo = get_current_units()
        self.thickness = BL_UI_Textbox(x_left, y_top - 2, 125, 24)
        self.thickness.max_input_chars = 8
        self.thickness.is_numeric = True
        self.thickness.label = unitinfo[0]
        input_keys = self.thickness.get_input_keys()
        input_keys.remove('RET')
        input_keys.remove('ESC')
        self.thickness.set_text_changed(self.on_input_changed)

        self.lbl_close = BL_UI_Label(195, y_top - 35, 50, 15)
        self.lbl_close.text = "Escape to Close"
        self.lbl_close.text_size = 10
        self.lbl_close.text_color = (0.9, 0.9, 0.9, 1.0)

        self.btn_apply = BL_UI_Button(20, y_top + 45, 110, 25)
        self.btn_apply.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_apply.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_apply.text_size = 14
        self.btn_apply.text = "Apply modifier"
        self.btn_apply.set_mouse_down(self.on_btn_apply_down)

        self.btn_close = BL_UI_Button(140, y_top + 45, 120, 25)
        self.btn_close.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_close.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_close.text_size = 14
        self.btn_close.text = "Close"
        self.btn_close.set_mouse_down(self.on_btn_close_down)

    def get_thickness(self):
        value = float(self.thickness.text)
        unitinfo = get_current_units()
        return unit_to_bu(value, unitinfo[1])

    def on_btn_close_down(self, widget):
        self.finish()

    def on_btn_apply_down(self, widget):
        mod_solid = self.get_solidify_modifier()

        if(mod_solid):
            bpy.ops.object.modifier_apply(modifier=mod_solid.name)

        self.finish()

    def on_input_changed(self, textbox, context, event):
      thickness = self.get_thickness()
      mod_solid = self.get_solidify_modifier()
      if mod_solid is not None:
        mod_solid.thickness = thickness

    def on_finish(self, context):
        context.window_manager.modal_running = False
        super().on_finish(context)

    def on_invoke(self, context, event):

        bpy.ops.object.mode_set(mode="OBJECT")
        
        self.add_solidify(context)

        # Add new widgets here
        widgets_panel = [self.lbl_width, self.thickness, self.lbl_close]
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

    def get_solidify_modifier(self):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            return active_obj.modifiers.get("Solidify")
        return None

    def init_widget_values(self):
        mod_solid = self.get_solidify_modifier()
        if mod_solid is not None:
            unitinfo = get_current_units()
            thickness = mod_solid.thickness
            unit_value = bu_to_unit(thickness, unitinfo[1])
            self.thickness.text  = "{:.2f}".format(unit_value)

    def add_solidify(self, context):
        
        active_object = bpy.context.view_layer.objects.active

        mod_solid = self.get_solidify_modifier()
        if mod_solid is None:
          execute_solidify(context.active_object)         
