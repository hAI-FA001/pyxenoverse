from recordclass import recordclass

from pyxenoverse.bac.types import BaseType

BACAnimation = recordclass('BACAnimation', [
    'start_time',
    'duration',
    'u_04',
    'character_type',
    'ean_type',
    'ean_index',
    'animation_flags',
    'play_face_animation_from_skill',
    'frame_start',
    'frame_end',
    'frame_loop_start',
    'u_16',
    'speed',
    'animation_transition_start_frame',
    'animation_transition_frame_step'
])


# Type 0
class Animation(BaseType):
    type = 0
    bac_record = BACAnimation
    byte_order = 'HHHHHHHHHHHHfff'
    size = 36

    dependencies = {
        ('ean_index', 'ean_type'): {0x5: 'Character', 0xFFFE: 'Skill'}
    }
    description_type = "ean_type"
    description = {
        0x0: "CMN.ean",
        0x1: "Race-specific animation (lby.ean)",
        0x2: "MCM.DBA.ean",
        0x5: "Char. EAN",
        0x6: "chara ean (lby.ean)",
        0x9: "CMN.tal.ean (tail)",
        0xa: "Char. fce.ean (mouth)",
        0xb: "Char. fce.ean (eye)",
        0x28: "Race-specific TTL animation",
        0x29: "MCM.XV1.ean",
        0x2a: "MCM.TTL.ean",
        0x2b: "MCM.TU6.ean",
        0x5e: "MCM.TU13.5.ean",
        0xfffe: "Skill Ean"
    }

    def __init__(self, index):
        super().__init__(index)
