// SPDX-License-Identifier: GPL-3.0-or-later
// Contract tests for the CAMERA's portable part (requests, whole-pixel
// enlarging, selfie framing, poses, names, delivery). Build with
//   c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//       tools/test_camera.cpp engine/common/scummverse_camera.cpp -o build/test_camera
#include "common/scummverse_camera.h"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>

using namespace Scummverse::Camera;

static Rect rect(int x, int y, int w, int h) { Rect r; r.x = x; r.y = y; r.w = w; r.h = h; return r; }
static bool inside(const Rect &a, const Rect &b) { return a.x >= b.x && a.y >= b.y && a.right() <= b.right() && a.bottom() <= b.bottom(); }

static void requests() {
	Request r;
	assert(!takeRequest(r));
	requestPhoto(false);
	assert(takeRequest(r) && r.kind == kClean && r.shots == 1 && !takeRequest(r));
	requestPhoto(true);
	assert(takeRequest(r) && r.kind == kFull && r.shots == 1);
	const int asked[] = {0, 1, 2, 3, 4, 5, 9}, got[] = {1, 1, 3, 3, 5, 5, 5};
	for (int i = 0; i < 7; ++i) {
		requestSelfie(asked[i]);
		assert(takeRequest(r) && r.kind == kSelfie && r.shots == got[i]);
	}
	// The latest request stands.
	requestPhoto(false); requestSelfie(3);
	assert(takeRequest(r) && r.kind == kSelfie && r.shots == 3 && !takeRequest(r));
	assert(!held() && !busy());
	setHold(true); setBusy(true);
	assert(held() && busy());
	setHold(false); setBusy(false);
	assert(!held() && !busy());
	std::string text;
	assert(!takeNote(text));
	note("first"); note("No selfie here");
	assert(takeNote(text) && text == "No selfie here" && !takeNote(text));
	puts("PASS: requests (photo kinds, selfie counts 1/3/5, one at a time), hold, busy, notes");
}

static void pictures() {
	int kx, ky;
	factors(320, 200, kx, ky); assert(kx == 5 && ky == 6);   // 1600 x 1200
	factors(320, 128, kx, ky); assert(kx == 5 && ky == 6);   // 1600 x 768
	factors(100, 90, kx, ky); assert(kx == 15 && ky == 18);  // 1500 x 1620
	factors(1, 1, kx, ky); assert(kx <= kMaxSide && ky <= kMaxSide && ky * 5 == kx * 6 && ky >= kTarget);
	factors(2000, 10, kx, ky); assert(kx == 5 && ky == 6);   // never shrinks below 5 x 6
	// A 3 x 2 picture: colors 1..6 at (0,0)..(2,1).
	const uint8_t pixels[] = {1, 2, 3, 99, 4, 5, 6, 99};
	uint8_t palette[768] = {};
	for (int c = 0; c < 256; ++c) { palette[c * 3] = (uint8_t)c; palette[c * 3 + 1] = (uint8_t)(c * 2); palette[c * 3 + 2] = (uint8_t)(255 - c); }
	Picture p;
	assert(enlarge(pixels, 4, 3, 2, palette, rect(0, 0, 3, 2), 5, 6, p));
	assert(p.width == 15 && p.height == 12 && p.rgba.size() == 15u * 12 * 4);
	for (int y = 0; y < p.height; ++y) for (int x = 0; x < p.width; ++x) {
		const uint8_t c = pixels[(y / 6) * 4 + x / 5];
		const uint8_t *d = &p.rgba[((size_t)y * p.width + x) * 4];
		assert(d[0] == c && d[1] == (uint8_t)(c * 2) && d[2] == 255 - c && d[3] == 255);
	}
	// A crop; one partly outside is cut to the picture; one wholly outside fails.
	assert(enlarge(pixels, 4, 3, 2, palette, rect(1, 1, 2, 1), 2, 3, p) && p.width == 4 && p.height == 3);
	assert(p.rgba[0] == 5 && p.rgba[((p.height - 1) * p.width + p.width - 1) * 4] == 6);
	assert(enlarge(pixels, 4, 3, 2, palette, rect(2, -5, 9, 9), 1, 1, p) && p.width == 1 && p.height == 2 && p.rgba[0] == 3 && p.rgba[4] == 6);
	assert(!enlarge(pixels, 4, 3, 2, palette, rect(5, 5, 2, 2), 1, 1, p));
	assert(!enlarge(nullptr, 4, 3, 2, palette, rect(0, 0, 3, 2), 1, 1, p));
	puts("PASS: whole-pixel factors (6/5 rows, 1600 long side, capped), enlarging (colors, crops, misses)");
}

