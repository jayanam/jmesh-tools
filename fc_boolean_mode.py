import bpy

from bpy.props import *

import blf
from . utils.fc_select_util import check_cutter_selected

from . utils.fc_view_3d_utils import get_hit_object
from . types.enums import next_enum
from . fc_preferences import get_preferences

from . types.action import Action

from . utils.fc_bool_util import execute_slice_op, is_delete_after_apply, select_active, execute_boolean_op, get_bool_mode_id
from . utils.fc_bevel_util import *

# Boolean mode operator
class FC_Boolean_Mode_Operator(bpy.types.Operator):
    bl_idname = "object.fc_boolean_mode_op"
    bl_label = "Boolean Mode Operator"
    bl_description = "Boolean Mode Operator"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context): 

        if context.window_manager.in_primitive_mode:
            return False

        return check_cutter_selected(context)

    def build_actions(self):
        self._actions = []
        bool_mode = bpy.context.scene.bool_mode
        self._actions.append(Action("O",                  "Operation",          bool_mode))
        self._actions.append(Action("Ctrl + Left Click",  "Execute Bool",       ""))

    def finish(self):
        self.unregister_handlers(bpy.context)
        return {"FINISHED"}

    def invoke(self, context, event):
        args = (self, context)  

        context.window_manager.in_primitive_mode = True    

        self.init_bool_mode(context)
        self.build_actions()

        self.register_handlers(args, context)
                   
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def register_handlers(self, args, context):

        self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_2d, args, "WINDOW", "POST_PIXEL")

        self.draw_event = context.window_manager.event_timer_add(0.1, window=context.window)
        
    def unregister_handlers(self, context):

        context.window_manager.in_primitive_mode = False

        context.window_manager.event_timer_remove(self.draw_event)
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2d, "WINDOW")
        
        self.draw_handle_2d = None
        self.draw_event  = None 

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        result = "PASS_THROUGH"

        mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)

        RM = "RUNNING_MODAL"

        if event.type == "ESC" and event.value == "PRESS":

          return self.finish()

        if event.value == "PRESS":
          if event.type == "ESC":
            return self.finish()

          if event.type == "O":
            context.scene.bool_mode = next_enum(context.scene.bool_mode, context.scene, "bool_mode")
            self.init_bool_mode(context)

            self.build_actions()
            result = RM


        if event.value == "PRESS" and event.type == "LEFTMOUSE":
          if event.ctrl:
            self.execute_boolean(mouse_pos_2d, context)
            result = RM

        return { result }

    def draw_action_line(self, action, pos_y, pos_x):

        prefs = get_preferences()
        lc = prefs.osd_label_color
        off_x = prefs.osd_offset_x

        blf.color(1, lc[0], lc[1], lc[2], lc[3])
        blf.position(1, off_x, pos_y , 1)

        title = action.title
        if action.content != "":
            title += ":"

        blf.draw(1, title) 
     
        if(action.content != ""):
            blf.position(1, pos_x[0], pos_y , 1)
            blf.draw(1, action.content) 

        tc = prefs.osd_text_color
        blf.color(1, tc[0], tc[1], tc[2], tc[3])
        blf.position(1, pos_x[1], pos_y, 1)
        blf.draw(1, action.id)
        
	  # Draw handler to paint in pixels
    def draw_callback_2d(self, op, context):
        self.draw_actions()

    def draw_actions(self):
        fsize = get_preferences().osd_font_size
        off_x = get_preferences().osd_offset_x
        blf.size(1, fsize, 72)

        line_height = 18
        pos_x = [115, 200]

        if fsize >= 20:
          line_height = 23
          pos_x = [200, 380]
          pos_y = 110
        elif fsize >= 17:
          line_height = 22
          pos_x = [160, 285]
          pos_y = 100
        elif fsize >= 14:
          pos_x = [155, 270]
          pos_y = 70

        pos_x[0] += off_x
        pos_x[1] += off_x

        for index, action in enumerate(self._actions):
          self.draw_action_line(action, (pos_y) - (index) * line_height, pos_x)

    def init_bool_mode(self, context):
      if context.scene.bool_mode == "Create":
        context.scene.bool_mode = next_enum(context.scene.bool_mode, context.scene, "bool_mode")  

    def execute_boolean(self, pos_2d, context):
      try:

          bool_mode = context.scene.bool_mode
          current_mode = context.object.mode 
          cutter = context.view_layer.objects.active

          bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

          new_target = get_hit_object(pos_2d, context)
          if new_target:
            bpy.context.scene.carver_target = new_target  

          target = bpy.context.scene.carver_target

          bool_id = get_bool_mode_id(bool_mode)

          if bool_id == 3:
            execute_slice_op(context, target)
          else:
            execute_boolean_op(context, target, get_bool_mode_id(bool_mode))

          if is_delete_after_apply():
            bpy.ops.object.delete()
            select_active(target)
          else:
            select_active(cutter)

          bpy.ops.object.mode_set(mode=current_mode, toggle=False)

      except RuntimeError:
          pass