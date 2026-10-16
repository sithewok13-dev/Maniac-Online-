// Real runtime worker thread and scheduling with a scripted reply provider:
// model-load survival, queued sends, fallback, departures, ambient preemption
// and cancellation. No weights needed. Build (also with -fsanitize=thread):
// c++ -std=c++17 -fsanitize=address,undefined -Iengine -Ibuild/llama-src/include
//   -Ibuild/llama-src/ggml/include tools/test_talk_provider.cpp <llama/ggml libs>
#define SCUMMVERSE_LOCAL_AI 1
#define SCUMMVERSE_AI_TEST_PROVIDER 1
#include <atomic>
#include <chrono>
#include <string>
#include <thread>

static std::atomic<int> loadDelayMs{0}, replyDelayMs{0}, ambientAborts{0}, generated{0};
static std::atomic<bool> emptyReplies{false}, ambientBlocks{false};

template <class Abort> static bool waitOrAbort(int ms, Abort aborted) {
	for (int n = 0; n < ms; ++n) { if (aborted()) return false; std::this_thread::sleep_for(std::chrono::milliseconds(1)); }
	return !aborted();
}
template <class Abort> bool scummverseTestLoad(const std::string &path, Abort aborted) {
	return path == "fake" && waitOrAbort(loadDelayMs, aborted);
}
template <class Lines, class Abort>
std::string scummverseTestGenerate(int actor, const std::string &question, const Lines &prior, Abort aborted) {
	if (question.empty()) { // Ambient encounter line.
		if (ambientBlocks) { while (!aborted()) std::this_thread::sleep_for(std::chrono::milliseconds(1)); ++ambientAborts; return ""; }
		return "Ambient hello.";
	}
	if (!waitOrAbort(replyDelayMs, aborted) || emptyReplies) return "";
	++generated;
	// Echo the last attributed line so ordering/context is observable.
	return "Reply" + std::to_string(actor) + " to " + prior.back().text + ".";
}

#include "backends/platform/ios7/scummverse_ai_runtime.inc"
#include <cassert>
#include <iostream>
using namespace ScummverseLocalAI;

static std::string dump(Runtime &r) {
	uint32_t revision = 0; std::vector<Scummverse::ConversationLine> lines; std::vector<std::string> queued; int replying;
	r.talkSnapshot(revision, lines, queued, replying);
	std::string out;
	for (const auto &l : lines) out += std::to_string(l.speaker) + (l.kind == Scummverse::LineKind::Classic ? "c:" : ":") + l.text + "|";
	return out;
}
template <class Done> static bool waitFor(Done done, int ms = 5000) {
	for (int n = 0; n < ms / 5; ++n) { if (done()) return true; std::this_thread::sleep_for(std::chrono::milliseconds(5)); }
	return done();
}

