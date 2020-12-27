import gpu
from gpu_extras.batch import batch_for_shader

class Shape_Action:

  def __init__(self):
    self._shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
    self.set_position(0, 0)

  def mouse_down(self, context, event, mouse_pos_2d, mouse_pos_3d) -> bool:
    x = mouse_pos_2d[0]
    y = mouse_pos_2d[1]

    if x >= self._x and x <= self._x + 14 and y <= self._y and y >= self._y - 14:
      return True

    return False

  def get_position(self):
    return (self._x, self._y)

  def set_position(self, x, y):
    self._x = x
    self._y = y

  def draw(self):
    pass

class Shape_Size_Action(Shape_Action):

    def draw(self):
      self._shader.bind()
      self._shader.uniform_float("color", (0.9, 0.0, 0.0, 1.0))
      self._batch.draw(self._shader)

    def set_position(self, x, y):
      super().set_position(x, y)

      x_r = x + 14
      y_r = y - 14

      indices = ((0, 1, 2), (2, 0, 3))
      coords_middle = [(x, y - 7), (x + 7,  y_r), (x_r, y - 7), (x + 7, y)]
      self._batch = batch_for_shader(self._shader, 'TRIS', {"pos" : coords_middle}, indices=indices)

class Shape_Array_Action(Shape_Action):

  def __init__(self, axis = 'y'):
    self._axis = axis
    super().__init__()

  def get_axis(self):
    return self._axis
    
  def draw(self):
    self._shader.bind()
    self._shader.uniform_float("color", (1.0, 0.2, 0.0, 1.0))
    self._batch.draw(self._shader)

  def set_position(self, x, y):
    super().set_position(x, y)

    x_r = x + 11
    y_b = y - 11

    lines = []

    if self._axis == 'y':
      for i in range(1, 5):
        lines.append((x,   y + 2 - (i * 3)))
        lines.append((x_r, y + 2 - (i * 3)))
    else:
      for i in range(1, 5):
        lines.append((x + (i * 3),   y))
        lines.append((x + (i * 3), y_b))

    self._batch = batch_for_shader(self._shader, 'LINES', {"pos": lines})
