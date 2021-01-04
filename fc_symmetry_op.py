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

        red   = (1.00, 0.21, 0.33, 1.0)
        green = (0.54, 0.86, 0,    1.0)
        blue  = (0.17, 0.55, 0.99, 1.0)

        d = 1.5

        self.add_action(red, "-X", Vector((-d,0,0)))
        self.add_action(red, "X", Vector((d,0,0)))

        self.add_action(green, "-Y", Vector((0,-d,0)))
        self.add_action(green, "Y", Vector((0,d,0)))

        self.add_action(blue, "-Z", Vector((0,0,-d)))
        self.add_action(blue, "Z", Vector((0,0,d)))

        return {"RUNNING_MODAL"}

    def add_action(self, color, axis, offset: Vector):
      action = Shape_Action_Symmetry(offset, axis, color)
      self._actions.append(action)

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        result = "PASS_THROUGH"

        if event.value == "PRESS" and event.type == "LEFTMOUSE":
          mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)

          for action in self._actions:
            if action.mouse_down(context, event, mouse_pos_2d, None):

              if context.mode == "OBJECT":
                bpy.ops.object.mode_set(mode="EDIT")
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.symmetrize(direction=action.get_symmetry_command())
                bpy.ops.object.mode_set(mode="OBJECT")
              elif context.mode == "SCULPT":
                  bpy.context.scene.tool_settings.sculpt.symmetrize_direction = action.get_symmetry_command()
                  bpy.ops.sculpt.symmetrize()
              return { "RUNNING_MODAL" }
                     
        if event.type == "ESC" and event.value == "PRESS":

          self.unregister_handlers(context)
          result = "FINISHED"

        return { result }
    
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