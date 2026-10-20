// Wanderers (common/scummverse_wander.cpp): places and doors, everyone out
// (mostly in their own game), moving along doors, jumps, gathering, toward
// the player, the crowd and small ones, weights, saving, the game's side.
// c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//   tools/test_wander.cpp engine/common/scummverse_wander.cpp
#include "common/scummverse_wander.h"
#include <algorithm>
#include <cassert>
#include <cstdio>
#include <set>
using namespace Scummverse::Wander;

// Two games: a ring of twelve rooms (game 3), a corridor of four Maniac
// rooms (game 0), and one Zak room with no doors (game 1).
static Map world() {
	Map map;
	for (int r = 1; r <= 12; ++r) map.add(placeCode(kWorld, 3, r), 1, 5);
	for (int r = 1; r <= 12; ++r) map.link(placeCode(kWorld, 3, r), placeCode(kWorld, 3, r % 12 + 1));
	for (int r = 1; r <= 4; ++r) map.add(placeCode(kManiac, 0, r), 3, 0);
	for (int r = 1; r < 4; ++r) { map.link(placeCode(kManiac, 0, r), placeCode(kManiac, 0, r + 1)); map.link(placeCode(kManiac, 0, r + 1), placeCode(kManiac, 0, r)); }
	map.add(placeCode(kZak, 0, 55), 12, 1);
	return map;
}

