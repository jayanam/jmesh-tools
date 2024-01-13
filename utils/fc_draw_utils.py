import gpu

from .. utils.shader_utils import *

def set_line_smooth(enabled=True):
    if enabled:
        gpu.state.blend_set('ALPHA')
    else:
        gpu.state.blend_set('NONE')

def set_poly_smooth(enabled=True):
    if enabled:
        gpu.state.blend_set('ALPHA')
    else:
        gpu.state.blend_set('NONE')

def draw_circle_2d(position, color, radius, segments=32, batch_type='TRI_FAN'):

    from math import sin, cos, pi
    import gpu
    from gpu.types import (
        GPUBatch,
        GPUVertBuf,
        GPUVertFormat,
    )

    if segments <= 0:
        raise ValueError("Amount of segments must be greater than 0.")

    set_line_smooth()
    gpu.state.depth_mask_set(False)
    
    with gpu.matrix.push_pop():
        gpu.matrix.translate(position)
        gpu.matrix.scale_uniform(radius)
        mul = (1.0 / (segments - 1)) * (pi * 2)
        verts = [(sin(i * mul), cos(i * mul)) for i in range(segments)]
        fmt = GPUVertFormat()
        pos_id = fmt.attr_add(id="pos", comp_type='F32', len=2, fetch_mode='FLOAT')
        vbo = GPUVertBuf(len=len(verts), format=fmt)
        vbo.attr_fill(id=pos_id, data=verts)
        batch = GPUBatch(type=batch_type, buf=vbo)
        shader = get_builtin_shader('UNIFORM_COLOR', '2D')
        batch.program_set(shader)
        shader.uniform_float("color", color)
        batch.draw()

    set_line_smooth(False)