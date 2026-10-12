// Real Qwen3 conversation, room/visitor lifecycle and cancellation probe.
#define SCUMMVERSE_LOCAL_AI 1
#define SCUMMVERSE_AI_PROBE 1
#include "backends/platform/ios7/scummverse_ai_runtime.inc"
#include <cassert>
#include <iostream>
int main(int argc, char **argv) {
	assert(argc == 2);
	using namespace ScummverseLocalAI;
	assert(cleanLine("I\xe2\x80\x99m watching you\xe2\x80\x94" "carefully!") == "I'm watching you-carefully!");
	Runtime &r = runtime(); char speech[160]; int speaker = 0;
	assert(r.scene(7, 3, 1u << 10, true, speaker, speech, sizeof(speech)) == 0);
	assert(!r.beginTalk(14)); assert(r.beginTalk(10));
	assert(!r.sendTalk("Hello")); // No model must not fabricate a reply.
	r.endTalk(); r.configure(argv[1], false);
	for (int n=0; n<1200 && r.getStatus().find("Ready") != 0; ++n)
		std::this_thread::sleep_for(std::chrono::milliseconds(100));
	assert(r.getStatus().find("Ready") == 0);
	assert(r.beginTalk(10));
	assert(!r.sendTalk(std::string(513, 'x')));
	assert(!r.request(14,7,3)); // Encounters cannot consume chat results.
	for (const char *question : {"Hello Edna. My name is Pickle. What are you cooking?", "Do you remember the name I just gave you?"}) {
		auto begin = std::chrono::steady_clock::now();
		assert(r.sendTalk(question)); assert(!r.sendTalk("another"));
		assert(r.scene(7,3,1u<<10,true,speaker,speech,sizeof(speech))==(1u<<10) && speaker==3 && std::string(speech)==question);
		std::string reply;
		for (int n=0; n<400 && !r.readTalk(speaker,reply); ++n)
			std::this_thread::sleep_for(std::chrono::milliseconds(100));
		assert(!reply.empty());
		std::cout << "QUESTION " << question << "\nREPLY " << reply << "\nSECONDS " << std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count() << std::endl;
		assert(reply[0] != '[' && !cleanLine(reply).empty());
		assert(!r.waitingForTalk());
		assert(r.scene(7,3,1u<<10,true,speaker,speech,sizeof(speech)) == (1u<<10));
		assert(reply == speech);
		int actor,room; assert(!r.poll(actor,room,speech,sizeof(speech)));
	}
	assert(r.sendTalk("Tell me about your family."));
	assert(r.scene(10,3,0,true,speaker,speech,sizeof(speech)) == 0);
	std::this_thread::sleep_for(std::chrono::milliseconds(500));
	std::string reply; assert(!r.readTalk(speaker,reply)); assert(!speech[0]);
	r.scene(7,3,1u<<10,true,speaker,speech,sizeof(speech)); assert(r.beginTalk(10));
	assert(r.scene(7,2,1u<<10,true,speaker,speech,sizeof(speech)) == 0); // Switching kid ends chat.
	assert(r.beginTalk(10)); r.cancel(); assert(!r.talkingTo()); // load/boot clears history.
	assert(r.beginTalk(10)); r.configure("",false); assert(!r.talkingTo());
	std::cout << "PASS: real two-turn conversation, bounded input, speech bridge, isolated results, cancellation and scene/visitor changes\n";
}
