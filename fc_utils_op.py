import bpy
from bpy.types import Operator
from bpy.props import StringProperty

from .utils.fc_bool_util import union_selected

# Set the pivot point of the active object
# to the center and add a mirror modifier
class FC_MirrorOperator(Operator):
    bl_idname = "object.mirror"
    bl_label = "Center Origin & Mirror"
    bl_description = "Mirror selected object" 
    bl_options = {'REGISTER', 'UNDO'} 
    
    @classmethod
    def poll(cls, context):

        if context.active_object == None:
            return False
        
        mode = context.active_object.mode       
        return len(context.selected_objects) == 1 and mode == "OBJECT"
    
    def execute(self, context):
        
        cursor_location = bpy.context.scene.cursor.location.copy()
                
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        
        bpy.ops.object.modifier_add(type='MIRROR')    
        
        bpy.context.scene.cursor.location = cursor_location

        return {'FINISHED'}

#3D cursor operators
class FC_OriginActiveOperator(Operator):
    bl_idname = "view3d.origin_active"
    bl_label = "Set origin to center"
    bl_description = "Set origin to center of active selection" 
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context): 

        if context.object is None:
            return False
            
        return context.object.mode == "EDIT"

    def execute(self, context):    
        bpy.ops.view3d.snap_cursor_to_active()
        bpy.ops.object.editmode_toggle()
        context.object.select_set(state=True)
        bpy.context.view_layer.objects.active = context.object
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}  

#3D cursor center
class FC_CenterActiveOperator(Operator):
    bl_idname = "view3d.snap_active"
    bl_label = "Snap cursor to active"
    bl_description = "Snap the cursor to the active selection" 
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context): 

        if context.active_object == None:
            return False
            
        return context.active_object.mode == "EDIT"

    def execute(self, context):    
        bpy.ops.view3d.snap_cursor_to_active()
        return {'FINISHED'}  

# Dissolve
class FC_DissolveEdgesOperator(Operator):
    bl_idname = "view3d.dissolve_edges"
    bl_label = "Dissolve edges"
    bl_description = "Dissolve the selected edges" 
    bl_options = {'REGISTER', 'UNDO'} 

    @classmethod
    def poll(cls, context):
        
        if context.active_object == None:
            return False

        mode = context.active_object.mode       
        return mode == "EDIT"

    def execute(self, context):       
        bpy.ops.mesh.dissolve_edges()
        return {'FINISHED'}  


# Symmetrize  
class FC_SymmetrizeOperator(Operator):
    bl_idname = "object.sym"
    bl_label = "Symmetrize"
    bl_description = "Symmetrize selected object" 
    bl_options = {'REGISTER', 'UNDO'}
    
    sym_axis : StringProperty(name="Symmetry axis", options={'HIDDEN'}, default="NEGATIVE_X")
          
    @classmethod
    def poll(cls, context):

        if context.active_object == None:
            return False
        
        mode = context.active_object.mode       
        return len(context.selected_objects) == 1 and mode == "OBJECT"
    

    def execute(self, context):
        
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.symmetrize(direction=self.sym_axis)
        bpy.ops.object.mode_set(mode="OBJECT")
        
        return {'FINISHED'}

# Union all selected objects
class FC_UnionSelectedOperator(Operator):
    bl_idname = "object.union_selected_op"
    bl_label = "Union selected objects"
    bl_description = "Union all selected objects" 
    bl_options = {'REGISTER', 'UNDO'} 
    
    @classmethod
    def poll(cls, context):
        
        if context.active_object == None:
            return False

        mode = context.active_object.mode       
        return len(context.selected_objects) > 1 and mode == "OBJECT"
    
    def execute(self, context):
        
        union_selected(context)
        return {'FINISHED'}