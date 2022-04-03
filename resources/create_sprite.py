import numpy as np
from PIL import Image

#imgs = [ 'ball.png', 'bar.png', 'block.png', 'wall.png', 'floor.png' ]
imgs = [ 'wall.png', 'floor.png' ]

As = []
for i in imgs:
    A = np.array(Image.open(i))
    H,W,_ = A.shape
    A = A[:,:,0:3]
    A = A.reshape((H//8,8,W//8,8,3)).transpose((0,2,1,3,4)).reshape(-1,8,8,3)
    As.append(A)

I = np.concatenate(As, axis=0).reshape(-1,3).astype(int)

I_rgb15 = (I[:,0] >> 3) | ((I[:,1] >> 3) << 5) | ((I[:,2] >> 3) << 10)

colors = np.unique(I_rgb15)
assert(colors.shape[0] < 16)

print(colors)

Ir = I.reshape(-1,3)
pI = np.zeros((Ir.shape[0]), dtype=np.uint32)
for i,c in enumerate(colors):
    B = (I_rgb15 == c)
    pI[B] = i+1

pI_4bit = np.zeros(Ir.shape[0] // 8, dtype=np.uint32)
for b in range(8):
    pI_4bit |= pI[b::8] << (b*4)

print(pI_4bit)

for b in range(8):
    print((pI_4bit[0] >> (4*b)) & 0xF)

