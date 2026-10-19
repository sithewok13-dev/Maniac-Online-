// Other-worlds scene loader with synthetic scenes (no game data).
// c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//   tools/test_world.cpp engine/common/scummverse_world.cpp
#include "common/scummverse_world.h"
#include "common/scummverse_world_catalog.h"
#include "common/scummverse_world_engine.h"
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
using namespace Scummverse::World;

static void put16(std::vector<uint8_t> &v, int x) { v.push_back((uint8_t)(x & 255)); v.push_back((uint8_t)((x >> 8) & 255)); }
static std::vector<uint8_t> sceneBytes(int w, int h, const std::vector<uint8_t> &pixels, const std::vector<SourceBox> &boxes) {
	std::vector<uint8_t> d = {'S', 'V', 'W', '1'};
	put16(d, 7); put16(d, w); put16(d, h); d.push_back((uint8_t)boxes.size()); d.push_back(0);
	for (int c = 0; c < 256; ++c) { d.push_back((uint8_t)c); d.push_back((uint8_t)(255 - c)); d.push_back((uint8_t)(c / 2)); }
	d.insert(d.end(), pixels.begin(), pixels.end());
	for (const auto &b : boxes) { for (int c = 0; c < 4; ++c) { put16(d, b.x[c]); put16(d, b.y[c]); } d.push_back((uint8_t)b.flags); d.push_back((uint8_t)b.mask); }
	return d;
}
static SourceBox box(int l, int t, int r, int b, int flags = 0) {
	SourceBox x; x.x[0] = l; x.y[0] = t; x.x[1] = r; x.y[1] = t; x.x[2] = r; x.y[2] = b; x.x[3] = l; x.y[3] = b; x.flags = flags; return x;
}
// The V1 tile stream decoder (engine GdiV1::decodeV1Gfx), returning bytes used.
static size_t decodeV1(const uint8_t *src, uint8_t *dst, int size) {
	const uint8_t *start = src; uint8_t common[4];
	for (int z = 0; z < 4; ++z) common[z] = *src++;
	int x = 0;
	while (x < size) {
		uint8_t run = *src++;
		if (run & 0x80) { uint8_t c = common[(run >> 5) & 3]; run &= 0x1F; for (int z = 0; z <= run; ++z) dst[x++] = c; }
		else if (run & 0x40) { run &= 0x3F; uint8_t c = *src++; for (int z = 0; z <= run; ++z) dst[x++] = c; }
		else for (int z = 0; z <= run; ++z) dst[x++] = *src++;
	}
	assert(x == size);
	return (size_t)(src - start);
}

struct Frame { int dir, kind, index, dx, dy, w, h; uint8_t color; };
static std::vector<uint8_t> spriteBytes(const std::vector<Frame> &frames) {
	std::vector<uint8_t> d = {'S', 'V', 'C', '1'};
	put16(d, 5); put16(d, (int)frames.size());
	for (int c = 0; c < 256; ++c) { d.push_back((uint8_t)c); d.push_back((uint8_t)c); d.push_back((uint8_t)(255 - c)); }
	for (const Frame &f : frames) {
		d.push_back((uint8_t)f.dir); d.push_back((uint8_t)f.kind); d.push_back((uint8_t)f.index); d.push_back(0);
		put16(d, f.dx); put16(d, f.dy); put16(d, f.w); put16(d, f.h);
		// Pixels: color in the left half, color+1 in the right; the top row is transparent.
		for (int y = 0; y < f.h; ++y) for (int x = 0; x < f.w; ++x) d.push_back((uint8_t)(f.color + (x >= f.w / 2)));
		for (int y = 0; y < f.h; ++y) for (int x = 0; x < f.w; ++x) d.push_back(y > 0);
	}
	return d;
}