static double shown(const Rect &r) { return r.w / (r.h * 1.2); }

static void framing() {
	const Rect view = rect(0, 0, 320, 128);
	const Rect player = rect(140, 40, 20, 60);
	// Near (10 px away) is in, far (100 px) is out.
	const Rect near = rect(170, 50, 18, 50), far = rect(260, 40, 20, 60);
	Rect f = frameSelfie(player, {near, far}, view);
	assert(inside(player, f) && inside(near, f) && !inside(far, f) && inside(f, view));
	assert(f.y < player.y && shown(f) >= 0.79 && shown(f) <= 1.34);
	// Alone: a portrait-ish frame around the player, with head room.
	f = frameSelfie(player, {}, view);
	assert(inside(player, f) && f.y <= player.y - 10 && shown(f) >= 0.79 && shown(f) <= 1.34);
	// A crowd in a row: wider than 4:3 is made taller (as far as the view lets it).
	std::vector<Rect> row = {rect(90, 40, 20, 60), rect(114, 40, 20, 60), rect(166, 40, 20, 60), rect(190, 40, 20, 60)};
	f = frameSelfie(player, row, view);
	for (const Rect &r : row) assert(inside(r, f));
	assert(inside(f, view) && shown(f) <= 1.34 && f.h > 80);
	// At the view's edge the frame slides in rather than leaving the player.
	f = frameSelfie(rect(2, 60, 20, 60), {}, view);
	assert(inside(f, view) && f.x == 0 && f.right() >= 22);
	// Taller than the view: cut to it.
	f = frameSelfie(rect(100, 0, 40, 128), {}, view);
	assert(inside(f, view) && f.h == 128);
	puts("PASS: selfie framing (near ones in, far ones out, head room, 4:5 to 4:3 as shown, inside the view)");
}

// A frame's width over its height as shown (rows rowAspect times taller).
static double seen(const Rect &r, double rowAspect) { return r.w / (r.h * rowAspect); }

