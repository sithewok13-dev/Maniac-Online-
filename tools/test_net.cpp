// Local WiFi play: codec bounds, handshake rules, relaying, departures,
// silences, engines away and hostile input over real loopback TCP (one
// process; not two devices).
// c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//   tools/test_net.cpp engine/common/scummverse_net.cpp
#include "common/scummverse_net.h"
#include "common/scummverse_net_engine.h"
#include <algorithm>
#include <arpa/inet.h>
#include <cassert>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <netinet/in.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <thread>
#include <unistd.h>
using namespace Scummverse::Net;

static const int kContent = 0x6E34;
// (From 0209) Hosts on the next port free here: another program may hold
// one (any port in the ephemeral range, even for a moment). Copies run at
// once start apart.
static uint16_t hostOn(Session &session, int actor) {
	static uint16_t next = 47913 + (getpid() * 37 % 2000);
	std::string error;
	for (int tries = 0; tries < 64; ++tries, ++next) if (session.host(next, kContent, actor, error)) return next++;
	std::fprintf(stderr, "No port to host on: %s\n", error.c_str()); std::abort();
}

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

// (patch 0221) A Session never falls silent while its process runs (its keeper
// answers for it), so a device gone without a word is one by hand: frames
// written and read on a raw loopback socket, then nothing.
static sockaddr_in loopback(uint16_t p) {
	sockaddr_in a; std::memset(&a, 0, sizeof(a));
	a.sin_family = AF_INET; a.sin_port = htons(p); inet_pton(AF_INET, "127.0.0.1", &a.sin_addr);
	return a;
}
struct Wire {
	int fd = -1; std::string got;
	bool next(Frame &f) { // The next frame that has arrived, if any.
		char buffer[512]; const ssize_t n = recv(fd, buffer, sizeof(buffer), MSG_DONTWAIT);
		if (n > 0) got.append(buffer, (size_t)n);
		const int used = decode(got.data(), got.size(), f);
		if (used <= 0) return false;
		got.erase(0, (size_t)used); return true;
	}
	bool until(FrameType type, Frame &f) { while (next(f)) if (f.type == type) return true; return false; }
	void put(const Frame &f) { std::string wire; assert(encode(f, wire) && send(fd, wire.data(), wire.size(), 0) == (ssize_t)wire.size()); }
};
static Wire joinByHand(uint16_t p, int actor) {
	Wire w; w.fd = socket(AF_INET, SOCK_STREAM, 0); const sockaddr_in a = loopback(p);
	assert(connect(w.fd, (const sockaddr *)&a, sizeof(a)) == 0);
	Frame hello; hello.type = FrameType::Hello; hello.protocol = kProtocol; hello.content = kContent; hello.actor = actor; w.put(hello);
	return w;
}
static Frame avatarFrame(int peer, const Avatar &avatar) { Frame f; f.type = FrameType::Avatar; f.peer = peer; f.avatar = avatar; return f; }

// Until the keeper of each of these (its engine away) has polled again: all
// of one poll after this was called.
static void kept(std::vector<Node *> away) {
	std::vector<int> before; for (Node *n : away) before.push_back(n->session.keeperPollsForTests());
	for (int i = 0; i < 2000; ++i) {
		bool all = true;
		for (size_t k = 0; k < away.size(); ++k) if (away[k]->session.keeperPollsForTests() <= before[k]) all = false;
		if (all) return;
		std::this_thread::sleep_for(std::chrono::milliseconds(5));
	}
	std::fprintf(stderr, "A keeper never polled\n"); std::abort();
}

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
	// (From 0209) Ping carries nothing; one carrying anything is refused.
	Frame ping; ping.type = FrameType::Ping; ping.peer = 3; std::string pinged;
	assert(encode(ping, pinged) && pinged.size() == 4 && decode(pinged.data(), pinged.size(), g) == 4 && g.type == FrameType::Ping && g.peer == 3);
	const char padded[] = {3, 0, 7, 0, 0}; assert(decode(padded, sizeof(padded), g) == -1);
	std::printf("PASS: codec bounds and validation\n");
}

