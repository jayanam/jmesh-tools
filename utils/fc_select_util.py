import bpy

def more_than_one_selected(context):
    return len(context.selected_objects) > 1

def check_cutter_selected(context):
    result = len(context.selected_objects) > 0
    result = result and not context.scene.carver_target is None
    result = result and not (context.scene.carver_target == context.view_layer.objects.active)
    return result