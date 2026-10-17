// SPDX-License-Identifier: GPL-3.0-or-later
// Contract tests for the CAMERA's portable part (requests, whole-pixel
// enlarging, selfie framing, poses, names, delivery). Build with
//   c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//       tools/test_camera.cpp engine/common/scummverse_camera.cpp -o build/test_camera
#include "common/scummverse_camera.h"

#include <cassert>
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

int main() {
	requests();
	pictures();
	framing();
	poses();
	names();
	delivery();
	return 0;
}
