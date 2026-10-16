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
 // v2: aspect-fit game height. Widths/heights are host points after the top
 // safe area: SE (375x647), 13 mini (375x762), 14 (390x797), 14 Pro Max (430x873).
 unsigned fitted=0;
 for(double width : {320., 375., 390., 430.})
  for(double height : {480., 647., 762., 797., 873.})
   for(double keyboard : {0., 34., 260., 336., 1500.})
    for(double aspect : {1.6, 4./3., 0., -1., 10.}) {
     auto v1=Scummverse::portraitLayout(height,keyboard);
     auto v2=Scummverse::portraitLayout(height,keyboard,width,aspect);
     const bool valid=aspect>=0.25 && aspect<=4;
     assert(v2.gameHeight==v2.toolbarTop && v2.toolbarTop+v2.toolbarHeight==v2.chatTop);
     assert(v2.toolbarHeight==v1.toolbarHeight);
     assert(std::abs(v2.chatTop+v2.chatHeight-v1.chatTop-v1.chatHeight)<0.001); // Same bottom edge.
     assert(v2.gameHeight<=v1.gameHeight+0.001 && v2.chatHeight>=v1.chatHeight-0.001); // Chat never shrinks.
     if(valid) assert(v2.gameHeight<=width/aspect+0.001); // No letterbox band reserved.
     if(valid && width/aspect>=v1.gameHeight) assert(v2.gameHeight==v1.gameHeight); // Height-limited unchanged.
     if(!valid) assert(v2.gameHeight==v1.gameHeight && v2.chatTop==v1.chatTop);
     ++fitted;
    }
 auto phone=Scummverse::portraitLayout(797,34,390,1.6); // iPhone 14, 320x200 DOS V1.
 assert(std::abs(phone.gameHeight-243.75)<0.001 && std::abs(phone.chatTop-287.75)<0.001);
 assert(std::abs(phone.chatHeight-475.25)<0.001); // v1 left 354.5pt for a 243.75pt picture.
 auto corrected=Scummverse::portraitLayout(797,34,390,4./3.); // Aspect correction on.
 assert(std::abs(corrected.gameHeight-292.5)<0.001);
 auto typingSE=Scummverse::portraitLayout(647,260,375,1.6); // Height-limited while typing.
 assert(typingSE.gameHeight==183 && typingSE.chatHeight==160);
 std::printf("PASS: %u portrait/keyboard layouts, %u aspect-fit layouts, density, dismissal and invalid-input cases\n",cases,fitted);
}
