from .shape import *

class Circle_Shape(Shape):

    def __init__(self):
        super().__init__()
        self._center = None
        self._radius = 0
        self._mouse_start_3d = None
        self._segments = 32       

    def __str__(self):
        return "Circle"

    def open_size_input(self, context, shape_action, unitinfo) -> bool:
        if super().open_size_input(context, shape_action, unitinfo):
            unit_value = bu_to_unit(self._radius, unitinfo[1])

            self._input_size.text = "{:.2f}".format(unit_value)
            return True

        return False

    def apply_input(self, context):
        value = float(self._input_size.text)
        unitinfo = get_current_units()

        self.set_size(context, unit_to_bu(value, unitinfo[1]))

        super().apply_input(context)

    def handle_mouse_wheel(self, inc, context):
        if self.is_processing():
            self._segments += inc
            if self._segments < 3:
                self._segments = 3

            self.build_actions()
            self.create_circle(context)
            return True

        return False

    def start_size(self, mouse_pos):

        if super().start_size(mouse_pos):
            self._mouse_start_3d = mouse_pos
            return True
        return False

    def set_size(self, context, radius):
        self._radius = radius
        
        self.create_circle(context)  

        array_count = len(self._array)
        if array_count > 0:
            self.create_array(array_count, self._current_array_action.offset)     

    def handle_mouse_move(self, mouse_pos_2d, mouse_pos_3d, event, context):

        if self.is_processing() or self._is_sizing:

            # Distance center to mouse pos
            self.set_size(context, (self._mouse_start_3d - mouse_pos_3d).length)

            return True

        if self.is_moving():
            diff = mouse_pos_3d - self._move_offset
            self._center += diff
            self._mouse_start_3d = self._center.copy()

        result = super().handle_mouse_move(mouse_pos_2d, mouse_pos_3d, event, context)

        return result


    def create_circle(self, context):

        from mathutils import Matrix

        rv3d      = context.space_data.region_3d
        view_rot  = rv3d.view_rotation

        segments = self._segments + 1
        mul = (1.0 / (segments - 1)) * (pi * 2)
        points = [(sin(i * mul) * self._radius, cos(i * mul) * self._radius, 0) 
        for i in range(segments-1)]

        rot_mat = view_rot

        offset = Vector()
        if self._snap_to_target and self._normal != None:

            # Use inverted matrix of shape instead of to_track_quat
            rot_mat = self._view_context._view_mat.to_3x3().inverted()
            
            # rot_mat = self._normal.to_track_quat('Z', 'X').to_matrix()
            offset = self._normal.normalized() * context.scene.snap_offset

        self._vertices = [rot_mat @ Vector(point) + 
                          self._center + offset for point in points]

        if self.has_mirror:
            self._vertices_m.clear()
            for v in self._vertices:
                self.add_vertex_mirror(v)

        self._vertices_2d = [get_2d_vertex(context, vertex) for vertex in self._vertices]

    def handle_mouse_press(self, mouse_pos_2d, mouse_pos_3d, event, context):

        if mouse_pos_3d is None:
            return False

        if self.is_none() and event.ctrl:

            self._center = self.get_center(mouse_pos_3d, context)

            self._mouse_start_3d = mouse_pos_3d.copy()

            self.state = ShapeState.PROCESSING
            return False

        elif self.is_processing():

            self.state = ShapeState.CREATED

            self.add_shape_action(Shape_Size_Action())

            self.add_shape_action(Shape_Array_Action("X"))

            self.add_shape_action(Shape_Array_Action())
            
            self.start_extrude_immediate(mouse_pos_2d, mouse_pos_3d, context)
            return False

        elif self.is_created() and event.ctrl:
            return True

        return False

    def get_gizmo_anchor_vertex(self):
        return self._center

    def get_gizmo_pos(self):
        if self.is_created():
            rv3d = self._view_context.region_3d
            region = self._view_context.region
            pos_2d = location_3d_to_region_2d(region, rv3d, self.get_gizmo_anchor_vertex())

            return pos_2d

        return None

    def to_center(self, axis):

        old_center = self._center.copy()

        self.set_center(axis, self._center)
        self.create_circle(bpy.context)

        # Bring the array to the center as well
        self.array_offset(self._center - old_center)

    def draw_text(self):
        if self.is_processing() or self.is_sizing():
            self.init_text()
            
            rv3d = self._view_context.region_3d
            region = self._view_context.region
            pos_text = location_3d_to_region_2d(region, rv3d, self._center)

            blf.position(2, pos_text[0] + 16, pos_text[1] + 5, 0)
            blf.draw(2, "r: {0:.3f}".format(self._radius))

    def get_point_size(self, context):
        if self._radius <= 0.2:
            return 3
        elif self._radius <= 0.3:
            return 5
        elif self._radius <= 0.5:
            return 7
        else:
            return super().get_point_size(context)
        
    def can_set_center_type(self):
        return True

    def build_actions(self):
        super().build_actions()
        bool_mode = bpy.context.scene.bool_mode
        center_type = bpy.context.scene.center_type

        self.add_action(Action(self.get_prim_id(),  "Primitive",          "Circle"),    None)
        self.add_action(Action("O",                 "Operation",          bool_mode),   None)

        mirror_type = bpy.context.scene.mirror_primitive
        self.add_action(Action("M",                 "Mirror",             mirror_type),    ShapeState.NONE)

        self.add_action(Action("S",                 "Scale",               ""),          ShapeState.CREATED)
        self.build_move_action()
        self.build_extrude_action()
        self.add_action(Action("C",                 "Startpos",             center_type), ShapeState.NONE)
        self.add_action(Action("Mouse wheel",       "Segments",           str(self._segments)), ShapeState.PROCESSING)
        self.add_action(Action("Left Click",        "Create",             ""),          ShapeState.PROCESSING)
        self.add_action(Action("Ctrl + Left Click", "Start",              ""),          ShapeState.NONE)
        self.add_action(Action("Ctrl + Left Click", "Apply",              ""),          ShapeState.CREATED)
        self.add_action(Action("Left Drag",         "Move points",        ""),          ShapeState.CREATED)
        self.add_action(Action("Alt + M",           "To Mesh",            ""),          ShapeState.CREATED)
        self.add_action(Action("Alt + M",           "From Mesh",          ""),          ShapeState.NONE)
        self.add_action(Action("Esc",               self.get_esc_title(), ""),          None)