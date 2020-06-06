import bpy

def get_current_units():
  lu = bpy.context.scene.unit_settings.length_unit

  if lu == 'KILOMETERS' :
    return ('km', 1000)
  elif lu == 'METERS':
    return ('m', 1)
  elif lu == 'CENTIMETERS':
    return ('cm', 1 / 100)
  elif lu == 'MILLIMETERS':
    return ('mm', 1 / 1000)
  elif lu == 'MICROMETERS':
    return ('mcm', 1 / 1000000)
  elif lu == 'MILES':
    return ('mi', 1760)
  elif lu == 'FEET':
    return ('ft', 1 / 3)
  elif lu == 'INCHES':
    return ('in', 1 / 36)
  elif lu == 'THOU':
    return ('thou', 1 / 36000)
  else:
    return ('bu', 1)

def bu_to_unit(value, scale):
  return value / scale

def unit_to_bu(value, scale):
  return value * scale
