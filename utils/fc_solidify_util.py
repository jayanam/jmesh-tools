import bpy
from bpy.props import *

def execute_solidify(obj):

  bpy.context.view_layer.objects.active = obj

  # Apply the scale before solidify
  bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)

  # Add a new bevel modifier
  bpy.ops.object.modifier_add(type = 'SOLIDIFY')
  mod_solid = obj.modifiers[-1]
  mod_solid.use_even_offset = True

  bpy.ops.object.modifier_move_to_index(modifier=mod_solid.name, index=0)