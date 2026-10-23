// Local WiFi play: codec bounds, handshake rules, relaying, departures and
// hostile input over real loopback TCP (one process; not two devices).
// c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//   tools/test_net.cpp engine/common/scummverse_net.cpp
#include "common/scummverse_net.h"
#include "common/scummverse_net_engine.h"
#include <arpa/inet.h>
#include <cassert>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <netinet/in.h>
#include <sys/socket.h>
#include <thread>
#include <unistd.h>
using namespace Scummverse::Net;

static const int kContent = 0x6E34;
static uint16_t port() { static uint16_t next = 47913 + (getpid() % 2000); return next++; }

struct Node {
	Session session; std::vector<Event> events;
	void pump() { session.poll(events); }
	bool has(Event::Kind kind, int actor, const char *text = nullptr) const {
		for (const auto &e : events) if (e.kind == kind && e.avatar.actor == actor && (!text || e.text == text)) return true;
		return false;
	}
	bool failedWith(const char *fragment) const {
		for (const auto &e : events) if (e.kind == Event::Failed && e.text.find(fragment) != std::string::npos) return true;
		return false;
	}
};

template <typename F> static bool pumpUntil(std::vector<Node *> nodes, F done) {
	for (int i = 0; i < 400; ++i) {
		for (Node *n : nodes) n->pump();
		if (done()) return true;
		std::this_thread::sleep_for(std::chrono::milliseconds(5));
	}
	return false;
}

static Avatar at(int actor, int room, int x, int y) { Avatar a; a.actor = actor; a.room = room; a.x = x; a.y = y; return a; }

static void codec() {
	Frame f; f.type = FrameType::Avatar; f.peer = 2; f.avatar = at(24, 134, -3, 60);
	std::string wire; assert(encode(f, wire));
	Frame g; assert(decode(wire.data(), wire.size(), g) == (int)wire.size());
	assert(g.type == FrameType::Avatar && g.peer == 2 && g.avatar == f.avatar);
	for (size_t cut = 0; cut < wire.size(); ++cut) assert(decode(wire.data(), cut, g) == 0); // Incomplete.
	Frame s; s.type = FrameType::Say; s.actor = 3; s.text = "Hello from the airport!";
	std::string say; assert(encode(s, say) && decode(say.data(), say.size(), g) > 0 && g.text == s.text);
	// Out-of-range fields never encode or decode.
	Frame bad = f; bad.avatar.actor = 25; std::string none; assert(!encode(bad, none) && none.empty());
	bad = s; bad.text = "caf\xc3\xa9"; assert(!encode(bad, none));
	bad.text = std::string(kMaxSay + 1, 'x'); assert(!encode(bad, none));
	bad.text = "   "; assert(!encode(bad, none));
	bad = f; bad.peer = kMaxPeers + 1; assert(!encode(bad, none));
	std::string tampered = say; tampered[6] = '\x01'; assert(decode(tampered.data(), tampered.size(), g) == -1);
	const char huge[] = {(char)0xFF, (char)0xFF, 1, 0}; assert(decode(huge, sizeof(huge), g) == -1);
	const char unknown[] = {2, 0, 99, 0}; assert(decode(unknown, sizeof(unknown), g) == -1);
	assert(validSay("Hi!") && !validSay("") && !validSay("tab\there"));
	// (From 0196: a place in another world, as a room, round trips; rooms
	// between the mansion's and those, and none, never.)
	Frame w = f; w.avatar = at(20, Scummverse::NetBridge::worldPlace(0, 33), 40, 60);
	std::string world; assert(encode(w, world) && decode(world.data(), world.size(), g) > 0 && g.avatar == w.avatar);
	assert(Scummverse::NetBridge::worldPlaceGame(g.avatar.room) == 0 && Scummverse::NetBridge::worldPlaceRoom(g.avatar.room) == 33);
	assert(Scummverse::NetBridge::worldPlace(11, 1023) < 65536 && Scummverse::NetBridge::worldPlaceGame(Scummverse::NetBridge::worldPlace(11, 1023)) == 11);
	for (int room : {0, 256, 4095, 65536}) { bad = f; bad.avatar.room = room; assert(!encode(bad, none)); }
	// Decoding checks the room too (its bytes set by hand: 4129 is 0x1021).
	Frame w2 = w; w2.avatar.room += 1; std::string next; assert(encode(w2, next) && next.size() == world.size());
	size_t low = 0; while (world[low] == next[low]) ++low;
	const size_t high = world[low + 1] == 0x10 ? low + 1 : low - 1;
	assert(world[high] == 0x10 && world[low] == 0x21);
	for (int room : {256, 4095, 4130}) {
		std::string hand = world; hand[high] = (char)(room >> 8); hand[low] = (char)(room & 0xFF);
		assert((decode(hand.data(), hand.size(), g) > 0) == (room == 4130));
	}
	// (From 0197: the look played, in 32 bits; none above kMaxLook. It is
	// the last field: a top byte set by hand is refused on receipt.)
	Frame l = f; l.avatar.look = 1000 * 1024 + 3 + 1;
	std::string looked; assert(encode(l, looked) && decode(looked.data(), looked.size(), g) > 0 && g.avatar == l.avatar && g.avatar.look == 1024004);
	for (int look : {-1, kMaxLook + 1}) { bad = f; bad.avatar.look = look; assert(!encode(bad, none)); }
	bad = f; bad.avatar.look = kMaxLook; assert(encode(bad, none) && decode(none.data(), none.size(), g) > 0 && g.avatar.look == kMaxLook);
	std::string top = looked; top[top.size() - 1] = 1; assert(decode(top.data(), top.size(), g) == -1);
	std::printf("PASS: codec bounds and validation\n");
}

