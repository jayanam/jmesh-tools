import bpy
from bpy.types import Operator
import bmesh

from .widgets . bl_ui_draw_op import *
from .widgets . bl_ui_label import * 
from .widgets . bl_ui_slider import *
from .widgets . bl_ui_drag_panel import *
from .widgets . bl_ui_button import *
from .widgets . bl_ui_checkbox import *

from .utils.fc_bool_util import union_selected

class FC_JoinAndRemesh(Operator):
    bl_idname = "view3d.join_and_remesh"
    bl_label = "Join and remesh"
    bl_description = "Joins and object with the target and does a voxel remesh" 
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context): 

        if len(context.selected_objects) < 1:
            return False

        return True

    def execute(self, context):
      try:
        bpy.ops.view3d.curve_convert()
      except RuntimeError:
        pass

      bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
      target = bpy.context.scene.carver_target
      if target:
        target.select_set(state=True)
        context.view_layer.objects.active = target
      
      bpy.ops.object.join()

      bpy.ops.object.mode_set(mode='SCULPT', toggle=False)
      bpy.ops.object.voxel_remesh()

      return {'FINISHED'}

    

class FC_MeshToCurveOperator(Operator):
    bl_idname = "view3d.mesh_to_curve"
    bl_label = "Mesh to Curve"
    bl_description = "Convert mesh to curve" 
    bl_options = {'REGISTER', 'UNDO'}   

    @classmethod
    def poll(cls, context): 

        if len(context.selected_objects) < 1:
            return False

        obj = context.view_layer.objects.active
        if obj.type != "MESH":
          return False
   
        return True

    def execute(self, context): 

        # Convert selected objects to curves
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)
        bpy.ops.mesh.delete(type='ONLY_FACE')

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.convert(target='CURVE')

        # Set curve properties
        for obj in context.selected_objects:
            obj.data.bevel_depth = 0.05
            obj.data.bevel_resolution = 10
  
        bpy.ops.object.shade_smooth()

        return {'FINISHED'}

class FC_CurveAdjustOperator(BL_UI_OT_draw_operator):
    bl_idname = "view3d.curve_adjust"
    bl_label = "Adjust curve"
    bl_description = "Adjust the active curve" 
    bl_options = {'REGISTER', 'UNDO'}  

    @classmethod
    def poll(cls, context): 
        if len(context.selected_objects) < 1:
          return False

        obj = context.view_layer.objects.active
        if obj.type != "CURVE":
          return False
   
        return True

    def __init__(self):
        
        super().__init__()
            
        self.panel = BL_UI_Drag_Panel(0, 0, 300, 160)
        self.panel.bg_color = (0.1, 0.1, 0.1, 0.9)

        self.lbl_depth = BL_UI_Label(20, 32, 40, 15)
        self.lbl_depth.text = "Depth:"
        self.lbl_depth.text_size = 14
        self.lbl_depth.text_color = (0.9, 0.9, 0.9, 1.0)

        self.sl_depth = BL_UI_Slider(110, 30, 150, 30)
        self.sl_depth.color = (0.3, 0.56, 0.94, 1.0)
        self.sl_depth.hover_color = (0.3, 0.56, 0.94, 0.8)
        self.sl_depth.min = 0.01
        self.sl_depth.max = 0.5
        self.sl_depth.decimals = 2
        self.sl_depth.show_min_max = False
        self.sl_depth.tag = 0
        self.sl_depth.set_value_change(self.on_depth_change)

        self.cb_fillcaps = BL_UI_Checkbox(20, 80, 120, 16)
        self.cb_fillcaps.cross_color = (0.3, 0.56, 0.94, 1.0)
        self.cb_fillcaps.text = "Fillcaps"
        self.cb_fillcaps.text_size = 14
        self.cb_fillcaps.set_state_changed(self.on_fillcaps_change)

        self.cb_cyclic = BL_UI_Checkbox(115, 80, 120, 16)
        self.cb_cyclic.cross_color = (0.3, 0.56, 0.94, 1.0)
        self.cb_cyclic.text_size = 14
        self.cb_cyclic.text = "Cyclic"
        self.cb_cyclic.set_state_changed(self.on_cyclic_change)

        self.btn_to_mesh = BL_UI_Button(20, 120, 70, 25)
        self.btn_to_mesh.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_to_mesh.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_to_mesh.text_size = 14
        self.btn_to_mesh.text = "To Mesh"
        self.btn_to_mesh.set_mouse_down(self.on_btn_to_mesh_down)

        self.btn_join = BL_UI_Button(100, 120, 110, 25)
        self.btn_join.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_join.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_join.text_size = 14
        self.btn_join.text = "Join & Remesh"
        self.btn_join.set_text_offset(0, 2)
        self.btn_join.set_mouse_down(self.on_btn_join_down)

        self.btn_close = BL_UI_Button(220, 120, 60, 25)
        self.btn_close.bg_color = (0.3, 0.56, 0.94, 1.0)
        self.btn_close.hover_bg_color = (0.3, 0.56, 0.94, 0.8)
        self.btn_close.text_size = 14
        self.btn_close.text = "Close"
        self.btn_close.set_mouse_down(self.on_btn_close_down)

    def on_cyclic_change(self, checkbox, value):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
          active_obj.data.splines[0].use_cyclic_u = value

    def on_fillcaps_change(self, checkbox, value):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
          active_obj.data.use_fill_caps = value

    def on_depth_change(self, slider, value):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
          active_obj.data.bevel_depth = value

    def on_btn_join_down(self, widget):
      bpy.ops.view3d.join_and_remesh()
      self.finish()

    def on_btn_to_mesh_down(self, widget):
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        bpy.ops.object.convert(target='MESH')

        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        obj = bpy.context.view_layer.objects.active

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        self.finish()

    def on_btn_close_down(self, widget):
        self.finish()

    def on_invoke(self, context, event):

      # Add new widgets here
      widgets_panel = [self.lbl_depth, self.sl_depth, self.cb_fillcaps, self.cb_cyclic, self.btn_to_mesh, self.btn_join, self.btn_close]

      widgets = [self.panel]

      widgets += widgets_panel

      self.init_widgets(context, widgets)

      self.panel.add_widgets(widgets_panel)

      # Open the panel at the mouse location
      self.panel.set_location(context.area.height / 2.0, 
                              context.area.height / 2.0)

      self.init_widget_values(context)

    def init_widget_values(self, context):
        active_obj = bpy.context.view_layer.objects.active
        if active_obj is not None:
          self.sl_depth.set_value(active_obj.data.bevel_depth)
          self.cb_fillcaps.is_checked = active_obj.data.use_fill_caps 
          self.cb_cyclic.is_checked = active_obj.data.splines[0].use_cyclic_u
                  
        return {'FINISHED'}

class FC_CurveConvertOperator(Operator):
    bl_idname = "view3d.curve_convert"
    bl_label = "Curve to Mesh"
    bl_description = "Convert curves to meshes and fill holes" 
    bl_options = {'REGISTER', 'UNDO'}   

    @classmethod
    def poll(cls, context): 

      selected_curves = [c for c in context.selected_objects if c.type == "CURVE" and c.visible_get()]
      if len(selected_curves) == 0:
        return False

      if context.active_object.mode != "OBJECT" and context.active_object.mode != "EDIT":
          return False
  
      return True

    def execute(self, context): 

        # Get all selected curves
        selected_curves = [c for c in context.selected_objects if c.type == "CURVE" and c.visible_get()]

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

        for curve in selected_curves:
          curve.data.use_fill_caps = True

        bpy.ops.object.convert(target='MESH')

        return {'FINISHED'}
        