// A group too wide for the view's height at 4:3 (the mansion's 136 rows):
// narrower, never wider than 4:3 as shown.
static void lowViews() {
	const Rect low = rect(0, 0, 320, 136);
	const Rect player = rect(148, 40, 24, 60); // (within reach: 45 either side)
	const Rect nearL = rect(120, 42, 24, 58), nearR = rect(176, 42, 24, 58);
	const Rect farL = rect(44, 45, 64, 55), farR = rect(216, 45, 74, 55); // (40 and 44 away)
	std::vector<Rect> group = {farR, nearL, farL, nearR};
	Rect f = frameSelfie(player, group, low);
	// The whole height, 4:3 as shown at most (it was 264 by 127: 1.73); the
	// player and the nearest whole, then as many as fit (the far one on the
	// left, not the farther one on the right as well).
	assert(inside(f, low) && f.h == 136 && f.w == 217 && seen(f, 1.2) <= 4.0 / 3 && seen(f, 1.2) > 1.32);
	assert(inside(player, f) && inside(nearL, f) && inside(nearR, f) && inside(farL, f) && !inside(farR, f));
	// (The other way round: the one on the right nearer.)
	f = frameSelfie(player, {rect(40, 45, 64, 55), nearL, rect(212, 45, 74, 55), nearR}, low);
	assert(inside(f, low) && f.w == 217 && inside(rect(212, 45, 74, 55), f) && !inside(rect(40, 45, 64, 55), f) && inside(player, f));
	// A few all fitting at 4:3 but not with their margins: all of them.
	const Rect narrowR = rect(216, 45, 40, 55);
	f = frameSelfie(player, {rect(40, 45, 64, 55), nearL, nearR, narrowR}, low);
	assert(inside(f, low) && f.h == 136 && f.w == 217 && inside(rect(40, 45, 64, 55), f) && inside(narrowR, f) && inside(player, f));
	assert(40 - f.x <= 2 && f.right() - narrowR.right() <= 2); // (216 of 217: centred)
	// One nearer that cannot be kept whole does not keep out a farther one
	// that can.
	const Rect lower = rect(0, 0, 320, 100), kid = rect(148, 30, 24, 50), wideNear = rect(10, 32, 130, 48), farther = rect(200, 32, 100, 48);
	f = frameSelfie(kid, {wideNear, farther}, lower); // (8 and 28 away; reach 37)
	assert(inside(f, lower) && f.w == 160 && f.h == 100 && inside(kid, f) && inside(farther, f) && !inside(wideNear, f));
	// Square pixels (the sandbox engine's), a low scene: 4:3 as it is.
	const Rect scene = rect(0, 80, 1280, 540);
	const Rect me = rect(600, 300, 60, 200), wideL = rect(270, 310, 190, 190), wideR = rect(810, 310, 190, 190), nextL = rect(520, 300, 70, 200);
	f = frameSelfie(me, {wideR, nextL, wideL}, scene, 1.0); // (140 and 150 away; reach 150)
	assert(inside(f, scene) && f.h == 540 && f.w == 720 && seen(f, 1.0) <= 4.0 / 3);
	assert(inside(me, f) && inside(nextL, f) && inside(wideL, f) && !inside(wideR, f));
	// At the view's edge: inside it, flush with that edge, the player whole
	// (the one far inside cut, the near one whole).
	const Rect edge = rect(290, 40, 24, 60), beside = rect(262, 42, 24, 58), bench = rect(80, 45, 166, 55);
	f = frameSelfie(edge, {bench, beside}, low);
	assert(inside(f, low) && f.right() == 320 && f.h == 136 && seen(f, 1.2) <= 4.0 / 3);
	assert(inside(edge, f) && inside(beside, f) && !inside(bench, f));
	f = frameSelfie(rect(6, 40, 24, 60), {rect(34, 42, 24, 58), rect(74, 45, 166, 55)}, low);
	assert(inside(f, low) && f.x == 0 && f.h == 136 && seen(f, 1.2) <= 4.0 / 3 && inside(rect(6, 40, 24, 60), f) && inside(rect(34, 42, 24, 58), f));
	// Alone in a low room: as before (portrait-ish, head room).
	f = frameSelfie(player, {}, low);
	assert(inside(player, f) && f.y <= player.y - 10 && seen(f, 1.2) >= 0.8 && seen(f, 1.2) <= 4.0 / 3 && f.h < 136);
	// Alone and wider than 4:3 of the view's height: the player is never cut.
	f = frameSelfie(rect(100, 0, 80, 40), {}, rect(0, 0, 320, 40));
	assert(inside(rect(100, 0, 80, 40), f) && f.w == 80 && f.h == 40);
	// A tall view: the same wide group made 4:3 by room above and below,
	// everyone whole.
	const Rect tall = rect(0, 0, 320, 240);
	f = frameSelfie(player, group, tall);
	for (const Rect &r : group) assert(inside(r, f));
	assert(inside(player, f) && inside(f, tall) && f.h > 136 && seen(f, 1.2) <= 4.0 / 3 + 0.01 && seen(f, 1.2) >= 4.0 / 3 - 0.01);
	// A view too narrow for 4:5: lower, the player whole (the room below the
	// feet goes first, then the head room).
	const Rect narrow = rect(0, 0, 120, 400), lanky = rect(40, 100, 40, 150);
	f = frameSelfie(lanky, {}, narrow, 1.0);
	assert(inside(f, narrow) && inside(lanky, f) && f.w == 120 && f.h == 150 && f.y == 100 && seen(f, 1.0) >= 0.8);
	f = frameSelfie(rect(40, 100, 40, 120), {}, narrow, 1.0);
	assert(inside(f, narrow) && f.w == 120 && f.h == 150 && f.y == 73 && f.bottom() >= 220 && seen(f, 1.0) >= 0.8); // (all the head room)
	puts("PASS: selfie framing in low views (narrower, 4:3 at most, the player and the nearest whole, at the edges, alone), tall and narrow views");
}

