from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
from .widgets . bl_ui_button import *
from .widgets . bl_ui_slider import *
from .widgets . bl_ui_up_down import *
from .widgets . bl_ui_drag_panel import *
from .widgets . bl_ui_draw_op import *

# Array mode operator
class FC_Array_Mode_Operator(BL_UI_OT_draw_operator):
    bl_idname = "object.fc_array_mode_op"
    bl_label = "Array Mode Operator"
    bl_description = "Array modifier utility"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):        
        return len(context.selected_objects) > 0

    def __init__(self):
        
        super().__init__()
            
        self.panel = BL_UI_Drag_Panel(0, 0, 300, 180)
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

        self.lbl_item_off_x = BL_UI_Label(20, 62, 50, 15)
        self.lbl_item_off_x.text = "Offset X:"
        self.lbl_item_off_x.text_size = 14
        self.lbl_item_off_x.text_color = (0.9, 0.9, 0.9, 1.0)

        self.lbl_item_off_y = BL_UI_Label(20, 100, 50, 15)
        self.lbl_item_off_y.text = "Offset Y:"
        self.lbl_item_off_y.text_size = 14
        self.lbl_item_off_y.text_color = (0.9, 0.9, 0.9, 1.0)

        self.lbl_item_off_z = BL_UI_Label(20, 140, 50, 15)
        self.lbl_item_off_z.text = "Offset Z:"
        self.lbl_item_off_z.text_size = 14
        self.lbl_item_off_z.text_color = (0.9, 0.9, 0.9, 1.0)

        self.sl_item_distance_x = BL_UI_Slider(110, 60, 150, 30)
        self.sl_item_distance_x.color = (0.2, 0.8, 0.8, 0.8)
        self.sl_item_distance_x.hover_color = (0.2, 0.9, 0.9, 1.0)
        self.sl_item_distance_x.min = 0.0
        self.sl_item_distance_x.max = 10.0
        self.sl_item_distance_x.decimals = 1
        self.sl_item_distance_x.show_min_max = False
        self.sl_item_distance_x.tag = 0
        self.sl_item_distance_x.set_value_change(self.on_item_distance_change)

        self.sl_item_distance_y = BL_UI_Slider(110, 100, 150, 30)
        self.sl_item_distance_y.color = (0.2, 0.8, 0.8, 0.8)
        self.sl_item_distance_y.hover_color = (0.2, 0.9, 0.9, 1.0)
        self.sl_item_distance_y.min = 0.0
        self.sl_item_distance_y.max = 10.0
        self.sl_item_distance_y.decimals = 1
        self.sl_item_distance_y.show_min_max = False
        self.sl_item_distance_y.tag = 1
        self.sl_item_distance_y.set_value_change(self.on_item_distance_change)

        self.sl_item_distance_z = BL_UI_Slider(110, 140, 150, 30)
        self.sl_item_distance_z.color = (0.2, 0.8, 0.8, 0.8)
        self.sl_item_distance_z.hover_color = (0.2, 0.9, 0.9, 1.0)
        self.sl_item_distance_z.min = 0.0
        self.sl_item_distance_z.max = 10.0
        self.sl_item_distance_z.decimals = 1
        self.sl_item_distance_z.show_min_max = False
        self.sl_item_distance_z.tag = 2
        self.sl_item_distance_z.set_value_change(self.on_item_distance_change)

    def on_invoke(self, context, event):

        # Add new widgets here
        widgets_panel = [self.lbl_item_count, self.ud_item_count, self.lbl_item_off_x, 
        self.lbl_item_off_y, self.lbl_item_off_z, self.sl_item_distance_x, 
        self.sl_item_distance_y, self.sl_item_distance_z]

        widgets =       [self.panel]

        widgets += widgets_panel

        self.init_widgets(context, widgets)

        self.panel.add_widgets(widgets_panel)

        # Open the panel at the mouse location
        self.panel.set_location(context.area.height / 2.0, 
                                context.area.height / 2.0)

        self.init_widget_values()

    def init_widget_values(self):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            mod_array = active_obj.modifiers.get("Array")
            if mod_array is None:
                bpy.ops.object.modifier_add(type = 'ARRAY')
                mod_array = active_obj.modifiers.get("Array")

            self.ud_item_count.set_value(mod_array.count)
            self.sl_item_distance_x.set_value(mod_array.relative_offset_displace[0])
            self.sl_item_distance_y.set_value(mod_array.relative_offset_displace[1])
            self.sl_item_distance_z.set_value(mod_array.relative_offset_displace[2])
            
    def on_item_count_value_change(self, up_down, value):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            mod_array = active_obj.modifiers.get("Array")

            mod_array.count = value

    def on_item_distance_change(self, slider, value):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
            mod_array = active_obj.modifiers.get("Array")
            mod_array.relative_offset_displace[slider.tag] = value