static void play() {
	const uint16_t p = port(); const std::string address = "127.0.0.1:" + std::to_string(p);
	Node host, annie, zak; std::string error;
	assert(host.session.host(p, kContent, 3, error));
	host.session.setLocal(at(3, 53, 30, 60));
	assert(annie.session.join(address, kContent, 20, error));
	assert(pumpUntil({&host, &annie}, [&] { return annie.session.connected() && annie.has(Event::Moved, 3); }));
	// The host learns about Annie once she reports her avatar.
	annie.session.setLocal(at(20, 53, 40, 60));
	assert(pumpUntil({&host, &annie}, [&] { return host.has(Event::Moved, 20); }));
	// A newcomer receives everyone already here, and everyone learns about them.
	assert(zak.session.join(address, kContent, 24, error));
	zak.session.setLocal(at(24, 55, 92, 59));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return zak.has(Event::Moved, 3) && zak.has(Event::Moved, 20) && annie.has(Event::Moved, 24) && host.has(Event::Moved, 24); }));
	assert(host.session.remoteCount() == 2);
	// (From 0197) The look played is relayed with the avatar.
	Avatar costumed = at(24, 55, 92, 59); costumed.look = 1000 * 1024 + 3 + 1;
	zak.session.setLocal(costumed);
	auto saw = [&](const Node &n) { for (const auto &e : n.events) if (e.kind == Event::Moved && e.avatar == costumed) return true; return false; };
	assert(pumpUntil({&host, &annie, &zak}, [&] { return saw(annie) && saw(host); }));
	// Speech is relayed with the speaker's own character.
	assert(annie.session.say("Over here!"));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return host.has(Event::Said, 20, "Over here!") && zak.has(Event::Said, 20, "Over here!"); }));
	assert(host.session.say("Welcome aboard"));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return annie.has(Event::Said, 3, "Welcome aboard") && zak.has(Event::Said, 3, "Welcome aboard"); }));
	assert(!annie.session.say("bad\x07"));
	// A device cannot take a character someone else controls.
	annie.events.clear(); zak.events.clear();
	annie.session.setLocal(at(24, 53, 40, 60));
	for (int i = 0; i < 20; ++i) { host.pump(); annie.pump(); zak.pump(); std::this_thread::sleep_for(std::chrono::milliseconds(5)); }
	assert(!zak.has(Event::Moved, 24));
	// Duplicate character and wrong version are refused with a reason.
	Node twin; assert(twin.session.join(address, kContent, 24, error));
	assert(pumpUntil({&host, &twin}, [&] { return twin.failedWith("already plays this character"); }));
	assert(!twin.session.active());
	Node old; assert(old.session.join(address, kContent + 1, 9, error));
	assert(pumpUntil({&host, &old}, [&] { return old.failedWith("different game version"); }));
	// Leaving returns that character to everyone else.
	zak.session.close();
	assert(pumpUntil({&host, &annie}, [&] { return host.has(Event::Left, 24) && annie.has(Event::Left, 24); }));
	assert(host.session.remoteCount() == 1);
	// Garbage from a stranger drops only that connection.
	{
		int fd = socket(AF_INET, SOCK_STREAM, 0); sockaddr_in a; std::memset(&a, 0, sizeof(a));
		a.sin_family = AF_INET; a.sin_port = htons(p); inet_pton(AF_INET, "127.0.0.1", &a.sin_addr);
		assert(connect(fd, (sockaddr *)&a, sizeof(a)) == 0);
		const char junk[] = "GET / HTTP/1.1\r\n\r\n"; assert(send(fd, junk, sizeof(junk), 0) > 0);
		char c; bool closed = pumpUntil({&host, &annie}, [&] { return recv(fd, &c, 1, MSG_DONTWAIT) == 0; });
		assert(closed); close(fd);
		assert(host.session.remoteCount() == 1 && annie.session.connected());
	}
	// The host closing ends the game for joined devices, who get characters back.
	annie.events.clear(); host.session.close();
	assert(pumpUntil({&annie}, [&] { return annie.failedWith("closed the game"); }));
	assert(annie.has(Event::Left, 3) && !annie.session.active());
	std::printf("PASS: loopback host/join, relay, speech, duplicates, versions, departures, garbage\n");
}