// Many made-up scenes (a fixed sequence): always inside the view, the
// player whole, 4:5 to 4:3 as shown unless the player alone is not.
static void framingSweep() {
	uint32_t state = 12345;
	auto next = [&](int n) { state ^= state << 13; state ^= state >> 17; state ^= state << 5; return (int)(state % (uint32_t)n); };
	int wholeHeight = 0, wholeWidth = 0;
	for (int round = 0; round < 50000; ++round) {
		const double rowAspect = next(2) ? 1.2 : 1.0;
		const Rect view = rect(next(50), next(50), 40 + next(1400), 40 + next(800));
		Rect player = rect(0, 0, 8 + next(std::max(1, view.w / 3)), 16 + next(std::max(1, view.h - 15)));
		player.w = std::min(player.w, view.w); player.h = std::min(player.h, view.h);
		player.x = view.x + next(view.w - player.w + 1); player.y = view.y + next(view.h - player.h + 1);
		std::vector<Rect> others;
		for (int i = next(8); i > 0; --i) others.push_back(rect(player.x - 300 + next(600), player.y - 60 + next(120), 4 + next(160), 8 + next(300)));
		const Rect f = frameSelfie(player, others, view, rowAspect);
		assert(inside(f, view) && inside(player, f));
		const bool wideAlone = player.w > (int)std::floor(view.h * rowAspect * 4 / 3), tallAlone = player.h > (int)std::floor(view.w / (rowAspect * 0.8));
		if (!wideAlone && !tallAlone) assert(seen(f, rowAspect) >= 0.8 && seen(f, rowAspect) <= 4.0 / 3);
		wholeHeight += f.h == view.h && f.w < view.w; wholeWidth += f.w == view.w && f.h < view.h;
	}
	assert(wholeHeight > 1000 && wholeWidth > 100);
	printf("PASS: selfie framing over 50000 made-up scenes (inside the view, the player whole, 4:5 to 4:3; %d the view's whole height, %d its whole width)\n", wholeHeight, wholeWidth);
}

static void poses() {
	const std::vector<int> xs = {40, 100, 160, 220};
	std::vector<Choice> a, b;
	int surprises = 0, notNoticed = 0, stares = 0, differ = 0, talk = 0, step = 0;
	for (uint32_t seed = 1; seed <= 400; ++seed) {
		const int s = planShot(seed, 0, 1, xs, a);
		assert(planShot(seed, 0, 1, xs, b) == s);
		for (size_t i = 0; i < a.size(); ++i) assert(a[i].facing == b[i].facing && a[i].pose == b[i].pose && a[i].step == b[i].step);
		// The player always faces the viewer and poses.
		assert(a.size() == 4 && a[1].facing == kFaceViewer && a[1].pose != kAsIs && a[1].step >= 0 && a[1].step < 4);
		if (s == kNotNoticed) {
			int asIs = 0;
			for (size_t i = 0; i < a.size(); ++i) asIs += a[i].facing == kFaceAsIs && a[i].pose == kAsIs;
			assert(asIs == 1 && a[1].pose != kAsIs);
			++notNoticed;
		} else if (s == kStareAtPlayer) {
			assert(a[0].facing == kFaceRight && a[2].facing == kFaceLeft && a[3].facing == kFaceLeft);
			++stares;
		} else {
			for (const Choice &c : a) assert(c.facing == kFaceViewer && c.pose != kAsIs);
		}
		surprises += s != kNoSurprise;
		std::vector<Choice> next;
		planShot(seed, 1, 1, xs, next);
		for (size_t i = 0; i < a.size(); ++i) differ += next[i].pose != a[i].pose || next[i].step != a[i].step;
		for (const Choice &c : a) { talk += c.pose == kTalk; step += c.pose == kStep; }
	}
	assert(surprises > 60 && surprises < 140 && notNoticed > 20 && stares > 20 && differ > 400 && talk > 200 && step > 200);
	// Alone: never a surprise.
	for (uint32_t seed = 1; seed <= 100; ++seed) assert(planShot(seed, 2, 0, {50}, a) == kNoSurprise && a[0].facing == kFaceViewer);
	assert(planShot(7, 0, 0, {}, a) == kNoSurprise && a.empty());
	printf("PASS: poses (repeatable, fresh each shot, %d surprises in 400: %d not noticed, %d staring)\n", surprises, notNoticed, stares);
}

