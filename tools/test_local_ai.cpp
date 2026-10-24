// Standalone real-inference probe; no game data or iOS SDK required.
#define SCUMMVERSE_LOCAL_AI 1
#include "backends/platform/ios7/scummverse_ai_runtime.inc"
#include <cassert>
#include <iostream>
#include <fstream>

int main(int argc, char **argv) {
	assert(argc == 2);
	using namespace ScummverseLocalAI;
	assert(cleanLine("\"Who left the fridge open?\"") == "Who left the fridge open?");
	assert(cleanLine("Edna: Hello there!").empty());
	assert(cleanLine("<tool>walk</tool>").empty());
	assert(cleanLine(std::string("Oops") + char(255) + "!").empty());
	assert(cleanLine("unfinished response").empty());
	Runtime &r = runtime();
	assert(!r.request(10, 7, 3));
	r.configure(argv[1], false);
	for (int n = 0; n < 600 && r.getStatus().find("Ready") != 0; ++n)
		std::this_thread::sleep_for(std::chrono::milliseconds(100));
	if (r.getStatus().find("Ready") != 0) { std::cerr << r.getStatus() << '\n'; r.shutdown(); return 1; }
	int generated = 0;
	for (int actor : {10, 5, 14}) {
		auto begin = std::chrono::steady_clock::now();
		assert(r.request(actor, 7, 3));
		assert(!r.request(9, 30, 3)); // Single worker, no unbounded queue.
		int returnedActor = 0, room = 0; char text[160] = {};
		bool got = false;
		for (int n = 0; n < 70 && !got; ++n) {
			std::this_thread::sleep_for(std::chrono::milliseconds(100));
			got = r.poll(returnedActor, room, text, sizeof(text));
		}
		if (got) {
			assert(returnedActor == actor && room == 7 && !cleanLine(text).empty());
			std::cout << "GENERATED actor=" << actor << " seconds=" << std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count() << " text=" << text << '\n';
			++generated;
		} else std::cout << "FALLBACK actor=" << actor << '\n';
	}
	assert(generated > 0);
	assert(r.request(10, 7, 3)); r.cancel();
	std::this_thread::sleep_for(std::chrono::milliseconds(200));
	int actor, room; char text[160]; assert(!r.poll(actor, room, text, sizeof(text)));
	r.configure("", false); assert(!r.request(10, 7, 3));
	r.configure("/nonexistent/model.gguf", false);
	for (int n=0; n<100 && r.getStatus().find("unavailable")==std::string::npos; ++n)
		std::this_thread::sleep_for(std::chrono::milliseconds(50));
	assert(!r.request(10,7,3));
	r.shutdown(); // (Before llama's statics go.)
	std::cout << "PASS: real local inference, bounded output, single request, cancellation, off/missing-model fallback\n";
}
