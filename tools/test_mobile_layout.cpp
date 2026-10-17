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

 // v3: split screen while chatting. Portrait: game half on top, chat below.
 unsigned split=0;
 for(double width : {320., 375., 390., 430., 667., 844., 932., 1194.})
  for(double height : {320., 375., 390., 430., 647., 797., 873., 1194.})
   for(double keyboard : {0., 21., 162., 216., 336., 2000.})
    for(double aspect : {1.6, 4./3., 0.})
     for(bool first : {true, false}) {
      auto open=Scummverse::splitLayout(width,height,keyboard,aspect,true,first);
      auto closed=Scummverse::splitLayout(width,height,keyboard,aspect,false,first);
      const double available=std::max(0.,height-std::max(0.,std::min(keyboard,height)));
      auto inside=[](Scummverse::Box inner, Scummverse::Box outer) {
       return inner.x>=outer.x-0.001 && inner.y>=outer.y-0.001 && inner.x+inner.w<=outer.x+outer.w+0.001 && inner.y+inner.h<=outer.y+outer.h+0.001;
      };
      assert(open.split && !closed.split);
      assert(inside(open.game,open.gameArea) && inside(closed.game,closed.gameArea));
      if(aspect>0 && open.game.h>0) assert(std::abs(open.game.w/open.game.h-aspect)<0.001);
      if(width<height) {
       // Halves: the game half (with toolbar) above, the chat half below.
       assert(std::abs(open.chat.y-available/2)<0.001 && std::abs(open.chat.y+open.chat.h-available)<0.001);
       assert(open.gameArea.y==0 && open.gameArea.y+open.gameArea.h<=open.toolbar.y+0.001);
       assert(std::abs(open.toolbar.y+open.toolbar.h-open.chat.y)<0.001);
       assert(open.chat.w==width && open.chat.x==0);
       // Closed keeps the v2 portrait layout.
       auto v2=Scummverse::portraitLayout(height,keyboard,width,aspect);
       assert(closed.chat.y==v2.chatTop && closed.gameArea.h==v2.gameHeight);
      } else {
       // Side by side: chat on the chosen half, above the keyboard.
       assert(std::abs(open.chat.w-width/2)<0.001 && std::abs(open.gameArea.w-width/2)<0.001);
       assert(open.chat.x==(first?0:width/2) && open.gameArea.x==(first?width/2:0));
       assert(std::abs(open.chat.h-available)<0.001 && open.gameArea.h==height);
       assert(closed.chat.w==0 && closed.gameArea.w==width && closed.gameArea.h==height);
       // Chat and game never overlap.
       assert(open.chat.x+open.chat.w<=open.game.x+0.001 || open.game.x+open.game.w<=open.chat.x+0.001);
      }
      ++split;
     }
 auto land=Scummverse::splitLayout(844,390,0,1.6,true,true); // iPhone 14 landscape, DOS V1.
 assert(land.chat.x==0 && land.chat.w==422 && land.gameArea.x==422);
 assert(std::abs(land.game.w-422)<0.001 && std::abs(land.game.h-263.75)<0.001 && std::abs(land.game.y-63.125)<0.001);
 auto swapped=Scummverse::splitLayout(844,390,0,1.6,true,false);
 assert(swapped.chat.x==422 && swapped.game.x==0);
 auto tall=Scummverse::splitLayout(390,797,34,1.6,true);
 assert(std::abs(tall.chat.y-381.5)<0.001 && std::abs(tall.game.h-243.75)<0.001 && std::abs(tall.toolbar.y-337.5)<0.001);
 std::printf("PASS: v3 split layout (%u cases)\n",split);
}