static void play() {
	Node host, annie, zak; std::string error;
	const uint16_t p = hostOn(host.session, 3); const std::string address = "127.0.0.1:" + std::to_string(p);
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
	// A device cannot take a character someone else controls: (from 0209)
	// it is told so and closed, and the one it played is everyone's again.
	annie.events.clear(); zak.events.clear(); host.events.clear();
	annie.session.setLocal(at(24, 53, 40, 60));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return annie.failedWith("already plays this character") && host.has(Event::Left, 20) && zak.has(Event::Left, 20); }));
	assert(!zak.has(Event::Moved, 24) && !host.has(Event::Moved, 24) && !annie.session.active() && host.session.remoteCount() == 1);
	assert(annie.session.join(address, kContent, 20, error));
	annie.session.setLocal(at(20, 53, 40, 60));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return annie.has(Event::Moved, 3) && annie.has(Event::Moved, 24) && zak.has(Event::Moved, 20); }));
	assert(host.session.remoteCount() == 2);
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
	// (From 0209) A device of the build before (protocol 2, no Ping) is
	// refused as another version, in a frame it reads.
	{
		int fd = socket(AF_INET, SOCK_STREAM, 0); sockaddr_in a; std::memset(&a, 0, sizeof(a));
		a.sin_family = AF_INET; a.sin_port = htons(p); inet_pton(AF_INET, "127.0.0.1", &a.sin_addr);
		assert(connect(fd, (sockaddr *)&a, sizeof(a)) == 0);
		Frame hello; hello.type = FrameType::Hello; hello.protocol = 2; hello.content = kContent; hello.actor = 9;
		std::string wire; assert(encode(hello, wire) && send(fd, wire.data(), wire.size(), 0) == (ssize_t)wire.size());
		std::string got; Frame reply;
		assert(pumpUntil({&host, &annie}, [&] {
			char buffer[64]; const ssize_t n = recv(fd, buffer, sizeof(buffer), MSG_DONTWAIT);
			if (n > 0) got.append(buffer, (size_t)n);
			return decode(got.data(), got.size(), reply) > 0;
		}));
		assert(reply.type == FrameType::Reject && reply.reason == (int)RejectReason::Version);
		close(fd);
	}
	// The host closing ends the game for joined devices, who get characters back.
	annie.events.clear(); host.session.close();
	assert(pumpUntil({&annie}, [&] { return annie.failedWith("closed the game"); }));
	assert(annie.has(Event::Left, 3) && !annie.session.active());
	std::printf("PASS: loopback host/join, relay, speech, duplicates, versions, departures, garbage\n");
}

