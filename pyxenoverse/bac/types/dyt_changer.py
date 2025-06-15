from recordclass import recordclass

from pyxenoverse.bac.types import BaseType

BACDYTChanger = recordclass('BACDYTChanger', [
    'start_time',
    'duration',
    'u_04',
    'character_type',

    'dyt_flags',
    'u_040',
    'switch_transition_start',
    'switch_transition_end',
    'u_16',
    'u_20',
    'u_24'
])


# Type 28
class DYTChanger(BaseType):
    type = 28
    bac_record = BACDYTChanger
    byte_order = 'HHHH IIffIII'
    size = 36

    def __init__(self, index):
        super().__init__(index)
