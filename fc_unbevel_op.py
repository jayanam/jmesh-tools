import bpy
from bpy.types import Operator


class FC_UnBevelOperator(Operator):
    bl_idname = "object.unbevel"
    bl_label = "Unbevel an object"
    bl_description = "Un-Bevels selected objects" 
    bl_options = {'REGISTER', 'UNDO'} 
       
    def get_display(mode):
        if mode == "OBJECT":
            return "Un-Bevel"
        else:
            return "Clear sharp"
        
    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0
         
    def execute(self, context):
        
        # API change 2.8: bpy.context.scene.objects.active
        active_obj = bpy.context.view_layer.objects.active 
        
        mode = context.active_object.mode
        
        # Sharpen and bevel in object mode
        if(mode == "OBJECT"):
            
            # We know that we are in object mode
            # cause the operator is for OM only
            for target_obj in context.selected_objects:
                
                bpy.context.view_layer.objects.active = target_obj
                
                # Set flat shading for the target object
                bpy.ops.object.shade_flat()
                
                # Reset the data from autosmooth
                bpy.context.object.data.use_auto_smooth = False
                
                # Remove the bevel modifier if exists
                modifier_to_remove = target_obj.modifiers.get("Bevel")
                if(not modifier_to_remove is None):
                    target_obj.modifiers.remove(modifier_to_remove)

                # Remove the Weighted Normal modifier if exists
                modifier_to_remove = target_obj.modifiers.get("Weighted Normal")
                if(modifier_to_remove is not None):
                    target_obj.modifiers.remove(modifier_to_remove)
                             
                # switch to edit mode and select sharp edges
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.mesh.edges_select_sharp()
                
                # Clear the sharp edges
                bpy.ops.transform.edge_bevelweight(value=-1.0)
                bpy.ops.mesh.mark_sharp(clear=True)
                

                # Back to object mode
                bpy.ops.object.editmode_toggle()
        else:
                
                # Clear the selected edges
                bpy.ops.transform.edge_bevelweight(value=-1.0)
                bpy.ops.mesh.mark_sharp(clear=True)
        
        # API change 2.8: bpy.context.scene.objects.active
        bpy.context.view_layer.objects.active = active_obj
        return {'FINISHED'} 