import bpy
import gpu

def get_builtin_shader(shader, pre):
  if bpy.app.version >= (4, 0, 0):
    return gpu.shader.from_builtin(shader)
  else:
    return gpu.shader.from_builtin(pre + '_' + shader)