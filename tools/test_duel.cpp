// Scummverse: insult sword fighting by a game's own rules
// (common/scummverse_duel.h, from 0298): the fight file read and written
// (damaged ones refused), and fights against the master and pirates played
// as their game's scripts play them, with rules made up here (no game text).
// Build: c++ -std=c++11 -Wall -Wextra -Werror -fsanitize=address,undefined
//   -Iengine tools/test_duel.cpp engine/common/scummverse_duel.cpp -lpthread
// (and with -fsanitize=thread).
#include "common/scummverse_duel.h"
#include "common/scummverse_duel_engine.h"

#include <algorithm>
#include <cassert>
#include <cstdio>
#include <cstring>
#include <set>
#include <string>
#include <thread>
#include <vector>

using namespace Scummverse::Duel;

// (Monkey Island's numbers, as its scripts have them; an accepted table of
// its shape: the pirates' insults 1..16 each their own comeback, the
// master's 17..33 the first sixteen again, four of them taking a second.)
static Rules rules() {
	Rules r;
	r.insults = 37; r.comebacks = 21;
	r.ownFirst = 1; r.ownLast = 16; r.masterFirst = 17; r.masterLast = 33;
	r.loseFrom = 17; r.repeat = 20; r.giveUp = 21; r.fallbackFrom = 34; r.insultGiveUp = 37;
	r.masterTarget = 5; r.pirateTarget = 3; r.tries = 20; r.skillRange = 10; r.wrongCount = 3; r.fallbackLines = 4;
	r.accepted.assign(3 * 38, 0);
	for (int n = 1; n <= 16; ++n) r.accepted[3 * n] = n;
	for (int n = 17; n <= 32; ++n) r.accepted[3 * n] = n - 16;
	r.accepted[3 * 33 + 1] = 16; r.accepted[3 * 33 + 2] = 4;
	r.accepted[3 * 21 + 1] = 16; r.accepted[3 * 19 + 1] = 11; r.accepted[3 * 25 + 1] = 14;
	return r;
}

static Data data() {
	Data d;
	d.rules = rules();
	for (int t = 1; t <= 7; ++t) { Type x; x.type = t; x.skill = t == 1 ? 10 : 3 + t; x.color = 10 + t; x.costume = t == 1 ? 45 : 87; d.types.push_back(x); }
	auto line = [&](int kind, int which, int speaker, int color, const char *text) { Line l; l.kind = kind; l.which = which; l.speaker = speaker; l.color = color; l.text = text; d.lines.push_back(l); };
	for (int n = 1; n <= 37; ++n) line(kLineInsult, n, kSpeakerOpponent, -1, ("insult " + std::to_string(n)).c_str());
	for (int n = 1; n <= 21; ++n) line(kLineComeback, n, kSpeakerPlayed, -1, ("comeback " + std::to_string(n)).c_str());
	line(kLineRepeat, 0, kSpeakerOpponent, -1, "again: ");
	line(kLineRepeat, 1, kSpeakerOpponent, -1, "!");
	for (int v = 0; v < 5; ++v) line(kLineLost, v, kSpeakerPlayed, -1, ("lost " + std::to_string(v)).c_str());
	line(kLineAnswer, 3, kSpeakerOpponent, 10, "first");
	line(kLineAnswer, 3, kSpeakerPlayed, -1, "second");
	line(kLineIntro, 0, kSpeakerNone, 7, "told over the place");
	Outcome o; o.kind = kLineAnswer; o.which = 6; o.flags = kFights; o.leaves = {0x8000 + 518, 1, 283, -2};
	d.outcomes.push_back(o);
	return d;
}

// (The first comeback an insult takes: insult 33's first slot is empty.)
static int rightFor(const Rules &r, int n) {
	for (int k = 0; k < 3; ++k) if (r.accepted[3 * n + k]) return r.accepted[3 * n + k];
	return 0;
}

static int failures = 0;
#define CHECK(c) do { if (!(c)) { std::printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c); ++failures; } } while (0)

