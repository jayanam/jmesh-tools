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
from .utils.fc_view_3d_utils import *

from .types.shape import *
from .types.rectangle_shape import *
from .types.polyline_shape import *
from .types.circle_shape import *
from .types.curve_shape import *

from .types.enums import *

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

        return context.object.mode == "OBJECT" or context.object.mode == "SCULPT"
		
    def __init__(self):
        self.draw_handle_2d = None
        self.draw_handle_3d = None
        self.draw_event  = None
        self.shape = Polyline_Shape()

        self.create_batch(None)
                
    def invoke(self, context, event):
        args = (self, context)  

        context.window_manager.in_primitive_mode = True

        self.current_mode = None

        if context.object is not None:
            self.current_mode = context.object.mode

        self.create_shape(context)                 

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

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        result = "PASS_THROUGH"
                              
        if event.type == "ESC" and event.value == "PRESS":

            was_none = self.shape.is_none()

            self.shape.reset()
            self.create_batch(None)

            if was_none:

                self.unregister_handlers(context)

                return {'FINISHED'}

        # The mouse wheel is moved
        if not self.shape.is_none():
            up = event.type == "WHEELUPMOUSE"
            down = event.type == "WHEELDOWNMOUSE"
            if up or down:
                inc = 1 if up else -1
                if self.shape.handle_mouse_wheel(inc, context):
                    mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)
                    mouse_pos_3d = self.get_3d_for_mouse(mouse_pos_2d, context)
                    
                    self.create_batch(mouse_pos_3d)
                    result = "RUNNING_MODAL"

        # The mouse is moved
        if event.type == "MOUSEMOVE" and not self.shape.is_none():
            
            mouse_pos_2d = self.shape.get_mouse_pos_2d(event.mouse_region_x, event.mouse_region_y)

            mouse_pos_2d, mouse_pos_3d = self.get_snapped_mouse_pos(mouse_pos_2d, context)

            if self.shape.handle_mouse_move(mouse_pos_2d, mouse_pos_3d, event, context):
                self.create_batch(mouse_pos_3d)

        # Left mouse button is released
        if event.value == "RELEASE" and event.type == "LEFTMOUSE":
            self.shape.set_vertex_moving(None)
        
        # Left mouse button is pressed
        if event.value == "PRESS" and event.type == "LEFTMOUSE":

            self.create_shape(context)

            mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)

            # If an object is hit, set it as target
            hit, hit_obj = self.shape.is_object_hit(mouse_pos_2d, context)
            if hit:
                context.scene.carver_target = hit_obj

            mouse_pos_2d, mouse_pos_3d = self.get_snapped_mouse_pos(mouse_pos_2d, context)

            if self.shape.is_moving():
                self.shape.stop_move(context)

            if self.shape.is_extruding():
                self.shape.stop_extrude(context)

            if self.shape.is_rotating():
                self.shape.stop_rotate(context)

            if self.shape.is_processing():
                result = "RUNNING_MODAL"

            if self.shape.is_created():
                if self.shape.set_vertex_moving(mouse_pos_3d):
                    result = "RUNNING_MODAL"

            if self.shape.handle_mouse_press(mouse_pos_2d, mouse_pos_3d, event, context):

                self.create_object(context)

            else:
                # So that the direction is defined during shape
                # creation, not when it is extruded
                if self.shape.is_processing():
                    view_context = ViewContext(context)
                    self.shape.set_view_context(view_context)
                
            self.create_batch(mouse_pos_3d)

        # Keyboard
        if event.value == "PRESS":

            # try to move the shape
            if event.type == "G":
                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)

                mouse_pos_2d, mouse_pos_3d = self.get_snapped_mouse_pos(mouse_pos_2d, context)

                if self.shape.start_move(mouse_pos_3d):
                    result = "RUNNING_MODAL"

            if event.type in ["X", "Y"]:
                self.shape.set_move_axis(event.type)
                result = "RUNNING_MODAL"

            # try to rotate the shape
            if event.type == "R":
                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)

                mouse_pos_3d = self.get_3d_for_mouse(mouse_pos_2d, context)

                if self.shape.start_rotate(mouse_pos_3d, context):
                    self.create_batch()
                    result = "RUNNING_MODAL"             

            # try to extrude the shape
            if event.type == "E":
                mouse_pos_2d = (event.mouse_region_x, event.mouse_region_y)

                if self.shape.start_extrude(mouse_pos_2d, context):
                    self.create_batch()
                    result = "RUNNING_MODAL"

            # toggle bool mode
            if event.type == "O":
                context.scene.bool_mode = next_enum(context.scene.bool_mode, 
                                                    context.scene, "bool_mode")

                self.shape.build_actions()

                result = "RUNNING_MODAL"

            if event.type == "C":
                if self.shape.can_set_center_type():
                    context.scene.center_type = next_enum(context.scene.center_type, context.scene, "center_type")
                    self.shape.build_actions()
                    result = "RUNNING_MODAL"

            if event.type == "F":
                if self.shape.can_start_from_center():
                    context.scene.start_center = not context.scene.start_center
                    self.shape.build_actions()
                    result = "RUNNING_MODAL"
                           
            # toggle primitve  
            if event.type == "P":
                if self.shape.is_none():
                    context.scene.primitive_type = next_enum(context.scene.primitive_type, 
                                                        context.scene, "primitive_type")

                    self.create_shape(context)
                    result = "RUNNING_MODAL"
             
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
            self.create_mesh(context)
        else:
            self.create_curve(context)

    def create_curve(self, context):
        if context.object is not None:
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.curve.primitive_bezier_curve_add(enter_editmode=True, location=(0, 0, 0))

        curve = context.active_object
        curve_shape = self.shape

        # TODO: Make this configurable
        obj_data = context.active_object.data
        obj_data.bevel_depth = 0.05
        obj_data.resolution_u = 12
        obj_data.fill_mode = 'FULL'  

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



    def create_mesh(self, context):
        try:

            if context.object is not None:
                bpy.ops.object.mode_set(mode='OBJECT')

            is_bool_create = (context.scene.bool_mode == "Create")

            # Create a mesh and an object and 
            # add the object to the scene collection
            mesh = bpy.data.meshes.new("MyMesh")
            obj  = bpy.data.objects.new("MyObject", mesh)

            bpy.context.scene.collection.objects.link(obj)
            
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

            # Extrude mesh if extrude mesh option is enabled
            self.extrude_mesh(context, bm, is_bool_create)

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
                        select_active(target_obj)
        except RuntimeError:
            pass
        finally:
            if self.current_mode is not None:
                bpy.ops.object.mode_set(mode=self.current_mode)

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
        if context.scene.extrude_mesh:

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

    def create_batch(self, mouse_pos = None):
        
        points = self.shape.get_vertices_copy(mouse_pos)

        extrude_points = self.shape.get_vertices_extruded_copy(mouse_pos)

        extrude_lines = []
        for index, vertex in enumerate(extrude_points):
            extrude_lines.append(points[index])
            extrude_lines.append(vertex)

        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
         
        self.batch = batch_for_shader(self.shader, 'LINE_LOOP', 
            {"pos": points})

        self.batch_extruded = batch_for_shader(self.shader, 'LINE_LOOP', 
            {"pos": extrude_points})

        self.batch_lines_extruded = batch_for_shader(self.shader, 'LINES', 
            {"pos": extrude_lines})

        self.batch_points = batch_for_shader(self.shader, 'POINTS', {"pos": points})

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

        # Draw text for primitive mode
        blf.size(1, 16, 72)

        size = 20
        pos_y = 160 # self.get_actions_height(size)

        self.draw_action_line(self.shape.actions[0], pos_y)

        for index in range(len(self.shape.actions)-1):
            action = self.shape.actions[index+1]
            self.draw_action_line(action, (pos_y - 10) - (index + 1) * size)

        blf.color(1, 1, 1, 1, 1)

    def get_actions_height(self, size):
        return len(self.shape.actions) * size


	# Draw handler to paint onto the screen
    def draw_callback_3d(self, op, context):

        self.shader.bind()

        if self.shape.connected_shape():

            # Draw lines
            bgl.glEnable(bgl.GL_LINE_SMOOTH)

            self.shader.uniform_float("color", (0.2, 0.5, 0.8, 1.0))
            bgl.glLineWidth(2)
            self.batch_extruded.draw(self.shader)

            bgl.glLineWidth(1)
            self.batch_lines_extruded.draw(self.shader)

            bgl.glLineWidth(3)
            self.shader.uniform_float("color", (0.1, 0.3, 0.7, 1.0))
            self.batch.draw(self.shader)

        else:
            self.shader.uniform_float("color", (0.1, 0.3, 0.7, 1.0))

        bgl.glPointSize(self.shape.get_point_size())
        self.batch_points.draw(self.shader)

