import bpy
from bpy.types import Operator

from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
from .widgets . bl_ui_button import *
from .widgets . bl_ui_slider import *
from .widgets . bl_ui_up_down import *
from .widgets . bl_ui_drag_panel import *
from .widgets . bl_ui_draw_op import *

from .utils.fc_bevel_util import execute_bevel


class FC_BevelOperator(BL_UI_OT_draw_operator):
    bl_idname = "object.bevel"
    bl_label = "Bevel an object"
    bl_description = "Bevels selected objects" 
    bl_options = {'REGISTER', 'UNDO'}

    
    def get_display(mode):
        if mode == "OBJECT":
            return "Bevel"
        else:
            return "Sharpen Edges"
                  
    @classmethod
    def poll(cls, context):  

        if context.window_manager.modal_running:
            return False

        return len(context.selected_objects) > 0

    def __init__(self):

        y_top = 25
        x_left = 100

        super().__init__()
        self.panel = BL_UI_Drag_Panel(0, 0, 270, 120)
        self.panel.bg_color = (0.1, 0.1, 0.1, 0.9)

        self.lbl_bvl_segm = BL_UI_Label(20, y_top, 50, 15)
        self.lbl_bvl_segm.text = "Segments:"
        self.lbl_bvl_segm.text_size = 14
        self.lbl_bvl_segm.text_color = (0.9, 0.9, 0.9, 1.0)

        self.ud_segm_count = BL_UI_Up_Down(x_left, y_top)
        self.ud_segm_count.color = (0.3, 0.56, 0.94, 1.0)
        self.ud_segm_count.hover_color = (0.3, 0.56, 0.94, 0.8)
        self.ud_segm_count.min = 1
        self.ud_segm_count.max = 10
        self.ud_segm_count.decimals = 0
        self.ud_segm_count.set_value(1.0)
        self.ud_segm_count.set_value_change(self.on_bevel_segm_count_change)

        self.lbl_bvl_width = BL_UI_Label(20, y_top + 45, 50, 15)
        self.lbl_bvl_width.text = "Width:"
        self.lbl_bvl_width.text_size = 14
        self.lbl_bvl_width.text_color = (0.9, 0.9, 0.9, 1.0)

        self.sl_width = BL_UI_Slider(x_left, y_top + 45, 150, 30)
        self.sl_width.color = (0.3, 0.56, 0.94, 1.0)
        self.sl_width.hover_color = (0.3, 0.56, 0.94, 0.8)
        self.sl_width.min = 0.0
        self.sl_width.max = 0.05
        self.sl_width.decimals = 3
        self.sl_width.show_min_max = False
        self.sl_width.tag = 0
        self.sl_width.set_value_change(self.on_bevel_width_value_change)

        self.lbl_close = BL_UI_Label(185, y_top - 25, 50, 15)
        self.lbl_close.text = "Escape to Close"
        self.lbl_close.text_size = 10
        self.lbl_close.text_color = (0.9, 0.9, 0.9, 1.0)

    def on_finish(self, context):
        context.window_manager.modal_running = False

    def on_invoke(self, context, event):

        self.add_bevel(context)

        active_object = bpy.context.view_layer.objects.active
        mode = active_object.mode

        if mode == "OBJECT":

            # Add new widgets here
            widgets_panel = [self.lbl_bvl_width, self.sl_width, self.lbl_bvl_segm, self.ud_segm_count, self.lbl_close]

            widgets = [self.panel]
            widgets += widgets_panel

            self.init_widgets(context, widgets)

            self.panel.add_widgets(widgets_panel)

            # Open the panel at the mouse location
            self.panel.set_location(context.area.height / 2.0, 
                                    context.area.height / 2.0)

            self.init_widget_values()

            context.window_manager.modal_running = True

    def init_widget_values(self):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            mod_bevel = active_obj.modifiers.get("Bevel")
            if mod_bevel is not None:
                self.sl_width.set_value(mod_bevel.width)
                self.ud_segm_count.set_value(mod_bevel.segments)

    def on_bevel_width_value_change(self, slider, value):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            mod_bevel = active_obj.modifiers.get("Bevel")
            mod_bevel.width = value

    def on_bevel_segm_count_change(self, up_down, value):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            mod_bevel = active_obj.modifiers.get("Bevel")
            mod_bevel.segments = value

    def add_bevel(self, context):
        
        active_object = bpy.context.view_layer.objects.active
        
        mode = active_object.mode
        
        # Sharpen and bevel in object mode
        if(mode == "OBJECT"):

            execute_bevel(context.selected_objects)
        
        # Sharpen edges in edit mode
        else:
            
            # Mark selected edges as sharp
            bpy.ops.mesh.mark_sharp()
            bpy.ops.transform.edge_bevelweight(value=1)
        
        bpy.context.view_layer.objects.active = active_object