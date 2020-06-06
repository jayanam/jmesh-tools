import bpy

def get_current_units():
  lu = bpy.context.scene.unit_settings.length_unit

  if lu == 'KILOMETERS' :
    return 'km'
  elif lu == 'METERS':
    return 'm'
  elif lu == 'CENTIMETERS':
    return 'cm'
  elif lu == 'MILLIMETERS':
    return 'mm'
  elif lu == 'MICROMETERS':
    return 'mcm'
  elif lu == 'MILES':
    return 'mi'
  elif lu == 'FEET':
    return 'ft'
  elif lu == 'INCHES':
    return 'in'
  elif lu == 'THOU':
    return 'thou'
  else:
    return 'bu'