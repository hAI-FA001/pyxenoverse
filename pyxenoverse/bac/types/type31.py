from recordclass import recordclass

from pyxenoverse.bac.types import BaseType

BACType31 = recordclass('BACType31', [
    'start_time',
    'duration',
    'u_04',
    'character_type',
    'u_12',
    'u_16',
    'u_18',
    'u_20',
    'u_08',
    'u_22',
    'f_24',
    'f_28',
    'u_32',
    'u_36',
    'u_40',
    'u_44',
    'u_48',
    'u_52',
    'u_56',
    'u_60',
])

# Type 31
class Type31(BaseType):
    type = 31
    bac_record = BACType31
    byte_order = 'HHHHIHHHIHffIIIIIIII'
    size = 64

    def __init__(self, index):
        super().__init__(index)
