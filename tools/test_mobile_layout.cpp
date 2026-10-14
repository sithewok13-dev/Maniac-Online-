// Portable layout acceptance cases. No UIKit or proprietary game fixtures.
#include "common/scummverse_layout.h"
#include <algorithm>
#include <initializer_list>
#include <cassert>
#include <cmath>
#include <cstdio>
int main() {
 unsigned cases=0;
 for(double height : {480., 548., 647., 785., 844., 932., 1024.})
  for(double keyboard : {0., 34., 216., 291., 350., 440., 1500.}) {
   auto l=Scummverse::portraitLayout(height,keyboard);
   assert(l.gameHeight>=0 && l.toolbarHeight>=0 && l.chatHeight>=0);
   assert(l.gameHeight==l.toolbarTop);
   assert(l.toolbarTop+l.toolbarHeight==l.chatTop);
   assert(l.chatTop+l.chatHeight<=height);
   assert(std::abs(l.chatTop+l.chatHeight-std::max(0.,height-keyboard))<0.001);
   assert(l.chatTop<=height/2);
   if(height-keyboard>=160) assert(l.chatHeight>=160);
   // The same point geometry at 1x, 2x and 3x yields identical input bounds
   // to within one physical pixel; backing surface height remains unchanged.
   for(double scale : {1.,2.,3.}) {
    int physical=(int)(l.gameHeight*scale);
    assert(std::abs(physical/scale-l.gameHeight)<1/scale+0.001);
    assert(physical<=l.toolbarTop*scale);
   }
   ++cases;
  }
 auto normal=Scummverse::portraitLayout(800,34);
 assert(normal.gameHeight==356 && normal.chatTop==400 && normal.chatHeight==366);
 auto typing=Scummverse::portraitLayout(548,291);
 assert(typing.gameHeight==53 && typing.toolbarHeight==44 && typing.chatTop==97 && typing.chatHeight==160);
 auto hidden=Scummverse::portraitLayout(800,0);
 assert(hidden.chatTop==400 && hidden.gameHeight==356);
 assert(Scummverse::portraitLayout(0,0).chatHeight==0);
 assert(Scummverse::portraitLayout(-1,0).gameHeight==0);
 assert(Scummverse::portraitLayout(800,-20).chatTop==400);
 std::printf("PASS: %u portrait/keyboard layouts, density, dismissal and invalid-input cases\n",cases);
}