int main() {
	Runtime &r = runtime(); int speaker; char text[600];
	const unsigned edna = 1u << 10, fred = 1u << 9;

	// 1. A room change during an active conversation must not discard a model
	// load in progress (it previously bumped the epoch unconditionally).
	r.scene(7, 3, edna, true, speaker, text, sizeof(text));
	loadDelayMs = 300; r.configure("fake", false);
	assert(waitFor([&] { return r.getStatus().find("Loading") == 0; }));
	std::this_thread::sleep_for(std::chrono::milliseconds(60)); // Worker is inside load().
	assert(r.beginTalk(10));
	assert(r.sendTalk("Before the model is ready")); // Classic while loading.
	assert(dump(r).find("10c:") != std::string::npos);
	r.scene(8, 3, edna, true, speaker, text, sizeof(text)); // Room change ends the talk.
	assert(!r.talkingWith());
	assert(waitFor([&] { return r.modelReady(); }));
	assert(r.getStatus().find("Ready") == 0);

	// 2. With a model: replies are generated, attributed and in order.
	r.scene(7, 3, edna, true, speaker, text, sizeof(text));
	assert(r.beginTalk(10) && r.sendTalk("Hi Edna"));
	assert(waitFor([&] { return !r.waitingForTalk(); }));
	assert(dump(r) == "0:Hi Edna|10:Reply10 to Hi Edna.|");

	// 3. A second message while the first reply is pending waits its turn.
	replyDelayMs = 150;
	assert(r.sendTalk("A") && r.sendTalk("B"));
	assert(r.waitingForTalk());
	assert(waitFor([&] { return !r.waitingForTalk(); }));
	assert(dump(r) == "0:Hi Edna|10:Reply10 to Hi Edna.|0:A|10:Reply10 to A.|0:B|10:Reply10 to B.|");

	// 4. A failed or filtered generation becomes a labelled classic line.
	emptyReplies = true;
	assert(r.sendTalk("C") && waitFor([&] { return !r.waitingForTalk(); }));
	assert(dump(r).substr(dump(r).size() - 6, 4) != "10:R" && dump(r).find("0:C|10c:") != std::string::npos);
	emptyReplies = false;

	// 5. Group: a departing speaker's in-flight reply never appears; the
	// other scheduled speaker still answers.
	r.scene(7, 3, edna | fred, true, speaker, text, sizeof(text));
	assert(r.beginGroup());
	replyDelayMs = 400; generated = 0;
	assert(r.sendTalk("Who answers?"));
	std::this_thread::sleep_for(std::chrono::milliseconds(50)); // Fred (lead) is generating.
	r.scene(7, 3, edna, true, speaker, text, sizeof(text));    // Fred leaves.
	assert(waitFor([&] { return !r.waitingForTalk(); }));
	assert(dump(r) == "0:Who answers?|10:Reply10 to Who answers?.|");

	// 6. Ending a conversation mid-reply leaves no late line and no stuck state.
	r.scene(7, 3, edna, true, speaker, text, sizeof(text));
	assert(r.beginTalk(10) && r.sendTalk("Bye"));
	std::this_thread::sleep_for(std::chrono::milliseconds(50));
	r.endTalk();
	std::this_thread::sleep_for(std::chrono::milliseconds(500));
	assert(!r.talkingWith() && !r.waitingForTalk() && dump(r).empty());
	assert(r.modelReady()); // Cancellation never unloads the model.

	// 7. A conversation pre-empts a slow ambient encounter line immediately.
	replyDelayMs = 0; ambientBlocks = true; ambientAborts = 0;
	assert(r.request(9, 7, 3));
	std::this_thread::sleep_for(std::chrono::milliseconds(50));
	auto begin = std::chrono::steady_clock::now();
	assert(r.beginTalk(10) && r.sendTalk("Quick question"));
	assert(waitFor([&] { return !r.waitingForTalk(); }, 2000)); // Ambient deadline is 5 s.
	assert(std::chrono::steady_clock::now() - begin < std::chrono::seconds(2));
	assert(ambientAborts == 1);
	int actor, room; assert(!r.poll(actor, room, text, sizeof(text))); // Ambient result discarded.
	assert(dump(r) == "0:Quick question|10:Reply10 to Quick question.|");
	ambientBlocks = false;

	// 8. Turning the model off mid-reply falls back cleanly.
	replyDelayMs = 400;
	assert(r.sendTalk("Still there?"));
	std::this_thread::sleep_for(std::chrono::milliseconds(50));
	r.configure("", false);
	assert(waitFor([&] { return r.getStatus().find("Off") == 0; }));
	assert(!r.modelReady() && !r.talkingWith());
	r.scene(7, 3, edna, true, speaker, text, sizeof(text));
	assert(r.beginTalk(10) && r.sendTalk("Classic again"));
	assert(dump(r).find("0:Classic again|10c:") == 0);
	std::cout << "PASS: worker scheduling, load survival, queued sends, fallback, departures, ambient preemption, cancellation\n";
}
