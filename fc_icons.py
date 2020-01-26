import os
import bpy
import bpy.utils.previews

icon_cache = {}
icons_loaded = False

def get_icon_value(id):
    icons = load_icons()
    return icons.get(id).icon_id

def load_icons():
    global icon_cache
    global icons_loaded

    if icons_loaded:
      return icon_cache["main"]

    fc_icons = bpy.utils.previews.new()

    icons_dir = os.path.join(os.path.dirname(__file__), "icons")

    # fc_icons.load( "fc_bevel", os.path.join(icons_dir, ".."), 'IMAGE')
    
    icon_cache["main"] = fc_icons
    icons_loaded = True

    return icon_cache["main"]

def clear_icons():
    global icons_loaded
    for icon in icon_cache.values():
        bpy.utils.previews.remove(icon)
    icon_cache.clear()
    icons_loaded = False