static void testSprites() {
	const std::vector<Frame> frames = {{kGuestFront, kGuestStand, 0, -10, -40, 20, 40, 30}, {kGuestLeft, kGuestWalk, 0, -8, -40, 16, 40, 50},
		{kGuestLeft, kGuestWalk, 1, -8, -38, 16, 38, 50}, {kGuestLeft, kGuestTalk, 0, -8, -40, 16, 40, 70}};
	auto bytes = spriteBytes(frames);
	SourceSprite src; std::string error;
	assert(parseSprite(bytes.data(), bytes.size(), src, error) && src.costume == 5 && src.frames.size() == 4);
	assert(src.frames[1].dx == -8 && src.frames[1].dy == -40 && src.frames[2].height == 38 && src.palette[3 * 50 + 2] == 205);
	for (size_t cut : {bytes.size() - 1, (size_t)20, (size_t)0}) assert(!parseSprite(bytes.data(), cut, src, error));
	auto bad = bytes; bad[8 + 768] = 9; assert(!parseSprite(bad.data(), bad.size(), src, error)); // direction
	bad = bytes; bad.push_back(0); assert(!parseSprite(bad.data(), bad.size(), src, error));
	assert(parseSprite(bytes.data(), bytes.size(), src, error));

	SandboxSprite fit;
	assert(fitSprite(src, 0.5, 224, 32, fit, error) && fit.frames.size() == 4 && fit.slotCount == 6);
	const SpriteFrame &front = fit.frames[0];
	assert(front.dx == -5 && front.dy == -20 && front.width == 10 && front.height == 20);
	// The feet stay on the anchor: the bottom edge of every frame is at y 0.
	for (const auto &f : fit.frames) assert(f.dy + f.height == 0 || f.dy + f.height == 1);
	int opaque = 0;
	for (size_t i = 0; i < front.pixels.size(); ++i) {
		const uint8_t p = front.pixels[i];
		assert(p == 0 || (p >= 224 && p < 230));
		if (p) { ++opaque; const int slot = p - 224; assert(fit.palette[slot * 3] == 30 || fit.palette[slot * 3] == 31); }
	}
	assert(opaque > 0);
	// Widened (square-pixel art): 1.2 times wider about the feet, as tall.
	{
		SourceSprite wideSrc = src; wideSrc.widen = 1.2;
		SandboxSprite wideFit; assert(fitSprite(wideSrc, 0.5, 224, 32, wideFit, error));
		assert(wideFit.frames[0].dx == -6 && wideFit.frames[0].width == 12 && wideFit.frames[0].height == 20 && wideFit.frames[0].dy == -20);
	}
	// At full size the transparent top row stays transparent.
	assert(fitSprite(src, 1.0, 224, 32, fit, error));
	for (int x = 0; x < 20; ++x) assert(fit.frames[0].pixels[x] == 0 && fit.frames[0].pixels[20 + x] != 0);
	// Too few slots: the most common colors are kept, the rest snap to them.
	assert(fitSprite(src, 1.0, 250, 3, fit, error) && fit.slotCount == 3);
	for (const auto &f : fit.frames) for (uint8_t p : f.pixels) assert(p == 0 || (p >= 250 && p < 253));
	assert(!fitSprite(src, 1.0, 0, 8, fit, error) && !fitSprite(src, 1.0, 250, 8, fit, error) && !fitSprite(src, 0, 224, 8, fit, error));

	// Lookup: exact frames, looping indices, pose and facing fallbacks.
	assert(fitSprite(src, 1.0, 224, 32, fit, error));
	assert(fit.frameCount(kGuestLeft, kGuestWalk) == 2 && fit.frameCount(kGuestBack, kGuestWalk) == 0);
	assert(fit.frame(kGuestLeft, kGuestWalk, 1)->height == 38 && fit.frame(kGuestLeft, kGuestWalk, 3)->height == 38);
	assert(fit.frame(kGuestRight, kGuestWalk, 0)->dir == kGuestLeft);            // nearest facing
	assert(fit.frame(kGuestFront, kGuestTalk, 0)->dir == kGuestLeft);            // talking only drawn facing left
	assert(fit.frame(kGuestFront, kGuestWalk, 0)->dir == kGuestLeft);
	assert(fit.frame(kGuestBack, kGuestStand, 0)->dir == kGuestFront);
	assert(!fit.frame(7, kGuestStand, 0) && !fit.frame(kGuestFront, 9, 0));
	// Seated: not drawn, standing; drawn (facing right only), from any facing;
	// a kind beyond seated is refused.
	assert(fit.frame(kGuestFront, kGuestSeated, 0)->kind == kGuestStand && !fit.frame(kGuestFront, kGuestKinds, 0));
	{
		std::vector<Frame> withSeat = frames;
		withSeat.push_back({kGuestRight, kGuestSeated, 0, -12, -30, 24, 30, 90});
		auto seatBytes = spriteBytes(withSeat);
		SourceSprite seatSrc; SandboxSprite seatFit;
		assert(parseSprite(seatBytes.data(), seatBytes.size(), seatSrc, error) && seatSrc.frames.size() == 5);
		assert(fitSprite(seatSrc, 1.0, 224, 32, seatFit, error) && seatFit.frameCount(kGuestRight, kGuestSeated) == 1);
		assert(seatFit.frame(kGuestRight, kGuestSeated, 0)->height == 30 && seatFit.frame(kGuestLeft, kGuestSeated, 0)->dir == kGuestRight);
		assert(seatFit.frame(kGuestRight, kGuestStand, 0)->kind == kGuestStand);
		seatBytes[seatBytes.size() - (12 + 2 * 24 * 30) + 1] = kGuestKinds; // the seated frame's kind
		assert(!parseSprite(seatBytes.data(), seatBytes.size(), seatSrc, error));
	}
	// Several characters share one palette by RGB value (here colors 30..71
	// in both, plus 90/91 only in the second), all within the slot budget.
	auto other = spriteBytes({{kGuestFront, kGuestStand, 0, -6, -20, 12, 20, 30}, {kGuestLeft, kGuestStand, 0, -6, -20, 12, 20, 90}});
	SourceSprite second; assert(parseSprite(other.data(), other.size(), second, error));
	std::vector<SandboxSprite> both;
	assert(fitSprites({src, second}, 1.0, 192, 64, both, error) && both.size() == 2);
	assert(both[0].slotCount == 8 && both[1].slotCount == 8 && both[0].palette == both[1].palette);
	assert(both[0].frames[0].pixels[20] == both[1].frames[0].pixels[12]); // Same RGB (color 30), same slot.
	assert(fitSprites({src, second}, 1.0, 250, 4, both, error) && both[0].slotCount == 4);
	for (const auto &sprite : both) for (const auto &f : sprite.frames) for (uint8_t p : f.pixels) assert(p == 0 || (p >= 250 && p < 254));
	assert(!fitSprites({}, 1.0, 192, 64, both, error));
	// One scale per character (a player's chosen character from another game
	// beside a scene's own): each frame scales on its own, colors still shared.
	assert(fitSprites({src, second}, std::vector<double>{1.0, 2.0}, 192, 64, both, error));
	assert(both[0].frames[0].height == 40 && both[1].frames[0].height == 40 && both[1].frames[0].dy == -40);
	assert(both[0].palette == both[1].palette);
	assert(!fitSprites({src, second}, std::vector<double>{1.0}, 192, 64, both, error));
	assert(!fitSprites({src, second}, std::vector<double>{1.0, 0.0}, 192, 64, both, error));
	// The bridge keeps characters without any scene (Maniac and Zak rooms);
	// guests need a scene to scale with.
	{
		const unsigned char *data[2] = {bytes.data(), other.data()};
		const size_t sizes[2] = {bytes.size(), other.size()};
		const double scales[2] = {1.5, 1.0};
		char problem[64];
		assert(!Scummverse::WorldBridge::mountGuests(data, sizes, 2, 192, 64, problem, sizeof(problem)));
		assert(!Scummverse::WorldBridge::mountCharacters(data, sizes, scales, 0, 192, 64, problem, sizeof(problem)));
		assert(Scummverse::WorldBridge::mountCharacters(data, sizes, scales, 2, 192, 64, problem, sizeof(problem)));
		int dx, dy, w, h;
		assert(Scummverse::WorldBridge::guestCount() == 2 && Scummverse::WorldBridge::guestFrame(0, kGuestFront, kGuestStand, 0, dx, dy, w, h) && h == 60);
		assert(Scummverse::WorldBridge::guestFrame(1, kGuestFront, kGuestStand, 0, dx, dy, w, h) && h == 20);
		Scummverse::WorldBridge::unmountGuests();
		assert(Scummverse::WorldBridge::guestCount() == 0);
		// Portrait: the front standing frame (20x40) fills the height of a 64
		// square less the margins, stands on the bottom, keeps its colors.
		std::vector<unsigned char> face(64 * 64 * 4, 7);
		assert(Scummverse::WorldBridge::spritePortrait(bytes.data(), bytes.size(), 64, face.data()));
		int top = 64, bottom = -1, left = 64, right = -1;
		for (int y = 0; y < 64; ++y) for (int x = 0; x < 64; ++x) if (face[(y * 64 + x) * 4 + 3]) {
			top = std::min(top, y); bottom = std::max(bottom, y); left = std::min(left, x); right = std::max(right, x);
		}
		assert(bottom == 61 && bottom - top + 1 >= 58 && right - left + 1 >= 28 && right - left + 1 <= 31);
		assert(face[0] == 0 && face[3] == 0); // Cleared outside the character.
		assert(!Scummverse::WorldBridge::spritePortrait(bytes.data(), 10, 64, face.data()));
	}
	std::printf("PASS: character frames (parse, scale anchored at the feet, colors, fallbacks, shared palette, own scales, without a scene)\n");
}

