import blf
import bpy 

def blf_set_size(fontid, size):
    if bpy.app.version >= (4, 0, 0):
        blf.size(fontid, size)
    else:
        blf.size(fontid, size, 72)