static void names() {
	Namer namer;
	assert(namer.next(2026, 10, 17, 14, 5, 9, kindName(kClean)) == "SCUMMVERSE 2026-10-17 14.05.09 clean.png");
	assert(namer.next(2026, 10, 17, 14, 5, 9, kindName(kSelfie)) == "SCUMMVERSE 2026-10-17 14.05.09-2 selfie.png");
	assert(namer.next(2026, 10, 17, 14, 5, 9, kindName(kSelfie)) == "SCUMMVERSE 2026-10-17 14.05.09-3 selfie.png");
	assert(namer.next(2026, 10, 17, 14, 5, 10, kindName(kFull)) == "SCUMMVERSE 2026-10-17 14.05.10 full.png");
	assert(!strcmp(kindName(kFull), "full") && !strcmp(kindName(kSelfie), "selfie") && !strcmp(kindName(kClean), "clean"));
	puts("PASS: names (date and time, kind, -2 and -3 within a second)");
}

static int g_calls = 0, g_kind = -1, g_shot = -1, g_shots = -1, g_width = 0;
static void sink(const Picture &picture, int kind, int shot, int shots, void *context) {
	++g_calls; g_kind = kind; g_shot = shot; g_shots = shots; g_width = picture.width;
	assert(context == &g_calls);
}

static void delivery() {
	Picture p; p.width = 2; p.height = 1; p.rgba.assign(8, 255);
	assert(!deliver(p, kClean, 0, 1));
	setSink(sink, &g_calls);
	assert(deliver(p, kSelfie, 2, 3) && g_calls == 1 && g_kind == kSelfie && g_shot == 2 && g_shots == 3 && g_width == 2);
	Picture none;
	assert(!deliver(none, kClean, 0, 1) && g_calls == 1);
	setSink(nullptr, nullptr);
	assert(!deliver(p, kClean, 0, 1) && g_calls == 1);
	puts("PASS: delivery (to the registered sink only, never an empty picture)");
}

// The sandbox engine's: a true-colour picture already shown square.
static int g_plainCalls = 0, g_plainWidth = 0, g_plainHeight = 0, g_plainKind = -1;
static uint8_t g_plainFirst[4], g_plainLast[4];
static void plain(const uint8_t *rgba, int width, int height, int kind, int, int, void *context) {
	++g_plainCalls; g_plainWidth = width; g_plainHeight = height; g_plainKind = kind;
	memcpy(g_plainFirst, rgba, 4);
	memcpy(g_plainLast, rgba + ((size_t)width * height - 1) * 4, 4);
	assert(context == &g_plainCalls);
}

