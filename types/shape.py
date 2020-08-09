import blf
import bgl
import gpu
from gpu_extras.batch import batch_for_shader

from enum import Enum

from math import sin, cos, pi, radians
from mathutils import Vector, geometry
from mathutils.geometry import intersect_line_plane, intersect_point_line

from ..utils.fc_view_3d_utils import *

from bpy_extras.view3d_utils import (
    region_2d_to_location_3d,
    location_3d_to_region_2d,
    region_2d_to_vector_3d,
    region_2d_to_origin_3d)

from .context_utils import *
from .action import Action
from .shape_action import *
from .enums import *

from ..widgets.bl_ui_textbox import *

from ..utils.unit_util import *

class Shape:

    def __init__(self):
        self._state = ShapeState.NONE
        self._vertices_2d = []
        self._vertices = []
        self._vertices_extruded = []

        self._vertices_m = []
        self._vertices_extruded_m = []

        self._vertex_moving = None
        self._is_moving = False
        self._is_sizing = False
        self._is_rotating = False
        self._is_extruding = False
        self._move_offset = Vector()
        self._move_axis = None
        self._extrude_axis = None
        self._rotation = 0.0
        self._extrusion = 0.0
        self._view_context = None
        self._mouse_pos_2d = [0, 0]
        self._is_extruded = False
        self._snap_to_target = False
        self._bvhtree = None
        self._hit = None
        self._normal = None
        self._actions = []
        self._extrude_pos = None
        self._mouse_pressed = False
        self._input_size = None
        self._shape_actions = []

        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.create_batch()



    def create_batch(self, mouse_pos = None):
        points = self.get_vertices_copy(mouse_pos)

        points_mirror = self.get_vertices_mirror_copy(mouse_pos)

        extrude_points = self.get_vertices_extruded_copy(mouse_pos)

        extrude_points_m = self.get_vertices_extruded_mirror_copy(mouse_pos)

        extrude_lines = []
        for index, vertex in enumerate(extrude_points):
            extrude_lines.append(points[index])
            extrude_lines.append(vertex)

        extrude_lines_m = []
        for index, vertex in enumerate(extrude_points_m):
            extrude_lines_m.append(points_mirror[index])
            extrude_lines_m.append(vertex)

        self.batch = batch_for_shader(self.shader, 'LINE_LOOP', 
            {"pos": points})

        self.batch_extruded = batch_for_shader(self.shader, 'LINE_LOOP', 
            {"pos": extrude_points})

        self.batch_lines_extruded = batch_for_shader(self.shader, 'LINES', 
            {"pos": extrude_lines})

        # Mirror batches
        self.batch_mirror = batch_for_shader(self.shader, 'LINE_LOOP', 
            {"pos": points_mirror})

        self.batch_extruded_m = batch_for_shader(self.shader, 'LINE_LOOP', 
            {"pos": extrude_points_m})

        self.batch_lines_extruded_m = batch_for_shader(self.shader, 'LINES', 
            {"pos": extrude_lines_m})

        # Batch for points
        self.batch_points = batch_for_shader(self.shader, 'POINTS', {"pos": points})

    def draw(self, context):
        self.shader.bind()

        if self.connected_shape():

            # Draw lines
            bgl.glEnable(bgl.GL_LINE_SMOOTH)

            self.shader.uniform_float("color", (0.2, 0.5, 0.8, 1.0))
            bgl.glLineWidth(2)
            self.batch_extruded.draw(self.shader)
            self.batch_extruded_m.draw(self.shader)

            bgl.glLineWidth(1)
            self.batch_lines_extruded.draw(self.shader)
            self.batch_lines_extruded_m.draw(self.shader)

            bgl.glLineWidth(3)
            self.shader.uniform_float("color", (0.1, 0.3, 0.7, 1.0))
            self.batch.draw(self.shader)
            self.batch_mirror.draw(self.shader)
        else:
            self.shader.uniform_float("color", (0.1, 0.3, 0.7, 1.0))

        bgl.glPointSize(self.get_point_size(context))
        self.batch_points.draw(self.shader)

    def add_shape_action(self, shape_action):
        self._shape_actions.append(shape_action)

    def shape_actions_draw(self):
        for action in self._shape_actions:
            action.draw()

    def set_shape_actions_position(self):
        pass

    def input_handle_event(self, event):
        if self._input_size is not None:
            if self._input_size.handle_event(event):
                return True

        return False

    def is_input_active(self):
        return self._input_size is not None

    def input_draw(self):
         if self._input_size is not None:
             self._input_size.draw()    

    def open_input(self, context, shape_action, unitinfo) -> bool:
        if self.is_created():
            
            self._input_size = BL_UI_Textbox(0, 0, 100, 24)
            self._input_size.max_input_chars = 12
            self._input_size.init(context)
            self._input_size.label = unitinfo[0]
            
            pos = shape_action.get_position()
            self._input_size.set_location(pos[0] + 20, self._input_size.get_area_height() - pos[1] - 4)

            self._input_size.set_text_changed(self.on_input_changed)
            return True

        return False

    def on_input_changed(self, textbox, context, event):
        if event.type == "ESC":
            self.close_input()
        elif event.type == "RET":
            self.apply_input(context)

    def close_input(self):
        self._input_size = None

    def apply_input(self, context):
        self.close_input()
        self.create_batch()

    def can_start_from_center(self):
        return False

    def get_raycast_param(self, view_layer):        
        if bpy.app.version >= (2, 91, 0):
            return view_layer.depsgraph
        else:
            return view_layer       

    def get_start_from_center(self, context):
        return context.scene.start_center and self.can_start_from_center()

    def is_object_hit(self, pos_2d, context):

        origin, direction = get_origin_and_direction(pos_2d, context)

        ray_cast_param = self.get_raycast_param(context.view_layer)
        hit, hit_loc, norm, face, hit_obj, *_ = context.scene.ray_cast(ray_cast_param, origin, direction)

        return hit, hit_obj

    def get_3d_for_2d(self, pos_2d, context):

        result = None

        scene = context.scene

        origin, direction = get_origin_and_direction(pos_2d, context)

        # Try to hit an object in the scene
        if self._hit is None:
            ray_cast_param = self.get_raycast_param(context.view_layer)
            hit, self._hit, self._normal, face, hit_obj, *_ = scene.ray_cast(ray_cast_param, origin, direction)
            if hit:
                self._snap_to_target = True
                result = self._hit.copy()

        # Object was hit before
        else:
            result = intersect_line_plane(
                origin, origin + direction, self._hit, self._normal)

        if result is not None:
            result += self._normal.normalized() * scene.snap_offset

        return result

    def initialize(self, context):
        # if target != None:
        #    self._bvhtree = bvhtree_from_object(context, target)

        self._snap_to_target = False
        self.build_actions()

    def is_none(self):
        return self._state is ShapeState.NONE

    def is_processing(self):
        return self._state is ShapeState.PROCESSING

    def is_created(self):
        return self._state is ShapeState.CREATED

    def is_extruded(self):
        return self._is_extruded

    def is_moving(self):
        return self._is_moving

    def is_sizing(self):
        return self._is_sizing

    def is_rotating(self):
        return self._is_rotating

    def is_extruding(self):
        return self._is_extruding

    def connected_shape(self):
        return True

    def set_vertex_moving(self, mouse_pos_3d):

        if mouse_pos_3d is None:
            self._vertex_moving = None
            return False

        min_dist = 1000
        idx = 0
        for i, v in enumerate(self._vertices):
            dist = (mouse_pos_3d - v).length
            if dist < min_dist:
                min_dist = dist
                idx = i

        if min_dist > 0.1:
            return False

        self._vertex_moving = idx
        return True


    def get_dir(self):

        if self._extrude_axis == "X":
            return Vector((1,0,0))
        elif self._extrude_axis == "Y":
            return Vector((0,1,0))
        elif self._extrude_axis == "Z":
            return Vector((0,0,1))

        else:
            if not self._snap_to_target or self._normal == None:
                view_rot = self._view_context.view_rotation
                return get_view_direction_by_rot_matrix(view_rot)
        
        return -self._normal

    def get_view_context(self):
        return self._view_context

    def set_view_context(self, value):
        self._view_context = value

    @property
    def vertices(self):
        return self._vertices

    @property
    def vertices_mirror(self):
        return self._vertices_m

    @property
    def vertices_extruded(self):
        return self._vertices_extruded

    @property
    def vertices_extruded_mirror(self):
        return self._vertices_extruded_m

    @property
    def vertices_2d(self):
        return self._vertices_2d

    @vertices.setter
    def vertices(self, value):
        self._vertices = value

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self.build_actions()

    def build_extrude_action(self):
        if not self._is_extruding:
            self.add_action(Action("E",       "Extrude",
                                   ""), ShapeState.CREATED)
        else:
            self.add_action(
                Action("Up, Down Arrow",  "Extrude",     ""), ShapeState.CREATED)        
            self.add_action(
                Action("X, Y, Z or N",  "Extrude Axis",    ""), ShapeState.CREATED)

    def build_move_action(self):
        if not self._is_moving:
            self.add_action(Action("G",       "Move",
                                   ""), ShapeState.CREATED)
        else:
            self.add_action(Action("X, Y or N",  "Move Axis lock",
                                   ""), ShapeState.CREATED)

    def build_actions(self):
        self._actions.clear()

    def set_next_input_method(self, context):
        pass

    def set_next_mirror(self, context):
        context.scene.mirror_primitive = next_enum(context.scene.mirror_primitive, 
                                                    context.scene, "mirror_primitive")

    def add_action(self, action, shape_state=None):
        if(self.state == shape_state or shape_state == None):
            self.actions.append(action)

    def get_prim_id(self):
        if(self.state == ShapeState.NONE):
            return "P"
        else:
            return ""

    def get_esc_title(self):
        if(self.state == ShapeState.NONE):
            return "Exit"
        else:
            return "Abort"

    @property
    def actions(self):
        return self._actions

    @property
    def extrusion(self):
        return self._extrusion

    def add_vertex(self, vertex):
        if vertex not in self._vertices:
            self._vertices.append(vertex)

    @property
    def has_mirror(self):
        return bpy.context.scene.mirror_primitive != "None"

    @property
    def extrude_immediate(self):
        return bpy.context.scene.extrude_immediate == True

    @property
    def mirror_type(self):
        return bpy.context.scene.mirror_primitive

    def get_vertex_mirror(self, vertex3d):
        if self.mirror_type == "X":
            vm = Vector((-vertex3d.x, vertex3d.y, vertex3d.z))
        elif self.mirror_type == "Y":
            vm = Vector((vertex3d.x, -vertex3d.y, vertex3d.z))
        else:
            vm = Vector((vertex3d.x, vertex3d.y, -vertex3d.z))

        return vm 

    def add_vertex_mirror(self, vertex3d):
        if self.has_mirror:
            vm = self.get_vertex_mirror(vertex3d)
            self._vertices_m.append(vm)

    def reset_extrude(self):
        self._is_extruded = False
        self._vertices_extruded.clear()
        self._vertices_extruded_m.clear()

    def to_center(self, axis = "N"):
        pass

    def __str__(self):
        return "Shape"

    def reset(self):
        self._vertices.clear()
        self._vertices_extruded.clear()
        self._vertices_2d.clear()
        self._vertices_m.clear()
        self._vertices_extruded_m.clear()
        self._shape_actions.clear()
        self.state = ShapeState.NONE
        self.create_batch()

    def close(self):
        return False

    def get_vertices_copy(self, mouse_pos=None):
        return self._vertices.copy()

    def get_vertices_extruded_copy(self, mouse_pos=None):
        return self._vertices_extruded.copy()

    def get_vertices_extruded_mirror_copy(self, mouse_pos=None):
        return self._vertices_extruded_m.copy()

    def get_vertices_mirror_copy(self, mouse_pos = None):
        return self._vertices_m.copy()

    def start_size(self, mouse_pos):
        if self.is_created() and mouse_pos is not None:
            self._is_sizing = True
            self.build_actions()
            return True
        return False

    def stop_size(self, context):
        self._is_sizing = False
        self.build_actions()

    def start_move(self, mouse_pos):
        if self.is_created() and mouse_pos is not None:
            self._is_moving = True
            self._move_axis = None
            self._move_offset = mouse_pos
            self.build_actions()
            return True
        return False

    def vertices_3d_to_2d(self, context):
        for index, vertex_3d in enumerate(self._vertices):
            rv3d = self._view_context.region_3d
            region = self._view_context.region
            self._vertices_2d[index] = location_3d_to_region_2d(
                region, rv3d, vertex_3d)

    def stop_move(self, context):

        self.vertices_3d_to_2d(context)

        self._move_axis = None
        self._is_moving = False
        self._move_offset = Vector()
        self.build_actions()

    def get_mouse_pos_2d(self, x, y):

        # Check if we have an axis constraint,
        # if not, just write and return the 2d positions
        if self._move_axis is None:
            self._mouse_pos_2d = [x, y]
        elif self._move_axis == "Y":
            self._mouse_pos_2d[1] = y
        else:
            self._mouse_pos_2d[0] = x

        return self._mouse_pos_2d

    def set_move_axis(self, axis):
        if axis == "N":
            self._move_axis = None
        else:
            self._move_axis = axis

    def start_rotate(self, mouse_pos, context):
        return False

    def stop_rotate(self, context):
        self._is_rotating = False
        self._rotation = 0.0

    def set_extrude_axis(self, axis):
        if axis == "N":
            self._extrude_axis = None
        else:
            self._extrude_axis = axis

    def start_extrude_immediate(self, mouse_pos_2d, mouse_pos_3d, context):
        if self.extrude_immediate:
            self.start_extrude(mouse_pos_2d, mouse_pos_3d, context)


    def start_extrude(self, mouse_pos_2d, mouse_pos_3d, context):
        self._extrude_pos = mouse_pos_2d
        self._is_extruding = True
        self.build_actions()
        return True

    def stop_extrude(self, context):
        self._extrude_pos = None
        self._is_extruding = False

    def can_set_center_type(self):
        return False

    def extrude_vertices(self, context):

        dir = self._extrusion * self.get_dir()

        for index, vertex3d in enumerate(self._vertices):
            if not self._is_extruded:
                self._vertices_extruded.append(vertex3d + dir)
            else:
                self._vertices_extruded[index] = vertex3d + dir

        for index, vertex3d in enumerate(self._vertices_m):
            if not self._is_extruded:
                self._vertices_extruded_m.append(vertex3d + dir)
            else:
                self._vertices_extruded_m[index] = vertex3d + dir

        self._is_extruded = True

    def handle_extrude(self, is_up_key, context):
        if self.is_extruding():
            if is_up_key:
                self._extrusion += 0.1
            else:
                self._extrusion -= 0.1

        self.extrude_vertices(context)

    def handle_mouse_wheel(self, inc, context):
        return False

    def handle_mouse_move(self, mouse_pos_2d, mouse_pos_3d, event, context):

        if self.is_extruding():

            dir = self.get_dir()
            region = context.region
            rv3d = context.space_data.region_3d

            mxy = event.mouse_region_x, event.mouse_region_y
            mpos_3d = region_2d_to_location_3d(region, rv3d, mxy, self._vertices[0])

            isect_pt, length = intersect_point_line(
                mpos_3d,
                self._vertices[0],
                self._vertices[0] + dir)

            self._extrusion = length

            self.extrude_vertices(context)
            return True

        if self._vertex_moving is not None:
            self._vertices[self._vertex_moving] = mouse_pos_3d
            self.vertex_moved(context)
            return True

        if self.is_created() and self._is_moving:
            diff = mouse_pos_3d - self._move_offset
            self._vertices = [vertex + diff for vertex in self._vertices]
            self._vertices_extruded = [
                vertex + diff for vertex in self._vertices_extruded]

            if self.has_mirror:
                diff_m = self.get_mirror_diff(diff)
                self._vertices_m = [vertex + diff_m for vertex in self._vertices_m]
                self._vertices_extruded_m = [
                vertex + diff_m for vertex in self._vertices_extruded_m]

            self.vertices_moved(diff)
                        
            self._move_offset = mouse_pos_3d
            return True

        return False

    def vertex_moved(self, context):
        pass

    def vertices_moved(self, diff):
        pass

    def get_mirror_diff(self, diff):
        diff_m = diff.copy()

        if self.mirror_type == "X":
            diff_m.x = -diff_m.x
        elif self.mirror_type == "Y":
            diff_m.y = -diff_m.y
        else:
            diff_m.z = -diff_m.z

        return diff_m 

    def handle_mouse_press(self, mouse_pos_2d, mouse_pos_3d, event, context):
        self._mouse_pressed = True
        return False

    def handle_mouse_release(self, mouse_pos_2d, event, context):
        self._mouse_pressed = False
        self.set_vertex_moving(None)
        return False

    def handle_apply(self):
        if self.is_processing():
            if not self.close():
                self.reset()

        # The shape is created, apply the shape
        elif self.is_created():
            return True

        return False

    def init_text(self):
        blf.size(2, 16, 72)
        blf.color(2, 0.1, 0.3, 0.7, 1.0)

    def draw_text(self):
        pass

    def get_gizmo_anchor_vertex(self):
        return None

    def get_gizmo_pos(self):
        if self.is_created():

            rv3d = self._view_context.region_3d
            region = self._view_context.region
            pos_2d = location_3d_to_region_2d(region, rv3d, self.get_gizmo_anchor_vertex())
            pos_2d.y -= 16
            pos_2d.x += 16

            return pos_2d

        return None

    def draw_gizmo(self, context):
        pass

    def get_point_size(self, context):
        return 10