static void capacity() {
	const uint16_t p = port(); const std::string address = "127.0.0.1:" + std::to_string(p);
	Node host; std::string error; assert(host.session.host(p, kContent, 1, error));
	Node guests[kMaxPeers + 1];
	for (int i = 0; i < kMaxPeers; ++i) {
		assert(guests[i].session.join(address, kContent, 2 + i, error));
		assert(pumpUntil({&host, &guests[i]}, [&] { return guests[i].session.connected(); }));
	}
	assert(guests[kMaxPeers].session.join(address, kContent, 20, error));
	assert(pumpUntil({&host, &guests[kMaxPeers]}, [&] { return guests[kMaxPeers].failedWith("full"); }));
	Node lost; assert(lost.session.join("127.0.0.1:1", kContent, 5, error));
	assert(pumpUntil({&lost}, [&] { return !lost.session.active(); }));
	assert(!lost.session.join("not an address", kContent, 5, error) && !error.empty());
	std::printf("PASS: capacity %d, unreachable host, invalid address\n", kMaxPeers);
}

static void control() {
	Request r; r.kind = Request::Join; r.text = "192.168.1.20"; postRequest(r);
	Request got; assert(takeRequest(got) && got.kind == Request::Join && got.text == "192.168.1.20" && !takeRequest(got));
	publishStatus("Hosting", true, 2); assert(status() == "Hosting" && online() && players() == 2);
	std::thread other([] { for (int i = 0; i < 1000; ++i) { Request q; q.kind = Request::Say; q.text = "x"; postRequest(q); } });
	for (int i = 0; i < 1000; ++i) { Request q; takeRequest(q); }
	other.join();
	while (takeRequest(got)) {}
	std::printf("PASS: cross-thread control\n");
}

int main() {
	codec(); play(); capacity(); control();
	std::printf("PASS: local WiFi session tests (loopback, one process)\n");
}