static void testFile() {
	const Data d = data();
	const std::vector<uint8_t> bytes = write(d);
	Data back;
	std::string error;
	CHECK(parse(bytes.data(), bytes.size(), back, error));
	CHECK(write(back) == bytes);
	CHECK(back.rules.accepts(33, 4) && back.rules.accepts(33, 16) && !back.rules.accepts(33, 0) && back.rules.accepts(17, 1) && !back.rules.accepts(17, 2));
	CHECK(back.said(kLineAnswer, 3).size() == 2 && back.said(kLineAnswer, 3)[0]->text == "first" && back.said(kLineAnswer, 3)[1]->speaker == kSpeakerPlayed);
	CHECK(back.said(kLineIntro, 0)[0]->color == 7 && back.said(kLineAnswer, 3)[1]->color == -1);
	CHECK(back.variants(kLineLost) == 5 && back.variants(kLineFallback) == 0 && back.type(1) && back.type(1)->costume == 45 && !back.type(8));
	CHECK(back.outcome(kLineAnswer, 6) && back.outcome(kLineAnswer, 6)->leaves.size() == 4 && back.outcome(kLineAnswer, 6)->leaves[3] == -2 && !back.outcome(kLineAnswer, 5));
	// (Every cut, and more after its end, refused, nothing read past it.)
	for (size_t n = 0; n < bytes.size(); ++n) {
		std::vector<uint8_t> cut(bytes.begin(), bytes.begin() + n);
		Data x;
		CHECK(!parse(cut.empty() ? nullptr : cut.data(), cut.size(), x, error) && x.lines.empty() && x.rules.insults == 0);
	}
	{
		std::vector<uint8_t> more = bytes;
		more.push_back(0);
		Data x;
		CHECK(!parse(more.data(), more.size(), x, error));
	}
	// (Rules out of range: a comeback past the last, a range past the
	// fallbacks, the give-up as the repeat, a skill past its draw.)
	auto refused = [&](void (*damage)(Data &)) {
		Data x = data();
		damage(x);
		const std::vector<uint8_t> b = write(x);
		Data y;
		return !parse(b.data(), b.size(), y, error);
	};
	CHECK(refused([](Data &x) { x.rules.accepted[3 * 5] = 22; }));
	CHECK(refused([](Data &x) { x.rules.masterLast = 34; }));
	CHECK(refused([](Data &x) { x.rules.giveUp = x.rules.repeat; }));
	CHECK(refused([](Data &x) { x.types[2].skill = 12; }));
	CHECK(refused([](Data &x) { x.lines[0].which = 0; }));
	CHECK(refused([](Data &x) { x.lines[3].text = std::string("a\0b", 3); }));
	CHECK(refused([](Data &x) { x.outcomes.push_back(x.outcomes[0]); }));
	CHECK(!refused([](Data &x) { x.rules.accepted[3 * 5 + 2] = 21; }));
	// (Every byte flipped: read or refused, never past its end.)
	for (size_t n = 4; n < bytes.size(); ++n) {
		std::vector<uint8_t> b = bytes;
		b[n] ^= 0xFF;
		Data x;
		if (parse(b.data(), b.size(), x, error)) CHECK(x.rules.valid());
	}
	std::puts("PASS: the fight file read and written, every cut and damaged one refused");
}

