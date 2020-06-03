from enum import Enum

class ShapeState(Enum):
    NONE = 0
    PROCESSING = 1
    CREATED = 2

def next_enum(enum_inst, rna_inst, prop_str):
    prop = type(rna_inst).bl_rna.properties[prop_str]
    
    for idx, e in enumerate(prop.enum_items):
        if e.identifier == enum_inst:
            index = (idx + 1) % len(prop.enum_items)
            return prop.enum_items[index].identifier  