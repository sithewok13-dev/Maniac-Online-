// Real runtime worker thread and scheduling with a scripted reply provider:
// model-load survival, queued sends, fallback, departures, ambient preemption,
// cancellation and remembered lines. No weights needed. Build (also with -fsanitize=thread):
// c++ -std=c++17 -fsanitize=address,undefined -Iengine -Ibuild/llama-src/include
//   -Ibuild/llama-src/ggml/include tools/test_talk_provider.cpp <llama/ggml libs>
#define SCUMMVERSE_LOCAL_AI 1
#define SCUMMVERSE_AI_TEST_PROVIDER 1
#include <atomic>
#include <chrono>
#include <string>
#include <thread>

static std::atomic<int> loadDelayMs{0}, replyDelayMs{0}, ambientAborts{0}, generated{0}, ambientLines{0};
static std::atomic<bool> emptyReplies{false}, ambientBlocks{false};
// The speaker's previous line as the last ambient prompt was given it (the
// worker writes it before its result is published; read after a poll).
static std::string lastPrevious;

template <class Abort> static bool waitOrAbort(int ms, Abort aborted) {
	for (int n = 0; n < ms; ++n) { if (aborted()) return false; std::this_thread::sleep_for(std::chrono::milliseconds(1)); }
	return !aborted();
}
template <class Abort> bool scummverseTestLoad(const std::string &path, Abort aborted) {
	return path == "fake" && waitOrAbort(loadDelayMs, aborted);
}
template <class Lines, class Abort>
std::string scummverseTestGenerate(int actor, const std::string &question, const Lines &prior, const std::string &event, const std::string &previous, Abort aborted) {
	if (!event.empty()) return "Remark" + std::to_string(actor) + ": " + event; // A line about what just happened.
	if (question.empty()) { // Ambient encounter line.
		if (ambientBlocks) { while (!aborted()) std::this_thread::sleep_for(std::chrono::milliseconds(1)); ++ambientAborts; return ""; }
		lastPrevious = previous;
		return "Ambient hello " + std::to_string(++ambientLines) + ".";
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
	// The worker has started the job (its status says so), not merely been
	// given it: a sleep is not enough under a sanitizer and load.
	auto replying = [&] { return r.getStatus().find(" is replying") != std::string::npos; };
	auto writingGreeting = [&] { return r.getStatus().find("Writing a line") == 0; };

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
	assert(waitFor(writingGreeting)); // (Started, not merely asked for.)
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

	// 9. Other-world characters (guest actors 25..29) reply with a model, and
	// a second message to one of them still works (their remembered line once
	// overflowed a 25-entry table and crashed the second reply).
	replyDelayMs = 0; loadDelayMs = 0; r.configure("fake", false);
	assert(waitFor([&] { return r.modelReady(); }));
	r.scene(10035, 3, (1u << 25) | (1u << 26) | (1u << 27), true, speaker, text, sizeof(text));
	assert(r.beginTalk(27) && r.sendTalk("Ahoy"));
	assert(waitFor([&] { return !r.waitingForTalk(); }));
	assert(r.sendTalk("Again"));
	assert(waitFor([&] { return !r.waitingForTalk(); }));
	assert(dump(r).find("27:Reply27 to Ahoy.|0:Again|27:Reply27 to Again.|") != std::string::npos);

	// 10. A remark (0200: heckled, answered back): the line about what just
	// happened, by the one asked, polled as a greeting; none during a
	// conversation, without words, or while one is out.
	assert(!r.remark(9, 7, 3, "He swung it.")); // (still talking with 27)
	r.endTalk();
	assert(!r.remark(9, 7, 3, ""));
	assert(r.remark(9, 7, 3, "Sith Ewok 3 just swung his lightsaber around."));
	assert(!r.remark(10, 7, 3, "Another."));
	assert(waitFor([&] { return r.poll(actor, room, text, sizeof(text)); }));
	assert(actor == 9 && room == 7 && std::string(text) == "Remark9: Sith Ewok 3 just swung his lightsaber around.");
	assert(r.remark(10, 7, 3, "Another."));
	assert(waitFor([&] { return r.poll(actor, room, text, sizeof(text)); }) && actor == 10);

	// 11. A line is remembered (not to be repeated) only for the one who said
	// it: a wanderer's slot (talk ID) taken by someone else starts afresh.
	using Scummverse::WorldCatalog::worldAppearanceKey;
	scummverseTalkVisitor(0, worldAppearanceKey(0, 1));
	assert(r.request(kWanderer, 7, 3) && waitFor([&] { return r.poll(actor, room, text, sizeof(text)); }));
	const std::string first = text;
	assert(r.request(kWanderer, 7, 3) && waitFor([&] { return r.poll(actor, room, text, sizeof(text)); }));
	assert(lastPrevious == first && first != text);
	scummverseTalkVisitor(0, worldAppearanceKey(3, 2)); // Another takes the slot.
	assert(r.request(kWanderer, 7, 3) && waitFor([&] { return r.poll(actor, room, text, sizeof(text)); }));
	assert(lastPrevious.empty());
	scummverseTalkVisitor(0, 0);

	// 12. Taking the one replying out of a chosen group: the next one answers
	// at once, with no game frame (scene) in between.
	r.scene(7, 3, edna | fred, true, speaker, text, sizeof(text));
	assert(r.toggleTalk(9) && r.toggleTalk(10) && r.talkingTo() == -2);
	replyDelayMs = 300;
	assert(r.sendTalk("Who first?"));
	{
		uint32_t revision = 0; std::vector<Scummverse::ConversationLine> lines; std::vector<std::string> queued; int replying = 0;
		r.talkSnapshot(revision, lines, queued, replying); assert(replying == 9);
	}
	assert(r.toggleTalk(9) && r.talkingTo() == 10);
	assert(waitFor([&] { return !r.waitingForTalk(); }, 2000));
	assert(dump(r) == "0:Who first?|10:Reply10 to Who first?.|");

	// 13. The app losing the screen (Control Center, the background): the
	// reply being written stops within the bound and is written again, in
	// full, on return; nothing starts while held; the conversation stays.
	r.scene(7, 3, edna, true, speaker, text, sizeof(text));
	assert(r.beginTalk(10));
	replyDelayMs = 3000; generated = 0;
	assert(r.sendTalk("Hold on"));
	assert(waitFor(replying)); // Edna is replying.
	begin = std::chrono::steady_clock::now();
	assert(r.suspend(300) && std::chrono::steady_clock::now() - begin < std::chrono::milliseconds(300));
	replyDelayMs = 0;
	assert(r.sendTalk("And this"));
	std::this_thread::sleep_for(std::chrono::milliseconds(200));
	assert(r.waitingForTalk() && generated == 0 && dump(r) == "0:Hold on|" && r.talkingTo() == 10);
	r.resume();
	assert(waitFor([&] { return !r.waitingForTalk(); }));
	assert(dump(r) == "0:Hold on|10:Reply10 to Hold on.|0:And this|10:Reply10 to And this.|");
	// Back before the reply being written has stopped (past the bound): it
	// is written again all the same.
	// (Long enough that it is still being written when suspended; the one
	// written again, after, is quick.)
	replyDelayMs = 3000;
	assert(r.sendTalk("Quick"));
	assert(waitFor(replying));
	assert(!r.suspend(0)); replyDelayMs = 0; r.resume();
	assert(waitFor([&] { return !r.waitingForTalk(); }));
	assert(dump(r).find("|0:Quick|10:Reply10 to Quick.|") != std::string::npos);
	// A greeting being written is dropped (the game says its own line); one
	// asked for afterwards comes.
	r.endTalk(); ambientBlocks = true; ambientAborts = 0;
	assert(r.request(9, 7, 3));
	assert(waitFor(writingGreeting));
	assert(r.suspend(300) && ambientAborts == 1);
	assert(!r.request(9, 7, 3) && !r.remark(9, 7, 3, "He swung it.")); // (none starts while held)
	ambientBlocks = false; r.resume();
	std::this_thread::sleep_for(std::chrono::milliseconds(100));
	assert(!r.poll(actor, room, text, sizeof(text)));
	assert(r.request(9, 7, 3) && waitFor([&] { return r.poll(actor, room, text, sizeof(text)); }) && actor == 9);
	// A model load is never undone by it: the model is ready after.
	loadDelayMs = 300; r.configure("fake", false);
	assert(waitFor([&] { return r.getStatus().find("Loading") == 0; }));
	std::this_thread::sleep_for(std::chrono::milliseconds(60)); // Worker is inside load().
	begin = std::chrono::steady_clock::now();
	assert(r.suspend(300) && std::chrono::steady_clock::now() - begin < std::chrono::milliseconds(100));
	assert(waitFor([&] { return r.getStatus().find("Ready") == 0; }) && r.modelReady());
	r.resume();

	// 14. Shutdown (before the process exits) with a reply being written:
	// prompt; again, or anything after, is harmless.
	r.scene(7, 3, edna, true, speaker, text, sizeof(text));
	assert(r.beginTalk(10)); replyDelayMs = 5000;
	assert(r.sendTalk("Last words"));
	std::this_thread::sleep_for(std::chrono::milliseconds(50));
	begin = std::chrono::steady_clock::now();
	r.shutdown();
	assert(std::chrono::steady_clock::now() - begin < std::chrono::seconds(1));
	r.shutdown(); r.configure("", false); assert(!r.request(9, 7, 3) && r.suspend(0));
	std::cout << "PASS: worker scheduling, load survival, queued sends, fallback, departures, ambient preemption, cancellation, remarks, remembered lines, losing the screen, shutdown\n";
}
