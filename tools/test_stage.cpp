// Sandbox stage (common/scummverse_stage.cpp) with synthetic scenes and
// characters (no game data): the view at any screen size, walk boxes and
// paths, scales, drawing in true colour, walking, the camera, spots.
// c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//   tools/test_stage.cpp engine/common/scummverse_stage.cpp engine/common/scummverse_world.cpp
#include "common/scummverse_stage.h"
#include <cassert>
#include <cmath>
#include <cstdio>
using namespace Scummverse;
using namespace Scummverse::Stage;

static void put16(std::vector<uint8_t> &v, int x) { v.push_back((uint8_t)(x & 255)); v.push_back((uint8_t)((x >> 8) & 255)); }
// An "SVW3" scene: palette c = (c, 255-c, c/2), no objects, box scales.
static std::vector<uint8_t> sceneBytes(int w, int h, const std::vector<uint8_t> &pixels, const std::vector<World::SourceBox> &boxes) {
	std::vector<uint8_t> d = {'S', 'V', 'W', '3'};
	put16(d, 7); put16(d, w); put16(d, h); d.push_back((uint8_t)boxes.size()); d.push_back(0);
	for (int c = 0; c < 256; ++c) { d.push_back((uint8_t)c); d.push_back((uint8_t)(255 - c)); d.push_back((uint8_t)(c / 2)); }
	d.insert(d.end(), pixels.begin(), pixels.end());
	for (const auto &b : boxes) { for (int c = 0; c < 4; ++c) { put16(d, b.x[c]); put16(d, b.y[c]); } d.push_back((uint8_t)b.flags); d.push_back((uint8_t)b.mask); }
	put16(d, 0);
	for (const auto &b : boxes) { d.push_back((uint8_t)b.scaleTop); d.push_back((uint8_t)b.scaleBottom); }
	return d;
}
static World::SourceBox box(int l, int t, int r, int b, int flags = 0, int top = 255, int bottom = 255) {
	World::SourceBox x;
	x.x[0] = l; x.y[0] = t; x.x[1] = r; x.y[1] = t; x.x[2] = r; x.y[2] = b; x.x[3] = l; x.y[3] = b;
	x.flags = flags; x.scaleTop = top; x.scaleBottom = bottom;
	return x;
}
static Box stageBox(int l, int t, int r, int b) {
	Box x;
	x.corner[0] = {(double)l, (double)t}; x.corner[1] = {(double)r, (double)t};
	x.corner[2] = {(double)r, (double)b}; x.corner[3] = {(double)l, (double)b};
	return x;
}

struct Frame { int dir, kind, index, dx, dy, w, h; uint8_t color; };
// An "SVC1" character: palette c = (c, c, 255-c); each frame one colour, its
// top row transparent.
static std::vector<uint8_t> spriteBytes(const std::vector<Frame> &frames) {
	std::vector<uint8_t> d = {'S', 'V', 'C', '1'};
	put16(d, 5); put16(d, (int)frames.size());
	for (int c = 0; c < 256; ++c) { d.push_back((uint8_t)c); d.push_back((uint8_t)c); d.push_back((uint8_t)(255 - c)); }
	for (const Frame &f : frames) {
		d.push_back((uint8_t)f.dir); d.push_back((uint8_t)f.kind); d.push_back((uint8_t)f.index); d.push_back(0);
		put16(d, f.dx); put16(d, f.dy); put16(d, f.w); put16(d, f.h);
		for (int y = 0; y < f.h; ++y) for (int x = 0; x < f.w; ++x) d.push_back(f.color);
		for (int y = 0; y < f.h; ++y) for (int x = 0; x < f.w; ++x) d.push_back(y > 0);
	}
	return d;
}
static uint32_t sceneColor(int c) { return 0xFF000000u | (uint32_t)c << 16 | (uint32_t)(255 - c) << 8 | (uint32_t)(c / 2); }
static uint32_t spriteColor(int c) { return 0xFF000000u | (uint32_t)c << 16 | (uint32_t)c << 8 | (uint32_t)(255 - c); }
static bool near(double a, double b, double within = 1e-6) { return std::fabs(a - b) <= within; }
static bool inSomeBox(const std::vector<Box> &boxes, Point p) {
	for (const Box &b : boxes) if (inside(b, p, 1.6)) return true;
	return false;
}

