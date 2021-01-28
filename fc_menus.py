import bpy
from bpy.types import Menu

from . fc_bevel_op   import FC_BevelOperator as bo
from . fc_unbevel_op import FC_UnBevelOperator as ubo

from . utils.fc_bool_util import *
from . utils.fc_select_util import *

class FC_MT_Bool_Menu(Menu):
    bl_idname = "FC_MT_Bool_Menu"
    bl_label = "JMesh Pie Menu"
   
    def draw(self, context):

        active_object = bpy.context.view_layer.objects.active

        layout = self.layout

        pie = layout.menu_pie()

        if active_object:

            is_curve = active_object.type == "CURVE"
            
            mode = active_object.mode

            if(mode == "OBJECT"):

                if not is_curve:
                    if check_cutter_selected(context):
                        pie.operator("object.bool_diff",  icon="SELECT_SUBTRACT")
                        pie.operator("object.bool_union", icon="SELECT_EXTEND")
                        pie.operator("object.bool_slice", icon="SELECT_DIFFERENCE")
                    
                    if more_than_one_selected(context):
                        pie.operator("object.union_selected_op", icon="SELECT_EXTEND")

                    if can_apply_bool(active_object, context):
                        pie.operator("object.apply_bool", icon="MOD_BOOLEAN")
 
            if active_object != context.scene.carver_target and not is_curve:
                pie.operator("object.bool_target", icon="MOD_BOOLEAN")

            pie.operator("view3d.join_and_remesh", icon='SELECT_EXTEND')
            pie.operator("object.mirror", text="Mirror", icon='MOD_MIRROR')
            pie.operator("object.fc_array_mode_op", icon='MOD_ARRAY')

            if not is_curve:
                pie.operator('object.fc_symmetry_op', text="Symmetrize", icon='MOD_MESHDEFORM')
                pie.operator("object.bevel", text=bo.get_display(context.object.mode), icon="MOD_BEVEL")     