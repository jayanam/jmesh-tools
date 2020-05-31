import bpy
from bpy.types import Operator

from .utils.fc_bool_util import *

class FC_ApplyBoolOperator(Operator):
    bl_idname = "object.apply_bool"
    bl_label = "Apply Selected Booleans"
    bl_description = "Apply selected pending bool operators" 
    bl_options = {'REGISTER', 'UNDO'} 

    @classmethod
    def poll(cls, context):
 
        for obj in context.view_layer.objects:
            for modifier in obj.modifiers:
                if modifier.name.startswith("FC_BOOL") and modifier.object in context.selected_objects:
                    return True
         
    def execute(self, context):
        
        obj2delete = []
        active_obj = bpy.context.view_layer.objects.active
              
        for obj in context.view_layer.objects:
            for modifier in obj.modifiers:
                if modifier.name.startswith("FC_BOOL"):

                    # API change 2.8: bpy.context.scene.objects.active = obj
                    if modifier.object in context.selected_objects:
                        bpy.context.view_layer.objects.active = obj
                        bpy.ops.object.modifier_apply(modifier=modifier.name)

                        if is_delete_after_apply():
                            obj2delete.append(modifier.object)

        bpy.ops.object.select_all(action='DESELECT')

        if is_delete_after_apply():
            for obj in obj2delete:
                obj.select_set(True)
                bpy.ops.object.delete()    

        return {'FINISHED'}