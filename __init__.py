bl_info = {
    "name": "JMesh Tools",
    "description": "Hardsurface and mesh tools for Blender",
    "author": "Jayanam",
    "version": (1, 9, 5, 3),
    "blender": (2, 80, 0),
    "location": "View3D",
    "category": "Object",
    "tracker_url": "https://github.com/jayanam/jmesh-tools" }

# Blender imports
import bpy

from bpy.props import *

import rna_keymap_ui

from . fc_bevel_op          import FC_BevelOperator
from . fc_unbevel_op        import FC_UnBevelOperator
from . fc_panel             import FC_PT_Panel
from . fc_selected_panel    import FC_PT_Selected_Panel
from . fc_primitive_panel   import FC_PT_Primitive_Panel
from . fc_bool_op           import FC_BoolOperator_Diff
from . fc_bool_op           import FC_BoolOperator_Union
from . fc_bool_op           import FC_BoolOperator_Slice
from . fc_bool_op           import FC_BoolOperator_Intersect
from . fc_bool_op           import FC_TargetSelectOperator
from . fc_curve_op          import FC_MeshToCurveOperator, FC_CurveConvertOperator
from . fc_curve_op          import FC_CurveAdjustOperator, FC_JoinAndRemesh
from . fc_mirror_op         import FC_MirrorOperator
from . fc_utils_op          import FC_SymmetrizeOperator
from . fc_utils_op          import FC_OriginActiveOperator
from . fc_utils_op          import FC_CenterActiveOperator
from . fc_utils_op          import FC_DissolveEdgesOperator
from . fc_utils_op          import FC_UnionSelectedOperator
from . fc_menus             import FC_MT_Bool_Menu
from . fc_apply_bool_op     import FC_ApplyAllModifiersOperator, FC_ApplyBoolOperator, FC_ApplyAllBoolOperator
from . fc_primitive_mode_op import FC_Primitive_Mode_Operator
from . fc_array_mode_op     import FC_Array_Mode_Operator
from . fc_circle_array_mode_op     import FC_Circle_Array_Mode_Operator
from . fc_preferences       import FC_AddonPreferences
from . fc_symmetry_op       import FC_Symmetry_Operator
from . fc_mesh_snap_op      import FC_Mesh_Snap_Operator
from . fc_solidify_op       import FC_SolidifyOperator
from . fc_cloth_op          import FC_ClothOperator

from .types.enums import *

# Scene properties
bpy.types.Scene.carver_target = PointerProperty(type=bpy.types.Object)

bpy.types.Scene.apply_bool    = BoolProperty(
                                      name="Apply Immediately", 
                                      description="Apply bool operation immediately",
                                      default = True)

bpy.types.Scene.delete_on_apply   = BoolProperty(
                                      name="Delete after apply", 
                                      description="Delete the object after apply",
                                      default = True)

bpy.types.Scene.self_intersect = BoolProperty(
    
                                      name="Self intersect", 
                                      description="Allow self-intersection",
                                      default = True)

bpy.types.Scene.hole_tolerant = BoolProperty(
                                      name="Hole Tolerant", 
                                      description="Better results when mesh has holes",
                                      default = True)

bpy.types.Scene.use_snapping   = BoolProperty(name="Snap to grid", 
                                        description="Use snapping to the grid",
                                        default = False)

bpy.types.Scene.snap_to_target   = BoolProperty(name="Snap to target", 
                                        description="Snap the primitive to the target",
                                        default = True)

bpy.types.WindowManager.in_primitive_mode = BoolProperty(name="Primitive Mode",
                                        default = False)

bpy.types.WindowManager.in_symmetry_mode = BoolProperty(name="Symmetry Mode",
                                        default = False)

bpy.types.WindowManager.modal_running = BoolProperty(name="Modal operator running",
                                        default = False)

bpy.types.Scene.extrude_immediate    = BoolProperty(
                                      name="Extrude Immediately", 
                                      description="Extrude primitive immediately after creation",
                                      default = False)

# bpy.types.Scene.snap_offset = bpy.props.FloatProperty( name="Snap_offset", description="Offset for primitive snap", default = 0.01)

mode_items = [ ("Create",     "Create", "", 0),
               ("Difference", "Difference", "", 1),
               ("Union",      "Union", "", 2),
               ("Intersect",  "Intersect", "", 3),
               ("Slice",      "Slice", "", 4)
             ]

