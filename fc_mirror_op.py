import bpy
from bpy.types import Operator

from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
from .widgets . bl_ui_drag_panel import *
from .widgets . bl_ui_button import *
from .widgets . bl_ui_checkbox import *

# Set the pivot point of the active object
# to the center and add a mirror modifier
class FC_MirrorOperator(BL_UI_OT_draw_operator):
    bl_idname = "object.mirror"
    bl_label = "Center Origin & Mirror"
    bl_description = "Mirror selected object" 
    bl_options = {'REGISTER', 'UNDO'} 

    def __init__(self):
        
      super().__init__()

      self.panel = BL_UI_Drag_Panel(0, 0, 280, 100)
      self.panel.bg_color = (0.1, 0.1, 0.1, 0.9)   

      self.cb_x = BL_UI_Checkbox(20, 20, 120, 16)
      self.cb_x.cross_color = (0.3, 0.56, 0.94, 1.0)
      self.cb_x.text = "X"
      self.cb_x.text_size = 14

      self.cb_y = BL_UI_Checkbox(90, 20, 120, 16)
      self.cb_y.cross_color = (0.3, 0.56, 0.94, 1.0)
      self.cb_y.text = "Y"
      self.cb_y.text_size = 14

      self.cb_z = BL_UI_Checkbox(160, 20, 120, 16)
      self.cb_z.cross_color = (0.3, 0.56, 0.94, 1.0)
      self.cb_z.text = "Z"
      self.cb_z.text_size = 14

      self.btn_apply = BL_UI_Button(20, 60, 110, 25)
      self.btn_apply.bg_color = (0.3, 0.56, 0.94, 1.0)
      self.btn_apply.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
      self.btn_apply.text_size = 14
      self.btn_apply.text = "Apply modifier"
      self.btn_apply.set_mouse_down(self.on_btn_apply_down)

      self.btn_close = BL_UI_Button(140, 60, 120, 25)
      self.btn_close.bg_color = (0.3, 0.56, 0.94, 1.0)
      self.btn_close.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
      self.btn_close.text_size = 14
      self.btn_close.text = "Close"
      self.btn_close.set_mouse_down(self.on_btn_close_down)

    def on_invoke(self, context, event):

      # Add new widgets here
      widgets_panel = [self.cb_x, self.cb_y, self.cb_z, self.btn_apply, self.btn_close]

      widgets = [self.panel]

      widgets += widgets_panel

      self.init_widgets(context, widgets)

      self.panel.add_widgets(widgets_panel)

      # Open the panel at the mouse location
      self.panel.set_location(context.area.height / 2.0, 
                              context.area.height / 2.0)

      self.init_widget_values(context)

      self.cb_x.set_state_changed(self.on_axis_change)
      self.cb_y.set_state_changed(self.on_axis_change)
      self.cb_z.set_state_changed(self.on_axis_change)


    def get_or_create_mirror_mod(self, context):
      result = None
      active_obj = context.view_layer.objects.active
      if active_obj is not None:
        result = active_obj.modifiers.get("FC_Mirror")
        if not result:

          # Create new mirror modifier
          bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
          cursor_location = context.scene.cursor.location.copy()      
          context.scene.cursor.location = (0.0, 0.0, 0.0)
          bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
          result = context.object.modifiers.new(type="MIRROR", name="FC_Mirror")
          result.use_axis[0] = True
          result.use_clip = True
          context.scene.cursor.location = cursor_location

      return result

    def init_widget_values(self, context):
        mirror_mod = self.get_or_create_mirror_mod(context)
        self.cb_x.is_checked = mirror_mod.use_axis[0]
        self.cb_y.is_checked = mirror_mod.use_axis[1]
        self.cb_z.is_checked = mirror_mod.use_axis[2]

    def on_btn_apply_down(self, widget):
        mirror_mod = self.get_or_create_mirror_mod(bpy.context)
        if mirror_mod:
          bpy.ops.object.modifier_apply(modifier="FC_Mirror")

        self.finish()

    def on_btn_close_down(self, widget):
        self.finish()

    def on_axis_change(self, checkbox, value):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
          mirror_mod = self.get_or_create_mirror_mod(bpy.context)
          if mirror_mod:
            mirror_mod.use_axis[0] = self.cb_x.is_checked
            mirror_mod.use_axis[1] = self.cb_y.is_checked
            mirror_mod.use_axis[2] = self.cb_z.is_checked

    @classmethod
    def poll(cls, context):

        if context.active_object == None:
            return False
        
        mode = context.active_object.mode       
        return len(context.selected_objects) == 1 and (mode == "OBJECT" or mode == "SCULPT")