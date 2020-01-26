from .shape import *
from ..utils.fc_view_3d_utils import get_view_direction_by_rot_matrix, get_3d_vertex_for_2d

class Rectangle_Shape(Shape):
    
    def __init__(self):
        super().__init__() 
        self._vertex1 = None
        self._vertex3 = None
        self._vertices_2d = [None, None, None, None]
        self._center_2d = None


    def can_start_from_center(self):
        return True

    def handle_mouse_press(self, mouse_pos_2d, mouse_pos_3d, event, context):

        if mouse_pos_3d is None:
            return False

        if self.is_none() and event.ctrl:

            if self.get_start_from_center(context):

                self._center_2d = mouse_pos_2d

            else:

                self._vertices_2d[0] = mouse_pos_2d

                self._vertex1 = mouse_pos_3d

            self.state = ShapeState.PROCESSING
            return False

        elif self.is_processing():
            self.state = ShapeState.CREATED
            return False

        elif self.is_created() and event.ctrl:
            return True

        return False

    def handle_mouse_move(self, mouse_pos_2d, mouse_pos_3d, event, context):

        if self.is_processing():

            # 0-------------1
            # |             |
            # 3-------------2

            if self.get_start_from_center(context):

                cx = self._center_2d[0]
                cy = self._center_2d[1]
                w = mouse_pos_2d[0] - cx
                h = mouse_pos_2d[1] - cy

                self._vertices_2d[0] = (cx - w, cy + h)
                self._vertices_2d[1] = (cx + w, cy + h)
                self._vertices_2d[2] = (cx + w, cy - h)
                self._vertices_2d[3] = (cx - w, cy - h)
                

            else:
                self._vertex3 = mouse_pos_3d
                self._vertices_2d[2] = mouse_pos_2d

                self._vertices_2d[1] = (self._vertices_2d[0][0], self._vertices_2d[2][1])
                self._vertices_2d[3] = (self._vertices_2d[2][0], self._vertices_2d[0][1])

                self.calc_center_2d()
 
            self.create_rect(context)
            return True

        result = super().handle_mouse_move(mouse_pos_2d, mouse_pos_3d, event, context)

        return result

    def calc_center_2d(self):

        self._center_2d = (self._vertices_2d[0][0] +  (self._vertices_2d[3][0] - self._vertices_2d[0][0]) / 2, 
                            self._vertices_2d[0][1] +  (self._vertices_2d[1][1] - self._vertices_2d[0][1]) / 2)


    def stop_move(self, context):
        super().stop_move(context)

        self.calc_center_2d()


    def create_rect(self, context):
        rv3d      = context.space_data.region_3d
        view_rot  = rv3d.view_rotation

        self._vertices.clear()

        # get missing 3d vertices
        if self._snap_to_target and self._normal != None:
            self._vertex1 = self.get_3d_for_2d(self._vertices_2d[0], context)

            vertex2 = self.get_3d_for_2d(self._vertices_2d[1], context)
            
            self._vertex3 = self.get_3d_for_2d(self._vertices_2d[2], context)
            vertex4 = self.get_3d_for_2d(self._vertices_2d[3], context)  
        else:
            self._vertex1 = get_3d_vertex(context, self._vertices_2d[0])
            vertex2 = get_3d_vertex(context, self._vertices_2d[1])
            self._vertex3 = get_3d_vertex(context, self._vertices_2d[2])
            vertex4 = get_3d_vertex(context, self._vertices_2d[3])
        
        self._vertices.extend([self._vertex1, vertex2, self._vertex3, vertex4])
        
    def start_rotate(self, mouse_pos, context):
        if self.is_created():
           
            tmp_vertices_2d = []
            ox = self._center_2d[0]
            oy = self._center_2d[1]

            for i, vertex2d in enumerate(self._vertices_2d):
                px = vertex2d[0]
                py = vertex2d[1]

                # 15 degree steps (TODO: parametrize?)
                angle = radians(15)
               
                x = ox + cos(angle) * (px - ox) - sin(angle) * (py - oy)
                y = oy + sin(angle) * (px - ox) + cos(angle) * (py - oy)

                tmp_vertices_2d.append((x,y))
                
                if not self._snap_to_target:
                    direction = get_view_direction_by_rot_matrix(self._view_context.view_rotation) * context.scene.draw_distance
                    self._vertices[i] = get_3d_vertex_for_2d(self._view_context, (x,y), -direction)
                else:
                    self._vertices[i] = self.get_3d_for_2d((x,y), context) 
            
            self._vertices_2d = tmp_vertices_2d

            return True
        
        return False

    def get_width(self):
        return (self._vertices[0] - self._vertices[3]).length

    def get_height(self):
        return (self._vertices[0] - self._vertices[1]).length

    def draw_text(self):
        if self.is_processing():
            
            if self._vertices_2d[1] is not None:
                self.init_text()

                x = self._vertices_2d[1][0]
                y = self._vertices_2d[1][1]

                blf.position(2, x, y - 25, 0)
                blf.draw(2, "Width: {0:.3f} | Height: {1:.3f}".format(self.get_width(), self.get_height()))

    def build_actions(self):
        super().build_actions()
        bool_mode = bpy.context.scene.bool_mode

        from_center = "Yes"

        if not bpy.context.scene.start_center:
            from_center = "No"

        self.add_action(Action(self.get_prim_id(),  "Primitive",          "Rectangle"), None)
        self.add_action(Action("O",                 "Operation",           bool_mode),   None)
        self.build_move_action()
        self.add_action(Action("R",                 "Rotate",             ""),          ShapeState.CREATED)
        self.add_action(Action("E",                 "Extrude",            ""),          ShapeState.CREATED)
        self.add_action(Action("F",                 "From Center", from_center),        ShapeState.NONE)
        self.add_action(Action("Left Click",        "Set 2nd point",      ""),          ShapeState.PROCESSING)
        self.add_action(Action("Ctrl + Left Click", "Start",              ""),          ShapeState.NONE)
        self.add_action(Action("Ctrl + Left Click", "Apply",              ""),          ShapeState.CREATED)
        self.add_action(Action("Left Drag",         "Move points",        ""),          ShapeState.CREATED)
        self.add_action(Action("Esc",               self.get_esc_title(), ""),          None)