static void testMaster() {
	const Rules r = rules();
	Learned learned;
	std::set<int> heard;
	// (Her insults hers only, each new this fight while one is left; heard
	// the first time, learned but not listed in this fight; the comebacks
	// listed those learned and those that lose; a right one a point, a
	// wrong one hers; asked again, the same insult; first to five.)
	for (uint32_t seed = 1; seed <= 200; ++seed) {
		Fight f;
		f.start(r, true, 10, seed);
		CHECK(f.turn() == Fight::kOpponentInsults && f.target() == 5);
		std::set<int> used;
		int exchanges = 0;
		Learned before = learned;
		for (int guard = 0; !f.over() && guard < 64; ++guard) {
			const int n = f.opponentInsult(learned);
			CHECK(n >= 17 && n <= 33 && f.insultNow() == n && f.opponentInsult(learned) == n);
			CHECK(learned.insult(n));
			heard.insert(n);
			// (Learned here: not on the list for an insult of the one played.)
			for (int k : f.insults(learned)) CHECK(k >= 34 || before.insult(k));
			CHECK(f.answer(r.repeat) == Fight::kRepeated && f.insultNow() == n && f.turn() == Fight::kOpponentInsults);
			const std::vector<int> listed = f.comebacks(learned);
			for (int k : listed) CHECK(k >= 17 || learned.comeback(k));
			CHECK(listed.size() >= 5 && listed[listed.size() - 5] == 17 && listed.back() == 21);
			// (Seed by seed: right, a losing one, a wrong one learned.)
			const int right = rightFor(r, n);
			const int pick = seed % 3 == 0 ? right : seed % 3 == 1 ? 17 + (exchanges % 3) : (right % 16) + 1;
			const bool scores = pick < 17 && r.accepts(n, pick);
			const int was = f.playerScore(), theirs = f.opponentScore();
			CHECK(f.answer(pick) == (scores ? Fight::kPlayerPoint : Fight::kOpponentPoint));
			CHECK(f.playerScore() == was + (scores ? 1 : 0) && f.opponentScore() == theirs + (scores ? 0 : 1));
			CHECK(f.over() || f.turn() == Fight::kOpponentInsults);
			// (New each exchange while the 20 tries find one: 17 of hers, nine at most.)
			CHECK(used.count(n) == 0 || used.size() >= 6);
			used.insert(n);
			++exchanges;
		}
		CHECK(f.over() && (f.playerScore() == 5 || f.opponentScore() == 5));
		CHECK(f.playerWon() == (f.playerScore() == 5) && exchanges <= 9 && !f.gaveUp());
		CHECK(learned.comebacks == before.comebacks);
	}
	CHECK(heard.size() == 17 && *heard.begin() == 17 && *heard.rbegin() == 33);
	// (Given up: lost at once.)
	{
		Fight f;
		f.start(r, true, 10, 7);
		f.opponentInsult(learned);
		CHECK(f.answer(r.giveUp) == Fight::kGaveUp && f.over() && !f.playerWon() && f.gaveUp() && f.turn() == Fight::kOver);
		CHECK(f.answer(1) == Fight::kNone);
	}
	// (Every comeback known: won five to none.)
	{
		Learned all;
		for (int n = 1; n <= 16; ++n) all.learnComeback(n);
		for (uint32_t seed = 1; seed <= 50; ++seed) {
			Fight f;
			f.start(r, true, 10, seed);
			for (int guard = 0; !f.over() && guard < 64; ++guard) {
				const int n = f.opponentInsult(all);
				CHECK(f.answer(rightFor(r, n)) == Fight::kPlayerPoint);
			}
			CHECK(f.playerWon() && f.playerScore() == 5 && f.opponentScore() == 0);
		}
	}
	std::puts("PASS: against the master, as its scripts 80, 76, 78, 84 and 71 have it");
}

