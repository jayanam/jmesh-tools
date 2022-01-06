import bpy

def more_than_one_selected(context):
    return len(context.selected_objects) > 1

def is_vertex_selection():
    return bpy.context.scene.tool_settings.mesh_select_mode[0]

def is_edge_selection(cntext):
    return bpy.context.scene.tool_settings.mesh_select_mode[1]

def is_face_selection():
    return bpy.context.scene.tool_settings.mesh_select_mode[2]

def check_cutter_selected(context):
    result = len(context.selected_objects) > 0
    result = result and not context.scene.carver_target is None
    result = result and not (context.scene.carver_target == context.view_layer.objects.active)
    return result