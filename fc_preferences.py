import bpy

from bpy.types import AddonPreferences

class FC_AddonPreferences(AddonPreferences):
    bl_idname = __package__
    
    def draw(self, context):
    
        wm = bpy.context.window_manager 
        km_items = wm.keyconfigs.user.keymaps['3D View'].keymap_items         
        km_item = km_items['object.fc_primitve_mode_op']

        row = self.layout.row()
        row.label(text=km_item.name)
        row.prop(km_item, 'type', text='', full_event=True)

        km_mnu_item = km_items['wm.call_menu_pie']
        row = self.layout.row()
        row.label(text=km_mnu_item.name)
        row.prop(km_mnu_item, 'type', text='', full_event=True) 