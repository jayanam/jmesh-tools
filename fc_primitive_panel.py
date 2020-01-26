import bpy
from bpy.types import Panel

class FC_PT_Primitive_Panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Primitives"
    bl_category = "JMesh"
   
    def draw(self, context):
        
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.prop(context.scene, "use_snapping", text="Snap grid")

        col = row.column()
        col.prop(context.scene, "snap_to_target", text="Snap to mesh")

        if context.scene.primitive_type != "Curve":   
            row = layout.row()
            col = row.column()
            col.prop(context.scene, "extrude_mesh", text="Extrude")

        row = layout.row()
        row.operator("object.fc_primitve_mode_op", text="Primitive Mode")
