// Local WiFi play: codec bounds, handshake rules, relaying, departures,
// silences and hostile input over real loopback TCP (one process; not two
// devices).
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
// time is moved on (advanceClockForTests), so nothing waits that long.
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
	// Zak's device leaves the WiFi without a word (no longer pumped): still
	// here short of the limit, then gone for everyone.
	for (int t = 0; t < kSilentMs - 2 * kPingMs; t += step) later({&host, &annie});
	assert(host.session.remoteCount() == 2 && host.events.empty());
	for (int t = 0; t < 4 * kPingMs && !host.has(Event::Left, 24); t += step) later({&host, &annie});
	assert(host.has(Event::Left, 24) && host.session.remoteCount() == 1 && !host.has(Event::Left, 20));
	assert(pumpUntil({&host, &annie}, [&] { return annie.has(Event::Left, 24); }));
	assert(annie.session.connected());
	// The host goes the same way: Annie hears nothing and says so.
	annie.events.clear();
	for (int t = 0; t < kSilentMs - 2 * kPingMs; t += step) later({&annie});
	assert(annie.session.connected() && annie.events.empty());
	for (int t = 0; t < 4 * kPingMs && annie.session.active(); t += step) later({&annie});
	assert(annie.failedWith("The host stopped answering.") && annie.has(Event::Left, 3) && !annie.session.active());
	std::printf("PASS: quiet links kept by pings; a silent player and a silent host dropped after %d ms\n", kSilentMs);
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
	codec(); play(); capacity(); fullWhileLeaving(); brokenListener(); liveness(); addresses(); addressCache(); control();
	std::printf("PASS: local WiFi session tests (loopback, one process)\n");
}
