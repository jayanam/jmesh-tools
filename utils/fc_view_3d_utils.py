import bpy
import bmesh
import mathutils
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import intersect_line_plane

from bpy_extras.view3d_utils import (
    region_2d_to_origin_3d,
    region_2d_to_location_3d, 
    region_2d_to_vector_3d,
    location_3d_to_region_2d
)

def get_snap_vertex_indizes(view_rot):
    v1 = round(abs(view_rot[0]), 3)
    v2 = round(abs(view_rot[1]), 3)

    # top / bottom
    if (v1== 1.0 and v2 == 0.0) or (v1==0.0 and v2 == 1.0):
        return (0,1)

    # front / back
    if v1== 0.5 and v2 == 0.5:
        return (1,2)

    # left / right
    if (v1 == 0.707 and v2== 0.707) or (v1 == 0.0 and v2 == 0.0):
        return (0,2)

    return None

def get_grid_snap_pos(pos, overlay3d):
    ratio = overlay3d.grid_scale / overlay3d.grid_subdivisions
    ratio_half = ratio / 2.0
    mod = pos % ratio
    if mod < ratio_half:
        mod = -mod
    else:
        mod = (ratio - mod)

    return mod

def get_view_rotation(context):
    rv3d      = context.space_data.region_3d
    view_rot  = rv3d.view_rotation
    return view_rot    

def get_view_direction(context):
    view_rot  = get_view_rotation(context)
    dir = view_rot @ mathutils.Vector((0,0,-1))
    return dir.normalized()

def get_view_direction_by_rot_matrix(view_rotation):
    dir = view_rotation @ mathutils.Vector((0,0,-1))
    return dir.normalized()

def get_origin_and_direction(pos_2d, context):
    region    = context.region
    region_3d = context.space_data.region_3d
    
    origin    = region_2d_to_origin_3d(region, region_3d, pos_2d)
    direction = region_2d_to_vector_3d(region, region_3d, pos_2d)

    return origin, direction

def get_3d_on_mesh(pos_2d, bvhtree, context):
    
    origin, direction = get_origin_and_direction(pos_2d, context)
    hit, normal, *_ = bvhtree.ray_cast(origin, direction)
    return hit, normal

def get_3d_on_plane(pos_2d, hit, normal, context):
    
    origin, direction = get_origin_and_direction(pos_2d, context)
            
    # get the intersection point on infinite plane
    return intersect_line_plane(origin, origin + direction, hit, normal)


def get_3d_vertex_for_2d(view_context, vertex_2d, dir):
 
    vec = region_2d_to_location_3d(view_context.region, view_context, vertex_2d, dir)
    return vec    

def get_3d_vertex_dir(context, vertex_2d, dir):
    region    = context.region
    rv3d      = context.space_data.region_3d
  
    vec = region_2d_to_location_3d(region, rv3d, vertex_2d, dir)  
    return vec

def get_2d_vertex(context, vertex_3d):
    region    = context.region
    rv3d      = context.space_data.region_3d
    return location_3d_to_region_2d(region, rv3d, vertex_3d)

def bvhtree_from_object(context, obj):
    bm = bmesh.new()
    depsgraph = context.evaluated_depsgraph_get()
    ob_eval = obj.evaluated_get(depsgraph)
    mesh = ob_eval.to_mesh()

    bm.from_mesh(mesh)
    bm.transform(obj.matrix_world)

    bvhtree = BVHTree.FromBMesh(bm)
    ob_eval.to_mesh_clear()
    return bvhtree

def get_snap_3d_vertex(context, vertex_3d):

    rv3d = context.space_data.region_3d
    overlay3d = context.space_data.overlay
    view_rot  = rv3d.view_rotation

    if (not rv3d.is_perspective and vertex_3d is not None):
        ind = get_snap_vertex_indizes(view_rot)
        if ind is not None:               
            vertex_3d[ind[0]] = vertex_3d[ind[0]] + get_grid_snap_pos(vertex_3d[ind[0]], overlay3d)
            vertex_3d[ind[1]] = vertex_3d[ind[1]] + get_grid_snap_pos(vertex_3d[ind[1]], overlay3d)
    return vertex_3d


def get_3d_vertex(context, vertex_2d):
    region    = context.region
    rv3d      = context.space_data.region_3d
    view_rot  = rv3d.view_rotation
    overlay3d = context.space_data.overlay

    distance = 4
    dir = get_view_direction(context) * -1 * distance
    
    vec = region_2d_to_location_3d(region, rv3d, vertex_2d, dir)   

    # if (not rv3d.is_perspective and context.scene.use_snapping):
    #     ind = get_snap_vertex_indizes(view_rot)
    #     if ind is not None:               
    #         vec[ind[0]] = vec[ind[0]] + get_grid_snap_pos(vec[ind[0]], overlay3d)
    #         vec[ind[1]] = vec[ind[1]] + get_grid_snap_pos(vec[ind[1]], overlay3d)

    return vec