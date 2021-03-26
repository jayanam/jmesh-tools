import bgl
import gpu

from gpu_extras.batch import batch_for_shader

class Shape_Gizmo:

  def __init__(self):
    self.__is_drag = False    
    self.shader_2d = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

  def get_axis(self, x, y):
    gp = self.shape.get_gizmo_pos()

    if gp is not None:
      if x >= gp[0] and x <= gp[0] + 15 and y <= gp[1] + 15 and y >= gp[1]:
        return "Y"

      elif x >= gp[0] + 15 and x <= gp[0] + 30 and y <= gp[1] and y >= gp[1] - 15:
        return "X"

      elif x >= gp[0] and x <= gp[0] + 14 and y <= gp[1] and y >= gp[1] - 15:
        return "N"

    return None

  def mouse_down(self, context, event, mouse_pos_2d, mouse_pos_3d): 
    axis = self.get_axis(mouse_pos_2d[0], mouse_pos_2d[1])
    if axis is not None:

      # If control key is pressed then try to center the primitive
      if event.ctrl:
        self.shape.to_center(axis)
        return True
      else:
        self.__is_drag = True  
        self.shape.start_move(mouse_pos_3d)
        self.shape.set_move_axis(axis)
        return True
    
    return False
    
  def mouse_up(self, context, mouse_pos_2d):  
    
    if self.__is_drag:
      self.shape.stop_move(context)
      self.__is_drag = False

  def is_dragging(self):
    return self.__is_drag

  def draw(self, shape):
    self.shape = shape
    gizmo_pos = self.shape.get_gizmo_pos()

    if gizmo_pos is None:
      return

    x = gizmo_pos[0]
    y = gizmo_pos[1]

    x_r = x + 15
    y_r = y - 15

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glEnable(bgl.GL_LINE_SMOOTH)
    bgl.glEnable(bgl.GL_POLYGON_SMOOTH)

    self.shader_2d.bind()

    #    /\
    #    -- 
    coords_up = [(x, y), (x + 7,  y + 15), (x + 15, y)]
    batch_gizmo_up = batch_for_shader(self.shader_2d, 'TRIS', {"pos" : coords_up })

    self.shader_2d.uniform_float("color", (0.3, 0.56, 0.94, 1.0))
    batch_gizmo_up.draw(self.shader_2d)

    #    |\
    #    |/ 
    coords_right = [(x_r, y_r), (x_r + 15,  y_r + 7), (x_r, y_r + 15)]
    batch_gizmo_right = batch_for_shader(self.shader_2d, 'TRIS', {"pos" : coords_right})

    self.shader_2d.uniform_float("color", (0.51, 0.78, 0.17, 1.0))
    batch_gizmo_right.draw(self.shader_2d)

    #   0  1
    #   ----
    #   |  |
    #   ----
    #   2  3
    indices = ((0, 1, 2), (2, 1, 3))
    coords_middle = [(x + 1, y_r + 1), (x_r - 1,  y_r + 1), (x + 1, y_r + 14), (x_r - 1, y_r + 14)]
    batch_gizmo_middle = batch_for_shader(self.shader_2d, 'TRIS', {"pos" : coords_middle}, indices=indices)

    self.shader_2d.uniform_float("color", (0.9, 0.9, 0.9, 1.0))
    batch_gizmo_middle.draw(self.shader_2d)

    bgl.glDisable(bgl.GL_POLYGON_SMOOTH)
    bgl.glDisable(bgl.GL_LINE_SMOOTH)
    bgl.glDisable(bgl.GL_BLEND)
