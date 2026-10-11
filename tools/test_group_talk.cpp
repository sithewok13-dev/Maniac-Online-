// Shared-history/turn scheduling and real Qwen3 group conversation probe.
#define SCUMMVERSE_LOCAL_AI 1
#define SCUMMVERSE_AI_PROBE 1
#include "backends/platform/ios7/scummverse_ai_runtime.inc"
#include <cassert>
#include <iostream>
int main(int argc, char **argv) {
	assert(argc == 2);
	using namespace ScummverseLocalAI;
	assert(cleanReply("Edna: That thing is a disaster, Fred!",10)=="That thing is a disaster, Fred!");
	assert(cleanReply("Fred: That thing is a disaster!",10).empty());
	assert(cleanReply("<think>reasoning</think>Hi there!",10).empty());
	const unsigned group = (1u<<9) | (1u<<10);
	std::vector<ChatLine> example = {{0,"What is that noise?"},{9,"My experiment has developed a snore!"}};
	std::string prompt = chatPrompt(10,7,3,group,example,true);
	assert(prompt.find("Dave: What is that noise?") != std::string::npos);
	assert(prompt.find("Dr Fred: My experiment has developed a snore!") != std::string::npos);
	assert(prompt.find("Now reply as Nurse Edna only.") != std::string::npos);
	Runtime &r = runtime(); int speaker = 0; char speech[160];
	r.scene(7,3,1u<<10,true,speaker,speech,sizeof(speech)); assert(!r.beginGroup());
	r.scene(7,3,group,true,speaker,speech,sizeof(speech)); assert(r.beginGroup());
	assert(r.talkingWith() == group && r.talkingTo() == -1); assert(!r.sendTalk("Hello"));
	r.endTalk(); r.configure(argv[1],false);
	for (int n=0; n<1200 && r.getStatus().find("Ready") != 0; ++n) std::this_thread::sleep_for(std::chrono::milliseconds(100));
	assert(r.getStatus().find("Ready") == 0); assert(r.beginGroup());
	int round = 0;
	for (const char *message : {"Hello Fred and Edna. What is making that noise upstairs?", "Do you two agree about what we should do?"}) {
		assert(r.sendTalk(message)); assert(!r.sendTalk("Another message")); assert(!r.request(14,7,3));
		std::vector<ChatLine> replies;
		for (int n=0; n<700 && (r.waitingForTalk() || replies.size()<2); ++n) {
			std::string text; int actor;
			while (r.readTalk(actor,text)) {
				replies.emplace_back(actor,text);
				std::cout << "GROUP_REPLY round=" << round << " actor=" << actor << " text=" << text << std::endl;
			}
			std::this_thread::sleep_for(std::chrono::milliseconds(100));
		}
		assert(replies.size()==2 && !r.waitingForTalk());
		assert(replies[0].actor == (round == 0 ? 9 : 10) && replies[1].actor == (round == 0 ? 10 : 9));
		for (const auto &reply : replies) {
			assert(reply.text[0]!='[' && !cleanLine(reply.text).empty());
			// The game cannot pop a line while another actor is still speaking.
			assert(r.scene(7,3,group,false,speaker,speech,sizeof(speech)) == group && speaker==0 && !speech[0]);
			assert(r.scene(7,3,group,true,speaker,speech,sizeof(speech)) == group);
			assert(speaker==reply.actor && speech==reply.text);
		}
		int actor,room; assert(!r.poll(actor,room,speech,sizeof(speech)));
		++round;
	}
	// New arrivals join the shared session; departures do not strand others.
	unsigned three = group | (1u<<14);
	assert(r.scene(7,3,three,true,speaker,speech,sizeof(speech))==three);
	assert(r.talkingWith()==three);
	assert(r.sendTalk("Tell us more."));
	// Next leading actor is Green; removing him cancels this round, not the chat.
	assert(r.scene(7,3,group,true,speaker,speech,sizeof(speech))==group);
	std::this_thread::sleep_for(std::chrono::milliseconds(700));
	std::string reply; assert(!r.readTalk(speaker,reply)); assert(!r.waitingForTalk());
	assert(r.scene(7,3,1u<<10,true,speaker,speech,sizeof(speech))==(1u<<10));
	assert(r.talkingTo()==-1);
	assert(r.scene(10,3,0,true,speaker,speech,sizeof(speech))==0); // Room change discards all state.
	r.scene(7,3,group,true,speaker,speech,sizeof(speech)); assert(r.beginGroup());
	assert(r.sendTalk("Hello again.")); r.endTalk();
	std::this_thread::sleep_for(std::chrono::milliseconds(500));
	assert(!r.readTalk(speaker,reply) && !r.talkingWith() && !r.waitingForTalk());
	assert(r.beginGroup()); r.cancel(); assert(!r.talkingWith());
	assert(r.beginGroup()); r.configure("",false); assert(!r.talkingWith());
	std::cout << "PASS: real shared group conversation, attributed rotating replies, serialized speech, join/leave, close/load/off cancellation\n";
}
