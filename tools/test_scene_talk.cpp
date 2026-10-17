// Scene picking, explicit groups and cancellation without downloading a model.
#define SCUMMVERSE_LOCAL_AI 1
#include "backends/platform/ios7/scummverse_ai_runtime.inc"
#include <cassert>
#include <iostream>
#include <cstdint>
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
 // No model: sending still works; replies are labelled classic lines in order.
 assert(!r.modelReady());
 assert(r.sendTalk("Hello everyone"));
 std::uint32_t revision=0; std::vector<Scummverse::ConversationLine> lines; std::vector<std::string> queued; int replying=-1;
 assert(r.talkSnapshot(revision,lines,queued,replying) && queued.empty() && replying==0);
 assert(lines.size()==3 && lines[0].speaker==0 && lines[0].text=="Hello everyone");
 assert(lines[1].kind==Scummverse::LineKind::Classic && lines[2].kind==Scummverse::LineKind::Classic);
 assert(lines[1].speaker!=lines[2].speaker && (lines[1].speaker==9 || lines[1].speaker==10));
 assert(!r.talkSnapshot(revision,lines,queued,replying)); // Unchanged revision.
 assert(!r.waitingForTalk());
 // Speech bubbles follow the transcript: the player (visitor 3) first.
 r.scene(56,3,nearby,true,speaker,text,sizeof(text)); assert(speaker==3 && std::string(text)=="Hello everyone");
 r.scene(56,3,nearby,false,speaker,text,sizeof(text)); assert(speaker==0); // Waits while speech shows.
 r.scene(56,3,nearby,true,speaker,text,sizeof(text)); assert(speaker==lines[1].speaker && lines[1].text==text);
 r.scene(56,3,nearby,true,speaker,text,sizeof(text)); assert(speaker==lines[2].speaker);
 r.scene(56,3,nearby,true,speaker,text,sizeof(text)); assert(speaker==0);
 assert(!r.sendTalk("") && !r.sendTalk(std::string(513,'x')));
 assert(r.sendTalk("<b>tags\nstripped</b>"));
 r.talkSnapshot(revision,lines,queued,replying);
 for(const auto &line:lines) assert(line.text.find('<')==std::string::npos && line.text.find('\n')==std::string::npos);
 assert(speechText("I\xe2\x80\x99m caf\xc3\xa9 \xf0\x9f\x91\xbd!")=="I'm caf? ?!"); // Smart quote, accent, emoji.
 assert(speechText("a@b^c{d}")=="a b c d ");
 for(int n=0;n<4;++n) assert(r.sendTalk("queue")); // Classic replies drain instantly; never stuck.
 assert(!r.waitingForTalk());
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
 // People chips and the always-ready composer.
 r.endTalk(); r.scene(60,3,(1u<<9)|(1u<<10),true,speaker,text,sizeof(text));
 assert(!r.toggleTalk(24) && !r.talkingWith()); // Not here.
 assert(r.toggleTalk(9) && r.talkingTo()==9 && r.talkingWith()==1u<<9);
 assert(r.toggleTalk(10) && r.talkingTo()==-2 && r.talkingWith()==((1u<<9)|(1u<<10)));
 assert(r.toggleTalk(9) && r.talkingTo()==10 && r.talkingWith()==1u<<10); // Back to one person.
 assert(r.toggleTalk(10) && !r.talkingWith() && !r.talkingTo());           // Last one ends it.
 assert(r.sendNearby("Hi all")==1 && r.talkingTo()==-1 && r.talkingWith()==((1u<<9)|(1u<<10)));
 r.scene(60,3,(1u<<9)|(1u<<10)|(1u<<11),true,speaker,text,sizeof(text));
 assert(r.talkingWith()==((1u<<9)|(1u<<10)|(1u<<11))); // Nearby group follows arrivals.
 assert(r.sendNearby("")==-1 && r.sendNearby(std::string(513,'x'))==-1);
 r.endTalk(); r.scene(61,3,1u<<11,true,speaker,text,sizeof(text));
 assert(r.sendNearby("Hello")==1 && r.talkingTo()==11 && r.talkingWith()==1u<<11); // One person directly.
 r.endTalk(); r.scene(62,3,0,true,speaker,text,sizeof(text));
 assert(r.sendNearby("Anyone?")==0 && !r.talkingWith());
 // Original residents are addressable by their scene identity.
 r.scene(68,3,1u<<15,true,speaker,text,sizeof(text));
 assert(std::string(actorName(15))=="Guru" && r.toggleTalk(15));
 r.scene(67,3,1u<<15,true,speaker,text,sizeof(text)); assert(std::string(actorName(15))=="Nepal guard");
 assert(std::string(roomName(200))=="Melee Island town" && std::string(roomName(206))=="Woodtick"); // Other worlds.
 std::cout<<"PASS people chips and nearby composer\n";
 std::cout<<"PASS scene picking, explicit participant membership, departures, stale selections, classic fallback and transcript order\n";
}
