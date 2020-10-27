import bpy
from bpy.types import Operator

from bpy.props import *

import bgl
import blf

import bmesh

import gpu
from gpu_extras.batch import batch_for_shader

from bpy_extras import view3d_utils

import mathutils

from .utils.fc_bool_util import select_active, execute_boolean_op, execute_slice_op, is_apply_immediate
from .utils.fc_bevel_util import *
from .utils.fc_view_3d_utils import *

from .types.shape import *
from .types.rectangle_shape import *
from .types.polyline_shape import *
from .types.circle_shape import *
from .types.curve_shape import *

from .types.enums import *

from .types.shape_gizmo import *

from .widgets.bl_ui_textbox import *

# Primitive mode operator
class FC_Primitive_Mode_Operator(bpy.types.Operator):
    bl_idname = "object.fc_primitve_mode_op"
    bl_label = "Primitive Mode Operator"
    bl_description = "Primitive Mode Operator"
    bl_options = {"REGISTER", "UNDO", "BLOCKING"}

    @classmethod
    def poll(cls, context): 
        # if context.object is None:
        #     return False

        if context.window_manager.in_primitive_mode:
            return False

        if context.object == None:
            return True

        return True
		
    def __init__(self):
        self.draw_handle_2d = None
        self.draw_handle_3d = None
        self.draw_event  = None
        self.shape = Polyline_Shape()
                
    def invoke(self, context, event):
        args = (self, context)  

        context.window_manager.in_primitive_mode = True

        self.create_shape(context)    

        self.shape_gizmo = Shape_Gizmo()       

        self.register_handlers(args, context)
                   
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}
    
    def register_handlers(self, args, context):
        self.draw_handle_3d = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_3d, args, "WINDOW", "POST_VIEW")

        self.draw_handle_2d = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_callback_2d, args, "WINDOW", "POST_PIXEL")

        self.draw_event = context.window_manager.event_timer_add(0.1, window=context.window)
        
    def unregister_handlers(self, context):

        context.window_manager.in_primitive_mode = False

        context.window_manager.event_timer_remove(self.draw_event)
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_2d, "WINDOW")
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handle_3d, "WINDOW")
        
        self.draw_handle_2d = None
        self.draw_handle_3d = None
        self.draw_event  = None 

    def get_snapped_mouse_pos(self, mouse_pos_2d, context):

        mouse_pos_3d = self.get_3d_for_mouse(mouse_pos_2d, context)

        if context.scene.use_snapping and mouse_pos_3d is not None:
            mouse_pos_3d = get_snap_3d_vertex(context, mouse_pos_3d)
            mouse_pos_2d = get_2d_vertex(context, mouse_pos_3d)

        return mouse_pos_2d, mouse_pos_3d

    def get_3d_for_mouse(self, mouse_pos_2d, context):

        # Check if to snap to the surface of the object
        if context.scene.snap_to_target:
            mouse_pos_3d = self.shape.get_3d_for_2d(mouse_pos_2d, context)

            if mouse_pos_3d is None:
                mouse_pos_3d = get_3d_vertex(context, mouse_pos_2d)
        else:

            mouse_pos_3d = get_3d_vertex(context, mouse_pos_2d)

        return mouse_pos_3d

    def is_mouse_valid(self, mouse_pos_2d):
        return mouse_pos_2d is not None and mouse_pos_2d[0] >= 0 and mouse_pos_2d[1] >= 0

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        result = "PASS_THROUGH"

        RM = "RUNNING_MODAL"

        if self.shape.input_handle_event(event):
            return { RM }
                              
        if event.type == "ESC" and event.value == "PRESS":

            was_none = self.shape.is_none()

            self.shape.reset()

            if was_none:
                self.unregister_handlers(context)
                return { "FINISHED" }

        # The mouse wheel is moved
        if not self.shape.is_none():
            up = event.type == "WHEELUPMOUSE"
            down = event.type == "WHEELDOWNMOUSE"
            if up or down:
                inc = 1 if up else -1
                if self.shape.handle_mouse_wheel(inc, context):
                    mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
                    mouse_pos_3d = self.get_3d_for_mouse(mouse_pos_2d, context)
                    
                    self.shape.create_batch(mouse_pos_3d)
                    result = RM

        # The mouse is moved
        if event.type == "MOUSEMOVE" and not self.shape.is_none():
            
            mouse_pos_2d = self.shape.get_mouse_pos_2d(event.mouse_region_x, event.mouse_region_y)

            if self.is_mouse_valid(mouse_pos_2d):
                mouse_pos_2d, mouse_pos_3d = self.get_snapped_mouse_pos(mouse_pos_2d, context)

                if self.shape.handle_mouse_move(mouse_pos_2d, mouse_pos_3d, event, context):
                    self.shape.create_batch(mouse_pos_3d)

        # Left mouse button is released
        if event.value == "RELEASE" and event.type == "LEFTMOUSE":

            mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
            self.shape.handle_mouse_release(mouse_pos_2d, event, context)

            self.shape_gizmo.mouse_up(context, mouse_pos_2d)

        
        # Left mouse button is pressed
        if event.value == "PRESS" and event.type == "LEFTMOUSE":


            mouse_pos_2d_r = (event.mouse_region_x, event.mouse_region_y)

            if self.is_mouse_valid(mouse_pos_2d_r):

                self.create_shape(context)

                if self.shape.is_input_active():
                    return { RM }

                old_bevel_state = False

                # If an object is hit, set it as target
                if event.ctrl:
                    hit, hit_obj = self.shape.is_object_hit(mouse_pos_2d_r, context)
                    if hit:
                        context.scene.carver_target = hit_obj

                        # workround: reset bevel modifier to non display to get the right hit face
                        # Seems to be a Blender bug
                        old_bevel_state = set_bevel_display(hit_obj, False)

                mouse_pos_2d, mouse_pos_3d = self.get_snapped_mouse_pos(mouse_pos_2d_r, context)

                # workround: Reset bevel display when it was set
                if old_bevel_state == True:
                   old_bevel_state = set_bevel_display(context.scene.carver_target, True)    

                gizmo_action = self.shape_gizmo.mouse_down(context, event, mouse_pos_2d_r, mouse_pos_3d)
                if gizmo_action:
                    result = RM

                for shape_action in self.shape._shape_actions:
                    if shape_action.mouse_down(context, event, mouse_pos_2d_r, mouse_pos_3d):
                        unitinfo = get_current_units()
                        if self.shape.open_input(context, shape_action, unitinfo):
                            result = RM

                if self.shape.is_moving() and not self.shape_gizmo.is_dragging():
                    self.shape.stop_move(context)

                if self.shape.is_sizing():
                    self.shape.stop_size(context)

                if self.shape.is_extruding():
                    self.shape.stop_extrude(context)

                if self.shape.is_rotating():
                    self.shape.stop_rotate(context)

                if self.shape.is_processing():
                    result = RM

                if self.shape.is_created() and not gizmo_action and not event.ctrl and not self.shape.is_input_active():
                    if self.shape.set_vertex_moving(mouse_pos_3d):
                        result = RM

                if not gizmo_action and not self.shape.is_input_active():
                    if self.shape.handle_mouse_press(mouse_pos_2d, mouse_pos_3d, event, context):

                        self.create_object(context)

                    else:
                        # So that the direction is defined during shape
                        # creation, not when it is extruded
                        if self.shape.is_processing():
                            view_context = ViewContext(context)
                            self.shape.set_view_context(view_context)
                    
                self.shape.create_batch(mouse_pos_3d)

        # Keyboard
        if event.value == "PRESS":

            if event.type == "M" and event.alt:
                if self.shape.can_convert_to_mesh():
                    self.create_mesh(context, False)

            if event.type == "S":
                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
                mouse_pos_2d, mouse_pos_3d = self.get_snapped_mouse_pos(mouse_pos_2d, context)

                if self.shape.start_size(mouse_pos_3d):

                    # TODO: Also size the extrusion?
                    self.shape.reset_extrude()
                    result = RM

            # try to move the shape
            if event.type == "G":
                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)

                mouse_pos_2d, mouse_pos_3d = self.get_snapped_mouse_pos(mouse_pos_2d, context)

                if self.shape.start_move(mouse_pos_3d):
                    result = RM

            if self.shape.is_moving():
                if event.type in ["X", "Y", "N"]:
                    self.shape.set_move_axis(event.type)
                    result = RM

            # try to rotate the shape
            if event.type == "R":
                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)

                mouse_pos_3d = self.get_3d_for_mouse(mouse_pos_2d, context)

                if self.shape.start_rotate(mouse_pos_3d, context):
                    self.shape.create_batch()
                    result = RM

            # Try set mirror type for primitives
            if event.type == "M" and not event.alt:
                if self.shape.is_none():
                    self.shape.set_next_mirror(context)
                    self.shape.build_actions()
                    result = RM

            # try to extrude the shape
            if self.shape.is_extruding():
                if (event.type == "DOWN_ARROW" or event.type == "UP_ARROW"):
                    self.shape.handle_extrude(event.type == "UP_ARROW", context)
                    self.shape.create_batch()
                    result = RM
                elif (event.type in ["X", "Y", "Z", "N"]):
                    self.shape.set_extrude_axis(event.type)
                    self.shape.create_batch()
                    result = RM

            if event.type == "E":
                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
                mouse_pos_3d = self.get_3d_for_mouse(mouse_pos_2d, context)

                if self.shape.start_extrude(mouse_pos_2d, mouse_pos_3d, context):
                    self.shape.create_batch()
                    result = RM

            # toggle input method
            if event.type == "I":
                self.shape.set_next_input_method(context)
                self.shape.build_actions()

                result = RM

            # toggle bool mode
            if event.type == "O":
                context.scene.bool_mode = next_enum(context.scene.bool_mode, 
                                                    context.scene, "bool_mode")

                self.shape.build_actions()

                result = RM

            if event.type == "C":
                if self.shape.can_set_center_type():
                    context.scene.center_type = next_enum(context.scene.center_type, context.scene, "center_type")
                    self.shape.build_actions()
                    result = RM

            if event.type == "F":
                if self.shape.can_start_from_center():
                    context.scene.start_center = not context.scene.start_center
                    self.shape.build_actions()
                    result = RM
                           
            # toggle primitve  
            if event.type == "P":
                if self.shape.is_none():
                    context.scene.primitive_type = next_enum(context.scene.primitive_type, 
                                                        context.scene, "primitive_type")

                    self.create_shape(context)
                    result = RM
             
        return { result }

    def create_shape(self, context):
        if self.shape.is_none():
            if context.scene.primitive_type == "Circle":
                self.shape = Circle_Shape()
            elif context.scene.primitive_type == "Polyline":
                self.shape = Polyline_Shape()
            elif context.scene.primitive_type == "Curve":
                self.shape = Curve_Shape()
            else:
                self.shape = Rectangle_Shape()

            self.shape.initialize(context)

    def create_object(self, context):
        # TODO: Refactor -> Creation factory with shape as parameter
        if self.shape.connected_shape():
            self.create_mesh(context, True)
        else:
            self.create_curve(context)

    def create_curve(self, context):
        curve_shape = self.shape
        if curve_shape.is_2_points_input():
            self.create_bezier(context)
        else:
            self.create_path(context)

    def set_bevel(self, curve):
        obj_data = curve.data
        obj_data.bevel_depth = 0.05
        obj_data.resolution_u = 24
        obj_data.bevel_resolution = 12
        obj_data.fill_mode = 'FULL'  


    def create_path(self, context):
        if context.object is not None:
            bpy.ops.object.mode_set(mode='OBJECT')

        curve_shape = self.shape
        bpy.ops.curve.primitive_nurbs_path_add(enter_editmode=True)

        self.set_bevel(context.active_object)

        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.delete()

        for point in curve_shape.get_points():
            bpy.ops.curve.vertex_add(location=point)

        self.shape.reset()


    def create_bezier(self, context):
        if context.object is not None:
            bpy.ops.object.mode_set(mode='OBJECT')

        curve_shape = self.shape
        bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=True, location=(0, 0, 0))

        curve = context.active_object
        
        self.set_bevel(curve)

        bez_points = curve.data.splines[0].bezier_points
        point_count = len(bez_points) - 1

        norm_start = curve_shape.get_normal_start()
        norm_end = curve_shape.get_normal_end()

        bez_points[0].co = curve_shape.get_start_point()
        if norm_start is not None:
            bez_points[0].handle_right = bez_points[0].co + norm_start
            bez_points[0].handle_left = bez_points[0].co - norm_start

        bez_points[point_count].co = curve_shape.get_end_point()
        if norm_end is not None:
            bez_points[point_count].handle_right = bez_points[point_count].co - norm_end
            bez_points[point_count].handle_left = bez_points[point_count].co + norm_end

        self.shape.reset()

    def add_bool_obj_to_collection(self, context, obj):

        # Ensure collection exists
        coll_name = "JM Bool Pending"
        if coll_name not in bpy.data.collections:
            new_collection = bpy.data.collections.new(coll_name)
            context.scene.collection.children.link(new_collection)
        else:
            new_collection = bpy.data.collections[coll_name]

        new_collection.objects.link(obj)

    def create_mesh(self, context, extrude_mesh):
        try:
            if context.object is not None:
                current_mode = context.object.mode
                bpy.ops.object.mode_set(mode='OBJECT')

            is_bool_create = (context.scene.bool_mode == "Create" or not extrude_mesh)

            # Create a mesh and an object and 
            # add the object to the scene collection
            mesh = bpy.data.meshes.new(str(self.shape) + "_Mesh")
            obj  = bpy.data.objects.new(str(self.shape) + "_Object", mesh)

            if is_apply_immediate() or is_bool_create:
                bpy.context.scene.collection.objects.link(obj)
            else:
                self.add_bool_obj_to_collection(context, obj)
            
            bpy.ops.object.select_all(action='DESELECT')

            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)

            # Create a bmesh and add the vertices
            # added by mouse clicks
            bm = bmesh.new()
            bm.from_mesh(mesh) 

            for v in self.shape.vertices:
                bm.verts.new(v)
            
            bm.verts.index_update()
            bm.faces.new(bm.verts)

            if self.shape.has_mirror:
                # Add faces for the mirrored vertices
                mirror_verts = []
                for v in self.shape.vertices_mirror:
                    mirror_verts.append(bm.verts.new(v))
                
                bm.verts.index_update()
                bm.faces.new(mirror_verts)

            # Extrude mesh if extrude mesh option is enabled
            if extrude_mesh:
                self.extrude_mesh(context, bm, is_bool_create)

            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

            bm.to_mesh(mesh)
            bm.free()

            bpy.context.view_layer.objects.active = obj
            obj.select_set(state=True)

            self.remove_doubles()

            # set origin to geometry
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')

            # Fast bool modes
            if not is_bool_create:

                target_obj = bpy.context.scene.carver_target
                if target_obj is not None:

                    bool_mode_id = self.get_bool_mode_id(context.scene.bool_mode)
                    if bool_mode_id != 3:
                        execute_boolean_op(context, target_obj, bool_mode_id)
                    else:
                        execute_slice_op(context, target_obj)

                    # delete the bool object if apply immediate is checked
                    if is_apply_immediate():
                        bpy.ops.object.delete()
                    else:
                        obj.hide_set(True)

                    select_active(target_obj)
        except:
            pass
        finally:
            if current_mode is not None:
                bpy.ops.object.mode_set(mode=current_mode)

    def get_bool_mode_id(self, bool_name):
        if bool_name == "Difference":
            return 0
        elif bool_name == "Union":
            return 1
        elif bool_name == "Intersect":
            return 2
        elif bool_name == "Slice":
            return 3
        return -1

    def remove_doubles(self):
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles()       

    def extrude_mesh(self, context, bm, is_bool_create):
        length = 1
        if not is_bool_create:
            length = 100
        
        dir = self.shape.get_dir() * length

        if self.shape.is_extruded():
            dir = self.shape.get_dir() * self.shape.extrusion

        # extr_geom = bm.edges[:]
        extr_geom = bm.faces[:]

        r = bmesh.ops.extrude_face_region(bm, geom=extr_geom)
        verts = [e for e in r['geom'] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=dir, verts=verts)

    def finish(self):
        self.unregister_handlers(bpy.context)
        return {"FINISHED"}

    def draw_action_line(self, action, pos_y):
        blf.color(1, 1, 1, 1, 1)
        blf.position(1, 10, pos_y , 1)
        blf.draw(1, action.title) 

        if(action.content != ""):
            blf.position(1, 115, pos_y , 1)
            blf.draw(1, ": " + action.content) 

        blf.color(1, 0, 0.5, 1, 1)
        blf.position(1, 250, pos_y, 1)
        blf.draw(1, action.id)

	# Draw handler to paint in pixels
    def draw_callback_2d(self, op, context):

        self.shape.draw_text()

        self.shape_gizmo.draw(self.shape)

        self.shape.input_draw()

        self.shape.shape_actions_draw()

        # Draw text for primitive mode
        blf.size(1, 16, 72)

        size = 20
        pos_y = 180 # self.get_actions_height(size)

        self.draw_action_line(self.shape.actions[0], pos_y)

        for index in range(len(self.shape.actions)-1):
            action = self.shape.actions[index+1]
            self.draw_action_line(action, (pos_y - 10) - (index + 1) * size)

        blf.color(1, 1, 1, 1, 1)

    def get_actions_height(self, size):
        return len(self.shape.actions) * size


	# Draw handler to paint onto the screen
    def draw_callback_3d(self, op, context):
        
        self.shape.draw(context)

        self.shape.set_shape_actions_position()