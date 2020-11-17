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
            for modifier in obj.modifiers[:]:
                if modifier.name.startswith("FC_BOOL"):

                    # API change 2.8: bpy.context.scene.objects.active = obj
                    if modifier.object in context.selected_objects:

                        if is_delete_after_apply():
                            if modifier.object not in obj2delete:
                                obj2delete.append(modifier.object)

                        bpy.context.view_layer.objects.active = obj
                        bpy.ops.object.modifier_apply(modifier=modifier.name)

        bpy.ops.object.select_all(action='DESELECT')

        if is_delete_after_apply():
            for obj in obj2delete:
                obj.select_set(True)
                bpy.ops.object.delete()    

        return {'FINISHED'}

class FC_ApplyAllBoolOperator(Operator):
    bl_idname = "object.apply_all_bool"
    bl_label = "Apply all Booleans"
    bl_description = "Apply all pending bool operators" 
    bl_options = {'REGISTER', 'UNDO'} 

    @classmethod
    def poll(cls, context):
 
        for obj in context.selected_objects:
            for modifier in obj.modifiers:
                if modifier.name.startswith("FC_BOOL"):
                    return True

    def apply_all_modifiers_with_object(self, context, mod_name, mod_obj):
        for obj in context.view_layer.objects:
            for modifier in obj.modifiers[:]:
                if modifier.name == mod_name and modifier.object is mod_obj:
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.modifier_apply(modifier=mod_name)

    def execute(self, context):
        
        obj2delete = []
        active_obj = bpy.context.view_layer.objects.active
              
        for obj in context.selected_objects:
            for modifier in obj.modifiers[:]:
                if modifier.name.startswith("FC_BOOL"):

                    if is_delete_after_apply():
                        if modifier.object is not None:
                            modifier.object.hide_set(False)
                            if modifier.object not in obj2delete:
                                obj2delete.append(modifier.object)
                                
                    # Apply all modifiers with this object
                    self.apply_all_modifiers_with_object(context, modifier.name, modifier.object)

        bpy.ops.object.select_all(action='DESELECT')

        if is_delete_after_apply():
            for obj in obj2delete:
                obj.select_set(True)
                bpy.ops.object.delete()    

        active_obj.select_set(True)
        bpy.ops.object.shade_smooth()
        bpy.context.view_layer.objects.active = active_obj

        return {'FINISHED'}