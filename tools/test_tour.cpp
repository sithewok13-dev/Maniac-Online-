// Scummverse TOUR, portable part: requests from the interface, the game's
// label. Build: c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined
//   -Iengine tools/test_tour.cpp engine/common/scummverse_tour.cpp
#include "common/scummverse_tour.h"

#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <thread>

namespace Tour = Scummverse::Tour;

int main() {
	Tour::reset();
	int command = -1, stop = -1;
	assert(!Tour::takeRequest(command, stop));
	// Requests wait in order, each taken once; past 16 the oldest go.
	Tour::request(Tour::kPause);
	Tour::request(Tour::kPrevious);
	Tour::request(Tour::kGoTo, 137);
	assert(Tour::takeRequest(command, stop) && command == Tour::kPause && stop == 0);
	assert(Tour::takeRequest(command, stop) && command == Tour::kPrevious);
	assert(Tour::takeRequest(command, stop) && command == Tour::kGoTo && stop == 137);
	assert(!Tour::takeRequest(command, stop));
	for (int i = 1; i <= 20; ++i) Tour::request(Tour::kGoTo, i);
	for (int i = 5; i <= 20; ++i) assert(Tour::takeRequest(command, stop) && command == Tour::kGoTo && stop == i);
	assert(!Tour::takeRequest(command, stop));
	Tour::request(Tour::kNone);
	assert(!Tour::takeRequest(command, stop));
	std::printf("PASS: requests (in order, taken once, at most 16 waiting)\n");

	// Paused: as the game says.
	assert(!Tour::paused());
	Tour::publishPaused(true); assert(Tour::paused());
	Tour::publishPaused(false); assert(!Tour::paused());
	std::printf("PASS: paused\n");

	// Nothing said yet; then the game's label, truncated to the buffer.
	bool running = true; int next = 0, total = 0;
	char label[16];
	assert(!Tour::status(running, label, sizeof(label), next, total) && !running && next == 1 && total == 0 && !label[0]);
	Tour::publish(true, "Stop 12 of 846 \xC2\xB7 Maniac 12", 12, 846);
	assert(Tour::status(running, label, sizeof(label), next, total) && running && next == 12 && total == 846);
	assert(strlen(label) == sizeof(label) - 1 && !strncmp(label, "Stop 12 of 846", 14));
	char whole[64];
	assert(Tour::status(running, whole, sizeof(whole), next, total) && !strcmp(whole, "Stop 12 of 846 \xC2\xB7 Maniac 12"));
	Tour::publish(false, nullptr, 13, 846);
	assert(Tour::status(running, whole, sizeof(whole), next, total) && !running && !whole[0] && next == 13);
	// Cut short before the middle dot: never half of it.
	char cut[17];
	Tour::publish(true, "Stop 12 of 846 \xC2\xB7 Maniac 12", 12, 846);
	assert(Tour::status(running, cut, sizeof(cut), next, total) && !strcmp(cut, "Stop 12 of 846 "));
	std::printf("PASS: label (published, read back, truncated at a whole character, cleared)\n");

	// Speed: 1 until set; 2, 4, 8 and 16 kept, anything else is 1.
	assert(Tour::speed() == 1);
	Tour::setSpeed(16); assert(Tour::speed() == 16);
	Tour::setSpeed(8); assert(Tour::speed() == 8);
	Tour::setSpeed(32); assert(Tour::speed() == 1);
	Tour::setSpeed(4); assert(Tour::speed() == 4);
	Tour::setSpeed(2); assert(Tour::speed() == 2);
	Tour::setSpeed(3); assert(Tour::speed() == 1);
	Tour::setSpeed(4); Tour::setSpeed(0); assert(Tour::speed() == 1);
	std::printf("PASS: speed (1, 2, 4, 8 or 16)\n");

	// The interface and the game on two threads.
	Tour::publish(false, "", 1, 2);
	std::thread game([] {
		for (int i = 0; i < 20000; ++i) {
			int c, s;
			Tour::takeRequest(c, s);
			Tour::publish(i & 1, (i & 1) ? "Stop 1 of 2 \xC2\xB7 Zak 84" : "", 1 + (i & 1), 2);
			const int speed = Tour::speed();
			assert(speed == 1 || speed == 2 || speed == 4 || speed == 8 || speed == 16);
			Tour::publishPaused(i & 2);
		}
	});
	for (int i = 0; i < 20000; ++i) {
		Tour::request(Tour::kNext);
		Tour::setSpeed(i % 17);
		Tour::paused();
		bool r; char text[40]; int n, t;
		Tour::status(r, text, sizeof(text), n, t);
		assert(!r || !strcmp(text, "Stop 1 of 2 \xC2\xB7 Zak 84"));
	}
	game.join();
	Tour::reset();
	assert(!Tour::status(running, whole, sizeof(whole), next, total) && !Tour::takeRequest(command, stop) && Tour::speed() == 1 && !Tour::paused());
	std::printf("PASS: two threads; reset\n");
	return 0;
}
