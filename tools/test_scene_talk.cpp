// Scene picking, explicit groups and cancellation without downloading a model.
#define SCUMMVERSE_LOCAL_AI 1
#include "backends/platform/ios7/scummverse_ai_runtime.inc"
#include <cassert>
#include <iostream>
int main() {
 using namespace ScummverseLocalAI;
 auto &r=runtime(); int speaker; char text[600];
 unsigned nearby=(1u<<9)|(1u<<10)|(1u<<24);
 r.scene(56,3,nearby,true,speaker,text,sizeof(text));
 assert(!r.pick(9)); r.armPick(false); assert(r.picking());
 assert(r.pick(0) && !r.talkingWith() && r.picking());
 assert(r.pick(9) && r.talkingTo()==9 && !r.picking());
 r.armPick(true); assert(r.pick(10));
 assert(r.talkingTo()==-2 && r.talkingWith()==((1u<<9)|(1u<<10)));
 r.scene(56,3,nearby,true,speaker,text,sizeof(text));
 assert(!(r.talkingWith() & (1u<<24))); // Uninvited bystander doesn't join.
 assert(!r.sendTalk("Keep this unsent message")); // No model, honest failure.
 r.scene(56,3,1u<<10,true,speaker,text,sizeof(text)); assert(r.talkingWith()==1u<<10);
 r.scene(57,3,nearby,true,speaker,text,sizeof(text)); assert(!r.talkingWith());
 r.armPick(false); r.scene(58,3,nearby,true,speaker,text,sizeof(text));
 assert(r.pick(9) && !r.talkingWith()); // Stale selection cannot target next room.
 r.armPick(false); r.endTalk(); assert(!r.picking());
 r.scene(54,3,(1u<<20)|(1u<<21)|(1u<<22),true,speaker,text,sizeof(text));
 r.armPick(false); assert(r.pick(20)); r.armPick(true); assert(r.pick(21)); r.armPick(true); assert(r.pick(22));
 assert(r.talkingWith()==((1u<<20)|(1u<<21)|(1u<<22)));
 assert(std::string(actorName(20))=="Annie Larris");
 assert(std::string(actorName(21))=="Melissa China");
 assert(std::string(actorName(22))=="Leslie Bennett");
 std::cout<<"PASS scene picking, explicit participant membership, departures, stale selections and no-model feedback\n";
}
