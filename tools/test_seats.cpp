// SPDX-License-Identifier: GPL-3.0-or-later
#include "common/scummverse_seats.h"
#include "engines/scumm/scummverse_plane.h"
#include <cassert>
#include <climits>
#include <cstring>
#include <iostream>
int main() {
 int seats[25]={};
 using ScummverseTransport::allocateSeats;
 assert(allocateSeats((1u<<3)|(1u<<24),seats,25,6));
 int original=seats[24]; seats[3]=-seats[3];
 assert(allocateSeats((1u<<3)|(1u<<24)|(1u<<1),seats,25,6));
 assert(seats[24]==original && seats[3]<0 && seats[1]>0);
 unsigned mask=0; for(int id : {1,3,5,20,21,24}) mask|=1u<<id;
 assert(allocateSeats(mask,seats,25,6));
 int snapshot[25]; memcpy(snapshot,seats,sizeof seats);
 assert(!allocateSeats(mask|(1u<<22),seats,25,6));
 assert(!memcmp(snapshot,seats,sizeof seats));
 seats[1]=INT_MIN;seats[5]=seats[24];
 assert(allocateSeats(mask,seats,25,6));
 unsigned used=0;
 for(int id=0;id<25;++id) if(mask&(1u<<id)) {
  int slot=seats[id]<0?-seats[id]:seats[id];
  assert(slot>=1 && slot<=6 && !(used&(1u<<slot)));used|=1u<<slot;
 }
 assert(allocateSeats(1u<<24,seats,25,6) && seats[3]==0);
 assert(!allocateSeats(1u<<30,seats,25,6));
 unsigned char masks[4096], before[4096];
 for(int i=0;i<4096;++i) masks[i]=(i*13)%251;
 memcpy(before,masks,sizeof masks);
 assert(!ScummverseZakPlane::extendChairMasks(masks,120,17));
 assert(!memcmp(before,masks,sizeof masks));
 assert(ScummverseZakPlane::extendChairMasks(masks,100,16));
 for(int seat : ScummverseZakPlane::seatX) for(int dx=-1;dx<=5;++dx) {
  for(int y=10;y<16;++y) assert(masks[(seat+dx)*16+y]==before[(63+dx)*16+y]);
  for(int y=0;y<10;++y) assert(masks[(seat+dx)*16+y]==before[(seat+dx)*16+y]);
 }
 std::cout<<"Seat allocation contract passed\n";
}
