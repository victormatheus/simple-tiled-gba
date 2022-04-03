
#include <string.h>
#include <stdio.h>
#include <tonc.h>

#include "tileset.h"
#include "test_map.h"

OBJ_ATTR obj_buffer[128];
OBJ_AFFINE *obj_aff_buffer = (OBJ_AFFINE*)obj_buffer;

#define CBB_0  0
#define SBB_0 28

#define CROSS_TX 15
#define CROSS_TY 10

BG_POINT bg0_pt= { 0, 0 };
SCR_ENTRY *bg0_map= se_mem[SBB_0];


u32 se_index(u32 tx, u32 ty, u32 pitch)
{	
	u32 sbb= ((tx>>5)+(ty>>5)*(pitch>>5));

	return sbb*1024 + ((tx&31)+(ty&31)*32);
}

void init_map()
{
	int ii, jj;

	// initialize a background
	REG_BG0CNT= BG_CBB(CBB_0) | BG_SBB(SBB_0) | BG_REG_64x64;
	REG_BG0HOFS= 0;
	REG_BG0VOFS= 0;

	// create the tiles: basic tile and a cross
	const TILE tiles[5] = 
	{
		{{0x22212221,
          0x11111111,
          0x21222121,
          0x11111111, 
		  0x22212221,
          0x11111111,
          0x21222121,
          0x11111111}},

		{{0x11111111,
          0x11111111,
          0x11111111,
          0x11121111, 
		  0x11111111,
          0x11111111,
          0x11111111,
          0x11111111}},

        {{0x31333131,
          0x11111111,
          0x31333131,
          0x11333111, 
		  0x31333131,
          0x11333111,
          0x31333131,
          0x11111111}},

        //FLIPPED BC ITS LITTLE-ENDIAN
        {{0x11313111,
          0x11333311,
          0x33313111,
          0x33333131, 
		  0x11111133,
          0x31333133,
          0x11311311,
          0x11111111}},

		{{0x00000000, 0x00100100, 0x01100110, 0x00011000,
		  0x00011000, 0x01100110, 0x00100100, 0x00000000}},
	};

    memcpy32(pal_bg_mem,   tileset_PAL_DATA,   tileset_PAL_SIZE/4);
    memcpy32(&tile_mem[0], tileset_TILES_DATA, tileset_TILES_SIZE/4);

	// Create a map: four contingent blocks of 
	//   0x0000, 0x1000, 0x2000, 0x3000.
	SCR_ENTRY *pse= bg0_map;
    int k = 0;
	for(ii=0; ii<4; ii++) {
		for(jj=0; jj<32*32; jj++) {
            int tile = test_map_DATA[k++];
			*pse++= SE_PALBANK(tile / 8) | tile;
        }
    }
    
    // OBJ tiles
    tile_mem[4][0] = tiles[3];

    // create a palette OBJ
    pal_obj_bank[0][1] = RGB15( 0, 0, 0);
    pal_obj_bank[0][2] = RGB15( 0,31, 0);
    pal_obj_bank[0][3] = RGB15(31,28,10);

	oam_init(obj_buffer, 128);

#if 0
	memset(bgt, 0, sizeof(TMapInfo));

	bgt->flags= bgnr;
	bgt->cnt= ctrl;
	bgt->dstMap= se_mem[BFN_GET(ctrl, BG_SBB)];

	REG_BGCNT[bgnr]= ctrl;
	REG_BG_OFS[bgnr].x= 0;
	REG_BG_OFS[bgnr].y= 0;


	bgt->srcMap= (SCR_ENTRY*)map;
	bgt->srcMapWidth= map_width;
	bgt->srcMapHeight= map_height;

	int ix, iy;
	SCR_ENTRY *dst= bgt->dstMap, *src= bgt->srcMap;
	for(iy=0; iy<32; iy++)
		for(ix=0; ix<32; ix++)
			dst[iy*32+ix]= src[	iy*bgt->srcMapWidth+ix];
#endif
}

int main()
{
	init_map();

	OBJ_ATTR *metr= &obj_buffer[0];
	obj_set_attr(metr, 
		ATTR0_SQUARE,				// Square, regular sprite
		ATTR1_SIZE_8,				// 8x8p, 
		ATTR2_PALBANK(0) | 0);		// palbank 0, tile 0

	REG_DISPCNT= DCNT_MODE0 | DCNT_BG0 | DCNT_OBJ | DCNT_OBJ_1D;

	u32 tx, ty, se_curr, se_prev= CROSS_TY*32+CROSS_TX;
	
    int hero_x = 0, hero_y = 0;

	bg0_map[se_prev]++;	// initial position of cross
	while(1)
	{
		vid_vsync();

		key_poll();
		bg0_pt.x += key_tri_horz();
		bg0_pt.y += key_tri_vert();

        //WHYYYY?
        if ( key_released(KI_LEFT) )  { hero_x -= 2; }
        if ( key_released(KI_RIGHT) ) { hero_x += 2; }
        if ( key_released(KI_UP) )    { hero_y -= 2; }
        if ( key_released(KI_DOWN) )  { hero_y += 2; }

		// Testing bg_se_id()
		// If all goes well the cross should be around the center of
		// the screen at all times.
		tx= ((bg0_pt.x>>3)+CROSS_TX) & 0x3F;
		ty= ((bg0_pt.y>>3)+CROSS_TY) & 0x3F;
		
		se_curr= se_index(tx, ty, 64);
		if(se_curr != se_prev)
		{
			bg0_map[se_prev]--;
			bg0_map[se_curr]++;
			se_prev= se_curr;
		}

		REG_BG_OFS[0]= bg0_pt;	// write new position

	    obj_set_pos(metr, hero_x, hero_y);

		oam_copy(oam_mem, obj_buffer, 1);	// only need to update one
	}
	return 0;
}
