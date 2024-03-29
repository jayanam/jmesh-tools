import bpy
from bpy.props import *

from . fc_bevel_util import *

import bmesh

def can_apply_bool(obj, context):
    target = context.scene.carver_target
    if target is None:
        return False
 
    bool_mod = target.modifiers.get("FC_BOOL")
    if bool_mod is None:
        return False
    
    if bool_mod.object != obj:
        return False

    return True
    

def select_active(obj):

    bpy.ops.object.select_all(action='DESELECT')
    
    # API change 2.8: obj.select = True
    obj.select_set(state=True)
    
    # API change 2.8: bpy.context.scene.objects.active = obj
    bpy.context.view_layer.objects.active = obj
    
def is_apply_immediate():
    return (bpy.context.scene.apply_bool == True)

def is_delete_after_apply():
    return (bpy.context.scene.delete_on_apply == True)

def is_self_intersect():
    return (bpy.context.scene.self_intersect == True)

def is_hole_tolerant():
    return (bpy.context.scene.hole_tolerant == True)

def recalc_normals(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.clear()
    mesh.update()
    bm.free()

def get_bool_mode_id(bool_name):
    if bool_name == "Difference":
        return 0
    elif bool_name == "Union":
        return 1
    elif bool_name == "Intersect":
        return 2
    elif bool_name == "Slice":
        return 3
    return -1

def bool_mod_and_apply(obj, bool_method, allow_delete = True):
    
    active_obj = bpy.context.active_object
    
    bool_mod = active_obj.modifiers.new(type="BOOLEAN", name="FC_BOOL")
    
    method = 'DIFFERENCE'
    
    if bool_method == 1:
        method = 'UNION'
    elif bool_method == 2:
        method = 'INTERSECT'
    
    bool_mod.operation = method

    if bpy.app.version >= (3, 0, 0):
        bool_mod.use_self = is_self_intersect()
        bool_mod.use_hole_tolerant = is_hole_tolerant()

    bool_mod.object = obj

    recalc_normals(obj.data)
    
    if is_apply_immediate():
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        if has_bevel_mod(active_obj):
            bpy.ops.object.shade_smooth()

        if is_delete_after_apply() and allow_delete:
            select_active(obj)
            bpy.ops.object.delete()
            return True

    else:  
        if bool_method == 0 or bool_method == 2:
            obj.display_type = 'WIRE'

    return False


def execute_slice_op(context, target_obj):
     
    # store active object
    current_obj = context.active_object
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)
    
    # clone target
    select_active(target_obj)  
    
    bpy.ops.object.duplicate(linked=True)
    
    clone_target = bpy.context.view_layer.objects.active
    
    # Intersect for clone     
    bpy.ops.object.make_single_user(object=True, obdata=True)
    
    bool_mod_and_apply(current_obj, 2, False)
        
    # Difference for target
    select_active(target_obj)
    bpy.ops.object.make_single_user(object=False, obdata=True)
            
    if not bool_mod_and_apply(current_obj, 0):
        select_active(current_obj)

def union_selected(context):
    active_obj = bpy.context.active_object
    for obj in context.selected_objects:
        if obj is not active_obj:          
            bool_mod = active_obj.modifiers.new(type="BOOLEAN", name="FC_BOOL")
            
            bool_mod.operation = 'UNION'
            bool_mod.object = obj

            recalc_normals(obj.data)
            
            bpy.ops.object.modifier_apply(modifier=bool_mod.name)

            select_active(obj)
            bpy.ops.object.delete()
            select_active(active_obj)
    
    
def execute_boolean_op(context, target_obj, bool_method = 0):
    
    '''
    function for bool operation
    @target_obj : target object of the bool operation
    @bool_method : 0 = difference, 1 = union, 2 = intersect  
    '''

    # store active object
    current_obj = context.object
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)
    
    # make target the active object
    select_active(target_obj)
        
    if not bool_mod_and_apply(current_obj, bool_method):
        select_active(current_obj)