// Places: keys round-trip and landmarks are found by game and room. The
// cast: every character is in a valid game, at most five per room, slots
// packed from 0, found by worldGuestAt. The frozen legacy order names real
// places.
static void testCatalog() {
	using namespace Scummverse::WorldCatalog;
	int scenes = 0, game = 0, room = 0;
	for (int g = 0; g < worldGameCount(); ++g)
		for (int i = 0; i < kWorldGames[g].sceneCount; ++i, ++scenes) {
			const WorldScene &scene = kWorldGames[g].scenes[i];
			assert(worldPlaceOfKey(worldPlaceKey(g, scene.room), game, room) && game == g && room == scene.room);
			assert(worldLandmark(g, scene.room) == &scene && scene.room < 1000);
		}
	int guests = 0;
	for (const auto &cast : kWorldCast) {
		assert(cast.game >= 0 && cast.game < worldGameCount() && cast.room > 0 && cast.room < 1000);
		assert(cast.slot >= 0 && cast.slot < kWorldMaxGuests && cast.guest.costume > 0 && cast.guest.name[0]);
		for (const char *line : cast.guest.lines) assert(line && line[0]);
		const int key = worldPlaceKey(cast.game, cast.room);
		assert(worldGuestAt(key, cast.slot) == &cast.guest);
		for (int k = 0; k < cast.slot; ++k) assert(worldGuestAt(key, k)); // packed
		++guests;
	}
	assert(!worldPlaceOfKey(53, game, room) && !worldGuestAt(42, 0) && !worldLandmark(worldGameCount(), 1));
	for (const auto &g : kWorldGames) assert(g.heroHeight >= 30 && g.heroHeight <= 480);
	for (const auto &legacy : kWorldLegacyPlaces) assert(worldLandmark(legacy.game, legacy.room));
	// Costume variants (one costume, another animation set) stand for a cast
	// member and name a different real costume, or their own with other
	// animations (the Dig's nest monster crawls); Murray bounces.
	for (const auto &v : kWorldCostumeVariants) {
		assert((v.real != v.costume || v.init >= 0 || v.paletteRoom > 0) && v.costume < 1024 && worldCostumeVariant(v.game, v.costume) == &v);
		bool cast = false;
		for (const auto &c : kWorldCast) cast = cast || (c.game == v.game && c.guest.costume == v.costume);
		assert(cast);
	}
	assert(!worldCostumeVariant(0, 9) && worldCostumeVariant(0, 906)->real == 9 && worldCostumeVariant(8, 128)->walk == 15);
	// Walks the game never drew both ways: each entry is a cast member,
	// found by its own key; a graft's relative is another costume, with
	// clothes to repaint; legs swing from somewhere inside the picture.
	auto member = [](int game, int costume) {
		for (const auto &c : kWorldCast) if (c.game == game && c.guest.costume == costume) return true;
		return false;
	};
	for (const auto &w : kWorldSideWalks) assert(member(w.game, w.costume) && worldSideWalk(w.game, w.costume) == &w && w.facing % 90 == 0);
	for (const auto &g : kWorldCostumeGrafts) {
		assert(member(g.game, g.costume) && worldCostumeGraft(g.game, g.costume) == &g && g.body != g.costume && g.head != g.mouth);
		assert(g.head >= 0 && g.head < 16 && g.mouth >= 0 && g.mouth < 16 && g.neck >= 0 && g.recolor[0][0] && g.recolor[0][1]);
	}
	for (const auto &s : kWorldLegSwings) assert(member(s.game, s.costume) && worldLegSwing(s.game, s.costume) == &s && s.hip > 0 && s.hip < 100 && s.reach > 0);
	assert(worldCostumeGraft(6, 102) && worldSideWalk(6, 201) && worldLegSwing(4, 93) && !worldCostumeGraft(6, 201) && !worldLegSwing(4, 94));
	// Seat fits are cast members, crammed in, partly sunk, no wider than past
	// the armrest. Seated poses are theirs: parts cut from inside the stance,
	// set from the origin or on a part that is; a seated frame is GuestKind's.
	static_assert(kWorldSeatedKind == kGuestSeated, "seated frames");
	for (const auto &f : kWorldSeatFits)
		assert(member(f.game, f.costume) && worldSeatFit(f.game, f.costume) == &f && f.sink > 0 && f.sink < 100 && f.squash >= 100 && f.top > 0 && f.width > 0 && f.width <= 64);
	for (const auto &p : kWorldSeatPoses) {
		assert(worldSeatPose(p.game, p.costume) == &p && worldSeatFit(p.game, p.costume));
		int parts = 0;
		for (const auto &q : p.parts) {
			if (q.x1 <= q.x0) continue;
			// Set on an earlier part or one set from the origin, never on itself.
			assert(q.x0 >= 0 && q.y0 >= 0 && q.y1 > q.y0 && q.scale > 0 && q.on < 6 && q.on != parts && (q.front == 0 || q.front == 1));
			assert(q.on < 0 || q.on < parts || p.parts[q.on].on < 0);
			++parts;
		}
		// Parts, or the whole stance with its gaps filled.
		assert((parts >= 2 || (!parts && p.fill >= 0)) && p.fill >= -1 && p.fill < 256);
	}
	assert(worldSeatFit(4, 93) && worldSeatPose(8, 128) && worldSeatPose(0, 34)->fill == 0 && !worldSeatFit(0, 1) && !worldSeatPose(8, 321));
	// Side views made from a relative: cast members, another costume, heads
	// drawn anew in a known palette (every letter in the legend), something
	// repainted.
	for (const auto &v : kWorldSideViews) {
		assert(member(v.game, v.costume) && worldSideView(v.game, v.costume) == &v && v.body != v.costume && v.heads >= 1 && v.size > 0 && (v.recolor[0][0] || v.recolor[0][1]));
		assert(v.head && v.headRows > 0 && v.legend && strlen(v.legend) <= 8 && v.stepX >= 0 && v.stepY >= 0);
		for (int y = 0; y < v.headRows; ++y) {
			assert(strlen(v.head[y]) == strlen(v.head[0]));
			for (const char *c = v.head[y]; *c; ++c) assert(*c == '.' || strchr(v.legend, *c));
		}
	}
	assert(worldSideView(0, 34) && worldSideView(0, 34)->heads == 3 && !worldSideView(0, 6));
	assert(worldBouncer(9, 49) && worldBouncer(9, 949) && worldBouncer(9, 49)->jaw > 0 && !worldHovers(9, 49) && !worldBouncer(0, 49));
	// Maniac's own looks: a pseudo game beyond the real ones, found by key,
	// hovering and airless (the Purple Meteor), domed, rolling; real keys
	// never reach it.
	{
		const int meteor = worldAppearanceKey(kWorldManiacLooks, 16);
		assert(worldNativeLook(meteor) && worldAppearance(meteor) && !strcmp(worldAppearance(meteor)->name, "Purple Meteor"));
		assert(worldHovers(kWorldManiacLooks, 16) && !worldBreathes(kWorldManiacLooks, 16));
		assert(!worldAppearance(worldAppearanceKey(kWorldManiacLooks, 17)) && kWorldManiacLooks > worldGameCount());
		for (const auto &c : kWorldCast) assert(!worldNativeLook(worldAppearanceKey(c.game, c.guest.costume)));
		for (const auto &look : kWorldManiacCast) assert(look.costume > 0 && look.costume < 44 && look.talkColor < 16 && look.lines[2]);
		assert(!worldNativeLook(0) && worldAppearance(worldAppearanceKey(8, 321)) && !strcmp(worldAppearance(worldAppearanceKey(8, 321))->name, "The Creator"));
		// The Meteor Police officer wears a dome, his helmet (no air needed on
		// Mars); the plant breathes (a fishbowl on Mars) and rolls on its pot,
		// always the grown plant (its costume's direction away from the viewer).
		assert(worldAppearance(worldAppearanceKey(kWorldManiacLooks, 15)) && !strcmp(worldAppearance(worldAppearanceKey(kWorldManiacLooks, 15))->name, "Meteor Police"));
		assert(!worldBreathes(kWorldManiacLooks, 15) && worldDomed(kWorldManiacLooks, 15) && !worldRoller(kWorldManiacLooks, 15) && !worldHovers(kWorldManiacLooks, 15));
		assert(worldAppearance(worldAppearanceKey(kWorldManiacLooks, 19)) && !strcmp(worldAppearance(worldAppearanceKey(kWorldManiacLooks, 19))->name, "Man-Eating Plant"));
		assert(worldBreathes(kWorldManiacLooks, 19) && !worldDomed(kWorldManiacLooks, 19));
		assert(worldRoller(kWorldManiacLooks, 19)->facing == 0 && worldRoller(kWorldManiacLooks, 19)->gear == kWorldPot);
		assert(!worldDomed(kWorldManiacLooks, 16) && !worldRoller(kWorldManiacLooks, 16) && !worldRoller(9, 19));
		// Dead Cousin Ted rolls on skates, in his own direction; Day of the
		// Tentacle's Ted glides dressed up for the contest, mirrored facing
		// left. Both wear a fishbowl on Mars. Chaos floats, needing no air.
		assert(worldAppearance(worldAppearanceKey(kWorldManiacLooks, 12)) && !strcmp(worldAppearance(worldAppearanceKey(kWorldManiacLooks, 12))->name, "Dead Cousin Ted"));
		assert(worldRoller(kWorldManiacLooks, 12)->facing == -1 && worldRoller(kWorldManiacLooks, 12)->gear == kWorldSkates && worldBreathes(kWorldManiacLooks, 12));
		assert(worldGlider(5, 235) && worldGlider(5, 235)->dressUp && worldGlider(5, 235)->oneWay && worldBreathes(5, 235) && !worldHovers(5, 235) && !worldRoller(5, 235));
		assert(worldHovers(2, 130) && !worldBreathes(2, 130) && !worldGlider(2, 130) && !worldGlider(kWorldManiacLooks, 12));
	}
	// Only Curse of Monkey Island (square pixels) is widened.
	for (int g = 0; g < worldGameCount(); ++g) assert(worldWiden(g) == (sameId(kWorldGames[g].gameid, "comi") ? 1.2 : 1.0));
	// Exploration presets: their rooms are visitable; tints apply to rooms
	// whose scripts run; switched objects and variables are the game's own.
	for (const auto &p : kWorldPresetScripts) assert(worldRoomKind(p.game, p.room) >= 0 && p.script >= 2000 && worldPresetRoom(p.game, p.room));
	for (const auto &t : kWorldPresetTints) assert(worldPresetRoom(t.game, t.room) && t.start <= t.end && t.end <= 255);
	for (const auto &c : kWorldPresetClassesOff) assert(c.game < worldGameCount() && c.cls >= 1 && c.cls <= 32);
	for (const auto &v : kWorldPresetVars) assert(v.game < worldGameCount() && v.var > 0);
	assert(worldPresetRoom(8, 77) && worldPresetRoom(8, 91) && !worldPresetRoom(8, 2) && !worldPresetRoom(0, 31));
	// Who needs no air on Mars: cast members (or Maniac's own looks) only;
	// Murray and the monkeys do.
	for (const auto &x : kWorldAirless) {
		bool cast = worldAppearance(worldAppearanceKey(x.game, x.costume)) != nullptr;
		for (const auto &c : kWorldCast) cast = cast || (c.game == x.game && c.guest.costume == x.costume);
		assert(cast && !worldBreathes(x.game, x.costume));
	}
	assert(worldBreathes(9, 49) && !worldBreathes(5, 6) && worldBreathes(0, 906));
	// The Dig's tram: every station is a visitable room whose car is a door to
	// the other end of its line; each station belongs to one line.
	for (const auto &line : kWorldTramLines) for (int e = 0; e < 2; ++e) {
		const WorldTramStop &stop = line.ends[e];
		assert(worldRoomKind(line.game, stop.room) >= 0 && stop.picture[0] && stop.tunnel >= -1 && stop.tunnel <= 1);
		const WorldLink *car = worldLinkFrom(line.game, stop.room, stop.car);
		assert(car && car->target == line.ends[1 - e].room);
		int l = -1, at = -1;
		assert(worldTramStop(line.game, stop.room, l, at) && &kWorldTramLines[l] == &line && at == e);
	}
	{ int l, at; assert(!worldTramStop(8, 2, l, at) && !worldTramStop(0, 80, l, at)); }
	// The van's landing sites: Mars first; other-world sites are visitable
	// rooms; labels in the destination computer's capitals and spaces.
	assert(kWorldVanSites[0].game == -1 && kWorldVanSites[0].room == 79);
	for (const auto &site : kWorldVanSites) {
		assert(site.game >= -1 && site.game < worldGameCount() && site.room > 0);
		if (site.game >= 0) assert(worldRoomKind(site.game, site.room) == kWorldScene);
		for (const char *c = site.label; *c; ++c) assert((*c >= 'A' && *c <= 'Z') || *c == ' ');
	}
	assert(kWorldVanRequest > worldPlaceRequest(worldGameCount() - 1, 1023) && kWorldVanRequest + kWorldVanSiteCount < kWorldAppearanceRequest);
	std::printf("PASS: %d named places, %d characters; place keys, cast slots, legacy places, costume variants, floating, presets, air, Dig tram, van sites\n", scenes, guests);
}

