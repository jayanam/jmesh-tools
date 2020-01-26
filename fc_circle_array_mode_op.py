from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
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

        self.panel = BL_UI_Drag_Panel(0, 0, 200, 50)
        self.panel.bg_color = (0.1, 0.1, 0.1, 0.9)

        self.lbl_item_count = BL_UI_Label(20, 13, 40, 15)
        self.lbl_item_count.text = "Item count:"
        self.lbl_item_count.text_size = 14
        self.lbl_item_count.text_color = (0.9, 0.9, 0.9, 1.0)

        self.ud_item_count = BL_UI_Up_Down(110, 15)
        self.ud_item_count.color = (0.2, 0.8, 0.8, 0.8)
        self.ud_item_count.hover_color = (0.2, 0.9, 0.9, 1.0)
        self.ud_item_count.min = 1.0
        self.ud_item_count.max = 50.0
        self.ud_item_count.decimals = 0
        self.ud_item_count.set_value(1.0)
        self.ud_item_count.set_value_change(self.on_item_count_value_change)

    @classmethod
    def poll(cls, context):        
        return len(context.selected_objects) > 0
        
    def on_invoke(self, context, event):

        # Add new widgets here
        widgets_panel = [self.lbl_item_count, self.ud_item_count]

        widgets =       [self.panel]

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
