from enum import Enum

import blf

from math import sin, cos, pi, radians

from mathutils import Vector, geometry

from mathutils.geometry import intersect_line_plane
from mathutils.geometry import intersect_point_line

from ..utils.fc_view_3d_utils import *

from bpy_extras.view3d_utils import (
    region_2d_to_location_3d,
    location_3d_to_region_2d,
    region_2d_to_vector_3d,
    region_2d_to_origin_3d)

from .action import Action


class ShapeState(Enum):
    NONE = 0
    PROCESSING = 1
    CREATED = 2


class ViewRegion():
    def __init__(self, region):
        self._width = region.width
        self._height = region.height

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height


class ViewContext():

    def __init__(self, context):
        self._region_3d = context.space_data.region_3d
        self._view_rot = self._region_3d.view_rotation.copy()
        self._view_mat = self._region_3d.view_matrix.copy()
        self._pers_mat = self._region_3d.perspective_matrix.copy()
        self._view_pers = self._region_3d.view_perspective
        self._is_perspective = self._region_3d.is_perspective
        self._region = ViewRegion(context.region)

    @property
    def region(self):
        return self._region

    @property
    def region_3d(self):
        return self._region_3d

    @property
    def view_rotation(self):
        return self._view_rot

    @property
    def view_perspective(self):
        return self._view_pers

    @property
    def perspective_matrix(self):
        return self._pers_mat

    @property
    def view_matrix(self):
        return self._view_mat

    @property
    def is_perspective(self):
        return self._is_perspective


class Shape:

    def __init__(self):
        self._state = ShapeState.NONE
        self._vertices_2d = []
        self._vertices = []
        self._vertices_extruded = []
        self._vertex_moving = None
        self._is_moving = False
        self._is_rotating = False
        self._is_extruding = False
        self._move_offset = 0.0
        self._move_axis = None
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

    def can_start_from_center(self):
        return False

    def get_start_from_center(self, context):
        return context.scene.start_center and self.can_start_from_center()

    def is_object_hit(self, pos_2d, context):

        origin, direction = get_origin_and_direction(pos_2d, context)

        hit, hit_loc, norm, face, hit_obj, *_ = context.scene.ray_cast(context.view_layer, origin, direction)

        return hit, hit_obj

    def get_3d_for_2d(self, pos_2d, context):

        result = None

        scene = context.scene

        origin, direction = get_origin_and_direction(pos_2d, context)

        # Try to hit an object in the scene
        if self._hit is None:
            hit, self._hit, self._normal, face, hit_obj, *_ = scene.ray_cast(context.view_layer, origin, direction)
            if hit:
                self._snap_to_target = True
                result = self._hit.copy()

        # Object was hit before
        else:
            result = intersect_line_plane(
                origin, origin + direction, self._hit, self._normal)

        if result is not None:
            result += self._normal.normalized() * 0.01

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
    def vertices_extruded(self):
        return self._vertices_extruded

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

    def build_move_action(self):
        if not self._is_moving:
            self.add_action(Action("G",       "Move",
                                   ""), ShapeState.CREATED)
        else:
            self.add_action(Action("X or Y",  "Move Axis lock",
                                   ""), ShapeState.CREATED)

    def build_actions(self):
        self._actions.clear()

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
            return "Undo"

    @property
    def actions(self):
        return self._actions

    @property
    def extrusion(self):
        return self._extrusion

    def add_vertex(self, vertex):
        self._vertices.append(vertex)

    def reset(self):
        self._vertices.clear()
        self._vertices_extruded.clear()
        self._vertices_2d.clear()
        self.state = ShapeState.NONE

    def close(self):
        return False

    def get_vertices_copy(self, mouse_pos=None):
        return self._vertices.copy()

    def get_vertices_extruded_copy(self, mouse_pos=None):
        return self._vertices_extruded.copy()

    def start_move(self, mouse_pos):
        if self.is_created() and mouse_pos is not None:
            self._is_moving = True
            self._move_axis = None
            self._move_offset = mouse_pos
            self.build_actions()
            return True
        return False

    def stop_move(self, context):

        for index, vertex_3d in enumerate(self._vertices):
            rv3d = self._view_context.region_3d
            region = self._view_context.region
            self._vertices_2d[index] = location_3d_to_region_2d(
                region, rv3d, vertex_3d)

        self._move_axis = None
        self._is_moving = False
        self._move_offset = 0.0
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
        self._move_axis = axis

    def start_rotate(self, mouse_pos, context):
        return False

    def stop_rotate(self, context):
        self._is_rotating = False
        self._rotation = 0.0

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

            print(str(length))

            self.extrude_vertices(context)
            return True

        if self._vertex_moving is not None:
            self._vertices[self._vertex_moving] = mouse_pos_3d
            return True

        if self.is_created() and self._is_moving:
            diff = mouse_pos_3d - self._move_offset
            self._vertices = [vertex + diff for vertex in self._vertices]
            self._vertices_extruded = [
                vertex + diff for vertex in self._vertices_extruded]
            self._move_offset = mouse_pos_3d
            return True

        return False

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

    def get_point_size(self, context):
        return 10