// Door maps: doors join visitable rooms; every visitable room is reached
// from a named place or a story area through doors (or by walking between
// neighboring named places); story areas are named, visitable rooms; menu
// place requests stay above every scene-bound request.
static void testMaps() {
	using namespace Scummverse::WorldCatalog;
	int rooms = 0, doors = 0, areas = 0;
	for (int g = 0; g < worldGameCount(); ++g) {
		const WorldMap *map = worldMap(g);
		if (!map) continue;
		std::vector<int> reached, todo;
		auto reach = [&](int room) { if (std::find(reached.begin(), reached.end(), room) == reached.end()) { reached.push_back(room); todo.push_back(room); } };
		for (int i = 0; i < kWorldGames[g].sceneCount; ++i) reach(kWorldGames[g].scenes[i].room);
		for (int i = 0; i < map->areaCount; ++i) {
			assert(map->areas[i].name && map->areas[i].name[0] && worldRoomKind(g, map->areas[i].room) >= 0);
			assert(worldPlaceRequest(g, map->areas[i].room) > (((255 * 32 + 31) << 8) | 255));
			reach(map->areas[i].room); ++areas;
		}
		for (int i = 0; i < map->linkCount; ++i) {
			const WorldLink &link = map->links[i];
			assert(worldRoomKind(g, link.room) >= 0 && worldRoomKind(g, link.target) >= 0 && link.room != link.target);
			assert(worldLinkFrom(g, link.room, link.object) == &link);
		}
		while (!todo.empty()) {
			const int room = todo.back(); todo.pop_back();
			for (int i = 0; i < map->linkCount; ++i) if (map->links[i].room == room) reach(map->links[i].target);
			for (int i = 0; i < kWorldGames[g].sceneCount; ++i) {
				if (kWorldGames[g].scenes[i].room != room) continue;
				if (i > 0) reach(kWorldGames[g].scenes[i - 1].room);
				if (i + 1 < kWorldGames[g].sceneCount) reach(kWorldGames[g].scenes[i + 1].room);
			}
		}
		for (int i = 0; i < map->roomCount; ++i) {
			if (std::find(reached.begin(), reached.end(), map->rooms[i].room) == reached.end()) {
				std::printf("FAIL: %s room %d cannot be reached\n", kWorldGames[g].gameid, map->rooms[i].room);
				assert(false);
			}
			++rooms;
		}
		doors += map->linkCount;
	}
	std::printf("PASS: door maps (%d rooms, %d doors, %d story areas; every room reachable)\n", rooms, doors, areas);
	// Castle Brunwald (Last Crusade, game 3) on foot: its three floors are
	// floor plans; every hall, room, corridor and tower room is reached from
	// the entrance hall (22) through doors and leads back to it. Only the
	// guards' corridor (132, a story encounter) is entered by menu.
	const int indy3 = 3;
	assert(std::string(kWorldGames[indy3].gameid) == "indy3");
	for (int floor : {20, 28, 32}) assert(worldRoomKind(indy3, floor) == kWorldFloorPlan);
	const WorldMap *castle = worldMap(indy3);
	auto walk = [&](int from, bool forward) {
		std::vector<int> seen{from}, todo{from};
		while (!todo.empty()) {
			const int room = todo.back(); todo.pop_back();
			for (int i = 0; i < castle->linkCount; ++i) {
				const WorldLink &l = castle->links[i];
				const int a = forward ? l.room : l.target, b = forward ? l.target : l.room;
				if (a == room && std::find(seen.begin(), seen.end(), b) == seen.end()) { seen.push_back(b); todo.push_back(b); }
			}
		}
		return seen;
	};
	const std::vector<int> out = walk(22, true), back = walk(22, false);
	int castleRooms = 0;
	for (int i = 0; i < castle->roomCount; ++i) {
		const int room = castle->rooms[i].room;
		if (!((room >= 20 && room <= 34) || (room >= 129 && room <= 166)) || room == 132) continue;
		if (std::find(out.begin(), out.end(), room) == out.end() || std::find(back.begin(), back.end(), room) == back.end()) {
			std::printf("FAIL: Castle Brunwald room %d is not walkable both ways\n", room);
			assert(false);
		}
		++castleRooms;
	}
	assert(castleRooms >= 48);
	std::printf("PASS: Castle Brunwald on foot (%d rooms both ways from the entrance hall; floors are floor plans)\n", castleRooms);
}