static void capacity() {
	Node host; std::string error;
	const uint16_t p = hostOn(host.session, 1); const std::string address = "127.0.0.1:" + std::to_string(p);
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

// (From 0209) A join while full, read in the same poll as a leave: refused
// as full (the one leaving keeps its id until it is gone), never left
// without an answer; then there is room.
static void fullWhileLeaving() {
	Node host; std::string error;
	const uint16_t p = hostOn(host.session, 1); const std::string address = "127.0.0.1:" + std::to_string(p);
	Node guests[kMaxPeers];
	for (int i = 0; i < kMaxPeers; ++i) {
		assert(guests[i].session.join(address, kContent, 2 + i, error));
		assert(pumpUntil({&host, &guests[i]}, [&] { return guests[i].session.connected(); }));
	}
	// (Its Hello waits to be accepted while a guest says goodbye.)
	Node late; assert(late.session.join(address, kContent, 20, error));
	for (int i = 0; i < 20; ++i) { late.pump(); std::this_thread::sleep_for(std::chrono::milliseconds(2)); }
	guests[0].session.close();
	host.pump();
	assert(host.has(Event::Left, 2) && host.session.remoteCount() == kMaxPeers - 1);
	assert(pumpUntil({&host, &late}, [&] { return late.failedWith("full"); }));
	assert(late.session.join(address, kContent, 20, error));
	assert(pumpUntil({&host, &late}, [&] { return late.session.connected() && host.session.remoteCount() == kMaxPeers; }));
	std::printf("PASS: a join while full, in the poll a player leaves, refused; then joined\n");
}

// (From 0209) A listener the system breaks (as iOS can while the app is
// away) is opened again on the same port; where it cannot be, hosting ends,
// saying why, and its players are told. Here the listener's descriptor is
// swapped for one that is not a socket.
static int listenerOn(uint16_t p) {
	for (int fd = 0; fd < 1024; ++fd) {
		sockaddr_in a; socklen_t size = sizeof(a); int listening = 0; socklen_t length = sizeof(listening);
		if (getsockname(fd, (sockaddr *)&a, &size) != 0 || a.sin_family != AF_INET || ntohs(a.sin_port) != p) continue;
		if (getsockopt(fd, SOL_SOCKET, SO_ACCEPTCONN, &listening, &length) == 0 && listening) return fd;
	}
	return -1;
}

static void brokenListener() {
	Node host, annie, zak; std::string error;
	const uint16_t p = hostOn(host.session, 3); const std::string address = "127.0.0.1:" + std::to_string(p);
	assert(annie.session.join(address, kContent, 20, error));
	assert(pumpUntil({&host, &annie}, [&] { return annie.session.connected(); }));
	const int nothing = open("/dev/null", O_RDONLY); assert(nothing >= 0);
	int fd = listenerOn(p); assert(fd >= 0 && dup2(nothing, fd) == fd && listenerOn(p) < 0);
	host.pump();
	assert(listenerOn(p) >= 0 && host.session.hosting() && host.events.empty());
	assert(zak.session.join(address, kContent, 24, error));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return zak.session.connected() && host.session.remoteCount() == 2 && annie.session.connected(); }));
#ifdef __linux__
	// (patch 0221) Shut down under it, so that accept() says EINVAL (as Linux
	// does): opened again too, and someone more can join.
	fd = listenerOn(p); assert(fd >= 0 && shutdown(fd, SHUT_RDWR) == 0 && listenerOn(p) < 0);
	host.pump();
	assert(listenerOn(p) >= 0 && host.session.hosting() && host.events.empty());
	{
		Node guest; assert(guest.session.join(address, kContent, 9, error)); guest.session.setLocal(at(9, 53, 10, 60));
		assert(pumpUntil({&host, &annie, &zak, &guest}, [&] { return guest.session.connected() && host.session.remoteCount() == 3 && annie.has(Event::Moved, 9); }));
		guest.session.close();
		assert(pumpUntil({&host, &annie, &zak}, [&] { return host.session.remoteCount() == 2 && annie.has(Event::Left, 9); }));
		assert(annie.session.connected() && zak.session.connected());
	}
#endif
	// Broken again, its port taken meanwhile.
	fd = listenerOn(p); assert(fd >= 0 && dup2(nothing, fd) == fd);
	const int squatter = socket(AF_INET, SOCK_STREAM, 0); int one = 1;
	setsockopt(squatter, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
	sockaddr_in a; std::memset(&a, 0, sizeof(a)); a.sin_family = AF_INET; a.sin_port = htons(p); a.sin_addr.s_addr = htonl(INADDR_ANY);
	assert(bind(squatter, (sockaddr *)&a, sizeof(a)) == 0 && listen(squatter, 1) == 0);
	host.pump();
	assert(host.failedWith("Hosting stopped: ") && host.has(Event::Left, 20) && host.has(Event::Left, 24) && !host.session.active());
	assert(pumpUntil({&annie, &zak}, [&] { return annie.failedWith("closed the game") && zak.failedWith("closed the game"); }));
	close(squatter); close(nothing);
	std::printf("PASS: a broken listener opened again; hosting stopped where it cannot be\n");
}

