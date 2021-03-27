import bpy
from bpy.types import Operator

from bpy.props import *

import bgl
import blf

from gpu_extras.batch import batch_for_shader

from bpy_extras import view3d_utils

from . types.shape_action import Shape_Action_Symmetry

from bpy_extras.view3d_utils import location_3d_to_region_2d
from mathutils import Vector

from . fc_preferences import get_preferences

# Symmetry operator
class FC_Symmetry_Operator(bpy.types.Operator):
    bl_idname = "object.fc_symmetry_op"
    bl_label = "Symmetry operator"
    bl_description = "Symmetrize object in 3D View"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context): 

        if context.window_manager.in_symmetry_mode:
            return False

        if context.object == None:
            return False

        return True
		
    def __init__(self):
        self.draw_handle_2d = None
        self.draw_event  = None
        self._actions = []
                
    def invoke(self, context, event):
        args = (self, context)  

        context.window_manager.in_symmetry_mode = True
    
        self.register_handlers(args, context)
                   
        context.window_manager.modal_handler_add(self)

        red   = [1.00, 0.21, 0.33, 1.0]
        green = [0.54, 0.86, 0,    1.0]
        blue  = [0.17, 0.55, 0.99, 1.0]

        d = 1.5

        self.add_action(red, "-X", Vector((-d,0,0)))
        self.add_action(red.copy(), "X", Vector((d,0,0)))

        self.add_action(green, "-Y", Vector((0,-d,0)))
        self.add_action(green.copy(), "Y", Vector((0,d,0)))

        self.add_action(blue, "-Z", Vector((0,0,-d)))
        self.add_action(blue.copy(), "Z", Vector((0,0,d)))

        return {"RUNNING_MODAL"}

    def add_action(self, color, axis, offset: Vector):
      action = Shape_Action_Symmetry(offset, axis, color)
      self._actions.append(action)

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        result = "PASS_THROUGH"
        mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)

        if event.type == "MOUSEMOVE":
          for action in self._actions:
            is_inside = action.mouse_inside(context, event, mouse_pos_2d, None)
            action.set_hover(is_inside)

        elif event.value == "PRESS" and event.type == "LEFTMOUSE":
          
          for action in self._actions:
            if action.mouse_inside(context, event, mouse_pos_2d, None):
              action.set_hover(False)
              
              if context.mode == "EDIT_MESH":

                # Symmetrize the active object in edit mode
                bpy.ops.mesh.symmetrize(direction=action.get_symmetry_command())
              elif context.mode == "OBJECT":

                # Symmetrize all selected objects
                sel_objs = bpy.context.selected_objects
                act_obj = bpy.context.active_object   
                for sel_obj in sel_objs:
                  bpy.context.view_layer.objects.active = sel_obj
                  bpy.ops.object.mode_set(mode="EDIT")
                  self.symmetrize_edit_mode(action)
                  bpy.ops.object.mode_set(mode="OBJECT")

                bpy.context.view_layer.objects.active = act_obj

              elif context.mode == "SCULPT":

                  # Symmetrize the active object in sculpt mode
                  bpy.context.scene.tool_settings.sculpt.symmetrize_direction = action.get_symmetry_command()
                  bpy.ops.sculpt.symmetrize()
                  
              return { "RUNNING_MODAL" }
                     
        if event.type == "ESC" and event.value == "PRESS":

          self.unregister_handlers(context)
          result = "FINISHED"

        return { result }
    
    def symmetrize_edit_mode(self, action):
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.symmetrize(direction=action.get_symmetry_command())
      bpy.ops.mesh.select_all(action='DESELECT')

    def register_handlers(self, args, context):

        self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_2d, args, "WINDOW", "POST_PIXEL")

        self.draw_event = context.window_manager.event_timer_add(0.1, window=context.window)
        
    def unregister_handlers(self, context):

        context.window_manager.event_timer_remove(self.draw_event)
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2d, "WINDOW")
        
        self.draw_handle_2d = None
        self.draw_event  = None

        context.window_manager.in_symmetry_mode = False

	  # Draw handler to paint in pixels
    def draw_callback_2d(self, op, context):

      rv3d = context.space_data.region_3d
      region = context.region

      for action in self._actions:
        pos_2d = location_3d_to_region_2d(region, rv3d, action.get_offset())
        action.set_position(pos_2d[0], pos_2d[1])
        action.draw()

      prefs = get_preferences()
      sd = prefs.symmetrize_direction

      header = "- Symmetrize (Mode: " + sd + ") -"

      blf.color(1, 1, 1, 1, 1)
      blf.size(1, 16, 72)

      region = context.region
      xt = int(region.width / 2.0)

      blf.position(1, xt - blf.dimensions(0, header)[0] / 2, 30 , 0)
      blf.draw(1, header)