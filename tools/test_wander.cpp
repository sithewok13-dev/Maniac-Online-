// Wanderers (common/scummverse_wander.cpp): places, starting out, moving
// along doors, jumps, gathering, taking turns, the player's place kept still.
// c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//   tools/test_wander.cpp engine/common/scummverse_wander.cpp
#include "common/scummverse_wander.h"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <set>
using namespace Scummverse::Wander;

// A ring of rooms in one game, a corridor of Maniac rooms, one Zak room.
static Map world() {
	Map map;
	for (int r = 1; r <= 12; ++r) map.add(placeCode(kWorld, 3, r));
	for (int r = 1; r <= 12; ++r) map.link(placeCode(kWorld, 3, r), placeCode(kWorld, 3, r % 12 + 1));
	for (int r = 1; r <= 4; ++r) map.add(placeCode(kManiac, 0, r));
	for (int r = 1; r < 4; ++r) { map.link(placeCode(kManiac, 0, r), placeCode(kManiac, 0, r + 1)); map.link(placeCode(kManiac, 0, r + 1), placeCode(kManiac, 0, r)); }
	map.add(placeCode(kZak, 0, 55));
	return map;
}

int main() {
	// Places: codes round trip, never 0; doors once, only between added places.
	for (int kind : {kManiac, kZak, kWorld}) for (int game : {0, 9}) for (int room : {0, 1, 200, 1023}) {
		const int code = placeCode(kind, game, room);
		assert(code > 0 && placeKind(code) == kind && placeGame(code) == game && placeRoom(code) == room);
	}
	Map map = world();
	assert(map.places.size() == 17 && map.find(placeCode(kZak, 0, 55)) == 16 && map.find(placeCode(kZak, 0, 56)) < 0);
	map.link(placeCode(kWorld, 3, 1), placeCode(kWorld, 3, 2)); map.link(placeCode(kWorld, 3, 1), placeCode(kZak, 0, 99));
	assert(map.doors[0].size() == 1 && map.add(placeCode(kWorld, 3, 1)) == 0);
	puts("PASS: places and doors");

	// Random: the same seed, the same numbers; below stays in range.
	{
		Random a(7), b(7), c(0);
		for (int i = 0; i < 100; ++i) { const int x = a.below(10); assert(x == b.below(10) && x >= 0 && x < 10); }
		assert(c.below(0) == 0 && c.state != 0);
	}
	puts("PASS: random");

	// A cast of 60, each living somewhere (or nowhere known).
	std::vector<int> cast, homes;
	for (int i = 0; i < 60; ++i) { cast.push_back(1000 + i); homes.push_back(i % 5 ? map.places[i % 17] : 0); }
	Cast people;
	for (size_t i = 0; i < cast.size(); ++i) people.add(cast[i], homes[i]);
	people.add(cast[0], 0); people.add(0, 0); // once each; nobody 0
	assert(people.size() == 60 && people.find(cast[7]) == 7 && people.find(5) < 0);
	int who[kMostWanderers] = {}, where[kMostWanderers] = {};
	Wanderers wanderers(who, where);
	assert(!wanderers.started() && !wanderers.out(1000) && wanderers.where(1000) == 0);
	Random random(42);
	wanderers.start(people, map, 40, random);
	{
		std::set<int> seen;
		for (int i = 0; i < kMostWanderers; ++i) { assert(who[i] && map.find(where[i]) >= 0); seen.insert(who[i]); }
		assert(seen.size() == 40 && wanderers.started());
	}
	// Starting again adds nobody (all slots taken); a smaller cast starts all.
	{
		int w2[kMostWanderers] = {}, p2[kMostWanderers] = {};
		Wanderers few(w2, p2); Random r(3);
		Cast three; for (int i = 0; i < 3; ++i) three.add(cast[i], homes[i]);
		few.start(three, map, 40, r);
		int n = 0; for (int i = 0; i < kMostWanderers; ++i) n += w2[i] != 0;
		assert(n == 3);
		assert(!few.send(cast[0], map.places[0]) && few.send(cast[10], map.places[2]) && few.where(cast[10]) == map.places[2]);
		assert(!few.send(0, map.places[0]) && !few.send(cast[11], 0));
		// More of the cast later (games exported since): the free places
		// fill with those not out yet, nobody twice.
		few.start(people, map, 40, r);
		std::set<int> seen; for (int i = 0; i < kMostWanderers; ++i) { assert(w2[i]); seen.insert(w2[i]); }
		assert(seen.size() == kMostWanderers && few.where(cast[10]) == map.places[2]);
	}
	puts("PASS: setting out (40 of 60, each once, at known places)");

	// Moving: along doors only (no jumps or joins); the player's place keeps
	// its wanderers; everyone else moves within a few hops' time.
	{
		Rules rules; rules.jump = 0; rules.join = 0; rules.toward = 0; rules.turn = 1 << 30;
		const int here = where[0];
		int staying[kMostWanderers], before[kMostWanderers];
		const int there = wanderers.at(here, staying, kMostWanderers);
		for (int i = 0; i < kMostWanderers; ++i) before[i] = where[i];
		bool moved = false;
		for (int t = 0; t < 40; ++t) {
			int last[kMostWanderers]; for (int i = 0; i < kMostWanderers; ++i) last[i] = where[i];
			moved = wanderers.advance(60 * 10, here, people, map, rules, random) || moved;
			for (int i = 0; i < kMostWanderers; ++i) {
				if (last[i] == here) assert(where[i] == here); // kept while the player watches
				else if (where[i] != last[i]) {
					const int from = map.find(last[i]);
					bool door = false;
					for (int d : map.doors[from]) door = door || map.places[d] == where[i];
					assert(door || map.doors[from].empty());
				}
			}
		}
		int changedCount = 0;
		for (int i = 0; i < kMostWanderers; ++i) if (before[i] != here) changedCount += before[i] != where[i];
		assert(moved && changedCount > 20 && wanderers.at(here, staying, kMostWanderers) >= there);
	}
	puts("PASS: moving through doors; the player's place keeps its wanderers");

	// Jumps go anywhere: the Zak room (no doors) gets visitors; joining
	// gathers wanderers in fewer places.
	{
		Rules rules; rules.jump = 100; rules.join = 0; rules.toward = 0; rules.turn = 1 << 30;
		bool zak = false;
		for (int t = 0; t < 200 && !zak; ++t) {
			wanderers.advance(60 * 30, 0, people, map, rules, random);
			zak = wanderers.at(placeCode(kZak, 0, 55), nullptr, 0) > 0;
		}
		assert(zak);
		auto spread = [&]() { std::set<int> s; for (int i = 0; i < kMostWanderers; ++i) s.insert(where[i]); return (int)s.size(); };
		const int wide = spread();
		rules.jump = 0; rules.join = 100;
		for (int t = 0; t < 400; ++t) wanderers.advance(60 * 30, 0, people, map, rules, random);
		assert(spread() < wide);
	}
	puts("PASS: jumps reach anywhere; joining gathers");

	// Toward the player: to a place next to the player's (and on through its
	// doors into it, while fewer than a crowd are there).
	{
		Rules rules; rules.jump = 0; rules.join = 0; rules.toward = 100; rules.turn = 1 << 30;
		const int here = placeCode(kManiac, 0, 2), at = map.find(here);
		const int before = wanderers.at(here, nullptr, 0);
		int moved = 0;
		for (int t = 0; t < 20; ++t) {
			int last[kMostWanderers]; for (int i = 0; i < kMostWanderers; ++i) last[i] = where[i];
			wanderers.advance(60 * 200, here, people, map, rules, random);
			for (int i = 0; i < kMostWanderers; ++i) {
				if (where[i] == last[i]) continue;
				++moved;
				bool next = where[i] == here;
				for (int d : map.doors[at]) next = next || map.places[d] == where[i];
				assert(next);
			}
			assert(wanderers.at(here, nullptr, 0) <= std::max(before, rules.crowd));
		}
		assert(moved > 30);
		// Through doors only (no pull): still no more than a crowd come in.
		rules.toward = 0;
		for (int t = 0; t < 50; ++t) wanderers.advance(60 * 200, here, people, map, rules, random);
		assert(wanderers.at(here, nullptr, 0) <= std::max(before, rules.crowd));
	}
	// Weights: a place weighing fifty times another is picked far more often.
	{
		Map weighted; weighted.add(placeCode(kManiac, 0, 1), 50); weighted.add(placeCode(kManiac, 0, 1), 1);
		for (int r = 1; r <= 10; ++r) weighted.add(placeCode(kWorld, 2, r));
		assert(weighted.total == 60 && weighted.weights[0] == 50);
		Random r(11); int heavy = 0;
		for (int n = 0; n < 1000; ++n) heavy += weighted.pick(r) == placeCode(kManiac, 0, 1);
		assert(heavy > 750 && heavy < 900);
		Map none; assert(none.pick(r) == 0);
	}
	// Weighted characters: two of a small game weighing as much as fifty of a
	// big one's are as likely to be the one setting out.
	{
		Cast games;
		for (int i = 0; i < 50; ++i) games.add(2000 + i, map.places[0], 1);
		games.add(3000, map.places[1], 25); games.add(3001, map.places[1], 25);
		int small = 0;
		for (uint32_t seed = 1; seed <= 400; ++seed) {
			int w[2][kMostWanderers] = {}; Wanderers one(w[0], w[1]); Random r(seed);
			one.start(games, map, 1, r);
			small += one.out(3000) || one.out(3001);
		}
		assert(small > 140 && small < 260);
	}
	puts("PASS: toward the player; weighted places and characters");

	// Taking turns: one goes home, someone new sets out from home; never
	// someone at or living in the player's place; nobody out twice.
	{
		Rules rules; rules.hop = 1 << 30; rules.turn = 60;
		const int here = map.places[1];
		int turns = 0;
		for (int t = 0; t < 300; ++t) {
			int last[kMostWanderers], lastWho[kMostWanderers];
			for (int i = 0; i < kMostWanderers; ++i) { last[i] = where[i]; lastWho[i] = who[i]; }
			wanderers.advance(60, here, people, map, rules, random);
			std::set<int> seen;
			for (int i = 0; i < kMostWanderers; ++i) {
				assert(seen.insert(who[i]).second);
				if (who[i] == lastWho[i]) continue;
				++turns;
				assert(last[i] != here);
				size_t h = 0; while (cast[h] != lastWho[i]) ++h;
				assert(homes[h] != here); // nobody goes home where the player is
				size_t c = 0; while (cast[c] != who[i]) ++c;
				assert(where[i] == homes[c] && homes[c] != here && homes[c]);
			}
		}
		assert(turns > 250 && turns <= 300);
	}
	puts("PASS: taking turns (from home, never where the player is, nobody twice)");

	// The game's side (WanderBridge): the same moves through plain calls.
	{
		namespace B = Scummverse::WanderBridge;
		B::reset(5);
		for (int code : map.places) B::addPlace(code);
		for (size_t p = 0; p < map.places.size(); ++p) for (int d : map.doors[p]) B::addDoor(map.places[p], map.places[d]);
		for (size_t c = 0; c < cast.size(); ++c) B::addCast(cast[c], homes[c]);
		B::addCast(cast[0], homes[1]); B::addCast(0, homes[1]); // once each; nobody 0
		assert(B::places() == (int)map.places.size() && B::cast() == (int)cast.size());
		int bw[2][kMostWanderers] = {};
		B::start(40); assert(B::at(map.places[0], nullptr, 0) == 0); // not bound: nothing
		B::bind(bw[0], bw[1]); B::start(40);
		int out = 0; for (int i = 0; i < kMostWanderers; ++i) out += bw[0][i] != 0;
		assert(out == 40 && B::where(bw[0][0]) == bw[1][0] && B::where(-5) == 0);
		bool moved = false;
		for (int t = 0; t < 50; ++t) moved = B::advance(60 * 60, bw[1][0]) || moved;
		int seen = 0; for (int code : map.places) seen += B::at(code, nullptr, 0);
		assert(moved && seen == 40);
		B::bind(bw[0], bw[1]); assert(B::where(bw[0][3]) == bw[1][3]); // binding again keeps them
	}
	puts("PASS: the game's side (bridge)");

	// The same seed moves them the same way.
	{
		int a[2][kMostWanderers] = {}, b[2][kMostWanderers] = {};
		Wanderers one(a[0], a[1]), two(b[0], b[1]);
		Random r1(9), r2(9); Rules rules;
		one.start(people, map, 40, r1); two.start(people, map, 40, r2);
		for (int t = 0; t < 100; ++t) {
			one.advance(60 * 20, map.places[0], people, map, rules, r1);
			two.advance(60 * 20, map.places[0], people, map, rules, r2);
		}
		for (int i = 0; i < kMostWanderers; ++i) assert(a[0][i] == b[0][i] && a[1][i] == b[1][i]);
		// An empty map: nobody starts or moves.
		Map none; int w[2][kMostWanderers] = {};
		Wanderers lost(w[0], w[1]); lost.start(people, none, 40, r1);
		assert(!lost.started() && !lost.advance(600, 0, people, none, rules, r1));
	}
	puts("PASS: deterministic; an empty map moves nobody");

	// Capacity: by floor width, less residents, within the pool.
	assert(capacity(320, 0, 26) == 8 && capacity(320, 3, 26) == 5 && capacity(320, 9, 26) == 0);
	assert(capacity(2000, 2, 26) == 26 && capacity(60, 0, 26) == 1 && capacity(0, 0, 26) == 0 && capacity(320, 0, 26, 0) == 0);
	puts("PASS: capacity");
	return 0;
}