// (From 0209) Quiet links stay up (each side pings); a device gone without
// a word is dropped after kSilentMs, and a host gone so is reported. Session
// time is moved on (advanceClockForTests), so nothing waits that long. (Round
// 3: the silent ones are devices by hand; see Wire.)
static void liveness() {
	Node host, annie, zak; std::string error;
	const uint16_t p = hostOn(host.session, 3); const std::string address = "127.0.0.1:" + std::to_string(p);
	host.session.setLocal(at(3, 53, 30, 60));
	assert(annie.session.join(address, kContent, 20, error)); annie.session.setLocal(at(20, 53, 40, 60));
	assert(zak.session.join(address, kContent, 24, error)); zak.session.setLocal(at(24, 53, 50, 60));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return host.session.remoteCount() == 2 && annie.has(Event::Moved, 24) && zak.has(Event::Moved, 20); }));
	const int step = kPingMs / 2;
	auto later = [&](std::vector<Node *> nodes) { // (Only these are pumped.)
		advanceClockForTests(step);
		for (int i = 0; i < 4; ++i) { for (Node *n : nodes) n->pump(); std::this_thread::sleep_for(std::chrono::milliseconds(2)); }
	};
	// Nobody moves for twice the limit: pings keep everyone.
	for (Node *n : {&host, &annie, &zak}) n->events.clear();
	for (int t = 0; t < 2 * kSilentMs; t += step) later({&host, &annie, &zak});
	for (Node *n : {&host, &annie, &zak}) assert(n->events.empty());
	assert(host.session.remoteCount() == 2 && annie.session.connected() && zak.session.connected());
	// A device joins by hand (playing 1), shows where it is, then leaves the
	// WiFi without a word: still here short of the limit, then gone for
	// everyone.
	Wire quiet = joinByHand(p, 1); Frame f;
	assert(pumpUntil({&host, &annie, &zak}, [&] { return quiet.until(FrameType::Welcome, f); }));
	quiet.put(avatarFrame(f.peer, at(1, 53, 60, 60)));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return host.session.remoteCount() == 3 && annie.has(Event::Moved, 1) && zak.has(Event::Moved, 1); }));
	for (Node *n : {&host, &annie, &zak}) n->events.clear();
	for (int t = 0; t < kSilentMs - 2 * kPingMs; t += step) later({&host, &annie, &zak});
	assert(host.session.remoteCount() == 3 && host.events.empty());
	for (int t = 0; t < 4 * kPingMs && !host.has(Event::Left, 1); t += step) later({&host, &annie, &zak});
	assert(host.has(Event::Left, 1) && host.session.remoteCount() == 2 && !host.has(Event::Left, 20) && !host.has(Event::Left, 24));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return annie.has(Event::Left, 1) && zak.has(Event::Left, 1); }));
	assert(annie.session.connected() && zak.session.connected());
	close(quiet.fd);
	// One whose app is killed (playing 2: its socket closed, no Bye) is gone
	// at once.
	Wire killed = joinByHand(p, 2);
	assert(pumpUntil({&host, &annie}, [&] { return killed.until(FrameType::Welcome, f); }));
	killed.put(avatarFrame(f.peer, at(2, 53, 70, 60)));
	assert(pumpUntil({&host, &annie}, [&] { return annie.has(Event::Moved, 2); }));
	close(killed.fd);
	assert(pumpUntil({&host, &annie}, [&] { return host.has(Event::Left, 2) && annie.has(Event::Left, 2); }));
	// A host goes the same way (by hand: it welcomes a guest, then says
	// nothing): the guest hears nothing and says so.
	const int silent = socket(AF_INET, SOCK_STREAM, 0); sockaddr_in a = loopback(0);
	socklen_t size = sizeof(a);
	assert(bind(silent, (sockaddr *)&a, sizeof(a)) == 0 && listen(silent, 1) == 0 && getsockname(silent, (sockaddr *)&a, &size) == 0);
	Node guest; assert(guest.session.join("127.0.0.1:" + std::to_string(ntohs(a.sin_port)), kContent, 9, error));
	Wire away; away.fd = accept(silent, nullptr, nullptr); assert(away.fd >= 0);
	assert(pumpUntil({&guest}, [&] { return away.until(FrameType::Hello, f); }) && f.actor == 9);
	Frame welcome; welcome.type = FrameType::Welcome; welcome.peer = 1; welcome.actor = 9; away.put(welcome);
	away.put(avatarFrame(0, at(3, 53, 30, 60)));
	assert(pumpUntil({&guest}, [&] { return guest.session.connected() && guest.has(Event::Moved, 3); }));
	guest.events.clear();
	// (The others pumped too: a session left alone while its clock jumps on
	// seconds a moment would be silent only here.)
	for (int t = 0; t < kSilentMs - 2 * kPingMs; t += step) later({&guest, &host, &annie, &zak});
	assert(guest.session.connected() && guest.events.empty());
	for (int t = 0; t < 4 * kPingMs && guest.session.active(); t += step) later({&guest, &host, &annie, &zak});
	assert(guest.failedWith("The host stopped answering.") && guest.has(Event::Left, 3) && !guest.session.active());
	close(away.fd);
	// (patch 0221) The same for another guest, its engine away: its keeper
	// hears the silence. A game it joins before its engine is back starts
	// clean, nothing of the one before held for it.
	Node other; assert(other.session.join("127.0.0.1:" + std::to_string(ntohs(a.sin_port)), kContent, 9, error));
	Wire gone; gone.fd = accept(silent, nullptr, nullptr); assert(gone.fd >= 0);
	assert(pumpUntil({&other}, [&] { return gone.until(FrameType::Hello, f); }));
	gone.put(welcome); gone.put(avatarFrame(0, at(3, 53, 30, 60)));
	assert(pumpUntil({&other}, [&] { return other.session.connected() && other.has(Event::Moved, 3); }));
	for (int t = 0; t < kSilentMs + 4 * kPingMs && other.session.active(); t += step) {
		advanceClockForTests(step); for (Node *n : {&host, &annie, &zak}) n->pump();
		kept({&other});
	}
	assert(!other.session.active());
	other.events.clear();
	assert(other.session.join(address, kContent, 9, error));
	assert(pumpUntil({&host, &other}, [&] { return other.session.connected() && host.session.remoteCount() == 3; }));
	for (const auto &e : other.events) assert(e.kind == Event::Moved);
	assert(other.session.connected());
	close(gone.fd); close(silent);
	std::printf("PASS: quiet links kept by pings; a silent player and a silent host dropped after %d ms, a closed one at once\n", kSilentMs);
}

