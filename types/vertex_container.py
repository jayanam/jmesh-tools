import gpu
from gpu_extras.batch import batch_for_shader

from mathutils import Vector
from .. utils.shader_utils import *

class VertexContainer:

  def __init__(self):
    self._shader = get_builtin_shader('UNIFORM_COLOR', '3D')
    self._vertices = []
    self._vertices_2d = []
    self._vertices_extruded = []

  def create_batch(self, mouse_pos = None):
    
    verts = self.vertices_copy

    if mouse_pos != None:
      verts.append(mouse_pos)

    self._batch = batch_for_shader(self._shader, 'LINE_LOOP', {"pos": verts})
    self._batch_points = batch_for_shader(self._shader, 'POINTS', {"pos": verts})

    extrude_lines = []
    for index, vertex in enumerate(self._vertices_extruded):
      extrude_lines.append(self._vertices[index])
      extrude_lines.append(vertex)

    self._batch_extruded = batch_for_shader(self._shader, 'LINE_LOOP', {"pos": self._vertices_extruded})
    self._batch_lines_extruded = batch_for_shader(self._shader, 'LINES', {"pos": extrude_lines})

  def draw(self):
    self._shader.bind()

    # Draw lines
    gpu.state.blend_set('ALPHA')

    self._shader.uniform_float("color", (0.2, 0.5, 0.8, 1.0))
    gpu.state.line_width_set(2)
    self._batch_extruded.draw(self._shader)

    gpu.state.line_width_set(1)
    self._batch_lines_extruded.draw(self._shader)

    gpu.state.line_width_set(3)
    self._shader.uniform_float("color", (0.1, 0.3, 0.7, 1.0))
    self._batch.draw(self._shader)
    self._batch_points.draw(self._shader)

    gpu.state.blend_set('NONE')

  def draw_points(self):
    self._batch_points.draw(self._shader)  

  def add_vertex(self, vertex: Vector):
    self._vertices.append(vertex)

  def extrude(self, dir):
    extr_count = len(self._vertices_extruded)

    for index, vertex3d in enumerate(self._vertices):
        if index >= extr_count:
            self._vertices_extruded.append(vertex3d + dir)
        else:
            self._vertices_extruded[index] = vertex3d + dir

    self.create_batch()

  def clear_3d(self):
    self._vertices.clear()
    self._vertices_extruded.clear()
    self.create_batch()

  def clear_extrude(self):
    self._vertices_extruded.clear()
    self.create_batch()

  def add_offset(self, vec_offset):

    for vec in self._vertices:
      vec += vec_offset

    for vec in self._vertices_extruded:
      vec += vec_offset

    self.create_batch()

  def add_vertices(self, vertices, offset=Vector((0.5, 0, 0))):
    for vec in vertices:
      v2 = vec + offset
      self.add_vertex(v2)

  def add_from_container(self, vertex_ctr, offset=Vector((0.5, 0, 0))):
    self.add_vertices(vertex_ctr.vertices, offset)
    self.create_batch()

  def clear(self):
    self._vertices.clear()
    self._vertices_extruded.clear()
    self._vertices_2d.clear()
    self.create_batch()

  @property
  def first_vertex(self):
      if len(self._vertices) > 0:
        return self._vertices[0]
      return None

  @property
  def last_vertex(self):
      if len(self._vertices) > 0:
        return self._vertices[-1]
      return None

  @property
  def vertex_count(self):
      return len(self._vertices)

  @property
  def vertices(self):
      return self._vertices

  @property
  def vertices_2d(self):
      return self._vertices_2d

  @vertices_2d.setter
  def vertices_2d(self, value):
      self._vertices_2d = value

  @property
  def vertices_copy(self):
      return self._vertices.copy()

  @vertices.setter
  def vertices(self, value):
      self._vertices = value

  def __str__(self):
    return str(self._vertices)