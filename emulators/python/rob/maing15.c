//  protocluster.c

//  Created by Lloyd Hasley on 5/16/25.
//  -- updated for G-15 compatibility RBK 5/22/25.

// emulates an 8x8 grid (64 sensors)
// ans:  4,4 4665

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>

extern void expandS2S4(void);
extern int EnergyDeCompress(int energy_float);

// protocol field sizes
#define FIELD_SIZE_S2      100	// number of bits of S2 mask
#define FIELD_SIZE_S4       32	// number of bits that have S4 active
#define FIELD_SIZE_CELLS    50	// energy cells above S2threshold

#define ARRAY_SIZE           8	// 8x8 (fiber data represents 8x8 grid)
#define NUM_CELLS_ARRAY ((1+ARRAY_SIZE+1) * (1+ARRAY_SIZE+1))
		   // count of cluster cells PLUS guards

// FIBER DATA PACKET
uint16_t    Data[FIELD_SIZE_CELLS] = {  // sparse data
		103, 167, 114, 103, 298, 557, 307, 144, 205, 555,
		962, 615, 121, 400, 582, 389, 157
	    };
uint32_t    S2mask[4] = {0x3800000, 0xf03c1f, 0x1, 0x0};	
				// which 8x8 elt represented by Data
uint32_t    S4in_mask = 0x400;	// which S2mask elt's are 4sigma
				// [applied to compressed mask] not

// original data:
//             0   1   2   3   4*  5   6   7   8   9
//  0           0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
//  1           0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
//  2           0,  0,  5,103,167,114,  0,  0,  0,  0,
//  3           0,  0,103,298,557,307,144,  0,  0,  0,
//  4*          0,  0,205,555,962,615, 77,  0,  0,  0,
//  5           0,  0,121,400,582,389, 18,  0,  0,  0,
//  6           0,  0,  0, 97,157, 48,  0,  0,  0,  0,
//  7           0,  0,  0,  0,  0,  0,  0   0,  0,  0,
//  8           0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
//  9           0,  0,  0,  0,  0,  0,  0,  0,  0,  0};

uint32_t    S4mask[4];			//  uncompressed S4mask
uint16_t    Energy[NUM_CELLS_ARRAY];    // uncompressed Data

    // convert S4 mask to uncompressed
void
expandS2S4(void) {
    int i_mask = 0;		// counts through the four 32-bit S2mask's
    uint32_t  S2temp  = S2mask[i_mask];	// gradually shifts down to empty
    uint32_t  S4input = S4in_mask;	// likewise shifts 
    int i = 0;
    int i_data = 0;
    for (int i_mask = 0; i_mask < 4; i_mask++) {
        uint32_t S4bit = 1;
        uint32_t S2temp = S2mask[i_mask];
	for (int j = 0; j < 32; j++) {
	    if (S2temp & 1) {
                if(S4input & 1) {
                    S4mask[i_mask] |= S4bit;
                }
                Energy[i] = EnergyDeCompress(Data[i_data++]);
                S4input >>= 1;
	    }
            S2temp >>= 1;
	    S4bit <<= 1;
	    i++;
	}
    }
DONE:;

printf("Reconstructed sensor input:\n");
int k = 0;
for (int r = 0; r < 10; r++) {
    printf("%2d: ", r);
    for (int c = 0; c < 10; c++) {
	printf("%5d", Energy[k]);
	k++;
    }
    printf("\n");
}

}

// search the 8x8 grid
// * for S4 data points marking cluster center
// * sum all of the energy obtained in the cluster
//   (s4 is center point; +- 1 for surround)

void
SumCluster() {
    int sum;
    int r,c;     // rectangle coordinate of cluster center for printout

    r = 1;
    c = 1;
    int i1 = 0;
    int i2 = 10;
    int i3 = 20;
    int jstart = 11;
    // S4mask[0] >>= 11;
    S4mask[0] /= 2048;
    for (int i_mask = 0; i_mask < 4; i_mask++) {
        uint32_t S4maskT = S4mask[i_mask];
	for (int j = jstart; j < 32; j++) {
            if (S4maskT & 1) { // S4 cluster ?
	        int sum = Energy[i1] + Energy[i1+1] + Energy[i1+2]
		        + Energy[i2] + Energy[i2+1] + Energy[i2+2]
		        + Energy[i3] + Energy[i3+1] + Energy[i3+2];
	         printf("cluster @ %d:%d: total energy=%d\n", r, c, sum);
	    }
            S4maskT >>= 1;
	    i1++;
	    i2++;
	    i3++;
	    if (++c >= 10) {
	        c = 0;
	        r++;
		if (r >= 10) goto DONE;
	    }
	}
	jstart = 0;
    }
DONE:
}

int EnergyDeCompress(int energy_float) {
	return energy_float;
//     int exp;
//     int mag;
//     int energy;
//     
//     exp = energy_float >> 6;
//     mag = energy_float & 0x3f;
//     
//     energy = mag << (exp << 2);
//     
//     return energy;
}

// int EnergyCompress(int energy) {
//     int exp;
//     int mag;
//     int energyCompressed;
//     
//     mag = energy;
//     if(energy & 0x3ffff) {
//         exp = 3;
//         mag >>= 6;
//     }
//     else if(energy & 0xffff) {
//         exp = 2;
//         mag >>= 4;
//     }
//     else if(energy & 0x3ff) {
//         exp = 1;
//         mag >>= 2;
//     } else {
//         exp = 0;
//     }
// 
//     mag &= 0xff;
//     energyCompressed = (exp<<8) | mag;
//     return energyCompressed;
// }


int main(int argc, const char * argv[]) {
    for (int i = 0; i<NUM_CELLS_ARRAY; i++) {	// clear Energy
        Energy[i] = 0;
    }
    expandS2S4();
    SumCluster();
    return 0;
}