static void testPirate() {
	const Rules r = rules();
	// (The one played first; their insults from those learned, not used this
	// fight, and the fallbacks; a pirate of skill 0 always wrong, 11 always
	// right (that comeback learned); a fallback the pirate's, with one of its
	// lines; one of the master's the one played's; the one who won the last
	// exchange insults next; first to three.)
	for (int skill : {0, 11}) {
		Learned learned;
		learned.learnInsult(2); learned.learnInsult(8); learned.learnInsult(20);
		Fight f;
		f.start(r, false, skill, 99);
		CHECK(f.turn() == Fight::kPlayerInsults && f.target() == 3);
		std::vector<int> listed = f.insults(learned);
		CHECK((listed == std::vector<int>{2, 8, 20, 34, 35, 36, 37}));
		int reply = 0;
		const Fight::Result first = f.insult(2, learned, reply);
		if (skill == 0) {
			CHECK(first == Fight::kPlayerPoint && reply >= 17 && reply <= 19 && !learned.comeback(2) && f.turn() == Fight::kPlayerInsults);
			listed = f.insults(learned);
			CHECK(std::find(listed.begin(), listed.end(), 2) == listed.end());
			CHECK(f.insult(20, learned, reply) == Fight::kPlayerPoint && reply == Fight::kReplyMaster);
			CHECK(f.insult(8, learned, reply) == Fight::kPlayerPoint && f.over() && f.playerWon() && f.playerScore() == 3);
		} else {
			CHECK(first == Fight::kOpponentPoint && reply == 2 && learned.comeback(2) && f.turn() == Fight::kOpponentInsults);
			const int n = f.opponentInsult(learned);
			CHECK(n >= 1 && n <= 16 && learned.insult(n));
			CHECK(f.answer(17) == Fight::kOpponentPoint && f.turn() == Fight::kOpponentInsults);
			const int m = f.opponentInsult(learned);
			learned.learnComeback(m);
			CHECK(f.answer(m) == Fight::kPlayerPoint && f.turn() == Fight::kPlayerInsults);
			CHECK(f.insult(35, learned, reply) == Fight::kOpponentPoint && reply >= Fight::kReplyFallback && reply < Fight::kReplyFallback + 4);
			CHECK(f.over() && !f.playerWon() && f.opponentScore() == 3);
		}
	}
	// (Given up with the last insult: lost at once.)
	{
		Learned learned;
		Fight f;
		f.start(r, false, 5, 3);
		int reply;
		CHECK(f.insults(learned) == (std::vector<int>{34, 35, 36, 37}));
		CHECK(f.insult(37, learned, reply) == Fight::kGaveUp && f.over() && f.gaveUp() && !f.playerWon());
	}
	// (A skill's chance: right about skill in 11 times.)
	{
		int right = 0, tries = 0;
		for (uint32_t seed = 1; seed <= 2000; ++seed) {
			Learned learned;
			learned.learnInsult(5);
			Fight f;
			f.start(r, false, 6, seed);
			int reply;
			f.insult(5, learned, reply);
			right += reply == 5; ++tries;
		}
		CHECK(right > tries * 6 / 11 - 120 && right < tries * 6 / 11 + 120);
	}
	std::puts("PASS: against a pirate, as its scripts 77, 79, 81, 84 and 71 have it");
}

// A player learning from pirates until every comeback is known, then
// beating the master: as the new engine's own check plays it.
static void testLearning() {
	const Rules r = rules();
	Learned learned;
	learned.learnInsult(2); learned.learnInsult(8); learned.learnComeback(2); learned.learnComeback(8); // (as the trainer leaves them)
	int fights = 0, wins = 0;
	auto known = [&]() { int k = 0; for (int n = 1; n <= 16; ++n) k += learned.comeback(n); return k; };
	while ((known() < 16 || wins < 3) && fights < 400) {
		Fight f;
		f.start(r, false, 2 + fights % 6, 1000 + fights);
		for (int guard = 0; !f.over() && guard < 64; ++guard) {
			if (f.turn() == Fight::kPlayerInsults) {
				// (An insult whose comeback is not known yet, else any.)
				int pick = 0;
				for (int k : f.insults(learned)) if (!pick && k < 34 && !learned.comeback(k)) pick = k;
				for (int k : f.insults(learned)) if (!pick && k < 34) pick = k;
				if (!pick) pick = 34;
				int reply;
				f.insult(pick, learned, reply);
			} else {
				const int n = f.opponentInsult(learned);
				f.answer(learned.comeback(rightFor(r, n)) ? rightFor(r, n) : 17);
			}
		}
		wins += f.playerWon();
		++fights;
	}
	CHECK(known() == 16 && wins >= 3 && fights < 400);
	Fight f;
	f.start(r, true, 10, 5);
	for (int guard = 0; !f.over() && guard < 64; ++guard) { const int n = f.opponentInsult(learned); f.answer(rightFor(r, n)); }
	CHECK(f.playerWon() && f.playerScore() == 5);
	std::printf("PASS: every comeback learned from pirates in %d fights (%d won), then the master beaten\n", fights, wins);
}

