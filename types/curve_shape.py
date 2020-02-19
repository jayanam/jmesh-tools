from .shape import *

class Curve_Shape(Shape):

    def __init__(self):
        super().__init__()
        self._normals = [None, None]

    def can_close(self):
        return len(self._vertices) >= 2

    def close(self):
            
        if self.can_close():
            self.state = ShapeState.CREATED
            return True
            
        return False

    def connected_shape(self):
        return False

    def get_vertices_copy(self, mouse_pos = None):
        result = self._vertices.copy()

        if mouse_pos is not None and self.is_processing():
            result.append(mouse_pos)

        return result

    def get_cuts(self):
        return len(self._vertices_2d) - 2

    def get_start_point(self):
        if(self.is_created()):
            return self._vertices[0]
        return None

    def get_end_point(self):
        if(self.is_created()):
            return self._vertices[-1]
        return None

    def get_points(self):
        return self._vertices

    def get_normal_start(self):
        return self._normals[0]

    def get_normal_end(self):
        return self._normals[1]

    def handle_mouse_press(self, mouse_pos_2d, mouse_pos_3d, event, context):

        if mouse_pos_3d is None or mouse_pos_2d is None:
            return False

        scene = context.scene
        region = context.region
        region3D = context.space_data.region_3d

        view_vector = region_2d_to_vector_3d(region,   region3D, mouse_pos_2d)
        origin      = region_2d_to_origin_3d(region,   region3D, mouse_pos_2d)

        # Get intersection with objects
        hit, loc_hit, normal, face, *_ = scene.ray_cast(context.view_layer, origin, view_vector)
        if hit:
            mouse_pos_3d = loc_hit

        if self.is_none() and event.ctrl:

            # Set startpoint
            self.add_vertex(mouse_pos_3d)
            self._vertices_2d.append(get_2d_vertex(context, mouse_pos_3d))
            self.state = ShapeState.PROCESSING
            self._normals[0] = normal

        elif self.is_processing() and not event.ctrl and not self.is_2_points_input():
            self.add_vertex(mouse_pos_3d)
            self._vertices_2d.append(get_2d_vertex(context, mouse_pos_3d))          

        elif self.is_processing() and event.ctrl:

            # Set end point
            self.add_vertex(mouse_pos_3d)
            self._vertices_2d.append(get_2d_vertex(context, mouse_pos_3d))
            self._normals[1] = normal
            return self.close()

        return False

    def handle_mouse_move(self, mouse_pos_2d, mouse_pos_3d, event, context):

        if self.is_processing():
            return True

        result = super().handle_mouse_move(mouse_pos_2d, mouse_pos_3d, event, context)

        return result

    def is_2_points_input(self):
        return bpy.context.scene.curve_input_method == "2-Points"

    def set_next_input_method(self, context):
        context.scene.curve_input_method = next_enum(context.scene.curve_input_method, 
                                                    context.scene, "curve_input_method")

    def build_actions(self):
        curve_2_points = self.is_2_points_input()
        input_method = bpy.context.scene.curve_input_method

        super().build_actions()
        bool_mode = bpy.context.scene.bool_mode
        self.add_action(Action(self.get_prim_id(),  "Primitive",          "Curve"),  None)
        self.add_action(Action("I",                 "Input",       input_method), None)

        self.add_action(Action("Ctrl + Left Click", "Set Startpoint",     ""),       ShapeState.NONE)

        if not curve_2_points:
            self.add_action(Action("Left Click", "Add Point",       ""),       ShapeState.PROCESSING)

        self.add_action(Action("Ctrl + Left Click", "Set Endpoint",       ""),       ShapeState.PROCESSING)
        self.add_action(Action("Esc",               self.get_esc_title(), ""),       None)