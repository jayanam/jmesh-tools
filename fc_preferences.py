import bpy

from bpy.props import *

from bpy.types import AddonPreferences

def get_preferences():
    return bpy.context.preferences.addons[__package__].preferences

class FC_AddonPreferences(AddonPreferences):
    bl_idname = __package__

    keyboard_section : BoolProperty(
        name="Keyboard Shortcuts",
        description="Keyboard Shortcuts",
        default=True
    )

    color_font_section : BoolProperty(
        name="Colors & Fonts",
        description="Colors & Fonts",
        default=False
    )

    operator_section : BoolProperty(
        name="Operator settings",
        description="Operator settings",
        default=False
    )

    osd_text_color : FloatVectorProperty(
        name="OSD text color",
        description="Color for On Screen Display text",
        default=(0.0, 0.5, 1.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    osd_label_color : FloatVectorProperty(
        name="OSD label color",
        description="Color for On Screen Display labels",
        default=(1.0, 1.5, 1.0, 1.0),
        min=0.0,
        max=1.0,
        size=4,
        subtype='COLOR'
    )

    osd_font_size : IntProperty(
        name="OSD font size",
        description="Font size of On Screen Display",
        default=16,
        min=10,
        max=24     
    )

    osd_offset_x : IntProperty(
        name="OSD Offset X",
        description="Offset X-axis On Screen Display",
        default=60,
        min=0   
    )

    sym_dir_items = [ ("Selected to opposite", "Selected to opposite", "",  0),
                      ("To Selected",   "To Selected", "", 1)
                    ]

    symmetrize_direction : EnumProperty(items=sym_dir_items, 
                                                   name="Symmetrize direction",
                                                   default="Selected to opposite")
    
    def draw(self, context):
        
        wm = bpy.context.window_manager 

        layout = self.layout

        # Keyboard shortcuts section
        layout.prop(self, "keyboard_section", icon='DISCLOSURE_TRI_DOWN' if self.keyboard_section else 'DISCLOSURE_TRI_RIGHT')
        if self.keyboard_section:

            km_items = wm.keyconfigs.user.keymaps['3D View'].keymap_items   

            km_item = km_items['object.fc_primitve_mode_op']

            row = self.layout.row()
            row.label(text=km_item.name)
            row.prop(km_item, 'type', text='', full_event=True)

            km_item = km_items['object.fc_boolean_mode_op']

            row = self.layout.row()
            row.label(text=km_item.name)
            row.prop(km_item, 'type', text='', full_event=True)

            km_mnu_item = km_items['wm.call_menu_pie']
            row = self.layout.row()
            row.label(text=km_mnu_item.name)
            row.prop(km_mnu_item, 'type', text='', full_event=True)

        # OSD section
        layout.prop(self, "color_font_section", icon='DISCLOSURE_TRI_DOWN' if self.keyboard_section else 'DISCLOSURE_TRI_RIGHT')
        if self.color_font_section:
            row = self.layout.row()
            row.prop(self, "osd_label_color")

            row = self.layout.row()
            row.prop(self, "osd_text_color")

            row = self.layout.row()
            row.label(text="OSD font size")
            row.prop(self, "osd_font_size", text='')

            row = self.layout.row()
            row.label(text="OSD Offset X")
            row.prop(self, "osd_offset_x", text='')

        # Operator settings section
        layout.prop(self, "operator_section", icon='DISCLOSURE_TRI_DOWN' if self.operator_section else 'DISCLOSURE_TRI_RIGHT')
        if self.operator_section:
            row = self.layout.row()
            row.label(text="Symmetrize direction")
            row.prop(self, "symmetrize_direction", text='')
        