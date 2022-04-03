import numpy as np
from PIL import Image
import sys

#each pallete bank is 15 colors + transparent (color 0)
#we can have 16 different pallete banks

png_file = sys.argv[1]

A = np.array(Image.open(png_file), dtype=np.uint32)
H,W,_ = A.shape
A = A[:,:,0:3]
I = A.reshape((H//8,8,W//8,8,3)).transpose((0,2,1,3,4))

I_rgb15 = (I[:,:,:,:,0] >> 3) | ((I[:,:,:,:,1] >> 3) << 5) | ((I[:,:,:,:,2] >> 3) << 10)

print(I.shape, I_rgb15.shape)

transparent_purple = 31 + (31 << 10)

ty,tx,_,_ = I_rgb15.shape

# we have 16 pallete banks, each tile line corresponds to a different palette
assert(ty <= 16)

palletes = []
for t in range(ty):
    colors = set(np.unique(I_rgb15[t]))
    if transparent_purple in colors:
        colors.remove( transparent_purple )

    # transparent_purple -> first elem always
    colors = [transparent_purple,] + sorted(colors)

    palletes.append(np.array(colors, dtype=np.uint32))

Ip = np.zeros((ty,tx,8,8), dtype=np.uint32)
for tty in range(ty):
    print((tty, palletes[tty], len(palletes[tty])))
    for ttx in range(tx):
        c = I_rgb15[tty,ttx,:,:].reshape((64,))
        m = np.zeros((64,), dtype=np.uint32)
        for pi,pc in enumerate(palletes[tty]):
            #lame
            m[c == pc] = pi
            assert( pi < 16 )
        Ip[tty,ttx] = m.reshape((8,8))

Ip_4bit = np.zeros((ty,tx,8,1), dtype=np.uint32)
for bx in range(8):
    kk = Ip[:,:,:,bx::8]
    Ip_4bit |= kk << (bx*4)

pal16u = np.zeros((16,16), dtype=np.uint16)
for i,p in enumerate(palletes):
    for j,c in enumerate(p):
        assert(c >= 0 and c < 0x7fff)
        pal16u[i,j] = c

def save_tileset(tileset_name, tileset_file, pal, tileset):
    header_file = tileset_file + ".h"
    asm_file    = tileset_file + ".s"

    pal = pal.ravel()
    tileset = tileset.ravel()

    pal_size     = pal.shape[0]     * 2
    tileset_size = tileset.shape[0] * 4

    with open(header_file, "w") as h:
        h.write("#pragma once\n")
        h.write("#define %s_PAL_SIZE   (%d)\n" % (tileset_name, pal_size))
        h.write("extern const short %s_PAL_DATA [%d];\n" % (tileset_name, pal.shape[0]))

        h.write("#define %s_TILES_SIZE   (%d)\n" % (tileset_name, tileset_size))
        h.write("extern const int %s_TILES_DATA [%d];\n" % (tileset_name, tileset.shape[0]))

    with open(asm_file, "w") as a:
        a.write(".section .rodata\n")
        a.write(".align 2\n")

        a.write(".global %s_PAL_DATA @ %d bytes\n" % (tileset_name, pal_size))
        a.write("%s_PAL_DATA:\n" % tileset_name)
        for c in range(0, pal.shape[0], 8):
            a.write(".hword %s\n" % ",".join(["0x{0:04x}".format(v) for v in pal[c:c+8]]))
        a.write("\n\n")

        a.write(".global %s_TILES_DATA @ %d bytes\n" % (tileset_name, tileset_size))
        a.write("%s_TILES_DATA:\n" % tileset_name)
        for c in range(0, tileset.shape[0], 8):
            a.write(".word %s\n" % ",".join(["0x{0:08x}".format(v) for v in tileset[c:c+8]]))
        a.write("\n\n")

#SAVE PALLETE

#TODO: SAVE TILESET TO .S AND .H AS A UINT32 ARRAY
save_tileset("tileset", "../src/tileset", pal16u, Ip_4bit)
