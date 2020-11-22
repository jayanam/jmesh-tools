from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
from .widgets . bl_ui_button import *
from .widgets . bl_ui_up_down import *
from .widgets . bl_ui_drag_panel import *
from .widgets . bl_ui_draw_op import *

from math import radians

from .utils.fc_bool_util import select_active

# Array mode operator
class FC_Circle_Array_Mode_Operator(BL_UI_OT_draw_operator):
    bl_idname = "object.fc_circle_array_mode_op"
    bl_label = "Circular Array Mode Operator"
    bl_description = "Create circular arrays"
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self):
        
        super().__init__()

        self.panel = BL_UI_Drag_Panel(0, 0, 270, 100)
        self.panel.bg_color = (0.1, 0.1, 0.1, 0.9)

        self.lbl_item_count = BL_UI_Label(20, 13, 40, 15)
        self.lbl_item_count.text = "Item count:"
        self.lbl_item_count.text_size = 14
        self.lbl_item_count.text_color = (0.9, 0.9, 0.9, 1.0)

        self.ud_item_count = BL_UI_Up_Down(110, 15)
        self.ud_item_count.color = (0.3, 0.56, 0.94, 1.0)
        self.ud_item_count.hover_color = (0.3, 0.56, 0.94, 0.8)
        self.ud_item_count.min = 1.0
        self.ud_item_count.max = 50.0
        self.ud_item_count.decimals = 0
        self.ud_item_count.set_value(1.0)
        self.ud_item_count.set_value_change(self.on_item_count_value_change)

        self.lbl_close = BL_UI_Label(185, 0, 50, 15)
        self.lbl_close.text = "Escape to Close"
        self.lbl_close.text_size = 10
        self.lbl_close.text_color = (0.9, 0.9, 0.9, 1.0)

        y_top = 60

        self.btn_apply = BL_UI_Button(20, y_top, 110, 25)
        self.btn_apply.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_apply.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_apply.text_size = 14
        self.btn_apply.text = "Apply modifier"
        self.btn_apply.set_mouse_down(self.on_btn_apply_down)

        self.btn_close = BL_UI_Button(140, y_top, 110, 25)
        self.btn_close.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_close.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_close.text_size = 14
        self.btn_close.text = "Close"
        self.btn_close.set_mouse_down(self.on_btn_close_down)

    @classmethod
    def poll(cls, context):        
        return len(context.selected_objects) > 0

    def get_array_modifier(self):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            return active_obj.modifiers.get("FC_Circle_Array")
        return None

    def on_btn_close_down(self, widget):
        self.finish()

    def on_btn_apply_down(self, widget):
        mod_array = self.get_array_modifier()
        if(mod_array):
            offset_obj = mod_array.offset_object
            if offset_obj:	
                bpy.data.objects.remove(offset_obj, do_unlink=True)

            bpy.ops.object.modifier_apply(modifier=mod_array.name)
            
        self.finish()

    def on_invoke(self, context, event):

        # Add new widgets here
        widgets_panel = [self.lbl_item_count, self.ud_item_count]

        widgets_panel.append(self.lbl_close)
        widgets_panel.append(self.btn_close)
        widgets_panel.append(self.btn_apply)

        widgets = [self.panel]

        widgets += widgets_panel

        self.init_widgets(context, widgets)

        self.panel.add_widgets(widgets_panel)

        # Open the panel at the mouse location
        self.panel.set_location(context.area.height / 2.0, 
                                context.area.height / 2.0)

        self.active_obj = bpy.context.view_layer.objects.active

        self.init_widget_values()

    def init_widget_values(self):

        # Create empty and array modifier if it not exists
        if self.active_obj is not None:
            mod_array = self.active_obj.modifiers.get("FC_Circle_Array")
            if mod_array is None:

                # Set the origin to the 3d cursor
                new_origin = bpy.context.scene.cursor.location

                select_active(self.active_obj)
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
                
                mod_array = self.active_obj.modifiers.new(type="ARRAY", name="FC_Circle_Array")
                mod_array.use_relative_offset = False
                mod_array.use_object_offset = True

                circle_empty = bpy.data.objects.new( "circle_empty", None )
                bpy.context.scene.collection.objects.link( circle_empty )
                circle_empty.location = new_origin

                circle_empty.empty_display_size = 1
                circle_empty.empty_display_type = 'ARROWS'
                mod_array.offset_object = circle_empty

                self.active_obj["circle_empty"] = circle_empty

            self.ud_item_count.set_value(mod_array.count)
            
    def on_item_count_value_change(self, up_down, value):
        
        # Get the circle array modifier
        mod_array = self.active_obj.modifiers.get("FC_Circle_Array")
        mod_array.count = value

        # Set the Z-Rotation for the empty to 360 / value
        angle = 360 / value

        circle_empty = self.active_obj["circle_empty"]
        circle_empty.rotation_euler = self.active_obj.rotation_euler

        circle_empty.rotation_euler.rotate_axis("Z", radians(angle))
