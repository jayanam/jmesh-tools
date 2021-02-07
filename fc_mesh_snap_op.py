import bpy
from bpy.types import Operator

from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
from .widgets . bl_ui_drag_panel import *
from .widgets . bl_ui_button import *
from .widgets . bl_ui_checkbox import *
from .widgets . bl_ui_slider import *
from .widgets . bl_ui_up_down import *

# Symmetry operator
class FC_Mesh_Snap_Operator(BL_UI_OT_draw_operator):
    bl_idname = "object.fc_mesh_snap_op"
    bl_label = "Mesh snap operator"
    bl_description = "Configure a mesh to snap to the target"
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self):      
      super().__init__()

      self.panel = BL_UI_Drag_Panel(0, 0, 280, 210)
      self.panel.bg_color = (0.1, 0.1, 0.1, 0.9)  

      y_pos = 20

      # Checkboxes
      self.cb_snap_face = BL_UI_Checkbox(20, y_pos, 120, 16)
      self.cb_snap_face.cross_color = (0.3, 0.56, 0.94, 1.0)
      self.cb_snap_face.text = "Snap to faces"
      self.cb_snap_face.text_size = 14

      y_pos += 30
      self.cb_smooth_shading = BL_UI_Checkbox(20, y_pos, 120, 16)
      self.cb_smooth_shading.cross_color = (0.3, 0.56, 0.94, 1.0)
      self.cb_smooth_shading.text = "Smooth shading"
      self.cb_smooth_shading.text_size = 14

      y_pos += 40
      self.lbl_bvl_width = BL_UI_Label(20, y_pos, 50, 15)
      self.lbl_bvl_width.text = "Width:"
      self.lbl_bvl_width.text_size = 14
      self.lbl_bvl_width.text_color = (0.9, 0.9, 0.9, 1.0)

      self.sl_width = BL_UI_Slider(80, y_pos, 160, 30)
      self.sl_width.color = (0.3, 0.56, 0.94, 1.0)
      self.sl_width.hover_color = (0.3, 0.56, 0.94, 0.8)
      self.sl_width.min = -0.1
      self.sl_width.max = 0.1
      self.sl_width.decimals = 3
      self.sl_width.show_min_max = False
      self.sl_width.tag = 0
      self.sl_width.set_value_change(self.on_width_value_change)

      y_pos += 40
      self.lbl_ss_levels = BL_UI_Label(20, y_pos, 50, 15)
      self.lbl_ss_levels.text = "Subsurface levels:"
      self.lbl_ss_levels.text_size = 14
      self.lbl_ss_levels.text_color = (0.9, 0.9, 0.9, 1.0)

      self.ud_ss_levels = BL_UI_Up_Down(150, y_pos)
      self.ud_ss_levels.color = (0.3, 0.56, 0.94, 1.0)
      self.ud_ss_levels.hover_color = (0.3, 0.56, 0.94, 0.8)
      self.ud_ss_levels.min = 0
      self.ud_ss_levels.max = 10
      self.ud_ss_levels.decimals = 0
      self.ud_ss_levels.set_value(1)
      self.ud_ss_levels.set_value_change(self.on_ss_levels_value_change)

      y_pos += 40
      self.btn_apply = BL_UI_Button(20, y_pos, 110, 25)
      self.btn_apply.bg_color = (0.3, 0.56, 0.94, 1.0)
      self.btn_apply.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
      self.btn_apply.text_size = 14
      self.btn_apply.text = "Apply modifiers"
      self.btn_apply.set_mouse_down(self.on_btn_apply_down)

      self.btn_close = BL_UI_Button(140, y_pos, 120, 25)
      self.btn_close.bg_color = (0.3, 0.56, 0.94, 1.0)
      self.btn_close.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
      self.btn_close.text_size = 14
      self.btn_close.text = "Close"
      self.btn_close.set_mouse_down(self.on_btn_close_down)

    @classmethod
    def poll(cls, context):

      if context.active_object == None:
        return False
        
      mode = context.active_object.mode       
      return len(context.selected_objects) == 1 and (mode == "EDIT" or mode == "OBJECT")

    def on_ss_levels_value_change(self, up_down, value):
      active_obj = bpy.context.view_layer.objects.active
      if active_obj is not None:
        mod_sol = active_obj.modifiers.get("FC_Subsurf")
        mod_sol.levels = value

    def on_width_value_change(self, slider, value):
      active_obj = bpy.context.view_layer.objects.active
      if active_obj is not None:
        mod_sol = active_obj.modifiers.get("FC_Solidify")
        mod_sol.thickness = value

    def on_invoke(self, context, event):

      # Add new widgets here
      widgets_panel = [self.cb_snap_face, self.cb_smooth_shading, self.sl_width, self.lbl_bvl_width, self.lbl_ss_levels, self.ud_ss_levels, self.btn_apply, self.btn_close]

      widgets = [self.panel]

      widgets += widgets_panel
      
      self.init_widgets(context, widgets)
      self.panel.add_widgets(widgets_panel)

      # Open the panel at the mouse location
      self.panel.set_location(context.area.height / 2.0, 
                              context.area.height / 2.0)

      self.init_widget_values(context)

      self.cb_snap_face.set_state_changed(self.on_snap_face_change)
      self.cb_smooth_shading.set_state_changed(self.on_smooth_shading_change)

    def get_or_create_subsurf_mod(self, context):
      result = None
      active_obj = context.view_layer.objects.active
      if active_obj is not None:
        result = active_obj.modifiers.get("FC_Subsurf")
        if not result:

          # Create new subsurface modifier
          result = context.object.modifiers.new(type="SUBSURF", name="FC_Subsurf")
          result.levels = 2

      return result

    def get_or_create_solidify_mod(self, context):
      result = None
      active_obj = context.view_layer.objects.active
      if active_obj is not None:
        result = active_obj.modifiers.get("FC_Solidify")
        if not result:

          # Create new subsurface modifier
          result = context.object.modifiers.new(type="SOLIDIFY", name="FC_Solidify")
          result.thickness = 0.02
          result.use_even_offset = True
          result.show_on_cage = True

      return result

    def get_or_create_shrinkwrap_mod(self, context):
      result = None
      active_obj = context.view_layer.objects.active
      if active_obj is not None:
        result = active_obj.modifiers.get("FC_Shrinkwrap")
        if not result:

          # Create new subsurface modifier
          result = context.object.modifiers.new(type="SHRINKWRAP", name="FC_Shrinkwrap")
          result.wrap_mode = "ABOVE_SURFACE"
          result.offset = 0.001
          result.target = context.scene.carver_target

      return result

    def init_widget_values(self, context):
      self.cb_snap_face.is_checked = bpy.context.scene.tool_settings.use_snap
      self.cb_smooth_shading.is_checked = bpy.context.active_object.data.polygons[0].use_smooth
      
      subsurf_mod = self.get_or_create_subsurf_mod(context)
      shrinkwrap_mod = self.get_or_create_shrinkwrap_mod(context)
      solidify_mod = self.get_or_create_solidify_mod(context)

      self.sl_width.set_value(solidify_mod.thickness)
      self.ud_ss_levels.set_value(subsurf_mod.levels)
      

    def on_btn_apply_down(self, widget):
      active_obj = bpy.context.view_layer.objects.active
      if active_obj:
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        for mod in active_obj.modifiers:
          bpy.ops.object.modifier_apply(modifier=mod.name)
      self.finish()

    def on_btn_close_down(self, widget):
      self.finish()

    def on_smooth_shading_change(self, checkbox, value):
      current_mode = bpy.context.active_object.mode
      bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
      if value:
        bpy.ops.object.shade_smooth()
      else:
        bpy.ops.object.shade_flat()
      bpy.ops.object.mode_set(mode=current_mode, toggle=False)


    def on_snap_face_change(self, checkbox, value):
      bpy.context.scene.tool_settings.snap_elements = {'FACE'}
      bpy.context.scene.tool_settings.use_snap_project = value
      bpy.context.scene.tool_settings.use_snap = value