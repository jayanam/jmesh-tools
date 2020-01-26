import bpy
from bpy.types import Operator

from .utils.fc_bevel_util import execute_bevel


class FC_BevelOperator(Operator):
    bl_idname = "object.bevel"
    bl_label = "Bevel an object"
    bl_description = "Bevels selected objects" 
    bl_options = {'REGISTER', 'UNDO'}
    
    def get_display(mode):
        if mode == "OBJECT":
            return "Bevel"
        else:
            return "Sharpen Edges"
                  
    @classmethod
    def poll(cls, context):        
        return len(context.selected_objects) > 0
         
    def execute(self, context):
        
        active_object = bpy.context.view_layer.objects.active
        
        mode = active_object.mode
        
        # Sharpen and bevel in object mode
        if(mode == "OBJECT"):

            execute_bevel(context.selected_objects)
        
        # Sharpen edges in edit mode
        else:
            
            # Mark selected edges as sharp
            bpy.ops.mesh.mark_sharp()
            bpy.ops.transform.edge_bevelweight(value=1)
        
        bpy.context.view_layer.objects.active = active_object
        return {'FINISHED'} 