// The same seed, the same fight, each in a thread of its own (no state
// shared between fights).
static void testSeeds() {
	const Rules r = rules();
	auto play = [&](uint32_t seed, std::vector<int> &out) {
		Learned learned;
		Fight f;
		f.start(r, true, 10, seed);
		for (int guard = 0; !f.over() && guard < 64; ++guard) { const int n = f.opponentInsult(learned); out.push_back(n); f.answer(n % 2 ? rightFor(r, n) : 18); }
		out.push_back(f.playerScore());
	};
	std::vector<int> a, b, c;
	std::thread one([&]() { play(42, a); }), two([&]() { play(42, b); });
	one.join(); two.join();
	play(43, c);
	CHECK(a == b && !a.empty() && a != c);
	Draws d(5), e(5);
	for (int k = 0; k < 1000; ++k) { const int x = d.upTo(16); CHECK(x >= 0 && x <= 16 && x == e.upTo(16)); }
	CHECK(d.upTo(0) == 0 && d.upTo(-3) == 0);
	std::puts("PASS: the same seed the same fight, in threads of their own");
}

// The engine's bridge: a file built as the export builds it, read back
// whole; its lines, types and outcomes; a fight through it the same as one
// of its own with the seed; a damaged file refused and none kept.
static void testBridge() {
	namespace B = Scummverse::DuelBridge;
	const Data d = data();
	int numbers[17] = {d.rules.insults, d.rules.comebacks, d.rules.ownFirst, d.rules.ownLast, d.rules.masterFirst, d.rules.masterLast, d.rules.loseFrom, d.rules.repeat,
		d.rules.giveUp, d.rules.fallbackFrom, d.rules.insultGiveUp, d.rules.masterTarget, d.rules.pirateTarget, d.rules.tries, d.rules.skillRange, d.rules.wrongCount, d.rules.fallbackLines};
	std::vector<int> accepted(d.rules.accepted.begin() + 3, d.rules.accepted.end());
	B::begin(numbers, accepted.data());
	for (const Type &t : d.types) B::addType(t.type, t.skill, t.color, t.costume);
	for (const Line &l : d.lines) B::addLine(l.kind, l.which, l.speaker, l.color, l.text.c_str());
	for (const Outcome &o : d.outcomes) B::addOutcome(o.kind, o.which, o.flags, o.leaves.data(), (int)o.leaves.size() / 2);
	const int size = B::written(nullptr, 0);
	std::vector<unsigned char> bytes(size);
	CHECK(size > 0 && B::written(bytes.data(), size) == size && std::vector<uint8_t>(bytes.begin(), bytes.end()) == write(d));
	char error[64];
	CHECK(!B::loaded(3) && B::load(3, bytes.data(), bytes.size(), error, sizeof(error)) && B::loaded(3));
	CHECK(B::rule(3, "masterTarget") == 5 && B::rule(3, "nothing") == -1 && B::rule(4, "insults") == -1 && B::accepts(3, 33, 4) && !B::accepts(3, 33, 5));
	int skill, color, costume, speaker, flags, leaves[16], count;
	char text[64];
	CHECK(B::type(3, 1, skill, color, costume) && costume == 45 && !B::type(3, 9, skill, color, costume));
	CHECK(B::lines(3, kLineAnswer, 3) == 2 && B::line(3, kLineAnswer, 3, 1, speaker, color, text, sizeof(text)) && speaker == kSpeakerPlayed && !std::strcmp(text, "second"));
	CHECK(B::line(3, kLineInsult, 7, 0, speaker, color, text, 4) && !std::strcmp(text, "ins") && !B::line(3, kLineAnswer, 3, 2, speaker, color, text, sizeof(text)));
	CHECK(B::variants(3, kLineLost) == 5 && B::outcome(3, kLineAnswer, 6, flags, leaves, count, 8) && flags == kFights && count == 2 && leaves[3] == -2 && !B::outcome(3, kLineAnswer, 7, flags, leaves, count, 8));
	// (Its fight as the module's own, seed for seed.)
	Learned own;
	Fight f;
	f.start(d.rules, true, 10, 77);
	unsigned long long insults = 0;
	unsigned comebacks = 0;
	CHECK(B::start(3, true, 10, 77) && B::turn() == B::kOpponentInsults && B::target() == 5);
	for (int guard = 0; !f.over() && guard < 64; ++guard) {
		const int n = f.opponentInsult(own), m = B::opponentInsult(insults, comebacks);
		CHECK(n == m && B::insultNow() == n && insults == own.insults);
		const int pick = n % 3 ? rightFor(d.rules, n) : 18;
		CHECK((int)f.answer(pick) == B::answer(pick) && f.playerScore() == B::playerScore() && f.opponentScore() == B::opponentScore());
	}
	CHECK(B::turn() == B::kOver && B::won() == f.playerWon() && !B::gaveUp());
	int listed[64];
	CHECK(B::start(3, false, 0, 5) && B::turn() == B::kPlayerInsults && B::insults(1ULL << 2, 0, listed, 64) == 5 && listed[0] == 2 && listed[1] == 34);
	int reply = 0;
	unsigned long long two = 1ULL << 2;
	CHECK(B::insult(2, two, comebacks, reply) == B::kPlayerPoint && reply >= 17 && B::comebacks(0, 0, listed, 64) == 5 && listed[4] == 21);
	// (Read again damaged while its fight is under way: refused, none kept,
	// the fight ended, nothing of it read after; and read again whole while
	// one is under way: that one ended too.)
	std::vector<unsigned char> cut(bytes.begin(), bytes.end() - 1);
	{
		unsigned long long ins = 0;
		unsigned comes = 0;
		int rep = 0;
		CHECK(B::start(3, true, 10, 9) && B::opponentInsult(ins, comes) >= 17);
		CHECK(!B::load(3, cut.data(), cut.size(), error, sizeof(error)) && !B::loaded(3));
		CHECK(B::turn() == B::kOver && B::opponentInsult(ins, comes) == 0 && B::insultNow() == 0 && B::answer(1) == B::kNone && B::insult(2, ins, comes, rep) == B::kNone &&
			B::comebacks(ins, comes, listed, 64) == 0 && B::insults(ins, comes, listed, 64) == 0 && B::target() == 0 && !B::won() && !B::gaveUp());
		CHECK(B::load(3, bytes.data(), bytes.size(), error, sizeof(error)) && B::start(3, false, 5, 9) && B::turn() == B::kPlayerInsults);
		CHECK(B::load(3, bytes.data(), bytes.size(), error, sizeof(error)) && B::turn() == B::kOver && B::insult(34, ins, comes, rep) == B::kNone);
	}
	// (Damaged: refused, none kept; another game's not touched.)
	CHECK(B::load(4, bytes.data(), bytes.size(), error, sizeof(error)) && !B::load(3, cut.data(), cut.size(), error, sizeof(error)) && !B::loaded(3) && B::loaded(4) && *error);
	CHECK(B::turn() == B::kOver || B::start(4, true, 1, 1));
	B::clear();
	CHECK(!B::loaded(4) && B::turn() == B::kOver && !B::start(4, true, 1, 1));
	std::puts("PASS: the engine's bridge: a file built as the export builds it, its lines, types and outcomes, its fight the module's");
}

int main() {
	testFile();
	testBridge();
	testMaster();
	testPirate();
	testLearning();
	testSeeds();
	if (failures) { std::printf("%d failed\n", failures); return 1; }
	std::puts("PASS: insult sword fighting");
	return 0;
}