int main() {
	// The view: as tall as the screen allows, no wider than the game's own
	// screen at that size, taller pixels for 320x200 art; centred; COMI's
	// square pixels; wide rooms scroll within the scene; round trips.
	View v = View::fit(320, 144, 1.2, 320, 1280, 720);
	assert(near(v.rowScale, 4.8) && near(v.colScale, 4.0) && v.width == 1280 && v.height == 691 && v.left == 0 && v.top == 14);
	View comi = View::fit(640, 480, 1.0, 640, 1280, 720);
	assert(near(comi.rowScale, 1.5) && comi.width == 960 && comi.height == 720 && comi.left == 160 && comi.top == 0);
	View tall = View::fit(320, 200, 1.2, 320, 2556, 1179); // an iPhone 15 Pro screen
	assert(tall.height <= 1179 && tall.width <= 2556 && near(tall.rowScale / tall.colScale, 1.2));
	View wide = View::fit(640, 144, 1.2, 320, 1280, 720);
	assert(wide.width == 2560 && wide.left == 0);
	wide.follow(10); assert(wide.camera == 0);
	wide.follow(320); assert(wide.camera == 640);
	wide.follow(639); assert(wide.camera == 1280);
	wide.follow(320);
	const Point s = wide.toScreen(400, 100), back = wide.toScene((int)s.x, (int)s.y);
	assert(near(s.x, 400 * 4.0 - 640) && near(s.y, 100 * 4.8 + 14) && near(back.x, 400, 0.3) && near(back.y, 100, 0.3));
	assert(View::fit(0, 144, 1.2, 320, 1280, 720).width == 0 && View::fit(320, 144, 1.2, 320, 0, 0).width == 0);
	std::puts("PASS: the view (full screen, taller pixels, square pixels, scrolling, round trips)");

	// Boxes: inside, closest, the box at a point (else the nearest), meeting
	// boxes, scales by row, switched-off boxes left out.
	const Box a = stageBox(0, 100, 100, 140), b = stageBox(100, 100, 200, 140), up = stageBox(150, 40, 190, 100), apart = stageBox(250, 100, 300, 140);
	assert(inside(a, {50, 120}) && !inside(a, {150, 120}) && inside(a, {100.4, 120}));
	assert(near(closest(a, {150, 120}).x, 100) && near(closest(a, {50, 10}).y, 100) && near(closest(a, {50, 120}).x, 50));
	Box slanted; slanted.corner[0] = {10, 100}; slanted.corner[1] = {90, 100}; slanted.corner[2] = {120, 140}; slanted.corner[3] = {-20, 140};
	assert(inside(slanted, {-10, 138}) && !inside(slanted, {0, 101}));
	Box backwards = a; std::swap(backwards.corner[1], backwards.corner[3]); // (the other winding)
	assert(inside(backwards, {50, 120}) && !inside(backwards, {150, 120}));
	// Flat boxes (a line, a point) hold only themselves, not their whole line.
	Box line = stageBox(93, 130, 75, 130), dot = stageBox(40, 40, 40, 40);
	assert(inside(line, {80, 130}) && !inside(line, {150, 130}) && near(closest(line, {200, 130}).x, 93));
	assert(!touching(line, stageBox(189, 130, 230, 142)) && touching(line, stageBox(60, 120, 76, 140)));
	assert(inside(dot, {40, 40}) && !inside(dot, {40, 41}) && !touching(dot, stageBox(0, 40, 30, 50)));
	const std::vector<Box> boxes = {a, b, up, apart};
	assert(boxAt(boxes, {50, 120}) == 0 && boxAt(boxes, {170, 60}) == 2 && boxAt(boxes, {230, 120}) == 3 && boxAt(std::vector<Box>(), {0, 0}) == -1);
	assert(touching(a, b) && touching(b, up) && !touching(a, up) && !touching(b, apart) && touching(stageBox(0, 0, 10, 10), stageBox(2, 2, 8, 8)));
	std::vector<Box> scaled = {stageBox(0, 100, 100, 140)}; scaled[0].scaleTop = 100; scaled[0].scaleBottom = 200;
	assert(scaleAt(scaled, {50, 100}) == 100 && scaleAt(scaled, {50, 140}) == 200 && scaleAt(scaled, {50, 120}) == 150 && scaleAt(std::vector<Box>(), {1, 1}) == 255);
	World::SourceScene source;
	source.boxes = {box(0, 0, 10, 10), box(0, 0, 10, 10, 0x80), box(-32000, -32000, -32000, -32000), box(0, 0, 10, 10, 0, 50, 60)};
	const std::vector<Box> kept = boxesOf(source);
	assert(kept.size() == 2 && kept[1].scaleTop == 50 && kept[1].scaleBottom == 60);
	std::puts("PASS: boxes (inside, closest, nearest box, meeting, flat ones, scales, switched off, placeholder)");

	// Paths: across meeting boxes and up into the next, every point in a
	// box, ending where asked (moved into the boxes); a box nobody can reach
	// leaves them as near as they get through the boxes they can; no boxes,
	// no path.
	std::vector<Point> route = path(boxes, {20, 120}, {170, 50});
	assert(route.size() == 3 && near(route.back().x, 170) && near(route.back().y, 50));
	for (const Point &p : route) assert(inSomeBox(boxes, p));
	assert(near(route[0].x, 100, 1.6) && near(route[1].y, 100, 1.6));
	route = path(boxes, {20, 120}, {60, 20}); // above the first box
	assert(route.size() == 1 && near(route[0].x, 60) && near(route[0].y, 100));
	route = path(boxes, {20, 120}, {280, 120}); // cut off: as near as the boxes reached allow
	assert(route.size() == 2 && near(route.back().x, 200) && near(route.back().y, 120));
	assert(path(std::vector<Box>(), {0, 0}, {5, 5}).empty());
	std::puts("PASS: paths (across, up, into the boxes, cut off, none)");

	// A scene drawn once at the screen's size, in its own colours: every
	// screen pixel shows the source pixel under it.
	const int w = 320, h = 144;
	std::vector<uint8_t> pixels((size_t)w * h);
	for (int y = 0; y < h; ++y) for (int x = 0; x < w; ++x) pixels[(size_t)y * w + x] = (uint8_t)((x / 8 + y / 8) % 200 + 20);
	std::vector<World::SourceBox> floor = {box(10, 100, 160, 140, 0, 128, 255), box(160, 100, 310, 140, 0, 255, 255), box(0, 0, 5, 5, 0x80)};
	const std::vector<uint8_t> sceneData = sceneBytes(w, h, pixels, floor);
	Scene scene; std::string error;
	assert(!scene.load(sceneData.data(), 100, 1.2, 320, 1280, 720, error) && !error.empty());
	assert(scene.load(sceneData.data(), sceneData.size(), 1.2, 320, 1280, 720, error) && scene.boxes().size() == 2);
	std::vector<uint32_t> screen((size_t)1300 * 720, 0x12345678u);
	const int pitch = 1300;
	scene.render(screen.data(), pitch);
	for (int y = 0; y < 720; y += 7)
		for (int x = 0; x < 1280; x += 5) {
			const uint32_t got = screen[(size_t)y * pitch + x];
			if (y < scene.view().top || y >= scene.view().top + scene.view().height) { assert(got == 0xFF000000u); continue; }
			const Point at = scene.view().toScene(x, y);
			const int sx = std::min(w - 1, (int)at.x), sy = std::min(h - 1, (int)at.y);
			assert(got == sceneColor(pixels[(size_t)sy * w + sx]));
		}
	assert(screen[1280] == 0x12345678u); // (past the screen's width, in the pitch: untouched)
	std::puts("PASS: the scene in true colour at the screen's size");

	// Characters: drawn at the person's height for where they stand (the
	// box's scale), in their own colours, transparent where the mask says,
	// over the scene; the nearer drawn last; facing where they walk.
	const std::vector<Frame> frames = {{2, 0, 0, -10, -40, 20, 40, 30}, {0, 0, 0, -8, -40, 16, 40, 40},
		{0, 1, 0, -8, -40, 16, 40, 50}, {0, 1, 1, -8, -38, 16, 38, 60}, {1, 1, 0, -8, -40, 16, 40, 70}};
	const std::vector<uint8_t> spriteData = spriteBytes(frames);
	assert(scene.addActor(spriteData.data(), 10, 1, 1.2, error) == -1);
	const int hero = scene.addActor(spriteData.data(), spriteData.size(), 1, 1.2, error);
	const int half = scene.addActor(spriteData.data(), spriteData.size(), 0.5, 1.2, error);
	assert(hero == 0 && half == 1 && scene.actorCount() == 2);
	scene.place(hero, {200, 140}); // full scale
	scene.place(half, {60, 300});  // (moved into the boxes: the bottom of the first, full scale there)
	assert(near(scene.actor(half).at.y, 140) && near(scene.actor(half).at.x, 60));
	int x0, y0, x1, y1;
	assert(scene.drawnRect(hero, x0, y0, x1, y1));
	assert(std::abs((y1 - y0) - (int)std::lround(40 * 4.8)) <= 1 && std::abs((x1 - x0) - (int)std::lround(20 * 4.0)) <= 1);
	int hx0, hy0, hx1, hy1;
	assert(scene.drawnRect(half, hx0, hy0, hx1, hy1) && std::abs((hy1 - hy0) - (int)std::lround(20 * 4.8)) <= 1);
	scene.place(half, {60, 100}); // the top of the first box: scale 128
	assert(scene.drawnRect(half, hx0, hy0, hx1, hy1) && std::abs((hy1 - hy0) - (int)std::lround(20 * 4.8 * 128 / 255)) <= 1);
	scene.render(screen.data(), pitch);
	const int midX = (x0 + x1) / 2, midY = (y0 + y1) / 2;
	assert(screen[(size_t)midY * pitch + midX] == spriteColor(30));
	const Point under = scene.view().toScene(midX, y0 + 1);
	assert(screen[(size_t)(y0 + 1) * pitch + midX] == sceneColor(pixels[(size_t)(int)under.y * w + (int)under.x])); // the top row is clear
	// Overlapping: the one further down the screen is in front.
	std::vector<Frame> otherFrames = frames; otherFrames[0].color = 90;
	const std::vector<uint8_t> otherData = spriteBytes(otherFrames);
	const int other = scene.addActor(otherData.data(), otherData.size(), 0.5, 1.2, error);
	scene.place(hero, {200, 120});
	scene.place(other, {200, 140}); // nearer
	scene.render(screen.data(), pitch);
	assert(scene.drawnRect(other, hx0, hy0, hx1, hy1) && screen[(size_t)((hy0 + hy1) / 2) * pitch + (hx0 + hx1) / 2] == spriteColor(90));
	scene.place(other, {200, 110}); // further back, behind the hero
	scene.render(screen.data(), pitch);
	assert(scene.drawnRect(other, hx0, hy0, hx1, hy1) && screen[(size_t)((hy0 + hy1) / 2) * pitch + (hx0 + hx1) / 2] == spriteColor(30));
	std::puts("PASS: characters (height, scale by place, colours, mask, nearer in front)");

	// Walking: along the path at a person's pace (slower where smaller),
	// facing the way they go, stepping through the walk frames, standing on
	// arrival; the camera keeps the one it follows in view.
	scene.place(hero, {20, 130});
	scene.walkTo(hero, {300, 130});
	assert(scene.actor(hero).moving);
	scene.update(1);
	assert(scene.actor(hero).dir == 1 && scene.actor(hero).at.x > 20);
	int ticks = 0;
	while (scene.actor(hero).moving && ticks < 10000) { scene.update(1); ++ticks; }
	assert(!scene.actor(hero).moving && near(scene.actor(hero).at.x, 300, 1e-6) && ticks > 280 / kWalkSpeed - 2);
	scene.walkTo(hero, {20, 130});
	scene.update(6);
	assert(scene.actor(hero).dir == 0);
	scene.render(screen.data(), pitch);
	assert(scene.drawnRect(hero, x0, y0, x1, y1) && screen[(size_t)((y0 + y1) / 2) * pitch + (x0 + x1) / 2] != spriteColor(40)); // walking, not standing
	scene.walkTo(hero, scene.actor(hero).at); // nowhere to go
	scene.update(1);
	assert(!scene.actor(hero).moving && scene.actor(hero).route.empty());

	const std::vector<uint8_t> wideData = sceneBytes(640, 144, std::vector<uint8_t>((size_t)640 * 144, 9), {box(0, 100, 640, 140)});
	Scene street;
	assert(street.load(wideData.data(), wideData.size(), 1.2, 320, 1280, 720, error) && street.view().width == 2560);
	const int walker = street.addActor(spriteData.data(), spriteData.size(), 1, 1.2, error);
	street.place(walker, {20, 120});
	street.follow(walker);
	assert(street.view().camera == 0);
	street.walkTo(walker, {620, 120});
	for (int t = 0; t < 2000; ++t) street.update(1);
	assert(street.view().camera == 1280 && street.drawnRect(walker, x0, y0, x1, y1));
	street.place(walker, {0, 120});
	street.follow(walker);
	street.render(screen.data(), pitch); // (partly off the left edge: no left-facing stand, the left one)
	assert(street.view().camera == 0 && street.drawnRect(walker, x0, y0, x1, y1) && x0 == 0);
	assert(screen[(size_t)((y0 + y1) / 2) * pitch] == spriteColor(40));
	std::puts("PASS: walking (pace, facing, steps, arrival, the camera)");

	// Spots for people: inside the boxes, spread out.
	for (int n : {1, 4, 12}) {
		const std::vector<Point> spots = scene.spots(n);
		assert((int)spots.size() == n);
		for (const Point &p : spots) assert(inSomeBox(scene.boxes(), p));
		for (int i = 0; i < n && n <= 4; ++i)
			for (int j = i + 1; j < n; ++j) assert(std::hypot(spots[i].x - spots[j].x, spots[i].y - spots[j].y) > 30);
	}
	assert(scene.spots(0).empty());
	std::puts("PASS: spots (in the boxes, spread out)");
	return 0;
}
