import blf
import bgl
import gpu
import bmesh
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
from ..widgets.bl_ui_slider import *
from ..widgets.bl_ui_label import *
from ..widgets.bl_ui_button import *
from ..widgets.bl_ui_drag_panel import *

from ..utils.unit_util import *

from .vertex_container import VertexContainer

class Shape:

    def __init__(self):
        self._state = ShapeState.NONE
        self._vertices_2d = []

        self._vertex_ctr = VertexContainer()
        self._vertex_ctr_m = VertexContainer()

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
        self._hit_face = -1
        self._hit_obj = None
        self._actions = []
        self._extrude_pos = None
        self._mouse_pressed = False

        self._panel_action = None
        self._txt_distance = None
        self._slider_count = None
        self._shape_actions = []

        self._current_array_action = None

        # vertex containers with vertices for arrays
        self._array = []

        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.create_batch()

    def get_center(self, mouse_pos_3d, context):
        if context.scene.center_type == "Mouse":
            return mouse_pos_3d
        elif context.scene.center_type == "3D-Cursor":
            return context.scene.cursor.location

        # get active mesh part (vertex, edge or face)
        # for edge: middle of edge
        # for face: face center
        else:
            return get_selected_mesh_center(context, mouse_pos_3d)

    def create_batch(self, mouse_pos = None):

        pos = self.connect_to_mouse_pos(mouse_pos)
        self._vertex_ctr.create_batch(pos)

        self._vertex_ctr_m.create_batch(self.get_vertex_mirror(pos))


    @property
    def vertex_containers(self):
        return self._array

    def draw(self, context):
        self.shader.bind()
        bgl.glPointSize(self.get_point_size(context))
        if self.connected_shape():

            # Draw lines
            # bgl.glEnable(bgl.GL_LINE_SMOOTH)

            # self.shader.uniform_float("color", (0.2, 0.5, 0.8, 1.0))
            # bgl.glLineWidth(2)
            # self.batch_extruded_m.draw(self.shader)

            # bgl.glLineWidth(1)
            # self.batch_lines_extruded_m.draw(self.shader)

            # bgl.glLineWidth(3)
            # self.shader.uniform_float("color", (0.1, 0.3, 0.7, 1.0))
            # self.batch_mirror.draw(self.shader)

            self._vertex_ctr_m.draw()

            self._vertex_ctr.draw()

        else:
            self.shader.uniform_float("color", (0.1, 0.3, 0.7, 1.0))
            self._vertex_ctr.draw_points()
            
        # Draw arrays
        for vc in self._array:
            vc.draw()

    def add_shape_action(self, shape_action):
        self._shape_actions.append(shape_action)

    def shape_actions_draw(self):
        for action in self._shape_actions:
            action.draw()

    def set_shape_actions_position(self):
        gizmo_pos = self.get_gizmo_pos()

        for i, shape_action in enumerate(self._shape_actions):    
            shape_action.set_position(gizmo_pos[0] + (i * 20), gizmo_pos[1] - 22)

        if self._panel_action is not None:
            self._panel_action.set_location(gizmo_pos[0], self._panel_action.get_area_height() - gizmo_pos[1] + 42)


    def shape_action_widgets_handle_event(self, event):

        handled = False

        if self._panel_action:
            for widget in self._panel_action.widgets:
                if widget.handle_event(event):
                    handled = True

        return handled

    def is_shape_action_active(self):
        return self._panel_action is not None

    def shape_action_widgets_draw(self):

        if self._panel_action is not None:
            self._panel_action.draw()
            for w in self._panel_action.widgets:
                w.draw()

    def clear_action_panel(self):
        if self._panel_action:
            for w in self._panel_action.widgets:
                w = None
            self._panel_action.widgets.clear()

            self._slider_count = None
            self._txt_distance = None

    def open_size_action(self, context, shape_action, unitinfo) -> bool:

        if self.is_created():
            self.clear_action_panel()

            self._panel_action = BL_UI_Drag_Panel(0, 0, 153, 65)
            self._panel_action.bg_color = (0.1, 0.1, 0.1, 0.9)
            self._panel_action.init(context)

            txt_size = BL_UI_Textbox(10, 10, 100, 24)
            txt_size.is_numeric = True
            txt_size.max_input_chars = 12
            txt_size.init(context)
            txt_size.label = unitinfo[0]

            self.add_hint_label(context, 30)

            self._panel_action.add_widget(txt_size)
            self._panel_action.layout_widgets()
            
            txt_size.set_text_changed(self.on_input_changed)

            self.on_open_size_action(txt_size, unitinfo)
            return True

        return False

    def on_open_size_action(self, widget, unitinfo)              :
        pass

    def create_mirror(self):
        self._vertex_ctr_m .clear()

        if self.has_mirror:
            for vertex in self._vertex_ctr.vertices:
                self.add_vertex_mirror(vertex)

            if self._is_extruded:
                dir = self._extrusion * self.get_dir()
                self._vertex_ctr_m.extrude(dir)

    def on_mirror_changed(self, button):
        bpy.context.scene.mirror_primitive = button.text
        self.close_input()
        self.create_mirror()
        self.create_batch()
        self.build_actions()

    def on_operation_changed(self, button):
        bpy.context.scene.bool_mode = button.text
        self.close_input()
        self.build_actions()

    def open_operation_input(self, context, shape_action, unitinfo)              :
        if self.is_created():
            self.clear_action_panel()
            self._panel_action = BL_UI_Drag_Panel(0, 0, 120, 190)
            self._panel_action.bg_color = (0.1, 0.1, 0.1, 0.9)
            self._panel_action.init(context)

            mode = context.scene.bool_mode

            sel_col = (1.0, 0.6, 0.2, 1.0)
            hov_col = (0.2, 0.6, 0.94, 1.0)
            col = (0.3, 0.56, 0.94, 1.0)

            btn_c = BL_UI_Button(10, 10, 100, 25)
            btn_c.hover_bg_color = hov_col
            btn_c.text_size = 14
            btn_c.text = "Create"
            btn_c.bg_color = sel_col if mode == btn_c.text else col
            btn_c.set_mouse_down(self.on_operation_changed)
            btn_c.init(context)

            btn_d = BL_UI_Button(10, 45, 100, 25)
            btn_d.hover_bg_color = hov_col
            btn_d.text_size = 14
            btn_d.text = "Difference"
            btn_d.bg_color = sel_col if mode == btn_d.text else col
            btn_d.set_mouse_down(self.on_operation_changed)
            btn_d.init(context)

            btn_u = BL_UI_Button(10, 80, 100, 25)
            btn_u.hover_bg_color = hov_col
            btn_u.text_size = 14
            btn_u.text = "Union"
            btn_u.bg_color = sel_col if mode == btn_u.text else col
            btn_u.set_mouse_down(self.on_operation_changed)
            btn_u.init(context)

            btn_i = BL_UI_Button(10, 115, 100, 25)
            btn_i.hover_bg_color = hov_col
            btn_i.text_size = 14
            btn_i.text = "Intersect"
            btn_i.bg_color = sel_col if mode == btn_i.text else col
            btn_i.set_mouse_down(self.on_operation_changed)
            btn_i.init(context)

            btn_s = BL_UI_Button(10, 150, 100, 25)
            btn_s.hover_bg_color = hov_col
            btn_s.text_size = 14
            btn_s.text = "Slice"
            btn_s.bg_color = sel_col if mode == btn_s.text else col
            btn_s.set_mouse_down(self.on_operation_changed)
            btn_s.init(context)

            self._panel_action.add_widget(btn_c)
            self._panel_action.add_widget(btn_d)
            self._panel_action.add_widget(btn_u)
            self._panel_action.add_widget(btn_i)
            self._panel_action.add_widget(btn_s)

            self._panel_action.layout_widgets()
            return True
        return False

    def open_mirror_input(self, context, shape_action, unitinfo)              :
        if self.is_created():
            self.clear_action_panel()
            self._panel_action = BL_UI_Drag_Panel(0, 0, 120, 80)
            self._panel_action.bg_color = (0.1, 0.1, 0.1, 0.9)
            self._panel_action.init(context)

            mode = context.scene.mirror_primitive

            sel_col = (1.0, 0.6, 0.2, 1.0)
            hov_col = (0.2, 0.6, 0.94, 1.0)
            col = (0.3, 0.56, 0.94, 1.0)

            btn_x = BL_UI_Button(10, 10, 30, 25)
            btn_x.hover_bg_color = hov_col
            btn_x.text_size = 14
            btn_x.text = "X"
            btn_x.bg_color = sel_col if mode == btn_x.text else col
            btn_x.set_mouse_down(self.on_mirror_changed)
            btn_x.init(context)

            btn_y = BL_UI_Button(45, 10, 30, 25)
            btn_y.hover_bg_color = hov_col
            btn_y.text_size = 14
            btn_y.text = "Y"
            btn_y.bg_color = sel_col if mode == btn_y.text else col
            btn_y.set_mouse_down(self.on_mirror_changed)
            btn_y.init(context)

            btn_z = BL_UI_Button(80, 10, 30, 25)
            btn_z.hover_bg_color = hov_col
            btn_z.text_size = 14
            btn_z.text = "Z"
            btn_z.bg_color = sel_col if mode == btn_z.text else col
            btn_z.set_mouse_down(self.on_mirror_changed)
            btn_z.init(context)

            btn_n = BL_UI_Button(10, 45, 100, 25)
            btn_n.hover_bg_color = hov_col
            btn_n.text_size = 14
            btn_n.text = "None"
            btn_n.bg_color = sel_col if mode == btn_n.text else col
            btn_n.set_mouse_down(self.on_mirror_changed)
            btn_n.init(context)

            self._panel_action.add_widget(btn_x)
            self._panel_action.add_widget(btn_y)
            self._panel_action.add_widget(btn_z)
            self._panel_action.add_widget(btn_n)
            self._panel_action.layout_widgets()

            return True
        return False
    
    def open_array_input(self, context, shape_action, unitinfo) -> bool:
        if self.is_created():
            self.clear_action_panel()
            self._current_array_action = shape_action 
            self._panel_action = BL_UI_Drag_Panel(0, 0, 200, 120)
            self._panel_action.bg_color = (0.1, 0.1, 0.1, 0.9)
            self._panel_action.init(context)

            lbl_array_count = BL_UI_Label(10, 10, 60, 24)
            lbl_array_count.text = "Count:"
            lbl_array_count.text_size = 12
            lbl_array_count.init(context)

            self._slider_count = BL_UI_Slider(90, 20, 100, 24)
            self._slider_count.color = (0.3, 0.56, 0.94, 1.0)
            self._slider_count.hover_color = (0.3, 0.56, 0.94, 0.8)
            self._slider_count.min = 1
            self._slider_count.max = 20
            self._slider_count.decimals = 0
            self._slider_count.show_min_max = False
            self._slider_count.init(context)

            lbl_array_distance = BL_UI_Label(10, 48, 60, 24)
            lbl_array_distance.text = "Distance:"
            lbl_array_distance.text_size = 12
            lbl_array_distance.init(context)

            self._txt_distance = BL_UI_Textbox(90, 55, 66, 24)
            self._txt_distance.max_input_chars = 8
            self._txt_distance.is_numeric = True
            self._txt_distance.label = unitinfo[0]
            input_keys = self._txt_distance.get_input_keys()
            input_keys.remove('RET')
            input_keys.remove('ESC')

            self._txt_distance.init(context)

            unit_value = bu_to_unit(self.get_array_distance(), unitinfo[1])

            self._txt_distance.text = "{:.2f}".format(unit_value)
            self._txt_distance.set_text_changed(self.on_distance_changed)

            self.add_hint_label(context, 80)
            
            self._panel_action.add_widget(lbl_array_count)
            self._panel_action.add_widget(lbl_array_distance)
            self._panel_action.add_widget(self._slider_count)
            self._panel_action.add_widget(self._txt_distance)
            self._panel_action.layout_widgets()

            self._slider_count.set_value_change(self.on_array_count_changed)
            self._slider_count.set_value(self.get_array_count())

            return True
        return False

    def add_hint_label(self, context, y):
        lbl_hint = BL_UI_Label(10, y, 120, 24)
        lbl_hint.text = "Esc or Enter: Close"
        lbl_hint.text_size = 11
        lbl_hint.init(context)
        self._panel_action.add_widget(lbl_hint)

    def get_array_distance(self):
        if self._current_array_action is None:
            return 0.5

        return self._current_array_action.offset

    def get_array_count(self):
        count = len(self._array)
        if count == 0:
            return 1
        return count

    def on_array_count_changed(self, slider, value):
        distance = self.get_distance(self._txt_distance)
        self.create_array(value, distance)

    def create_array(self, count: int, distance: float):
        self._array.clear()
        axis = self._current_array_action.get_axis()

        for i in range(int(count)):

            # inverted rotation matrix of shape matrix
            rot_mat = self._view_context._view_mat.to_3x3().inverted()
            if axis == 'X':
                offset = rot_mat @ Vector((distance, 0, 0))
            else:
                offset = rot_mat @ Vector((0, distance, 0))     

            vc = VertexContainer()
            vc.add_from_container(self._vertex_ctr, offset * (i+1))
            
            self._array.append(vc)

        if self._is_extruded:
            self.extrude_vertices(bpy.context)

    def get_distance(self, textbox):
        value = float(textbox.text)
        unitinfo = get_current_units()
        return unit_to_bu(value, unitinfo[1])


    def on_distance_changed(self, textbox, context, event):
        distance = self.get_distance(textbox)

        self.create_array(self._slider_count.get_value(), distance)
        self._current_array_action.offset = distance

    def on_input_changed(self, textbox, context, event):
        if event == None or (event.type != "RET" and event.type != "ESC"):
            self.apply_size_action(textbox, context, False)   

        elif event.type == "ESC":
            self.close_input()
        elif event.type == "RET":
            self.apply_size_action(textbox, context)

    def close_array(self):
        for vc in self._array:
            vc.clear()

        self._array.clear()

        self._current_array_action = None

        self.close_array_widgets()

    def close_array_widgets(self):

        if self._panel_action is not None:
            self._panel_action.widgets.clear()

        self._txt_distance = None
        self._slider_count = None
        self._panel_action = None


    def close_input(self):
        self.clear_action_panel()
        self._panel_action = None

    def apply_size_action(self, widget, context, close_input = True):
        if close_input:
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
            hit, self._hit, self._normal, self._hit_face, self._hit_obj, *_ = scene.ray_cast(ray_cast_param, origin, direction)

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
        for i, v in enumerate(self._vertex_ctr.vertices):
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
        return self._vertex_ctr.vertices

    @property
    def vertices_mirror(self):
        return self._vertex_ctr_m.vertices

    @property
    def vertices_extruded_mirror(self):
        return self._vertex_ctr_m._vertices_extruded

    @property
    def vertices_2d(self):
        return self._vertices_2d

    @vertices.setter
    def vertices(self, value):
        self._vertex_ctr.vertices = value

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
        if vertex not in self._vertex_ctr.vertices:
            self._vertex_ctr.add_vertex(vertex)

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
        if vertex3d == None:
            return None

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
            self._vertex_ctr_m.add_vertex(vm)

    def reset_extrude(self):
        self._is_extruded = False
        self._vertex_ctr.clear_extrude()
        self._vertex_ctr_m.clear_extrude()

    def get_array_center_offset(self, axis):
        array_count = len(self._array)
        if array_count == 0:
            return 0

        if self._current_array_action.get_axis() != axis:
            return 0

        return (array_count / 2.0) * self._current_array_action.offset

    def array_offset(self, diff):

        self.create_batch()

        for vc in self._array:
            vc.add_offset(diff)

    def set_center(self, axis, vec_center):
     
        if axis == "N":
            face_center = get_face_center(self._hit_face, self._hit_obj)
            array_center_offset_x = self.get_array_center_offset('X')
            array_center_offset_y = self.get_array_center_offset('Y')
            
            rot_mat = self._view_context._view_mat.to_3x3()
            diff_vec = rot_mat.inverted() @ Vector((array_center_offset_x, array_center_offset_y, 0))
            face_center -= diff_vec
            vec_center.xyz = face_center.xyz
            
        else:
            rot_mat = self._view_context._view_mat.to_3x3()

            v = rot_mat @ vec_center

            array_center_offset = self.get_array_center_offset(axis)

            if axis == "X":
                v = Vector((-v[0] - array_center_offset,0,0))
            elif axis == "Y":
                v = Vector((0,-v[1] - array_center_offset,0))

            vec_center += rot_mat.inverted() @ v


    def to_center(self, axis = "N"):
        pass

    def __str__(self):
        return "Shape"

    def accept(self):
        if self.is_shape_action_active():
            self.close_array_widgets()

    def reset(self):
        
        if not self.is_shape_action_active():
            self._vertex_ctr.clear()
            self._vertex_ctr_m.clear()
            self._vertices_2d.clear()
            
            self._shape_actions.clear()
            self.state = ShapeState.NONE
            self.create_batch()

        self.close_array()

    def close(self):
        return False

    def connect_to_mouse_pos(self, mouse_pos):
        return None

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

    def can_convert_to_mesh(self):
        return self.is_created()

    def can_create_from_mesh(self):
        return self.is_none()

    def create_from_mesh(self, context):
        return False

    def vertices_3d_offset(self, vec_offset):
        self._vertex_ctr.add_offset(vec_offset)
        # for vertex_3d in self._vertices:
        #     vertex_3d += vec_offset

    def vertex_3d_to_2d(self, context, v3d):

        rv3d = context.space_data.region_3d
        region = context.region
        return location_3d_to_region_2d(region, rv3d, v3d)       

    def vertices_3d_to_2d(self, context):
        for index, vertex_3d in enumerate(self._vertex_ctr.vertices):
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
        if not self.is_created():
            return False

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

        self._vertex_ctr.extrude(dir)

        # Extrude vertices of array
        for vc in self._array:
            vc.extrude(dir)

        self._vertex_ctr_m.extrude(dir)

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
            mpos_3d = region_2d_to_location_3d(region, rv3d, mxy, self._vertex_ctr.first_vertex)

            isect_pt, length = intersect_point_line(
                mpos_3d,
                self._vertex_ctr.first_vertex,
                self._vertex_ctr.first_vertex + dir)

            self._extrusion = length

            self.extrude_vertices(context)
            return True

        if self._vertex_moving is not None:
            self._vertex_ctr.vertices[self._vertex_moving] = mouse_pos_3d
            self.vertex_moved(context)
            return True

        if self.is_created() and self._is_moving:
            diff = mouse_pos_3d - self._move_offset
            self._vertex_ctr.add_offset(diff)

            for vc in self._array:
                vc.add_offset(diff)

            if self.has_mirror:
                diff_m = self.get_mirror_diff(diff)
                self._vertex_ctr_m.add_offset(diff_m)

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

    def get_point_size(self, context):
        return 10