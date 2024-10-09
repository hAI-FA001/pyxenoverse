import math
from recordclass import recordclass
import struct
import numpy as np

from pyxenoverse import BaseRecord, read_name, write_name
from pyxenoverse.esk.bone import Bone


LIBXENOVERSE_ESK_SIGNATURE = b'#ESK'

ESKHeader = recordclass('ESKHeader', [
    'bone_count',
    'flag',
    'bone_indices_offset',
    'bone_names_offset',
    'skinning_matrix_offset',
    'transform_matrix_offset',
    'unknown_offset_0',
    'unknown_offset_1',
    'unknown_offset_2',
    'unknown_offset_3'
])
ESK_HEADER_SIZE = 36
ESK_HEADER_BYTE_ORDER = 'HHIIIIIIII'

UNK1_I_00_NAME = "Number Sections"
UNK1_SECTION_NAMES = ["Section Flags", "Control Flags", "Bone", "BoneParent1", "BoneParent2", "Pad1", "Factor", "Pad2"]
UNK1Section = recordclass("UNK1Section", [
    "sectionFlags",
    "controlFlags",
    "bone",
    "boneParent1",
    "boneParent2",
    "pad1",
    "factor",
    "pad2"
    ])
UNK1_SECTION_SIZE = 24
UNK1_SECTION_BYTE_ORDER = 'IHHHHIfI'


