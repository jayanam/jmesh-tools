class Shape_Action:

  def __init__(self, tag):
    self.shader_2d = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    self._tag = tag
    self._x = 0
    self._y = 0

  def mouse_down(self, context, event, mouse_pos_2d, mouse_pos_3d) -> bool:
    return True

  def draw(self):

    self.shader_2d.bind()

    x = gizmo_pos[0]
    y = gizmo_pos[1]

    x_r = x + 15
    y_r = y - 15

    indices = ((0, 1, 2), (2, 1, 3))
    coords_middle = [(x + 1, y_r + 1), (x_r - 1,  y_r + 1), (x + 1, y_r + 14), (x_r - 1, y_r + 14)]
    batch_gizmo_middle = batch_for_shader(self.shader_2d, 'TRIS', {"pos" : coords_middle}, indices=indices)

    self.shader_2d.uniform_float("color", (0.9, 0.9, 0.9, 1.0))
    batch_gizmo_middle.draw(self.shader_2d)