// (patch 0221) The engine away (the ScummVM menu, the pause banner, a save's
// name typed, the app losing the screen) never drops anyone: its session's
// keeper keeps the links, pings and relays, however long. What it heard
// waits for the engine, for each player only the latest: where they are,
// their line, whether they left (and came back).
static void engineAway() {
	Node host, annie, zak; std::string error;
	const uint16_t p = hostOn(host.session, 3); const std::string address = "127.0.0.1:" + std::to_string(p);
	host.session.setLocal(at(3, 53, 30, 60));
	assert(annie.session.join(address, kContent, 20, error)); annie.session.setLocal(at(20, 53, 40, 60));
	assert(zak.session.join(address, kContent, 24, error)); zak.session.setLocal(at(24, 53, 50, 60));
	assert(pumpUntil({&host, &annie, &zak}, [&] { return host.session.remoteCount() == 2 && annie.has(Event::Moved, 24) && zak.has(Event::Moved, 20); }));
	const int step = kPingMs / 2;
	// (Those here are pumped, then those away polled by their keepers only,
	// each at least once after; later: session time moved on a step first.)
	auto settle = [&](std::vector<Node *> here, std::vector<Node *> away) {
		for (int i = 0; i < 4; ++i) { for (Node *n : here) n->pump(); std::this_thread::sleep_for(std::chrono::milliseconds(2)); }
		kept(away);
		for (Node *n : here) n->pump();
	};
	auto later = [&](std::vector<Node *> here, std::vector<Node *> away) { advanceClockForTests(step); settle(here, away); };
	auto only = [](const Node &n, int actor) { std::vector<Event> out; for (const auto &e : n.events) if (e.avatar.actor == actor) out.push_back(e); return out; };
	auto noneLost = [&] {
		for (Node *n : {&host, &annie, &zak}) for (const auto &e : n->events) assert(e.kind != Event::Left && e.kind != Event::Failed);
		assert(host.session.remoteCount() == 2 && annie.session.connected() && zak.session.connected());
	};
	for (Node *n : {&host, &annie, &zak}) n->events.clear();
	// The host's engine away for twice the limit while Annie walks: Zak sees
	// each step (the keeper relays); back, the host's engine hears her once,
	// where she is now.
	int x = 40;
	for (int t = 0; t < 2 * kSilentMs; t += step) { annie.session.setLocal(at(20, 53, ++x, 60)); later({&annie, &zak}, {&host}); }
	assert(pumpUntil({&annie, &zak}, [&] { return !only(zak, 20).empty() && only(zak, 20).back().avatar.x == x; }));
	kept({&host});
	noneLost();
	host.pump();
	assert(only(host, 20).size() == 1 && only(host, 20)[0].kind == Event::Moved && only(host, 20)[0].avatar == at(20, 53, x, 60));
	noneLost();
	// Annie's engine away while Zak walks and talks: back, she has his last
	// place and his last line.
	for (Node *n : {&host, &annie, &zak}) n->events.clear();
	for (int t = 0, line = 0; t < 2 * kSilentMs; t += step) {
		zak.session.setLocal(at(24, 53, 50 + t / step, 60)); assert(zak.session.say("Line " + std::to_string(++line)));
		later({&host, &zak}, {&annie});
	}
	const int lines = 2 * kSilentMs / step;
	assert(pumpUntil({&host, &zak}, [&] { return host.has(Event::Said, 24, ("Line " + std::to_string(lines)).c_str()); }));
	settle({&host, &zak}, {&annie}); // (Relayed, and heard by Annie's keeper.)
	noneLost();
	annie.pump();
	std::vector<Event> heard = only(annie, 24);
	assert(heard.size() == 2 && heard[0].kind == Event::Moved && heard[0].avatar.x == 50 + lines - 1);
	assert(heard[1].kind == Event::Said && heard[1].text == "Line " + std::to_string(lines));
	noneLost();
	// Annie's engine away while Zak speaks, then walks on: back, she has his
	// last place first, then his line (an engine takes a line only from
	// someone it has placed).
	for (Node *n : {&host, &annie, &zak}) n->events.clear();
	assert(zak.session.say("Over here")); later({&host, &zak}, {&annie});
	for (int i = 1; i <= 3; ++i) { zak.session.setLocal(at(24, 53, 70 + i, 60)); later({&host, &zak}, {&annie}); }
	assert(pumpUntil({&host, &zak}, [&] { return !only(host, 24).empty() && only(host, 24).back().avatar.x == 73; }));
	settle({&host, &zak}, {&annie});
	noneLost();
	annie.pump();
	heard = only(annie, 24);
	assert(heard.size() == 2 && heard[0].kind == Event::Moved && heard[0].avatar == at(24, 53, 73, 60));
	assert(heard[1].kind == Event::Said && heard[1].text == "Over here");
	noneLost();
	// Everyone's engine away at once (every device in a menu): all still
	// there after.
	for (int t = 0; t < 2 * kSilentMs; t += step) later({}, {&host, &annie, &zak});
	for (Node *n : {&host, &annie, &zak}) n->pump();
	noneLost();
	// Away while Zak leaves and joins other: Annie hears that he left, then
	// where he is now; nothing of before.
	for (Node *n : {&host, &annie, &zak}) n->events.clear();
	zak.session.setLocal(at(24, 53, 20, 60)); later({&host, &zak}, {&annie});
	zak.session.close();
	assert(pumpUntil({&host}, [&] { return host.has(Event::Left, 24); }));
	settle({&host}, {&annie});
	assert(zak.session.join(address, kContent, 24, error)); zak.session.setLocal(at(24, 55, 92, 59));
	assert(pumpUntil({&host, &zak}, [&] { return host.has(Event::Moved, 24) && only(host, 24).back().avatar == at(24, 55, 92, 59) && zak.session.connected(); }));
	settle({&host, &zak}, {&annie});
	annie.pump();
	heard = only(annie, 24);
	assert(heard.size() == 2 && heard[0].kind == Event::Left && heard[1].kind == Event::Moved && heard[1].avatar == at(24, 55, 92, 59));
	assert(annie.session.connected() && host.session.remoteCount() == 2);
	// Away while Zak leaves for good: once.
	annie.events.clear(); zak.session.close();
	assert(pumpUntil({&host}, [&] { return host.has(Event::Left, 24); }));
	settle({&host}, {&annie});
	annie.pump();
	heard = only(annie, 24);
	assert(heard.size() == 1 && heard[0].kind == Event::Left && annie.session.connected());
	std::printf("PASS: an engine away %d ms (host, player, everyone) drops nobody; what was heard waits, the latest of each\n", 2 * kSilentMs);
}