class ESK(BaseRecord):
    def __init__(self, endian='<'):
        self.name = ""
        self.bones = []
        self.m_have_128_unknown_bytes = True
        self.endian = endian
        self.filename = ''

        super().__init__()

    def load(self, filename):
        with open(filename, 'rb') as f:
            if f.read(4) != LIBXENOVERSE_ESK_SIGNATURE:
                return False
            self.endian = '>' if f.read(2) == 0xFEFF else '<'
            f.seek(16)
            address = struct.unpack(self.endian + 'I', f.read(4))[0]
            f.seek(address)
            self.read(f, self.endian)
        self.filename = filename
        return True

    def save(self, filename=None):
        if filename:
            self.filename = filename
        with open(self.filename, 'wb') as f:
            f.write(LIBXENOVERSE_ESK_SIGNATURE)
            f.write(struct.pack(self.endian + 'II', 0x001CFFFE, 0x00010001))
            f.seek(16)
            address = 32
            f.write(struct.pack(self.endian + 'I', address))
            f.seek(address)
            self.write(f, self.endian)
        return None

    def read(self, f, endian):
        base_skeleton_address = f.tell()
        self.data = ESKHeader(*struct.unpack(endian + ESK_HEADER_BYTE_ORDER, f.read(ESK_HEADER_SIZE)))
        # print("--------------- read ESK \n[{}] bone_count : {}, flag : {}, bone_indices_offset : [{}],"
        #       " bone_names_offset : [{}], skinning_matrix_offset : [{}], transform_matrix_offset : [{}],"
        #       " unknown_offset_0 : [{}], unknown_offset_1 : [{}], unknown_offset_2 : [{}], unknown_offset_3 : [{}]"
        #       .format(base_skeleton_address, self.bone_count, self.flag, self.bone_indices_offset,
        #               self.bone_names_offset, self.skinning_matrix_offset, self.transform_matrix_offset,
        #               self.unknown_offset_0, self.unknown_offset_1, self.unknown_offset_2, self.unknown_offset_3))

        self.bones.clear()

        for i in range(self.bone_count):
            bone = Bone(i)
            # print("pyxenoverse {}".format(i))

            # Read Bone Indices
            f.seek(base_skeleton_address + self.bone_indices_offset + i * 8)
            bone.read_indices(f, endian)
            # print("    Indices - parent: {}, child: {}, sibling(next): {}, index4: {}".format(
            # pyxenoverse.parent_index, pyxenoverse.child_index, pyxenoverse.sibling_index, pyxenoverse.index_4))

            # Read Bone Name
            f.seek(base_skeleton_address + self.bone_names_offset + i * 4)
            address = struct.unpack(endian + 'I', f.read(4))[0]
            f.seek(base_skeleton_address + address)
            bone.name = read_name(f)
            # print("    Name - {}".format(pyxenoverse.name))

            # Read Skinning Matrices
            f.seek(base_skeleton_address + self.skinning_matrix_offset + i * 48)
            bone.read_skinning_matrix(f, endian)
            # print("    Skinning matrix\n{}\n".format(pyxenoverse.get_skinning_matrix_debug()))

            if self.transform_matrix_offset:
                # Read Bone matrices
                f.seek(base_skeleton_address + self.transform_matrix_offset + i * 64)
                bone.read_transform_matrix(f, endian)
                # print("    Transform matrix\n{}\n".format(pyxenoverse.get_transform_matrix_debug()))

            self.bones.append(bone)

        f.seek(0, 2)
        fsize = f.tell()
        self.fsize = fsize

        # if we can read all 128 bytes, then do it -- this case handles, say, accessoories' esk, which don't use this set of unks
        if self.unknown_offset_0 and fsize - (base_skeleton_address + self.unknown_offset_0 + 4 * 31) >= 0:
            self.m_have_128_unknown_bytes = True
            self.num_unknown_bytes = self.unknown_offset_1 - self.unknown_offset_0
            self.num_unknown_sections = (self.num_unknown_bytes - 4) // 24
            
            if (self.num_unknown_bytes - 4) % 24 != 0:
                print(f"WARNING: UNK1 SECTION DOES NOT HAVE MULTIPLE OF 24 BYTES (GOT {self.num_unknown_bytes-4} BYTES)")
            
            f.seek(base_skeleton_address + self.unknown_offset_0)
            self.unk1_I_00 = struct.unpack(endian + 'I', f.read(4))[0]
            
            self.unk1_sections = []
            for _ in range(self.num_unknown_sections):
                self.unk1_sections.append(UNK1Section(
                    *struct.unpack(
                        endian + UNK1_SECTION_BYTE_ORDER,
                        f.read(UNK1_SECTION_SIZE)
                        )
                    ))
        else:
            self.m_have_128_unknown_bytes = False
            self.num_unknown_bytes = 0
            self.num_unknown_sections = 0
            self.unk1_I_00 = 0
            self.unk1_sections = []
        
        # check if unk2 exist
        self.unk2_list = []
        if self.unknown_offset_1 != 0:
            self.m_have_unk2 = True
            f.seek(base_skeleton_address + self.unknown_offset_1)
            for i in range(2 * self.bone_count):
                self.unk2_list.append(struct.unpack(endian + 'I', f.read(4))[0])
        else:
            self.m_have_unk2 = False
        

    def write(self, f, endian, with_transform_matrix=True):
        base_skeleton_address = f.tell()
        name_size = sum([len(bone.name) + 1 for bone in self.bones])
        self.bone_count = len(self.bones)
        
        self.bone_indices_offset = 36
        self.bone_names_offset = self.bone_indices_offset + self.bone_count * 8
        self.skinning_matrix_offset = math.ceil((self.bone_names_offset + self.bone_count * 4 + name_size) / 16.0) * 16
        self.transform_matrix_offset = self.skinning_matrix_offset + self.bone_count * 48 if with_transform_matrix \
            else 0
        self.unknown_offset_0 = self.transform_matrix_offset + self.bone_count * 64 if with_transform_matrix \
            else self.skinning_matrix_offset + self.bone_count * 48
        self.unknown_offset_1 = self.unknown_offset_0 + 124

        if not self.m_have_128_unknown_bytes:
            self.unknown_offset_1 = self.unknown_offset_0
            self.unknown_offset_0 = 0

        f.write(struct.pack(endian + ESK_HEADER_BYTE_ORDER, *self.data))
        # print("--------------- write ESK \n[{}] bone_count : {}, flag : {}, bone_indices_offset : [{}],"
        #       " bone_names_offset : [{}], skinning_matrix_offset : [{}], transform_matrix_offset : [{}],"
        #       " unknown_offset_0 : [{}], unknown_offset_1 : [{}], unknown_offset_2 : [{}], unknown_offset_3 : [{}]"
        #       .format(base_skeleton_address, self.bone_count, self.flag, self.bone_indices_offset,
        #               self.bone_names_offset, self.skinning_matrix_offset, self.transform_matrix_offset,
        #               self.unknown_offset_0, self.unknown_offset_1, self.unknown_offset_2, self.unknown_offset_3))

        name_size = 0
        for i, bone in enumerate(self.bones):
            # Write Bone Indicies
            f.seek(base_skeleton_address + self.bone_indices_offset + i * 8)
            bone.write_indices(f, endian)

            # Write Bone Names
            f.seek(base_skeleton_address + self.bone_names_offset + i * 4)
            address = self.bone_names_offset + self.bone_count * 4 + name_size
            f.write(struct.pack(endian + 'I', address))
            f.seek(base_skeleton_address + address)
            name_size += len(bone.name) + 1
            write_name(f, bone.name)

            # Write Skinning Matrices
            f.seek(base_skeleton_address + self.skinning_matrix_offset + i * 48)
            bone.write_skinning_matrix(f, endian)

            if self.transform_matrix_offset:
                f.seek(base_skeleton_address + self.transform_matrix_offset + i * 64)
                bone.write_transform_matrix(f, endian)

        # unknown_offset_0: 128 bytes always the same
        if self.unknown_offset_0:
            f.seek(base_skeleton_address + self.unknown_offset_0)
            # print(f.tell())
            f.write(struct.pack(
                '<' + 'I' * 31,
                0x00000005, 0x00180001, 0x00080200, 0x00040003, 0x00000000, 0x3F000000, 0x00000000, 0x00180001,
                0x000E0200, 0x000A0009, 0x00000000, 0x3F000000, 0x00000000, 0x00180001, 0x00150200, 0x00160014,
                0x00000000, 0x3F000000, 0x00000000, 0x00180001, 0x00400200, 0x002D002C, 0x00000000, 0x3F000000,
                0x00000000, 0x00180001, 0x00600200, 0x004B0046, 0x00000000, 0x3F000000, 0x00000000
            ))

        # unknown_offset_1 : the same for all bones : 8 octets with FFFF 0000 0000 0000 (except the last)
        # Hyp : it's the weights of a pyxenoverse on animation ? FFFF for full influence ?
        f.seek(base_skeleton_address + self.unknown_offset_1)

        for i in range(self.bone_count):
            f.write(struct.pack(endian + 'II', 0, 0x0000FFFF))

    def get_bone_difference(self, other):
        bone_names = set(bone.name for bone in self.bones[1:])
        return [bone for bone in other.bones if bone.name not in bone_names and bone.index != 0]

