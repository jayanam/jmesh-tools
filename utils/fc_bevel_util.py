import bpy
from bpy.props import *

def try_find_bevel_op(bevel_objects):
    for bevel_obj in bevel_objects:
        bevel_mod = bevel_obj.modifiers.get("Bevel")
        if(bevel_mod is not None):
            return bevel_mod
    return None


def execute_bevel(bevel_objects):
    if len(bevel_objects) == 0:
        return

    # Default value for bevel
    width = 0.01

    bevel_op = try_find_bevel_op(bevel_objects)
    if(bevel_op is not None):
        width = bevel_op.width

    for target_obj in bevel_objects:

        bpy.context.view_layer.objects.active = target_obj
        
        # Apply the scale before beveling
        bpy.ops.object.transform_apply(scale=True)
        
        # Set smooth shading for the target object
        bpy.ops.object.shade_smooth()
        
        # Set the data to autosmooth
        bpy.context.object.data.use_auto_smooth = True
        bpy.context.object.data.auto_smooth_angle = 1.0472
        
        # Remove the bevel modifier if exists
        modifier_to_remove = target_obj.modifiers.get("Bevel")
        if(modifier_to_remove is not None):
            target_obj.modifiers.remove(modifier_to_remove)
            
        # Add a new bevel modifier
        bpy.ops.object.modifier_add(type = 'BEVEL')

        # get the last added modifier
        bevel = target_obj.modifiers[-1]
        bevel.limit_method = 'WEIGHT'
        #bevel.edge_weight_method = 'LARGEST'
        bevel.use_clamp_overlap = False
        bevel.width = width
        bevel.segments = 3
        bevel.profile = 0.7
        
        # switch to edit mode and select sharp edges
        bpy.ops.object.editmode_toggle()
        
        bpy.context.tool_settings.mesh_select_mode = (False, True, False)

        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.edges_select_sharp()
        
        # Mark edges as sharp
        bpy.ops.mesh.mark_sharp()
        bpy.ops.transform.edge_bevelweight(value=1)

        # Back to object mode
        bpy.ops.object.editmode_toggle()