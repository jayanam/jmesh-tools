import bgl

def set_line_smooth(enabled=True):
    if enabled:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
    else:
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        bgl.glDisable(bgl.GL_BLEND)

def set_poly_smooth(enabled=True):
    if enabled:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glEnable(bgl.GL_LINE_SMOOTH)
        bgl.glEnable(bgl.GL_POLYGON_SMOOTH)
    else:
        bgl.glDisable(bgl.GL_POLYGON_SMOOTH)
        bgl.glDisable(bgl.GL_LINE_SMOOTH)
        bgl.glDisable(bgl.GL_BLEND)

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
    bgl.glDepthMask(False)
    
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
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch.program_set(shader)
        shader.uniform_float("color", color)
        batch.draw()

    set_line_smooth(False)