int main() {
	// Places: codes round trip, never 0, below 65536; doors once, only
	// between added places; games keep their places.
	for (int kind : {kManiac, kZak, kWorld}) for (int game : {0, 9}) for (int room : {0, 1, 200, 1023}) {
		const int code = placeCode(kind, game, room);
		assert(code > 0 && code < 65536 && placeKind(code) == kind && placeGame(code) == game && placeRoom(code) == room);
	}
	Map map = world();
	assert(map.places.size() == 17 && map.find(placeCode(kZak, 0, 55)) == 16 && map.find(placeCode(kZak, 0, 56)) < 0);
	map.link(placeCode(kWorld, 3, 1), placeCode(kWorld, 3, 2)); map.link(placeCode(kWorld, 3, 1), placeCode(kZak, 0, 99));
	assert(map.doors[0].size() == 1 && map.add(placeCode(kWorld, 3, 1), 9, 2) == 0 && map.weights[0] == 1 && map.groups[0] == 5);
	assert(map.members[5].size() == 12 && map.members[0].size() == 4 && map.members[1].size() == 1 && map.total == 12 + 12 + 12);
	puts("PASS: places, doors and games");

	// Random: the same seed, the same numbers; picks by weight and in a game.
	{
		Random a(7), b(7), c(0);
		for (int i = 0; i < 100; ++i) { const int x = a.below(10); assert(x == b.below(10) && x >= 0 && x < 10); }
		assert(c.below(0) == 0 && c.state != 0);
		Random r(11); int zak = 0;
		for (int n = 0; n < 3000; ++n) zak += map.pick(r) == placeCode(kZak, 0, 55);
		assert(zak > 800 && zak < 1200); // one place weighing a third of the map
		for (int n = 0; n < 50; ++n) assert(placeGame(map.pickIn(5, r)) == 3 && map.pickIn(1, r) == placeCode(kZak, 0, 55));
		assert(map.pickIn(4, r) == 0 && map.pickIn(99, r) == 0 && Map().pick(r) == 0);
	}
	puts("PASS: random; by weight; within a game");

	// A cast of 60 in game 3 (some living nowhere known), 20 in the Maniac
	// game; four small ones.
	Cast cast;
	for (int i = 0; i < 60; ++i) cast.add(1000 + i, i % 5 ? map.places[i % 12] : 0, 5, 1, i < 4);
	for (int i = 0; i < 20; ++i) cast.add(2000 + i, placeCode(kManiac, 0, 1 + i % 4), 0);
	cast.add(1000, 0, 5); cast.add(0, 0, 5); // once each; nobody 0
	assert(cast.size() == 80 && cast.find(1007) == 7 && cast.find(5) < 0 && cast.small[3] && !cast.small[4]);
	{
		Cast again = cast; assert(again.signature() == cast.signature() && again.signature() & 1);
		again.add(3000, 0); assert(again.signature() != cast.signature());
	}

	// Everyone out: each somewhere known, anywhere at all (every game an
	// equal share); leaning to their own game keeps most there.
	Wanderers everyone; Random random(42); Rules rules;
	assert(!everyone.started() && everyone.where(0) == 0 && rules.lean == 0);
	auto own = [&](const Wanderers &w) {
		int n = 0;
		for (int i = 0; i < 80; ++i) { assert(map.find(w.where(i)) >= 0); n += map.groups[map.find(w.where(i))] == cast.games[i]; }
		return n;
	};
	everyone.start(cast, map, rules, random);
	{
		assert(everyone.started() && own(everyone) < 45); // a third of the map's weight each: about 27 of 80
		int ids[80]; const int n = everyone.at(everyone.where(5), ids, 80);
		assert(n >= 1 && std::find(ids, ids + std::min(n, 80), 5) != ids + std::min(n, 80) && everyone.at(0, ids, 80) == 0);
		Wanderers homely; Rules lean; lean.lean = 75; Random r(8);
		homely.start(cast, map, lean, r);
		assert(own(homely) > 55);
	}
	puts("PASS: everyone out anywhere; a lean keeps them home");

	// Moving: along doors only (no jumps, joins or pull); the player's place
	// keeps those there; the rest move on within a few hops' time.
	{
		Rules doors; doors.jump = 0; doors.join = 0; doors.toward = 0;
		const int here = everyone.where(10);
		int before[80]; for (int i = 0; i < 80; ++i) before[i] = everyone.where(i);
		for (int t = 0; t < 40; ++t) {
			int last[80]; for (int i = 0; i < 80; ++i) last[i] = everyone.where(i);
			everyone.advance(60 * 10, here, cast, map, doors, random);
			for (int i = 0; i < 80; ++i) {
				if (last[i] == here) assert(everyone.where(i) == here); // kept while the player watches
				else if (everyone.where(i) != last[i]) {
					const int from = map.find(last[i]);
					bool door = false;
					for (int d : map.doors[from]) door = door || map.places[d] == everyone.where(i);
					// (A place with no doors moves anywhere.)
					assert(door || map.doors[from].empty());
				}
			}
		}
		int moved = 0;
		for (int i = 0; i < 80; ++i) if (before[i] != here) moved += before[i] != everyone.where(i);
		assert(moved > 40);
	}
	puts("PASS: moving through doors; the player's place keeps them");

	// Jumps reach anywhere (the Zak room, with no doors in); joining gathers.
	{
		Rules jumps; jumps.jump = 1000; jumps.join = 0; jumps.toward = 0;
		bool zak = false;
		for (int t = 0; t < 200 && !zak; ++t) {
			everyone.advance(60 * 30, 0, cast, map, jumps, random);
			zak = everyone.at(placeCode(kZak, 0, 55), nullptr, 0) > 0;
		}
		assert(zak);
		auto spread = [&]() { std::set<int> s; for (int i = 0; i < 80; ++i) s.insert(everyone.where(i)); return (int)s.size(); };
		const int wide = spread();
		Rules gather; gather.join = 1000; gather.jump = 0; gather.toward = 0;
		for (int t = 0; t < 400; ++t) everyone.advance(60 * 30, 0, cast, map, gather, random);
		assert(spread() < wide);
	}
	puts("PASS: jumps reach anywhere; joining gathers");

	// Toward the player: to a room next to the player's, and on through its
	// doors in, while fewer than a crowd (small ones aside) are there.
	{
		Wanderers some; Random r(3); some.start(cast, map, rules, r);
		const int here = placeCode(kManiac, 0, 2), at = map.find(here);
		for (int i = 0; i < 80; ++i) if (some.where(i) == here) some.place(i, placeCode(kManiac, 0, 4));
		Rules pull; pull.jump = 0; pull.join = 0; pull.toward = 1000;
		int moved = 0;
		for (int t = 0; t < 20; ++t) {
			int last[80]; for (int i = 0; i < 80; ++i) last[i] = some.where(i);
			some.advance(60 * 200, here, cast, map, pull, r);
			for (int i = 0; i < 80; ++i) {
				if (some.where(i) == last[i]) continue;
				++moved;
				bool next = false;
				for (int d : map.doors[at]) next = next || map.places[d] == some.where(i);
				assert(next);
			}
		}
		assert(moved > 40);
		pull.toward = 0;
		for (int t = 0; t < 60; ++t) some.advance(60 * 200, here, cast, map, pull, r);
		assert(some.crowdAt(here, cast) <= pull.crowd && some.crowdAt(here, cast) > 0);
		int small = 0; for (int i = 0; i < 4; ++i) small += some.where(i) == here;
		assert(some.at(here, nullptr, 0) == some.crowdAt(here, cast) + small);
	}
	{
		// A critter comes in whoever is there; nobody else once four are.
		Map rooms; const int hall = placeCode(kManiac, 0, 1), side = placeCode(kManiac, 0, 2);
		rooms.add(hall); rooms.add(side); rooms.link(side, hall); rooms.link(hall, side);
		Cast critters;
		for (int i = 0; i < 4; ++i) critters.add(4000 + i, hall);
		critters.add(5000, side, 0, 1, true); critters.add(5001, side);
		Wanderers w; Random r(5); Rules doors; doors.jump = 0; doors.join = 0; doors.toward = 0;
		w.start(critters, rooms, doors, r);
		for (int i = 0; i < 4; ++i) w.place(i, hall);
		w.place(4, side); w.place(5, side);
		for (int t = 0; t < 40; ++t) w.advance(60 * 200, hall, critters, rooms, doors, r);
		assert(w.where(4) == hall && w.where(5) == side);
	}
	puts("PASS: toward the player; the crowd; small ones always fit");

	// The same seed moves them the same way; an empty map moves nobody.
	{
		Wanderers one, two; Random r1(9), r2(9);
		one.start(cast, map, rules, r1); two.start(cast, map, rules, r2);
		for (int t = 0; t < 100; ++t) {
			one.advance(60 * 20, map.places[0], cast, map, rules, r1);
			two.advance(60 * 20, map.places[0], cast, map, rules, r2);
		}
		for (int i = 0; i < 80; ++i) assert(one.where(i) == two.where(i));
		Map none; Wanderers lost; lost.start(cast, none, rules, r1);
		assert(lost.where(3) == 0 && !lost.advance(600, 0, cast, none, rules, r1));
	}
	puts("PASS: deterministic; an empty map moves nobody");

	// The game's side: everyone out, saved two places to a value and read
	// back; a character sent somewhere; small ones known.
	{
		namespace B = Scummverse::WanderBridge;
		B::reset(5);
		for (size_t p = 0; p < map.places.size(); ++p) B::addPlace(map.places[p], map.weights[p], map.groups[p]);
		for (size_t p = 0; p < map.places.size(); ++p) for (int d : map.doors[p]) B::addDoor(map.places[p], map.places[d]);
		for (size_t c = 0; c < cast.size(); ++c) B::addCast(cast.who[c], cast.homes[c], cast.games[c], cast.weights[c], cast.small[c]);
		assert(B::places() == 17 && B::cast() == 80 && B::signature() == cast.signature() && B::packedCount() == 40);
		assert(!B::started() && B::where(1000) == 0 && !B::advance(60, 0) && !B::send(1000, map.places[0]));
		B::start(); assert(B::started() && B::where(1000) && B::small(1000) && !B::small(1004) && !B::small(7));
		bool moved = false;
		for (int t = 0; t < 50; ++t) moved = B::advance(60 * 60, B::where(1010)) || moved;
		int seen = 0; for (int code : map.places) seen += B::at(code, nullptr, 0);
		assert(moved && seen == 80);
		int saved[40]; for (int i = 0; i < 40; ++i) saved[i] = B::packed(i);
		const int kept = B::where(2019);
		assert(B::send(2019, placeCode(kWorld, 9, 400)) && B::where(2019) == placeCode(kWorld, 9, 400) && !B::send(77, map.places[0]));
		for (int i = 0; i < 40; ++i) B::unpack(i, saved[i]);
		assert(B::where(2019) == kept);
		int here[80]; const int n = B::at(B::where(1020), here, 80);
		assert(n > 0 && std::count(here, here + std::min(n, 80), 1020) == 1);
	}
	puts("PASS: the game's side (saved, read back, sent, small)");

	// Capacity: by floor width, less residents, within the pool.
	assert(capacity(320, 0, 26) == 8 && capacity(320, 3, 26) == 5 && capacity(320, 9, 26) == 0);
	assert(capacity(2000, 2, 26) == 26 && capacity(60, 0, 26) == 1 && capacity(0, 0, 26) == 0 && capacity(320, 0, 26, 0) == 0);
	puts("PASS: capacity");
	return 0;
}
