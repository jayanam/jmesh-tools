import bpy
from bpy.types import Operator

from .utils.fc_bool_util import execute_boolean_op, execute_slice_op

def check_cutter_selected(context):
    result = len(context.selected_objects) > 0
    result = result and not bpy.context.scene.carver_target is None
    result = result and not (bpy.context.scene.carver_target == context.view_layer.objects.active)
    return result
    
# Difference operator
class FC_BoolOperator_Diff(Operator):
    bl_idname = "object.bool_diff"
    bl_label = "Bool difference"
    bl_description = "Difference for 2 selected objects" 
    bl_options = {'REGISTER', 'UNDO'} 
        
    @classmethod
    def poll(cls, context):
        return check_cutter_selected(context)
        
    def execute(self, context):
        try:
            target_obj = bpy.context.scene.carver_target
        
            execute_boolean_op(context, target_obj, 0)

        except RuntimeError:
            pass

        return {'FINISHED'}
    
class FC_BoolOperator_Union(Operator):
    bl_idname = "object.bool_union"
    bl_label = "Bool union"
    bl_description = "Union for 2 selected objects" 
    bl_options = {'REGISTER', 'UNDO'} 
         
    @classmethod
    def poll(cls, context):
        return check_cutter_selected(context)
       
    def execute(self, context):
        try:
            target_obj = bpy.context.scene.carver_target
            
            execute_boolean_op(context, target_obj, 1)
        except RuntimeError:
            pass
        return {'FINISHED'}

class FC_BoolOperator_Intersect(Operator):
    bl_idname = "object.bool_intersect"
    bl_label = "Bool intersect"
    bl_description = "Intersect for 2 selected objects" 
    bl_options = {'REGISTER', 'UNDO'} 
         
    @classmethod
    def poll(cls, context):
        return check_cutter_selected(context)
       
    def execute(self, context):
        try:
            target_obj = bpy.context.scene.carver_target
        
            execute_boolean_op(context, target_obj, 2)
        except RuntimeError:
            pass

        return {'FINISHED'}

class FC_BoolOperator_Slice(Operator):
    bl_idname = "object.bool_slice"
    bl_label = "Bool slice"
    bl_description = "Slice for 2 selected objects" 
    bl_options = {'REGISTER', 'UNDO'} 
    
    @classmethod
    def poll(cls, context):
        return check_cutter_selected(context)
           
    def execute(self, context):
        try:
            target_obj = bpy.context.scene.carver_target
        
            execute_slice_op(context, target_obj)
        except RuntimeError:
            pass

        return {'FINISHED'}
    
class FC_TargetSelectOperator(Operator):
    bl_idname = "object.bool_target"
    bl_label = "Selected as Target"
    bl_description = "Set selected to target" 
    bl_options = {'REGISTER', 'UNDO'} 
         
    @classmethod
    def poll(cls, context):        
        return len(context.selected_objects) > 0
       
    def execute(self, context):
        bpy.context.scene.carver_target = context.view_layer.objects.active

        return {'FINISHED'}