center_items = [ ("Mouse",     "Mouse", "", 0),
                 ("3D-Cursor", "3D-cursor", "", 1),
                 ("Mesh", "Mesh", "", 2)
               ]

shape_input_method = [ ("Click", "Click", "", 0),
                       ("Draw",  "Draw", "", 1)
                     ]

curve_input_method = [ ("2-Points", "2-Points", "", 0),
                       ("Points",   "Points", "", 1)
                     ]

axis_input_method = [ ("None", "None", "", 0),
                      ("X", "X", "", 1),
                      ("Y", "Y", "", 2),
                      ("Z", "NoZne", "", 3) 
                    ]

bpy.types.Scene.bool_mode = bpy.props.EnumProperty(items=mode_items, 
                                                   name="Operation",
                                                   default="Create")

bpy.types.Scene.center_type = bpy.props.EnumProperty(items=center_items, 
                                                   name="Center_Type",
                                                   default="Mouse")

bpy.types.Scene.shape_input_method = bpy.props.EnumProperty(items=shape_input_method, 
                                                   name="Input_Method",
                                                   default="Click")

bpy.types.Scene.curve_input_method = bpy.props.EnumProperty(items=curve_input_method, 
                                                   name="Curve_Input_Method",
                                                   default="2-Points")

bpy.types.Scene.mirror_primitive = bpy.props.EnumProperty(items=axis_input_method, 
                                                   name="Mirror_Primitive",
                                                   default="None")

primitive_types = [ ("Polyline",   "Polyline",  "", 0),
                    ("Circle",     "Circle",    "", 1),
                    ("Rectangle",  "Rectangle", "", 2),
                    ("Curve",      "Curve",     "", 3)
                  ]

bpy.types.Scene.primitive_type = bpy.props.EnumProperty(items=primitive_types, 
                                                        name="Primitive",
                                                        default="Polyline")

bpy.types.Scene.start_center    = BoolProperty(
                                      name="From Center", 
                                      description="Start primtive from center",
                                      default = False)

addon_keymaps = []

classes = (
    FC_PT_Panel,
    FC_PT_Selected_Panel,
    FC_PT_Primitive_Panel,
    FC_BevelOperator,
    FC_UnBevelOperator,
    FC_BoolOperator_Diff,
    FC_BoolOperator_Union,
    FC_BoolOperator_Slice,
    FC_BoolOperator_Intersect,
    FC_TargetSelectOperator,
    FC_MirrorOperator,
    FC_SymmetrizeOperator,
    FC_OriginActiveOperator,
    FC_CenterActiveOperator,
    FC_DissolveEdgesOperator,
    FC_UnionSelectedOperator,
    FC_CurveConvertOperator,
    FC_CurveAdjustOperator,
    FC_MeshToCurveOperator,
    FC_ApplyBoolOperator,
    FC_ApplyAllBoolOperator,
    FC_Primitive_Mode_Operator,
    FC_Array_Mode_Operator,
    FC_Circle_Array_Mode_Operator,
    FC_MT_Bool_Menu,
    FC_AddonPreferences,
    FC_Symmetry_Operator,
    FC_JoinAndRemesh,
    FC_Mesh_Snap_Operator,
    FC_SolidifyOperator,
    FC_ClothOperator,
    FC_ApplyAllModifiersOperator
)
     
    
def register():
    for c in classes:
        bpy.utils.register_class(c)
   
    # add keymap entry
    kc = bpy.context.window_manager.keyconfigs.addon

    if kc is not None:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')

        kmi = km.keymap_items.new("object.fc_primitve_mode_op", 'P', 'PRESS', shift=True, ctrl=True)
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new("object.fc_array_mode_op", 'A', 'PRESS', shift=True, ctrl=True)
        addon_keymaps.append((km, kmi))

        kmi = km.keymap_items.new("object.fc_circle_array_mode_op", 'C', 'PRESS', shift=True, ctrl=True)
        addon_keymaps.append((km, kmi))

        kmi_mnu = km.keymap_items.new("wm.call_menu_pie", "COMMA", "PRESS", shift=True)
        kmi_mnu.properties.name = FC_MT_Bool_Menu.bl_idname

        addon_keymaps.append((km, kmi_mnu))
    
def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    # remove keymap entry
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)

    addon_keymaps.clear()