// (A player who joins while the host's engine is away, speaks, then moves:
// back, the host's engine has them placed first, then their line, which it
// would drop from someone it has not placed.)
static void joinedWhileAway() {
	Node host, suzy; std::string error;
	const uint16_t p = hostOn(host.session, 3);
	host.session.setLocal(at(3, 53, 30, 60)); host.pump();
	advanceClockForTests(kAwayMs + kKeepMs); // (The host's engine away from here on.)
	assert(suzy.session.join("127.0.0.1:" + std::to_string(p), kContent, 5, error));
	suzy.session.setLocal(at(5, 53, 40, 60));
	for (int i = 0; i < 400 && !suzy.has(Event::Moved, 3); ++i) { suzy.pump(); kept({&host}); }
	assert(suzy.session.connected() && suzy.has(Event::Moved, 3));
	assert(suzy.session.say("Hello there")); suzy.pump(); kept({&host}); kept({&host});
	suzy.session.setLocal(at(5, 53, 42, 60)); suzy.pump(); kept({&host}); kept({&host});
	assert(host.session.remoteCount() == 1 && host.events.empty());
	host.pump();
	assert(host.events.size() == 2 && host.events[0].kind == Event::Moved && host.events[0].peer == 1 && host.events[0].avatar == at(5, 53, 42, 60));
	assert(host.events[1].kind == Event::Said && host.events[1].peer == 1 && host.events[1].avatar.actor == 5 && host.events[1].text == "Hello there");
	std::printf("PASS: joined, spoke and moved while the host's engine was away: placed first, then heard\n");
}

