import bpy
from bpy.types import Panel

class FC_PT_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Booleans"
    bl_category = "JMesh"
    
    def draw(self, context):
       
        layout = self.layout
        scene = context.scene
        
        # Carver Target
        row = layout.row()
        col = row.column()
        col.prop_search(context.scene, "carver_target", context.scene, "objects", text="Target")

        col = row.column()  
        col.operator('object.bool_target', text='', icon='BACK')

        # New row
        row = layout.row()

        # Bool diff button
        col = row.column()
        col.operator('object.bool_diff', text='Difference', icon='SELECT_SUBTRACT')
        
        # Bool union button
        col = row.column()
        col.operator('object.bool_union', text='Union', icon='SELECT_EXTEND')

        if context.mode != "SCULPT":
                        
            row = layout.row()

            # Bool Slice button
            col = row.column()
            col.operator('object.bool_slice', text='Slice', icon='SELECT_DIFFERENCE')
            
            # Bool intersect button
            col = row.column()
            col.operator('object.bool_intersect', text='Intersect', icon='SELECT_INTERSECT')
            
            # Apply immediately
            row = layout.row()
            col = row.column()
            col.prop(context.scene, "apply_bool")

            # Delete object after immediately
            col = row.column()
            col.prop(context.scene, "delete_on_apply")

            # Self intersect
            if bpy.app.version >= (3, 0, 0):
                row = layout.row()
                col = row.column()
                col.prop(context.scene, "self_intersect")

                col = row.column()
                col.prop(context.scene, "hole_tolerant")

            # Apply selected booleans
            row = layout.row()
            row.operator('object.apply_bool',icon='MOD_BOOLEAN')

            # Apply all pending booleans
            row = layout.row()
            row.operator('object.apply_all_bool',icon='MOD_BOOLEAN')