int main() {
	testCatalog();
	testMaps();
	testSprites();
	// A 96x48 two-color scene; three walkable boxes in a row plus a disabled one.
	const int W = 96, H = 48;
	std::vector<uint8_t> pixels(W * H);
	for (int y = 0; y < H; ++y) for (int x = 0; x < W; ++x) pixels[y * W + x] = x < 48 ? 10 : 200;
	std::vector<SourceBox> boxes = {box(0, 30, 40, 46), box(40, 30, 80, 46), box(80, 36, 95, 46), box(10, 0, 20, 10, 0x80), box(60, 0, 70, 6)};
	auto bytes = sceneBytes(W, H, pixels, boxes);
	SourceScene src; std::string error;
	assert(parseScene(bytes.data(), bytes.size(), src, error) && src.width == W && src.height == H && src.boxes.size() == 5);
	assert(src.boxes[1].x[1] == 80 && src.boxes[3].flags == 0x80 && src.palette[3 * 200] == 200);
	// Malformed input never parses.
	assert(!parseScene(bytes.data(), bytes.size() - 1, src, error));
	auto bad = bytes; bad[0] = 'X'; assert(!parseScene(bad.data(), bad.size(), src, error));
	bad = bytes; bad[6] = 0; bad[7] = 0; assert(!parseScene(bad.data(), bad.size(), src, error));
	assert(!parseScene(nullptr, 0, src, error));
	assert(parseScene(bytes.data(), bytes.size(), src, error));

	SandboxScene fit;
	assert(fitScene(src, 32, 16, 240, fit, error));
	assert(fit.height == 32 && fit.width == 64 && fit.width % 8 == 0); // 96*32/48 = 64.
	assert(fit.slotCount == 2 && fit.palette.size() == 6);
	for (uint8_t p : fit.pixels) assert(p >= 16 && p < 18);
	// Colors keep exact RGB in their slots; the left half stays color 10.
	const int left = fit.pixels[5 * 64 + 3] - 16;
	assert(fit.palette[left * 3] == 10 && fit.palette[left * 3 + 1] == 245);
	assert(fit.boxes.size() == 4); // The disabled box is dropped.
	for (const auto &b : fit.boxes) assert(b.ulx <= b.urx && b.llx <= b.lrx && b.uy <= b.ly && b.ly <= 16);
	// Routing: 0-1-2 chain; the isolated box (index 3) is unreachable.
	auto hop = [&](int a, int b) { return fit.next[a * fit.boxes.size() + b]; };
	assert(hop(0, 2) == 1 && hop(2, 0) == 1 && hop(1, 2) == 2 && hop(0, 0) == 0 && hop(0, 3) == -1 && hop(3, 0) == -1);
	assert(fit.spawnX >= 0 && fit.spawnY > 0);
	assert(fit.leftX == 0 && fit.rightX >= fit.width / 8 - 2);

	// V1 room: header, boxes, routing and tile streams decode to exact sizes.
	auto room = buildV1Room(fit);
	assert(room[4] == fit.width / 8 && room[5] == fit.height / 8 && room[20] == 0 && room[21] == 28);
	assert(room[0] + (room[1] << 8) == (int)room.size());
	const int n = room[28]; assert(n == 4);
	assert(room[29] == fit.boxes[0].uy && room[30] == fit.boxes[0].ly && room[31] == fit.boxes[0].ulx);
	const uint8_t *matrix = room.data() + 29 + n * 8;
	for (int i = 0; i < n; ++i) assert(matrix[i] == i * n);
	assert((int8_t)matrix[n + 0 * n + 2] == 1);
	uint8_t buffer[4096];
	const int cols = fit.width / 8, rows = fit.height / 8, sizes[4] = {2048, cols * rows, cols * rows, cols * rows};
	for (int s = 0; s < 4; ++s) {
		const int off = room[10 + s * 2] | (room[11 + s * 2] << 8);
		memset(buffer, 0xAA, sizeof(buffer));
		decodeV1(room.data() + off, buffer, sizes[s]);
		for (int i = 0; i < sizes[s]; ++i) assert(buffer[i] == 0);
	}
	const int maskOff = room[18] | (room[19] << 8);
	assert(room[maskOff] == 8 && room[maskOff + 1] == 0);
	std::printf("PASS: parse, fit (slots, exact colors, boxes, routing), V1 room layout\n");

	// Many colors: only the most common fit the slots; the rest snap to them.
	std::vector<uint8_t> rich(256 * 8);
	for (int i = 0; i < (int)rich.size(); ++i) rich[i] = (uint8_t)(i % 256);
	auto richBytes = sceneBytes(256, 8, rich, {});
	assert(parseScene(richBytes.data(), richBytes.size(), src, error));
	assert(fitScene(src, 8, 16, 240, fit, error) && fit.slotCount == 240 && fit.boxes.empty());
	for (uint8_t p : fit.pixels) assert(p >= 16);
	// Bad targets are refused.
	assert(!fitScene(src, 12, 16, 240, fit, error) && !fitScene(src, 8, 100, 200, fit, error));
	// A scene too wide for one-byte V1 columns is refused rather than wrapped.
	std::vector<uint8_t> wide(4000 * 8, 1);
	auto wideBytes = sceneBytes(4000, 8, wide, {});
	assert(parseScene(wideBytes.data(), wideBytes.size(), src, error) && !fitScene(src, 8, 16, 240, fit, error));
	// Narrow scenes are padded to the screen width, centered, boxes shifted.
	assert(parseScene(bytes.data(), bytes.size(), src, error));
	SandboxScene narrow; assert(fitScene(src, 32, 16, 240, narrow, error, 320));
	assert(narrow.width == 320 && narrow.padLeft == 128 && narrow.padLeft % 8 == 0);
	assert(narrow.boxes[0].ulx == 16 && narrow.pixels[0] == narrow.pixels[319]); // Pad color both sides.
	assert(narrow.leftX == 16 && narrow.rightX >= (128 + 64) / 8 - 2 && narrow.rightX <= 24);
	assert(narrow.contentWidth == 64 && narrow.scaleX == narrow.scale);
	// Square-pixel art (Curse of Monkey Island) widened 1.2 beside art shown
	// 1.2 times taller: wider picture, boxes and objects; rows unchanged.
	{
		std::vector<uint8_t> px(640 * 480);
		for (int y = 0; y < 480; ++y) for (int x = 0; x < 640; ++x) px[(size_t)y * 640 + x] = (uint8_t)(x < 320 ? 1 : 2);
		auto square = sceneBytes(640, 480, px, {box(320, 400, 639, 479)});
		assert(parseScene(square.data(), square.size(), src, error));
		SandboxScene plain, wide;
		assert(fitScene(src, 128, 16, 240, plain, error, 320));
		src.widen = 1.2;
		assert(fitScene(src, 128, 16, 240, wide, error, 320));
		assert(plain.contentWidth == 171 && wide.contentWidth == 205 && wide.scale == plain.scale && wide.height == 128);
		assert(std::abs(wide.scaleX - plain.scale * 1.2) < 1e-9 && wide.padLeft == 56);
		// The color boundary at source column 320 lands 1.2 times further in.
		const int seam = wide.padLeft + 102;
		assert(wide.pixels[(size_t)64 * 320 + seam - 3] != wide.pixels[(size_t)64 * 320 + seam + 3]);
		assert(plain.pixels[(size_t)64 * 320 + plain.padLeft + 85 + 3] == wide.pixels[(size_t)64 * 320 + seam + 3]);
		// Plain: content 171 at pad 72, box columns 20..30; widened: 205 at 56, 20..33.
		assert(plain.padLeft == 72 && plain.boxes[0].ulx == 20 && plain.boxes[0].lrx == 30);
		assert(wide.boxes[0].ulx == 20 && wide.boxes[0].lrx == 33 && wide.boxes[0].uy == plain.boxes[0].uy && wide.boxes[0].ly == plain.boxes[0].ly);
	}
	std::printf("PASS: color budget, invalid targets, width limit, narrow padding, widened square pixels\n");

	// SVW2: the room's objects follow the boxes; rectangles scale and shift
	// with the scene, walk-to points become V1 units.
	auto v2 = sceneBytes(W, H, pixels, boxes);
	v2[3] = '2';
	put16(v2, 2);
	for (int f : {101, 12, 6, 24, 18, 30, 44}) put16(v2, f);
	for (int f : {102, 0, 0, 8, 8, 2, 40}) put16(v2, f);
	assert(parseScene(v2.data(), v2.size(), src, error) && src.objects.size() == 2 && src.objects[0].id == 101 && src.objects[0].walkY == 44);
	assert(!parseScene(v2.data(), v2.size() - 1, src, error));
	auto noCount = sceneBytes(W, H, pixels, boxes); noCount[3] = '2';
	assert(!parseScene(noCount.data(), noCount.size(), src, error));
	auto v1Extra = bytes; v1Extra.push_back(0); assert(!parseScene(v1Extra.data(), v1Extra.size(), src, error));
	assert(parseScene(v2.data(), v2.size(), src, error));
	SandboxScene withObjects; assert(fitScene(src, 32, 16, 240, withObjects, error, 320));
	const SandboxObject &door = withObjects.objects[0];
	assert(withObjects.objects.size() == 2 && door.id == 101);
	assert(door.x == 8 + 128 && door.y == 4 && door.width == 16 && door.height == 12); // x 12*2/3 + pad 128
	assert(door.walkX == (int)std::lround((30 * 2.0 / 3 + 128) / 8) && door.walkY == (int)std::lround(44 * 2.0 / 3 / 2));
	std::printf("PASS: SVW2 room objects (parse, truncation, sandbox rectangles and walk points)\n");

	// SVW3: per box, the character scale at its top and bottom edges follows
	// the objects; the sandbox keeps those of the boxes it keeps and
	// interpolates by row. Older files are full size everywhere.
	auto v3 = v2; v3[3] = '3';
	for (int b = 0; b < 5; ++b) { v3.push_back((uint8_t)(100 + b)); v3.push_back((uint8_t)(200 + b)); }
	assert(!parseScene(v3.data(), v3.size() - 1, src, error));
	assert(parseScene(v3.data(), v3.size(), src, error) && src.boxes[1].scaleTop == 101 && src.boxes[4].scaleBottom == 204);
	SandboxScene scaled; assert(fitScene(src, 32, 16, 240, scaled, error, 320));
	assert(scaled.boxes.size() == 4 && scaled.scaleTop[3] == 104 && scaled.scaleBottom[2] == 202); // disabled box 3 dropped
	const V2Box &near = scaled.boxes[0];
	assert(scaled.boxScale(0, near.uy) == 100 && scaled.boxScale(0, near.ly) == 200);
	const int mid = scaled.boxScale(0, (near.uy + near.ly) / 2);
	assert(mid > 100 && mid < 200);
	assert(scaled.boxScale(-1, 0) == 255 && scaled.boxScale(9, 0) == 255 && withObjects.boxScale(0, near.uy) == 255);
	std::printf("PASS: SVW3 box scales (parse, truncation, kept boxes, interpolation, older files)\n");

	// SVW4: each object record ends with its state; older files say shown.
	auto v4 = sceneBytes(W, H, pixels, boxes);
	v4[3] = '4';
	put16(v4, 2);
	for (int f : {101, 12, 6, 24, 18, 30, 44, 0}) put16(v4, f);
	for (int f : {102, 0, 0, 8, 8, 2, 40, 1}) put16(v4, f);
	for (int b = 0; b < 5; ++b) { v4.push_back(255); v4.push_back(255); }
	assert(!parseScene(v4.data(), v4.size() - 1, src, error));
	assert(parseScene(v4.data(), v4.size(), src, error) && src.objects.size() == 2 && src.objects[0].state == 0 && src.objects[1].state == 1);
	SandboxScene states; assert(fitScene(src, 32, 16, 240, states, error, 320));
	assert(states.objects[0].state == 0 && states.objects[1].state == 1 && withObjects.objects[0].state == 1);
	std::printf("PASS: SVW4 object states (parse, truncation, sandbox, older files shown)\n");
	// A picture of the scene in another state (a parked car): a 12x8 block of
	// color 120 at (60,20). Fitted at 2/3 scale into the scene's own colors
	// (120 is not one of them: it snaps to the nearest), only where it differs.
	{
		std::vector<uint8_t> car = pixels;
		for (int y = 20; y < 28; ++y) for (int x = 60; x < 72; ++x) car[y * W + x] = 120;
		SourceScene base, shown;
		auto carBytes = sceneBytes(W, H, car, boxes);
		assert(parseScene(bytes.data(), bytes.size(), base, error) && parseScene(carBytes.data(), carBytes.size(), shown, error));
		SandboxScene fitted; assert(fitScene(base, 32, 16, 240, fitted, error, 320));
		ScenePicture picture;
		assert(fitPicture(base, shown, fitted, picture, error));
		const int px = fitted.padLeft + 40, py = 13; // 60*2/3, 20*2/3
		assert(picture.x >= px - 1 && picture.x <= px && picture.y >= py - 1 && picture.y <= py);
		assert(picture.width >= 8 && picture.width <= 10 && picture.height >= 5 && picture.height <= 7);
		int shownPixels = 0;
		for (size_t i = 0; i < picture.mask.size(); ++i) if (picture.mask[i]) {
			++shownPixels; assert(picture.pixels[i] >= fitted.firstSlot && picture.pixels[i] < fitted.firstSlot + fitted.slotCount);
		}
		assert(shownPixels >= 40);
		// Fitted in the picture's colors, the car keeps its own color 120.
		SandboxScene joint; assert(fitScene(base, 32, 16, 240, joint, error, 320, &shown) && joint.slotCount == 3);
		assert(fitPicture(base, shown, joint, picture, error));
		for (size_t i = 0; i < picture.mask.size(); ++i) if (picture.mask[i]) {
			const uint8_t *rgb = &joint.palette[(size_t)(picture.pixels[i] - joint.firstSlot) * 3];
			assert(rgb[0] == 120 && rgb[1] == 135 && rgb[2] == 60);
		}
		assert(!fitPicture(base, base, fitted, picture, error));
		SourceScene other = base; other.width = 10; other.pixels.resize(10 * H);
		assert(!fitPicture(base, other, fitted, picture, error));
	}
	std::printf("PASS: scene pictures (only what differs, scene scale and colors, joint colors, refused when equal or another size)\n");
}