static void trueColour() {
	int k;
	squareFactor(3, 2, k); assert(k == 534);         // (1602 by 1068)
	squareFactor(1280, 720, k); assert(k == 2);
	squareFactor(2000, 900, k); assert(k == 1);
	squareFactor(1000, 30, k); assert(k == 2);
	squareFactor(3000, 4000, k); assert(k == 1);      // (never smaller)
	squareFactor(800, 2100, k); assert(k == 1);       // (long enough already)
	const uint32_t pixels[] = {0xFF102030, 0xFF405060, 0xFF708090, 0xFFA0B0C0,
	                           0xFF000000, 0xFFFFFFFF, 0xFF123456, 0xFF654321};
	setPlainSink(plain, &g_plainCalls);
	// The middle two of each row (pitch 4 words), each pixel 800 by 800.
	assert(shootTrue(pixels, 4, 4, 2, rect(1, 0, 2, 2), kSelfie, 0, 1));
	assert(g_plainCalls == 1 && g_plainWidth == 1600 && g_plainHeight == 1600 && g_plainKind == kSelfie);
	assert(g_plainFirst[0] == 0x40 && g_plainFirst[1] == 0x50 && g_plainFirst[2] == 0x60 && g_plainFirst[3] == 255);
	assert(g_plainLast[0] == 0x12 && g_plainLast[1] == 0x34 && g_plainLast[2] == 0x56);
	// Cut to the picture; nothing of it, nothing taken.
	assert(shootTrue(pixels, 4, 4, 2, rect(3, 1, 5, 5), kClean, 0, 1) && g_plainWidth == 1600 && g_plainHeight == 1600 && g_plainFirst[0] == 0x65);
	assert(!shootTrue(pixels, 4, 4, 2, rect(4, 0, 2, 2), kClean, 0, 1) && g_plainCalls == 2);
	assert(!shootTrue(nullptr, 4, 4, 2, rect(0, 0, 2, 2), kClean, 0, 1));
	setPlainSink(nullptr, nullptr);
	assert(!shootTrue(pixels, 4, 4, 2, rect(0, 0, 2, 2), kClean, 0, 1) && g_plainCalls == 2);
	// Standing in for the sink set before (the iPhone's), which is back after.
	const int before = g_calls;
	setSink(sink, &g_calls);
	setPlainSink(plain, &g_plainCalls);
	assert(shootTrue(pixels, 4, 4, 2, rect(0, 0, 2, 2), kClean, 0, 1) && g_plainCalls == 3 && g_calls == before);
	setPlainSink(plain, &g_plainCalls); // (again: still the iPhone's held)
	setPlainSink(nullptr, nullptr);
	assert(shootTrue(pixels, 4, 4, 2, rect(0, 0, 2, 2), kClean, 0, 1) && g_plainCalls == 3 && g_calls == before + 1);
	setSink(nullptr, nullptr);
	// A selfie framed on square pixels: 4:5 to 4:3 as it is.
	const Rect view = rect(0, 0, 1280, 720);
	Rect f = frameSelfie(rect(600, 300, 60, 200), nullptr, 0, view, 1.0);
	assert(inside(rect(600, 300, 60, 200), f) && inside(f, view));
	assert(f.w / (double)f.h >= 0.8 - 0.02 && f.w / (double)f.h <= 4.0 / 3 + 0.02);
	// (Two near either side: a wide group, made 4:3 by room above and below.)
	const Rect wide[] = {rect(380, 320, 60, 180), rect(660, 310, 60, 190)};
	f = frameSelfie(rect(560, 300, 60, 200), wide, 2, view, 1.0);
	assert(inside(wide[0], f) && inside(wide[1], f) && inside(rect(560, 300, 60, 200), f));
	assert(f.w / (double)f.h <= 4.0 / 3 + 0.02 && f.w / (double)f.h >= 4.0 / 3 - 0.02);
	puts("PASS: true colour (whole-pixel enlarging of square pixels, cut to the picture, a plain-types sink); selfies framed on square pixels");
}

int main() {
	requests();
	pictures();
	framing();
	lowViews();
	framingSweep();
	poses();
	names();
	delivery();
	trueColour();
	return 0;
}