// (patch 0221) A host out of descriptors (EMFILE) keeps its listener: one
// joining waits in the backlog and comes in once there are some other, and
// nobody is dropped. (0209 opened the listener other on any accept() error:
// the backlog reset, and hosting ended where that failed too.)
static void crowdedListener() {
	Node host, annie, zak; std::string error;
	const uint16_t p = hostOn(host.session, 3); const std::string address = "127.0.0.1:" + std::to_string(p);
	assert(annie.session.join(address, kContent, 20, error));
	assert(pumpUntil({&host, &annie}, [&] { return annie.session.connected(); }));
	// Every descriptor taken but one, for Zak's device's socket.
	rlimit was; assert(getrlimit(RLIMIT_NOFILE, &was) == 0);
	int highest = 0; for (int fd = 0; fd < 4096; ++fd) if (fcntl(fd, F_GETFD) != -1) highest = fd;
	rlimit few = was; few.rlim_cur = (rlim_t)highest + 8; assert(setrlimit(RLIMIT_NOFILE, &few) == 0);
	std::vector<int> taken; for (int fd; (fd = open("/dev/null", O_RDONLY)) >= 0;) taken.push_back(fd);
	assert(errno == EMFILE && !taken.empty());
	close(taken.back()); taken.pop_back();
	assert(zak.session.join(address, kContent, 24, error));
	for (int i = 0; i < 100; ++i) { for (Node *n : {&host, &annie, &zak}) n->pump(); std::this_thread::sleep_for(std::chrono::milliseconds(2)); }
	const bool waiting = zak.session.active() && !zak.session.connected();
	for (int fd : taken) close(fd);
	assert(setrlimit(RLIMIT_NOFILE, &was) == 0);
	assert(waiting && host.session.hosting() && host.events.empty() && annie.session.connected());
	assert(pumpUntil({&host, &annie, &zak}, [&] { return zak.session.connected() && host.session.remoteCount() == 2; }));
	assert(annie.session.connected() && host.events.empty());
	std::printf("PASS: out of descriptors, a host keeps its listener; the one joining comes in after\n");
}

