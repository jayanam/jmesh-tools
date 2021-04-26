import bpy
from bpy.props import *
import bmesh

def execute_cloth(obj):

  bpy.context.view_layer.objects.active = obj

  bpy.ops.object.shade_smooth()

  # Apply the scale before solidify
  bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)

  # Add a new cloth modifier
  bpy.ops.object.modifier_add(type = 'CLOTH')
  mod_cloth = obj.modifiers[-1]

  # Add pressure
  mod_cloth.settings.use_pressure = True

  mod_cloth.settings.uniform_pressure_force = 12
  mod_cloth.settings.pressure_factor = 1
  mod_cloth.settings.shrink_min = -0.4

  # Add outline as pin group
  vg_name = "JM_Pin_Cloth"
  mod_cloth.settings.vertex_group_mass = vg_name
  v_group = obj.vertex_groups.new( name = vg_name)

  bpy.ops.object.mode_set(mode='EDIT', toggle=False)

  vertices = []

  bm = bmesh.from_edit_mesh(obj.data)
  bm.verts.ensure_lookup_table()

  vert = bm.verts[0]
  prev = None

  for i in range(len(bm.verts)):
      next = None
      for v in [e.other_vert(vert) for e in vert.link_edges if e.is_boundary]:
          if (v != prev):
              next = v

      vertices.append(vert.index)

      if next == None:
          break
      
      prev, vert = vert, next
 
  bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

  v_group.add( vertices, 1.0, 'REPLACE' )