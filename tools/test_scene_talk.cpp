// Scene picking, explicit groups and cancellation without downloading a model.
#define SCUMMVERSE_LOCAL_AI 1
#include "backends/platform/ios7/scummverse_ai_runtime.inc"
#include <cassert>
#include <iostream>
#include <cstdint>
int main() {
 using namespace ScummverseLocalAI;
 // Who follows: Maniac's and Zak's people by their numbers; in the new engine
 // (sandbox), its visitors (kWanderer + slot) by their slots, any of them able
 // to be asked along. The chat's token from the place told.
 scummverseTravelScene(5,3,1u<<7,0,0);
 assert(follows(7) && !follows(8) && canFollow(7) && !canFollow(kWanderer) && sceneToken()==((5*32+3)<<8));
 assert(!canFollow(kZakResidentActor)); // (The game never lets the resident actor follow.)
 scummverseSandboxActive(true);
 scummverseTravelScene(10033,1,1u<<2,0,0);
 assert(follows(kWanderer+2) && !follows(kWanderer+3) && !follows(2) && canFollow(kWanderer) && canFollow(kTalkActors-1) && !canFollow(kTalkActors) && !canFollow(kGuestActor));
 assert(sceneToken()==((10033*32+1)<<8));
 scummverseSandboxActive(false); scummverseTravelScene(0,0,0,0,0);
 assert(!follows(kWanderer+2) && !canFollow(kWanderer));
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
 assert(speechText("2+2=4 a_b ~ok~")=="2+2=4 a_b ~ok~"); // The transcript keeps them; only bubbles say them otherwise.
 // A sentence ends at its end: not after a title or an initial, inside a
 // number or at an ellipsis before more of it. A reply still arriving
 // (complete false) has a sentence only once what follows shows it ended.
 assert(cleanLine("Go and ask Dr. Smith about it. Then leave.")=="Go and ask Dr. Smith about it.");
 assert(cleanLine("It runs on 3.5 volts, Mr. Jones! Really.")=="It runs on 3.5 volts, Mr. Jones!");
 assert(cleanLine("The U.S. Navy called again today.")=="The U.S. Navy called again today.");
 assert(cleanLine("I wonder... maybe it hears us. No.")=="I wonder... maybe it hears us.");
 assert(cleanLine("So do I. Let us go now.")=="So do I." && cleanLine("That is Ed's. Put it back.")=="That is Ed's.");
 assert(cleanLine("Really?! Wow, okay.")=="Really?!" && cleanLine("We need plan B.")=="We need plan B.");
 assert(cleanLine("Go and ask Dr.",false).empty() && cleanLine("Go and ask Dr. Smith",false).empty());
 assert(cleanLine("It runs on 3.",false).empty() && cleanLine("Hello there, friend!",false).empty());
 assert(cleanLine("Hello there, friend! ",false)=="Hello there, friend!");
 assert(cleanLine("Go and ask Dr. Smith about it. T",false)=="Go and ask Dr. Smith about it.");
 assert(cleanReply("Edna: It is 3.5 meters tall, Mr. Jones. Indeed.",10,false)=="It is 3.5 meters tall, Mr. Jones.");
 // As generate() reads a reply arriving: it stops at the first sentence known to have ended.
 for(const char *reply:{"Go and ask Dr. Smith about it. Then leave.","It is 3.5 meters tall.","I wonder... maybe it hears us.","The U.S. Navy called again today."}) {
  std::string arrived; const std::string full=reply;
  for(char c:full) { arrived+=c; if(!cleanReply(arrived,10,false).empty()) break; }
  assert(cleanReply(arrived,10)==cleanLine(full) && full.compare(0,cleanLine(full).size(),cleanLine(full))==0);
 }
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
 assert(r.sendNearby(std::string(513,'x'))==-1);
 // Nothing a bubble can show: a distinct result (not "three waiting"), with no side effects.
 assert(r.sendNearby("")==-2 && r.sendNearby("<@^>")==-2 && !r.sendTalk("{ }"));
 assert(r.talkingWith()==((1u<<9)|(1u<<10)|(1u<<11)));
 // In "Everyone" no one's chip is shown chosen: a name talks with them
 // alone. A group down to one is a talk with that one (their chip ends it).
 assert(r.toggleTalk(10) && r.talkingTo()==10 && r.talkingWith()==1u<<10);
 r.endTalk(); assert(r.sendNearby("Hi all")==1 && r.talkingTo()==-1);
 r.scene(60,3,1u<<10,true,speaker,text,sizeof(text)); // Fred and Ed walk off.
 assert(r.talkingTo()==10 && r.talkingWith()==1u<<10);
 r.scene(60,3,(1u<<9)|(1u<<10),true,speaker,text,sizeof(text));
 assert(r.talkingTo()==10 && r.talkingWith()==1u<<10 && r.toggleTalk(10) && !r.talkingWith());
 assert(r.toggleTalk(9) && r.toggleTalk(10) && r.talkingTo()==-2);
 r.scene(60,3,1u<<9,true,speaker,text,sizeof(text)); assert(r.talkingTo()==9 && r.talkingWith()==1u<<9);
 r.endTalk(); r.scene(60,3,(1u<<9)|(1u<<10)|(1u<<11),true,speaker,text,sizeof(text));
 assert(r.sendNearby("<>")==-2 && !r.talkingWith()); // (none started)
 r.endTalk(); r.scene(61,3,1u<<11,true,speaker,text,sizeof(text));
 assert(r.sendNearby("Hello")==1 && r.talkingTo()==11 && r.talkingWith()==1u<<11); // One person directly.
 r.endTalk(); r.scene(62,3,0,true,speaker,text,sizeof(text));
 assert(r.sendNearby("Anyone?")==0 && !r.talkingWith());
 // Original residents are addressable by their scene identity.
 r.scene(68,3,1u<<15,true,speaker,text,sizeof(text));
 assert(std::string(actorName(15))=="Guru" && r.toggleTalk(15));
 r.scene(67,3,1u<<15,true,speaker,text,sizeof(text)); assert(std::string(actorName(15))=="Nepal guard");
 // Other worlds arrive as place keys: 10000 + game * 1000 + that game's room.
 assert(std::string(roomName(10033))=="Melee Island town" && std::string(roomName(11007))=="Woodtick");
 assert(std::string(roomName(10099))=="The Secret of Monkey Island"); // An unnamed room of that game.
 assert(std::string(roomName(10070))=="Catacombs and the ghost ship"); // A story area's entrance.
 // Other-world characters are guest actors 25..29, one per cast slot of the
 // place (game 0 room 35 has three characters; game 6 room 9 is Sam & Max's street).
 using Scummverse::WorldCatalog::worldGuestAt;
 assert(worldGuestAt(10035,0) && worldGuestAt(10035,2) && worldGuestAt(16009,0));
 r.scene(10035,3,(1u<<25)|(1u<<26)|(1u<<27),true,speaker,text,sizeof(text));
 assert(std::string(actorName(25))==worldGuestAt(10035,0)->name && std::string(actorName(27))==worldGuestAt(10035,2)->name);
 assert(std::string(personality(26))==worldGuestAt(10035,1)->personality && r.toggleTalk(27));
 r.scene(16009,3,(1u<<25),true,speaker,text,sizeof(text)); assert(std::string(actorName(25))==worldGuestAt(16009,0)->name);
 assert(std::string(actorName(15))=="visitor"); // The resident actor stays with Zak's residents.
 r.scene(10999,3,0,true,speaker,text,sizeof(text)); assert(std::string(actorName(25))=="visitor");
 // A sandbox character playing someone from another game chats as them.
 using Scummverse::WorldCatalog::worldAppearanceKey; using Scummverse::WorldCatalog::worldAppearance;
 const int indy=worldAppearanceKey(3,2);
 scummverseTalkAppearance(3,indy);
 assert(std::string(actorName(3))=="Indiana Jones" && std::string(personality(3))==worldAppearance(indy)->personality);
 assert(worldAppearance(indy)->lines[0] && classicReply(3,0)==worldAppearance(indy)->lines[0] && classicReply(3,4)==worldAppearance(indy)->lines[1]);
 scummverseTalkAppearance(3,worldAppearanceKey(3,999)); assert(std::string(actorName(3))=="Dave"); // Unknown: himself.
 scummverseTalkAppearance(3,0); assert(std::string(actorName(3))=="Dave" && classicReply(3,0)!=worldAppearance(indy)->lines[0]);
 scummverseTalkAppearance(30,indy); scummverseTalkAppearance(-1,indy); // Out of range: ignored.
 // Wanderers visiting are talk IDs 30..55 (past 32 bits): named and played
 // as themselves, picked, joined and left like anyone.
 const int guybrush=worldAppearanceKey(0,1);
 scummverseTalkVisitor(0,guybrush); scummverseTalkVisitor(25,indy); scummverseTalkVisitor(26,indy); scummverseTalkVisitor(-1,indy);
 assert(std::string(actorName(30))=="Guybrush Threepwood" && std::string(actorName(55))=="Indiana Jones" && std::string(personality(55))==worldAppearance(indy)->personality);
 r.endTalk();
 const uint64_t far=(uint64_t(1)<<30)|(uint64_t(1)<<55)|(1u<<10);
 r.scene(10,3,far,true,speaker,text,sizeof(text));
 assert(r.actorsInRoom()==far && r.toggleTalk(55) && r.talkingTo()==55 && r.talkingWith()==uint64_t(1)<<55);
 assert(r.toggleTalk(30) && r.talkingTo()==-2 && r.talkingWith()==((uint64_t(1)<<30)|(uint64_t(1)<<55)));
 r.scene(10,3,(uint64_t(1)<<30)|(1u<<10),true,speaker,text,sizeof(text)); // Indy walks off.
 assert(r.talkingWith()==uint64_t(1)<<30);
 assert(!r.toggleTalk(56) && !r.toggleTalk(55)); // Past the last slot; not here.
 r.endTalk(); assert(r.sendNearby("Ahoy")==1 && r.talkingTo()==-1 && r.talkingWith()==((uint64_t(1)<<30)|(1u<<10)));
 r.endTalk(); scummverseTalkVisitor(0,0); assert(std::string(actorName(30))=="visitor");
 std::cout<<"PASS wanderers past 32 talk IDs\n";
 std::cout<<"PASS people chips and nearby composer\n";
 std::cout<<"PASS scene picking, explicit participant membership, departures, stale selections, classic fallback and transcript order\n";
}
