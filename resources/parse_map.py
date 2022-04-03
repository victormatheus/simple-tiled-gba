import xml.etree.ElementTree as ET
import csv
from io import BytesIO
import numpy as np
import struct
import sys

map_tree = ET.parse('map.tmx')
root = map_tree.getroot()

FLIPPED_HORIZONTALLY_FLAG = 1<<31
FLIPPED_VERTICALLY_FLAG   = 1<<30
FLIPPED_DIAGONALLY_FLAG   = 1<<29

def save_map(map_name, map_file, map_array):
    header_file = map_file + ".h"
    asm_file    = map_file + ".s"

    H,W = map_array.shape

    qs = [0,0,0,0]
    qs[0] = map_array[:32,:32]
    qs[1] = map_array[:32,32:]
    qs[2] = map_array[32:,:32]
    qs[3] = map_array[32:,32:]

    with open(header_file, "w") as h:
        h.write("#pragma once\n")
        h.write("#define %s_WIDTH  (%d)\n" % (map_name,W))
        h.write("#define %s_HEIGHT (%d)\n" % (map_name,H))
        h.write("#define %s_SIZE   (%d)\n" % (map_name,W*H*2))
        h.write("extern const short %s_DATA [%d];\n" % (map_name,W*H))

    with open(asm_file, "w") as a:
        a.write(".section .rodata\n")
        a.write(".align 2\n")
        a.write(".global %s_DATA @ %d bytes\n" % (map_name, W*H*2))
        a.write("%s_DATA:\n" % map_name)
        for q in qs:
            for qy in q:
                for c in range(0,qy.shape[0],8):
                    a.write(".hword %s\n" % ",".join(["0x{0:04x}".format(v) for v in qy[c:c+8]]))
                a.write("\n")
            a.write("\n\n")


for child in root:
    print(child.tag, child.attrib)
    if child.tag == 'layer':
        layer = child
        for data in layer:
            print(data.tag, data.attrib)
            t = data.text
            t = t.replace('\n', '')
            buff = BytesIO(t)
            reader = csv.reader(buff, delimiter=',')
            layer_data_str = reader.next()
            layer_data_int = [int(k) for k in layer_data_str]
            layer_data = np.array(layer_data_int, dtype=np.uint32).reshape((64,64))

            map_ = np.zeros((64,64), dtype = np.uint16)
            first_index = 1

            f_h = (layer_data & FLIPPED_HORIZONTALLY_FLAG) != 0
            f_v = (layer_data & FLIPPED_VERTICALLY_FLAG)   != 0
            f_d = (layer_data & FLIPPED_DIAGONALLY_FLAG)   != 0
            fx = f_h^f_d
            fy = f_v^f_d
            tile_i = layer_data & ((1<<29) - 1)
            tile_i = tile_i - first_index
            # Bit   Expl.
            # 0-9   Tile Number     (0-1023) (a bit less in 256 color mode, because
            #                          there'd be otherwise no room for the bg map)
            # 10    Horizontal Flip (0=Normal, 1=Mirrored)
            # 11    Vertical Flip   (0=Normal, 1=Mirrored)
            # 12-15 Palette Number  (0-15)    (Not used in 256 color/1 palette mode)
            m = tile_i + (fx << 10) + (fy << 11)
            map_ = m

            save_map("test_map", "../src/test_map", map_)
