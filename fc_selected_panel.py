import bpy
from bpy.types import Panel

from . fc_bevel_op import FC_BevelOperator
from . fc_unbevel_op import FC_UnBevelOperator

class FC_PT_Selected_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Selected objects"
    bl_category = "JMesh"
    
    def has_bevel_modifier(self, obj):
        if obj is None:
            return False

        for modifier in obj.modifiers:
            if modifier.type == "BEVEL":
                return True
        return False

    @classmethod
    def poll(cls, context):
        if context.object is None:
            return False

        return True
     
    def draw(self, context):
        
        layout = self.layout

        if context.mode != "SCULPT":
        
            if context.object is not None:

                # Draw type
                row = layout.row()
                row.prop(context.object, "display_type", text="Display")

            mode = context.object.mode    

            # Bevel button
            row = layout.row()     
            col = row.column()
            col.operator('object.bevel', text=FC_BevelOperator.get_display(context.object.mode), icon='MOD_BEVEL')

            # Un-Bevel button
            col = row.column()
            col.operator('object.unbevel', text=FC_UnBevelOperator.get_display(context.object.mode), icon='MOD_BEVEL')   

            if(mode == "OBJECT"):                

                if self.has_bevel_modifier(context.active_object):
                    row = layout.row()
                    row.prop(context.object.modifiers["Bevel"], "width", text="Bevel width")
        
            row = layout.row()
            row.operator('object.union_selected_op', text='Union selected', icon='MOD_BOOLEAN')
            
            # Array
            row = layout.row()
            col = row.column()
            col.operator('object.fc_array_mode_op', text='Array', icon='MOD_ARRAY')

            # Circular Array
            col = row.column()
            col.operator('object.fc_circle_array_mode_op', text='Circle Array', icon='MOD_ARRAY')
           
            row = layout.row()
            col = row.column()
            col.operator('view3d.origin_active', text='Set Origin', icon='PIVOT_CURSOR')

            col = row.column()
            col.operator('view3d.snap_active', text='Cursor to Active', icon='PIVOT_CURSOR')

            row = layout.row()
            row.operator('view3d.curve_convert', text='Curve to mesh & fill', icon='LINENUMBERS_OFF')

            row = layout.row()
            col = row.column()
            col.operator('view3d.mesh_to_curve', text='Mesh to curve', icon='LINENUMBERS_OFF')

            col = row.column()
            col.operator('view3d.curve_adjust', text='Adjust curve', icon='LINENUMBERS_OFF')
        
        # Mirror and symmetrize
        row = layout.row()
        col = row.column()
        col.operator('object.mirror', text='Mirror', icon='MOD_MIRROR')

        col = row.column()
        col.operator('object.fc_symmetry_op', text="Symmetrize", icon='MOD_MESHDEFORM')

        # Mesh snap
        row = layout.row()
        row.operator('object.fc_mesh_snap_op', text='Mesh Snap', icon='MOD_MIRROR')

        