// The addresses a host shares: only interfaces up and running, not loopback
// or point-to-point (cellular, VPN), WiFi and the hotspot first, each address
// once and whole (192.168.1.2 is not part of 192.168.1.20).
static Interface entry(const char *name, const char *dotted, bool running = true, bool pointToPoint = false) {
	Interface i; i.name = name; in_addr a;
	if (inet_pton(AF_INET, dotted, &a) != 1) std::abort();
	i.address = ntohl(a.s_addr); i.up = true; i.running = running; i.pointToPoint = pointToPoint; i.loopback = !std::strncmp(name, "lo", 2);
	return i;
}
static void addresses() {
	// (As an iPhone lists them: cellular and the VPN before the WiFi.)
	const std::vector<Interface> phone = {
		entry("lo0", "127.0.0.1"), entry("pdp_ip0", "10.64.12.7", true, true), entry("utun3", "10.8.0.2", true, true),
		entry("anpi0", "10.0.0.5"), entry("en0", "192.168.1.20"), entry("bridge100", "172.20.10.1"),
		entry("en0", "192.168.1.2"), entry("en2", "169.254.3.4", false), entry("en1", "192.168.1.20")};
	const std::vector<std::string> expected = {"192.168.1.20", "192.168.1.2", "172.20.10.1", "10.0.0.5"};
	assert(reachableAddresses(phone) == expected);
	// Down, or loopback only: none (localAddresses then says "this device").
	std::vector<Interface> off = {entry("lo0", "127.0.0.1"), entry("en0", "192.168.1.20")};
	off[1].up = false;
	assert(reachableAddresses(off).empty() && reachableAddresses({}).empty());
	// This machine's own list: never loopback, never one address twice.
	const std::string here = localAddresses();
	std::vector<std::string> listed;
	for (size_t at = 0; at <= here.size();) {
		const size_t end = std::min(here.find(", ", at), here.size());
		listed.push_back(here.substr(at, end - at)); at = end + 2;
	}
	for (const std::string &one : listed) assert(!one.empty() && one.compare(0, 4, "127.") != 0);
	std::sort(listed.begin(), listed.end());
	assert(std::adjacent_find(listed.begin(), listed.end()) == listed.end());
	std::printf("PASS: shared addresses: up and running, no cellular, VPN or loopback, WiFi first, whole (here: %s)\n", here.c_str());
}

// A host's status is asked on every engine update: the system's list is read
// as hosting starts (again when hosting anew), then at most every
// kAddressRefreshMs; it says what a fresh look says.
static void addressCache() {
	Session host;
	const uint16_t p = hostOn(host, 3);
	const int first = addressLookupsForTests();
	const std::string said = host.describe();
	assert(addressLookupsForTests() == first + 1);
	const std::string here = localAddresses();
	assert(said == "Hosting on " + here + " port " + std::to_string(p) + " - 0 other players");
	const int looked = first + 2;
	for (int i = 0; i < 200; ++i) assert(host.describe() == said);
	advanceClockForTests(kAddressRefreshMs / 2);
	assert(host.describe() == said && addressLookupsForTests() == looked);
	advanceClockForTests(kAddressRefreshMs / 2);
	assert(host.describe() == said && addressLookupsForTests() == looked + 1);
	assert(host.describe() == said && addressLookupsForTests() == looked + 1);
	host.close();
	const uint16_t q = hostOn(host, 3);
	assert(host.describe() == "Hosting on " + here + " port " + std::to_string(q) + " - 0 other players");
	assert(addressLookupsForTests() == looked + 2);
	host.close();
	std::printf("PASS: a host's addresses read as it starts, then at most every %d ms\n", kAddressRefreshMs);
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
	codec(); play(); capacity(); fullWhileLeaving(); brokenListener(); crowdedListener(); liveness(); engineAway(); joinedWhileAway(); addresses(); addressCache(); control();
	std::printf("PASS: local WiFi session tests (loopback, one process)\n");
}
