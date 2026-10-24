// Sandbox stage (common/scummverse_stage.cpp) with synthetic scenes and
// characters (no game data): the view at any screen size, walk boxes and
// paths, scales, drawing in true colour, walking, the camera, spots.
// c++ -std=c++11 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//   tools/test_stage.cpp engine/common/scummverse_stage.cpp engine/common/scummverse_world.cpp
#include "common/scummverse_stage.h"
#include "common/scummverse_stage_engine.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
using namespace Scummverse;
using namespace Scummverse::Stage;

static void put16(std::vector<uint8_t> &v, int x) { v.push_back((uint8_t)(x & 255)); v.push_back((uint8_t)((x >> 8) & 255)); }
// An "SVW3" scene: palette c = (c, 255-c, c/2), its objects, box scales.
static std::vector<uint8_t> sceneBytes(int w, int h, const std::vector<uint8_t> &pixels, const std::vector<World::SourceBox> &boxes,
		const std::vector<World::SourceObject> &objects = std::vector<World::SourceObject>()) {
	std::vector<uint8_t> d = {'S', 'V', 'W', '3'};
	put16(d, 7); put16(d, w); put16(d, h); d.push_back((uint8_t)boxes.size()); d.push_back(0);
	for (int c = 0; c < 256; ++c) { d.push_back((uint8_t)c); d.push_back((uint8_t)(255 - c)); d.push_back((uint8_t)(c / 2)); }
	d.insert(d.end(), pixels.begin(), pixels.end());
	for (const auto &b : boxes) { for (int c = 0; c < 4; ++c) { put16(d, b.x[c]); put16(d, b.y[c]); } d.push_back((uint8_t)b.flags); d.push_back((uint8_t)b.mask); }
	put16(d, (int)objects.size());
	for (const auto &o : objects) for (int f : {o.id, o.x, o.y, o.width, o.height, o.walkX, o.walkY}) put16(d, f);
	for (const auto &b : boxes) { d.push_back((uint8_t)b.scaleTop); d.push_back((uint8_t)b.scaleBottom); }
	return d;
}
// The same as "SVW5": objects with their states, the game's next box from
// each box toward each other one, colour cycles, names and pictures.
static std::vector<uint8_t> scene5Bytes(int w, int h, const std::vector<uint8_t> &pixels, const std::vector<World::SourceBox> &boxes,
		const std::vector<World::SourceObject> &objects, const std::vector<uint8_t> &next, const std::vector<World::SourceCycle> &cycles) {
	std::vector<uint8_t> d = {'S', 'V', 'W', '5'};
	put16(d, 7); put16(d, w); put16(d, h); d.push_back((uint8_t)boxes.size()); d.push_back(0);
	for (int c = 0; c < 256; ++c) { d.push_back((uint8_t)c); d.push_back((uint8_t)(255 - c)); d.push_back((uint8_t)(c / 2)); }
	d.insert(d.end(), pixels.begin(), pixels.end());
	for (const auto &b : boxes) { for (int c = 0; c < 4; ++c) { put16(d, b.x[c]); put16(d, b.y[c]); } d.push_back((uint8_t)b.flags); d.push_back((uint8_t)b.mask); }
	put16(d, (int)objects.size());
	for (const auto &o : objects) for (int f : {o.id, o.x, o.y, o.width, o.height, o.walkX, o.walkY, o.state}) put16(d, f);
	for (const auto &b : boxes) { d.push_back((uint8_t)b.scaleTop); d.push_back((uint8_t)b.scaleBottom); }
	d.insert(d.end(), next.begin(), next.end());
	d.push_back((uint8_t)cycles.size());
	for (const auto &c : cycles) { put16(d, c.delay); d.push_back((uint8_t)c.first); d.push_back((uint8_t)c.last); d.push_back((uint8_t)c.mode); }
	for (const auto &o : objects) {
		d.push_back((uint8_t)o.name.size()); d.insert(d.end(), o.name.begin(), o.name.end());
		d.push_back((uint8_t)o.pictures.size());
		if (o.pictures.empty()) continue;
		d.push_back((uint8_t)o.shown);
		for (int f : {o.pictureX, o.pictureY, o.pictureWidth, o.pictureHeight}) put16(d, f);
		for (const auto &picture : o.pictures) d.insert(d.end(), picture.begin(), picture.end());
	}
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
static int x0n(const Scene &place, int n) { return (int)place.actor(n).at.x; }
static bool inSomeBox(const std::vector<Box> &boxes, Point p) {
	for (const Box &b : boxes) if (inside(b, p, 0.6)) return true;
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
	assert(touching(stageBox(34, 124, 138, 134), stageBox(140, 132, 206, 134)) && !touching(stageBox(0, 0, 10, 10), stageBox(15, 0, 25, 10))); // (two apart: met; five: not)
	assert(touching(stageBox(0, 0, 10, 10), stageBox(13, 0, 20, 10)) && !touching(stageBox(0, 0, 10, 10), stageBox(14, 0, 20, 10))); // (three: met; four: not)
	assert(touching(stageBox(0, 0, 10, 10), stageBox(12, 12, 20, 20)) && kBoxGap == 3); // (diagonally two by two)
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
	assert(near(route[0].x, 100, kBoxGap + 0.6) && near(route[1].y, 100, kBoxGap + 0.6));
	route = path(boxes, {20, 120}, {60, 20}); // above the first box
	assert(route.size() == 1 && near(route[0].x, 60) && near(route[0].y, 100));
	route = path(boxes, {20, 120}, {280, 120}); // cut off: as near as the boxes reached allow
	assert(route.size() == 2 && near(route.back().x, 200) && near(route.back().y, 120));
	assert(path(std::vector<Box>(), {0, 0}, {5, 5}).empty());
	const Links links = linksOf(boxes);
	Links broken = links; broken.meet.pop_back();
	assert(!broken.meets(0, 1)); // (a table of the wrong size meets nothing)
	assert(links.group[0] == links.group[1] && links.group[1] == links.group[2] && links.group[3] != links.group[0]);
	assert(links.meets(0, 1) && links.meets(1, 0) && !links.meets(0, 2) && !links.meets(0, 9));
	assert(path(boxes, links, {20, 120}, {170, 50}).size() == 3);
	std::puts("PASS: paths (across, up, into the boxes, cut off, none; groups of boxes)");

	// The way through the fewest boxes, of those the shortest (not round by
	// a box that comes first in the file); already in the next box, on from
	// there (not back to its edge, nor sideways along a shared one); boxes
	// apart that the game's table joins: to the edge facing the other first,
	// across the gap there (not on a slant over the floor's edge).
	{
		auto walked = [](Point at, const std::vector<Point> &way) {
			double length = 0;
			for (const Point &p : way) { length += std::hypot(p.x - at.x, p.y - at.y); at = p; }
			return length;
		};
		auto strays = [](const std::vector<Box> &on, Point at, const std::vector<Point> &way) {
			double most = 0;
			for (const Point &p : way) {
				for (int k = 0; k <= 64; ++k) {
					const Point q(at.x + (p.x - at.x) * k / 64, at.y + (p.y - at.y) * k / 64);
					double off = 1e9;
					for (const Box &piece : on) { const Point c = closest(piece, q); off = std::min(off, std::hypot(c.x - q.x, c.y - q.y)); }
					most = std::max(most, off);
				}
				at = p;
			}
			return most;
		};
		const std::vector<Box> ring = {stageBox(0, 0, 100, 140), stageBox(0, 140, 300, 180), stageBox(100, 0, 200, 40), stageBox(200, 0, 300, 140)};
		route = path(ring, {90, 20}, {210, 20}); // (along the top, not down and round the bottom)
		assert(near(walked({90, 20}, route), 120, 0.01));
		route = path({stageBox(0, 0, 100, 100), stageBox(50, 0, 150, 100)}, {60, 50}, {140, 50}); // (in both: not back to 50 first)
		assert(near(walked({60, 50}, route), 80, 0.01) && near(route.back().x, 140));
		route = path({stageBox(0, 0, 320, 50), stageBox(0, 50, 320, 100)}, {105, 50}, {105, 90}); // (on the edge: straight down)
		assert(near(walked({105, 50}, route), 40, 0.01));
		std::vector<Box> gap = {stageBox(0, 100, 300, 140), stageBox(250, 40, 290, 84)};
		gap[0].source = 0; gap[1].source = 1;
		const Links table = linksOf(gap, {0, 1, 0, 1}, 2);
		assert(table.meets(0, 1) && !touching(gap[0], gap[1]));
		route = path(gap, table, {20, 130}, {270, 60}); // (16 apart: up to the edge, then across)
		assert(route.size() == 3 && near(route[0].y, 100) && near(route[1].y, 84) && near(route.back().x, 270) && near(route.back().y, 60));
		assert(strays(gap, {20, 130}, route) < 9);
	}
	std::puts("PASS: ways (the fewest boxes, then the shortest; on from inside the next box; up to a gap the game's table joins, then across)");

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
	// (From 0210) A point on both: the one drawn in front there (by the row
	// they stand on), else the one behind when the front one is skipped.
	scene.place(other, {200, 122}); // (just in front, over the hero)
	assert(scene.drawnRect(other, hx0, hy0, hx1, hy1));
	{
		int px = -1, py = -1;
		for (int y = hy0; y < hy1 && px < 0; ++y) for (int x = hx0; x < hx1 && px < 0; ++x) if (scene.drawnAt(hero, x, y) && scene.drawnAt(other, x, y)) { px = x; py = y; }
		assert(px >= 0);
		assert(scene.actorAt(px, py) == other && scene.actorAt(px, py, other) == hero && scene.actorAt(0, 0) == -1);
		scene.place(other, {200, 118}); // (just behind)
		assert(scene.drawnAt(hero, px, py) && scene.actorAt(px, py) == hero);
	}
	// (From 0210) A place narrower than the screen: nobody drawn on the bar
	// beside it, nor found there; a point box off the picture is no box.
	{
		const int nw = 100, nh = 50;
		std::vector<uint8_t> narrowPixels((size_t)nw * nh, 7);
		World::SourceBox floor; floor.x[0] = 0; floor.y[0] = 0; floor.x[1] = nw - 1; floor.y[1] = 0; floor.x[2] = nw - 1; floor.y[2] = nh - 1; floor.x[3] = 0; floor.y[3] = nh - 1;
		World::SourceBox dot; for (int c = 0; c < 4; ++c) { dot.x[c] = -1; dot.y[c] = -1; }
		const std::vector<uint8_t> narrowData = sceneBytes(nw, nh, narrowPixels, {floor, dot});
		Scene narrow;
		assert(narrow.load(narrowData.data(), narrowData.size(), 1.0, nw, 400, 100, error) && narrow.boxes().size() == 1 && narrow.view().left > 0);
		std::vector<uint32_t> bare((size_t)400 * 100, 0), out((size_t)400 * 100, 0);
		narrow.render(bare.data(), 400);
		const int edge = narrow.addActor(spriteData.data(), spriteData.size(), 1, 1.2, error);
		narrow.place(edge, {1, 40});
		narrow.render(out.data(), 400);
		int ex0, ey0, ex1, ey1;
		assert(narrow.drawnRect(edge, ex0, ey0, ex1, ey1) && ex0 >= narrow.view().left && out != bare);
		for (int y = 0; y < 100; ++y) for (int x = 0; x < narrow.view().left; ++x) assert(out[(size_t)y * 400 + x] == bare[(size_t)y * 400 + x]);
		assert(narrow.actorAt(narrow.view().left - 2, (ey0 + ey1) / 2) == -1);
	}
	std::puts("PASS: characters (height, scale by place, colours, mask, nearer in front; the front one found under a point; none on the bars beside a narrower place)");

	// Walking as the games do: a step every six ticks, at most 8 across and 2
	// up or down the scene at full scale (smaller where smaller), the legs in
	// step (a walk frame a step), facing the way they go, standing on arrival.
	scene.place(hero, {20, 130});
	scene.walkTo(hero, {300, 130});
	assert(scene.actor(hero).moving);
	scene.update(1); // (the first step at once)
	assert(scene.actor(hero).dir == 1 && scene.actor(hero).at.x > 20 && scene.actor(hero).at.x <= 28 && scene.actor(hero).steps == 1);
	const double stepped = scene.actor(hero).at.x;
	scene.update(4); // (between steps, still)
	assert(scene.actor(hero).at.x == stepped && scene.actor(hero).steps == 1);
	scene.update(2);
	assert(scene.actor(hero).at.x > stepped && scene.actor(hero).steps == 2);
	int ticks = 7;
	while (scene.actor(hero).moving && ticks < 10000) { scene.update(1); ++ticks; }
	assert(!scene.actor(hero).moving && near(scene.actor(hero).at.x, 300, 1e-6) && ticks >= 280 / 8 * 6 && ticks <= 280 / 2 * 6);
	scene.place(hero, {200, 100});
	scene.walkTo(hero, {200, 140}); // 40 down the scene
	int down = 0;
	while (scene.actor(hero).moving && down < 10000) { scene.update(1); ++down; }
	scene.walkTo(hero, {240, 140}); // 40 across
	int across = 0;
	while (scene.actor(hero).moving && across < 10000) { scene.update(1); ++across; }
	assert(near(scene.actor(hero).at.x, 240) && near(scene.actor(hero).at.y, 140) && down >= 3 * across && across > 0);
	scene.walkTo(hero, {20, 130});
	scene.update(1);
	assert(scene.actor(hero).dir == 0);
	scene.render(screen.data(), pitch);
	assert(scene.drawnRect(hero, x0, y0, x1, y1));
	const uint32_t firstStep = screen[(size_t)((y0 + y1) / 2) * pitch + (x0 + x1) / 2];
	scene.update(6);
	scene.render(screen.data(), pitch);
	assert(scene.drawnRect(hero, x0, y0, x1, y1));
	const uint32_t nextStep = screen[(size_t)((y0 + y1) / 2) * pitch + (x0 + x1) / 2];
	assert(firstStep != spriteColor(40) && nextStep != spriteColor(40) && firstStep != nextStep); // walking, a frame a step
	scene.walkTo(hero, scene.actor(hero).at); // nowhere to go
	scene.update(6);
	assert(!scene.actor(hero).moving && scene.actor(hero).route.empty());
	// Turned towards a point standing (not while walking); talking, its talk
	// frames in turn, a frame each kTalkTicks (the front stood where it has
	// none that way).
	scene.face(hero, {scene.actor(hero).at.x + 50, scene.actor(hero).at.y});
	assert(scene.actor(hero).dir == 1);
	scene.face(hero, {scene.actor(hero).at.x - 50, scene.actor(hero).at.y + 5});
	assert(scene.actor(hero).dir == 0);
	scene.face(hero, {scene.actor(hero).at.x, scene.actor(hero).at.y + 30});
	assert(scene.actor(hero).dir == 2);
	scene.face(hero, scene.actor(hero).at);
	assert(scene.actor(hero).dir == 2);
	{
		const std::vector<Frame> talkFrames = {{2, 0, 0, -10, -40, 20, 40, 30}, {2, 2, 0, -10, -40, 20, 40, 100}, {2, 2, 1, -10, -40, 20, 40, 110},
			{1, 0, 0, -10, -40, 20, 40, 120}, {1, 1, 0, -10, -40, 20, 40, 130}};
		const std::vector<uint8_t> talkData = spriteBytes(talkFrames);
		const int talker = scene.addActor(talkData.data(), talkData.size(), 1, 1.2, error);
		scene.place(talker, {100, 140});
		auto middle = [&]() {
			scene.render(screen.data(), pitch);
			int a0, b0, a1, b1;
			assert(scene.drawnRect(talker, a0, b0, a1, b1));
			return screen[(size_t)((b0 + b1) / 2) * pitch + (a0 + a1) / 2];
		};
		assert(middle() == spriteColor(30));
		scene.talk(talker, true);
		assert(scene.actor(talker).talking);
		const uint32_t first = middle();
		scene.update(kTalkTicks);
		const uint32_t second = middle();
		assert((first == spriteColor(100) || first == spriteColor(110)) && (second == spriteColor(100) || second == spriteColor(110)) && first != second);
		scene.face(talker, {200, 140}); // (no talk frames that way: it stands)
		assert(scene.actor(talker).dir == 1 && middle() == spriteColor(120));
		scene.talk(talker, false);
		scene.face(talker, {100, 200}); // (to the front)
		assert(scene.actor(talker).dir == 2 && middle() == spriteColor(30));
		scene.walkTo(talker, {300, 140});
		scene.update(1);
		scene.face(talker, {0, 140}); // (walking: still facing the way it goes)
		assert(scene.actor(talker).dir == 1);
		// Stopped: standing where they are, and turning again.
		const Point was = scene.actor(talker).at;
		scene.stop(talker);
		scene.update(30);
		assert(!scene.actor(talker).moving && scene.actor(talker).at.x == was.x && scene.actor(talker).at.y == was.y);
		scene.face(talker, {0, 140});
		assert(scene.actor(talker).dir == 0);
		// Posed for a photo: the frame asked for, whatever time does; their
		// own way or pose where -1; let go, as they were.
		const uint32_t own = middle();
		scene.pose(talker, 2, 2, 1);
		assert(scene.actor(talker).posed && middle() == spriteColor(110));
		scene.update(kTalkTicks * 3);
		assert(middle() == spriteColor(110));
		scene.pose(talker, 1, 1, 0);
		assert(middle() == spriteColor(130));
		scene.pose(talker, 2, -1, 0); // (their own pose: standing)
		assert(middle() == spriteColor(30));
		scene.talk(talker, true);
		scene.pose(talker, 2, -1, 0); // (their own: talking)
		assert(middle() == spriteColor(100) || middle() == spriteColor(110));
		scene.talk(talker, false);
		scene.pose(talker, -1, 0, 0); // (their own way: none of its own there)
		assert(middle() == own);
		scene.unpose(talker);
		assert(!scene.actor(talker).posed && middle() == own && scene.actor(talker).dir == 0);
		scene.pose(-1, 2, 0, 0); scene.unpose(99); // (no one: nothing)
	}
	std::puts("PASS: facing a point, talking (talk frames in turn, standing where there are none), stopping and posing");

	// The camera: centred on the one followed, then still until they come
	// within a quarter of the screen of an edge, then scrolling to centre
	// them again; walking about the middle never moves it.
	const std::vector<uint8_t> wideData = sceneBytes(640, 144, std::vector<uint8_t>((size_t)640 * 144, 9), {box(0, 100, 640, 140)});
	Scene street;
	assert(street.load(wideData.data(), wideData.size(), 1.2, 320, 1280, 720, error) && street.view().width == 2560);
	const int walker = street.addActor(spriteData.data(), spriteData.size(), 1, 1.2, error);
	street.place(walker, {20, 120});
	street.follow(walker);
	assert(street.view().camera == 0);
	street.walkTo(walker, {620, 120});
	double scrolledAt = -1;
	for (int t = 0; t < 4000; ++t) {
		street.update(1);
		if (scrolledAt < 0 && street.view().camera) scrolledAt = street.actor(walker).at.x;
		assert(street.drawnRect(walker, x0, y0, x1, y1) && x0 > 0 && x1 < 1280); // (never off screen)
	}
	assert(scrolledAt > 240 && scrolledAt <= 250 && street.view().camera == 1280 && street.drawnRect(walker, x0, y0, x1, y1));
	street.place(walker, {300, 120});
	street.follow(walker);
	const int middle = street.view().camera;
	assert(middle == 300 * 4 - 640);
	street.walkTo(walker, {340, 120});
	for (int t = 0; t < 600; ++t) street.update(1);
	assert(street.view().camera == middle && near(street.actor(walker).at.x, 340));
	street.walkTo(walker, {20, 120}); // back to the left: scrolling the other way
	for (int t = 0; t < 4000; ++t) street.update(1);
	assert(street.view().camera == 0);
	street.lookAt(320); // (looking elsewhere: the camera stays while they walk)
	const int looked = street.view().camera;
	street.walkTo(walker, {100, 120});
	for (int t = 0; t < 600; ++t) street.update(1);
	assert(looked == 320 * 4 - 640 && street.view().camera == looked);
	street.setWalk(0, -1, 0); // (nonsense: the games' own pace)
	const int stroller = street.addActor(spriteData.data(), spriteData.size(), 1, 1.2, error);
	assert(street.actor(stroller).speedX == 8 && street.actor(stroller).speedY == 2 && street.actor(stroller).stepTicks == 1);
	assert(street.groupAt({50, 120}) == 0 && scene.groupAt({60, 120}) == scene.groupAt({250, 120}));
	street.place(walker, {0, 120});
	street.follow(walker);
	street.render(screen.data(), pitch); // (partly off the left edge: no left-facing stand, the left one)
	assert(street.view().camera == 0 && street.drawnRect(walker, x0, y0, x1, y1) && x0 == 0);
	assert(screen[(size_t)((y0 + y1) / 2) * pitch] == spriteColor(40));
	std::puts("PASS: walking (steps of 8 and 2, legs in step, facing, arrival; the camera at the edges)");

	// Doors and hotspots: the one under a tap beats one only near it, then
	// the smallest; only those asked about; none beyond the slack.
	World::SourceObject doorA, hotspot, doorB;
	doorA.id = 101; doorA.x = 100; doorA.y = 40; doorA.width = 20; doorA.height = 40; doorA.walkX = 110; doorA.walkY = 100;
	hotspot.id = 102; hotspot.x = 0; hotspot.y = 0; hotspot.width = 320; hotspot.height = 144;
	doorB.id = 103; doorB.x = 115; doorB.y = 40; doorB.width = 10; doorB.height = 10;
	const std::vector<uint8_t> doorData = sceneBytes(w, h, pixels, floor, {doorA, hotspot, doorB});
	Scene hall;
	assert(hall.load(doorData.data(), doorData.size(), 1.2, 320, 1280, 720, error) && hall.source().objects.size() == 3);
	const std::vector<int> all = {0, 1, 2}, doorOnly = {0}, doorAndHotspot = {0, 1};
	assert(hall.objectAt({110, 60}, all) == 0 && hall.objectAt({118, 45}, all) == 2);
	assert(hall.objectAt({98, 60}, doorAndHotspot) == 1 && hall.objectAt({98, 60}, doorOnly) == 0);
	assert(hall.objectAt({90, 60}, doorOnly) == -1 && hall.objectAt({110, 60}, std::vector<int>()) == -1 && hall.objectAt({110, 60}, {7}) == -1);
	// Only near: the nearest, though bigger; as near, the smaller; nothing
	// of no size.
	World::SourceObject big, small, flat, twin;
	big.id = 201; big.x = 10; big.y = 10; big.width = 40; big.height = 40;
	small.id = 202; small.x = 54; small.y = 20; small.width = 4; small.height = 4;
	flat.id = 203; flat.x = 52; flat.y = 20; flat.width = 0; flat.height = 10;
	twin.id = 204; twin.x = 10; twin.y = 10; twin.width = 40; twin.height = 40;
	const std::vector<uint8_t> nearData = sceneBytes(w, h, pixels, floor, {big, small, flat, twin});
	Scene porch;
	assert(porch.load(nearData.data(), nearData.size(), 1.2, 320, 1280, 720, error));
	assert(porch.objectAt({51, 21}, {0, 1, 2}) == 0 && porch.objectAt({52.5, 21}, {0, 1}) == 1);
	assert(porch.objectAt({30, 30}, {0, 3}) == 0 && porch.objectAt({30, 30}, {3, 0}) == 3); // (as big: the first)
	// (Two ways out drawn as one, each with its walk-to point: the one whose
	// point is nearer the tap, whichever comes first.)
	World::SourceObject westWay = twin, eastWay = twin;
	westWay.id = 205; westWay.walkX = 12; westWay.walkY = 48;
	eastWay.id = 206; eastWay.walkX = 48; eastWay.walkY = 48;
	const std::vector<uint8_t> twinData = sceneBytes(w, h, pixels, floor, {westWay, eastWay});
	Scene ways;
	assert(ways.load(twinData.data(), twinData.size(), 1.2, 320, 1280, 720, error));
	assert(ways.objectAt({45, 30}, {0, 1}) == 1 && ways.objectAt({45, 30}, {1, 0}) == 1 && ways.objectAt({15, 30}, {0, 1}) == 0 && ways.objectAt({15, 30}, {1, 0}) == 0);
	std::puts("PASS: doors (under before near, the smallest, only those asked; two drawn as one, by their walk-to points)");

	// The game's own connections ("SVW5") join boxes apart, walked across;
	// touching boxes still meet; a switched-off box stays out (in the middle
	// of the file: the connections name the file's boxes).
	{
		const std::vector<World::SourceBox> parts = {box(10, 100, 100, 140), box(0, 0, 5, 5, 0x80), box(120, 100, 200, 140), box(200, 100, 300, 140)};
		std::vector<uint8_t> next(16, 255);
		for (int i = 0; i < 4; ++i) next[i * 4 + i] = (uint8_t)i;
		next[0 * 4 + 2] = 2; next[2 * 4 + 0] = 0; // file boxes 0 and 2 joined (20 apart); 2 and 3 only touch
		const std::vector<uint8_t> data = scene5Bytes(w, h, pixels, parts, std::vector<World::SourceObject>(), next, std::vector<World::SourceCycle>());
		Scene joined;
		assert(joined.load(data.data(), data.size(), 1.2, 320, 1280, 720, error) && joined.boxes().size() == 3);
		assert(joined.boxes()[0].source == 0 && joined.boxes()[1].source == 2 && joined.boxes()[2].source == 3);
		assert(joined.groupAt({50, 120}) == joined.groupAt({150, 120}) && joined.groupAt({150, 120}) == joined.groupAt({250, 120}));
		const int walker5 = joined.addActor(spriteData.data(), spriteData.size(), 1, 1.2, error);
		joined.place(walker5, {50, 120});
		joined.walkTo(walker5, {150, 120});
		for (int t = 0; t < 2000; ++t) joined.update(1);
		assert(near(joined.actor(walker5).at.x, 150));
		joined.walkTo(walker5, {250, 120});
		for (int t = 0; t < 2000; ++t) joined.update(1);
		assert(near(joined.actor(walker5).at.x, 250));
		std::vector<uint8_t> wrong(next); // (naming the kept boxes instead would join 0 and 1 here, not 0 and 2)
		wrong[0 * 4 + 2] = 255; wrong[2 * 4 + 0] = 255; wrong[0 * 4 + 1] = 1; wrong[1 * 4 + 0] = 0;
		const std::vector<uint8_t> wrongData = scene5Bytes(w, h, pixels, parts, std::vector<World::SourceObject>(), wrong, std::vector<World::SourceCycle>());
		Scene unjoined;
		assert(unjoined.load(wrongData.data(), wrongData.size(), 1.2, 320, 1280, 720, error) && unjoined.groupAt({50, 120}) != unjoined.groupAt({150, 120}));
		const std::vector<uint8_t> apartData = sceneBytes(w, h, pixels, parts);
		Scene apart2;
		assert(apart2.load(apartData.data(), apartData.size(), 1.2, 320, 1280, 720, error) && apart2.groupAt({50, 120}) != apart2.groupAt({150, 120})); // (without them: apart)
	}
	std::puts("PASS: the game's own box connections (the file's boxes; joined apart; touching still meet)");

	// Colour cycles against the games' own code (palette.cpp): rotations
	// turn the palette a step at a time (doCyclePalette), the older games'
	// sweep maps each entry through a shadow palette; overlapping rotations
	// add up; a range ending at 255; at most a step an update.
	{
		auto rotate = [](uint32_t *palette, int first, int last, bool forward) { // (doCyclePalette)
			const int num = last - first;
			uint32_t tmp;
			if (forward) { tmp = palette[last]; std::memmove(palette + first + 1, palette + first, num * sizeof(uint32_t)); palette[first] = tmp; }
			else { tmp = palette[first]; std::memmove(palette + first, palette + first + 1, num * sizeof(uint32_t)); palette[last] = tmp; }
		};
		std::vector<uint8_t> strip(pixels);
		for (int x = 0; x < 64; ++x) for (int y = 0; y < 4; ++y) strip[(size_t)y * w + x] = (uint8_t)(192 + x); // 192..255 along the top
		auto shown = [&](Scene &target, int index) {
			target.render(screen.data(), pitch);
			const Point at = target.view().toScreen(index - 192 + 0.5, 1.5);
			return screen[(size_t)(int)at.y * pitch + (int)at.x];
		};
		const std::vector<World::SourceBox> two = {box(10, 100, 160, 140), box(160, 100, 310, 140)};
		std::vector<uint8_t> next(4, 255);
		next[0] = 0; next[3] = 1; next[1] = 1; next[2] = 0;
		World::SourceCycle rising, falling, top;
		rising.delay = 6; rising.first = 200; rising.last = 207; rising.mode = 0;  // up
		falling.delay = 4; falling.first = 204; falling.last = 215; falling.mode = 1;  // down, over rising's last four
		top.delay = 5; top.first = 240; top.last = 255; top.mode = 0;  // up to 255
		const std::vector<uint8_t> data = scene5Bytes(w, h, strip, two, std::vector<World::SourceObject>(), next, {rising, falling, top});
		Scene water;
		assert(water.load(data.data(), data.size(), 1.2, 320, 1280, 720, error));
		uint32_t palette[256];
		for (int i = 0; i < 256; ++i) palette[i] = sceneColor(i);
		int clockA = 0, clockB = 0, clockC = 0, version = 0;
		for (int tick = 1; tick <= 6 * 8 * 3; ++tick) { // (three times round a)
			water.update(1);
			if (++clockA >= rising.delay) { clockA = 0; rotate(palette, rising.first, rising.last, true); ++version; }
			if (++clockB >= falling.delay) { clockB = 0; rotate(palette, falling.first, falling.last, false); ++version; }
			if (++clockC >= top.delay) { clockC = 0; rotate(palette, top.first, top.last, true); ++version; }
			for (int i : {200, 203, 204, 207, 208, 215, 240, 255}) assert(shown(water, i) == palette[i]);
			assert(water.paletteVersion() == version);
		}
		water.update(100); // (a long wait: still a step each, not a jump)
		rotate(palette, rising.first, rising.last, true); rotate(palette, falling.first, falling.last, false); rotate(palette, top.first, top.last, true);
		for (int i : {200, 204, 215, 255}) assert(shown(water, i) == palette[i]);

		// The older games' sweep (cyclePalette's small-header branch):
		// counter from first to last and round; entry j shows the colour of
		// counter - (j - first), wrapped within the range.
		World::SourceCycle sweep;
		sweep.delay = 4; sweep.first = 220; sweep.last = 227; sweep.mode = 2;
		const std::vector<uint8_t> sweepData = scene5Bytes(w, h, strip, two, std::vector<World::SourceObject>(), next, {sweep});
		Scene flames;
		assert(flames.load(sweepData.data(), sweepData.size(), 1.2, 320, 1280, 720, error));
		for (int i = 220; i <= 227; ++i) assert(shown(flames, i) == sceneColor(i)); // (as drawn until the first frame)
		int counter = sweep.first;
		for (int frame = 1; frame <= 2 * 8 + 3; ++frame) {
			flames.update(4);
			if (++counter > sweep.last) counter = sweep.first;
			int value = counter;
			for (int j = sweep.first; j <= sweep.last; ++j) {
				assert(shown(flames, j) == sceneColor(value));
				if (--value < sweep.first) value = sweep.last;
			}
		}
	}
	std::puts("PASS: colour cycles against the games' own code (up, down, overlapping, to 255, the older sweep)");

	// An object's pictures: the render after showing one is the render of
	// the scene with that picture in it (one in the middle, one at the
	// scene's right and bottom edge); not past its pictures.
	{
		World::SourceObject chest, edge;
		chest.id = 301; chest.x = 100; chest.y = 40; chest.width = 21; chest.height = 30; chest.state = 1; chest.name = "chest"; chest.shown = 1;
		chest.pictureX = 100; chest.pictureY = 40; chest.pictureWidth = 21; chest.pictureHeight = 30;
		std::vector<uint8_t> shut(630), open(630);
		for (int i = 0; i < 630; ++i) { shut[i] = (uint8_t)(5 + i % 7); open[i] = (uint8_t)(70 + i % 11); }
		chest.pictures = {shut, open};
		edge.id = 302; edge.x = w - 13; edge.y = h - 9; edge.width = 13; edge.height = 9; edge.state = 1;
		edge.pictureX = w - 13; edge.pictureY = h - 9; edge.pictureWidth = 13; edge.pictureHeight = 9;
		edge.pictures = {std::vector<uint8_t>(117, 33), std::vector<uint8_t>(117, 44)};
		const std::vector<World::SourceBox> two = {box(10, 100, 160, 140), box(160, 100, 310, 140)};
		std::vector<uint8_t> next(4, 255);
		next[0] = 0; next[3] = 1; next[1] = 1; next[2] = 0;
		const std::vector<uint8_t> data = scene5Bytes(w, h, pixels, two, {chest, edge}, next, std::vector<World::SourceCycle>());
		auto pasted = [&](const World::SourceObject &o, int picture) {
			std::vector<uint8_t> copy(pixels);
			for (int y = 0; y < o.pictureHeight; ++y)
				for (int x = 0; x < o.pictureWidth; ++x) copy[(size_t)(o.pictureY + y) * w + o.pictureX + x] = o.pictures[picture][(size_t)y * o.pictureWidth + x];
			return copy;
		};
		for (const int screenWidth : {1280, 300}) { // (larger than the scene, and smaller)
			const int screenHeight = screenWidth == 1280 ? 720 : 140;
			std::vector<uint32_t> got((size_t)screenWidth * screenHeight), want((size_t)screenWidth * screenHeight);
			for (int o = 0; o < 2; ++o)
				for (int k = 0; k < 2; ++k) {
					const World::SourceObject &obj = o ? edge : chest;
					Scene room, reference;
					assert(room.load(data.data(), data.size(), 1.2, 320, screenWidth, screenHeight, error));
					assert(room.source().objects[0].shown == 1 && room.source().objects[1].shown == 0); // (the one the scene shows)
					const std::vector<uint8_t> refData = scene5Bytes(w, h, pasted(obj, k), two, {chest, edge}, next, std::vector<World::SourceCycle>());
					assert(reference.load(refData.data(), refData.size(), 1.2, 320, screenWidth, screenHeight, error));
					assert(room.showObject(o, k));
					room.render(got.data(), screenWidth);
					reference.render(want.data(), screenWidth);
					assert(got == want);
				}
		}
		Scene room;
		assert(room.load(data.data(), data.size(), 1.2, 320, 1280, 720, error) && room.source().objects[0].name == "chest");
		assert(!room.showObject(0, 2) && !room.showObject(2, 0) && !room.showObject(-1, 0));
		// (Looked at where it is: as the picture shown, until another is
		// drawn over it.)
		assert(room.showObject(0, 0) && room.looksAs(0, 0) && !room.looksAs(0, 1) && room.showObject(0, 1) && room.looksAs(0, 1) && !room.looksAs(0, 0));
		assert(!room.looksAs(0, 2) && !room.looksAs(2, 0) && !room.looksAs(-1, 0));
	}
	std::puts("PASS: object pictures (the render as with the picture in the scene; middle and edge; small and large screens)");

	// Objects drawn again as their game draws them (layObjects): a box under
	// a cover (the garage door over the car's trunk), its pictures without
	// the cover over it (as exported from version 23); the cover's taken
	// with the box shut. The cover drawn over the box opened, through its
	// hole the box as it is now; the cover away, the box opened, not the
	// box as under the cover's picture; one hidden (inside one shut) not
	// drawn; Sam & Max's order the other way; opaque, the whole picture;
	// nothing until one is shown.
	{
		const int w = 320, h = 200;
		std::vector<uint8_t> pixels((size_t)w * h, 1);
		World::SourceObject cover, box_;
		cover.id = 144; cover.x = 0; cover.y = 0; cover.width = 32; cover.height = 24; cover.state = 1; cover.name = "cover";
		cover.shown = 1; cover.pictureX = 0; cover.pictureY = 0; cover.pictureWidth = 32; cover.pictureHeight = 24;
		cover.pictures = {std::vector<uint8_t>(32 * 24, 1), std::vector<uint8_t>(32 * 24, 30)};
		for (int y = 10; y < 14; ++y) for (int x = 12; x < 16; ++x) cover.pictures[1][(size_t)y * 32 + x] = 1; // (its hole)
		box_ = cover; box_.id = 151; box_.name = "box"; box_.x = box_.pictureX = 8; box_.y = box_.pictureY = 8; box_.width = box_.pictureWidth = 16;
		box_.height = box_.pictureHeight = 16; box_.shown = 0;
		box_.pictures = {std::vector<uint8_t>(16 * 16, 1), std::vector<uint8_t>(16 * 16, 20)};
		for (int y = 0; y < 16; ++y) box_.pictures[1][(size_t)y * 16] = 1; // (its left column the place's own)
		for (int y = 0; y < 24; ++y) for (int x = 0; x < 32; ++x) pixels[(size_t)y * w + x] = cover.pictures[1][(size_t)y * 32 + x];
		const std::vector<uint8_t> data = scene5Bytes(w, h, pixels, {box(0, 100, 320, 190)}, {cover, box_}, {0}, {});
		Scene place;
		assert(place.load(data.data(), data.size(), 1.0, 320, 320, 200, error));
		std::vector<uint32_t> out((size_t)w * h);
		auto at = [&](int x, int y) { place.render(out.data(), w); return out[(size_t)y * w + x]; };
		place.layObjects({}, false, false);
		assert(at(4, 4) == sceneColor(30) && at(13, 11) == sceneColor(1) && at(40, 4) == sceneColor(1));
		// (Opened under the cover: its picture has no cover; drawn again over it.)
		assert(place.showObject(1, 1) && at(10, 10) == sceneColor(20)); // (the box's picture alone, no cover)
		place.layObjects({}, false, false);
		assert(at(10, 10) == sceneColor(30) && at(13, 11) == sceneColor(20) && at(4, 4) == sceneColor(30));
		// (The cover away: the box as it is now, not as under the cover's picture.)
		assert(place.showObject(0, 0) && at(13, 11) == sceneColor(1));
		place.layObjects({}, false, false);
		assert(at(10, 10) == sceneColor(20) && at(8, 10) == sceneColor(1) && at(4, 4) == sceneColor(1) && at(23, 23) == sceneColor(20));
		// (Hidden: not drawn; shut again: the place without either.)
		place.layObjects({false, true}, false, false);
		assert(at(10, 10) == sceneColor(1));
		place.layObjects({}, false, false);
		assert(at(10, 10) == sceneColor(20));
		assert(place.showObject(1, 0));
		place.layObjects({}, false, false);
		assert(at(10, 10) == sceneColor(1) && at(4, 4) == sceneColor(1));
		// (Sam & Max's order: the later on top.)
		assert(place.showObject(0, 1) && place.showObject(1, 1));
		place.layObjects({}, true, false);
		assert(at(10, 10) == sceneColor(20) && at(4, 4) == sceneColor(30) && at(8, 10) == sceneColor(30));
		place.layObjects({}, false, false);
		assert(at(10, 10) == sceneColor(30) && at(13, 11) == sceneColor(20));
		// (Opaque, as the oldest games' tiles: the cover's whole picture, no
		// hole where it matched what was under it.)
		place.layObjects({}, false, true);
		assert(at(10, 10) == sceneColor(30) && at(13, 11) == sceneColor(1));
		// (A new place: nothing until one is shown or hidden.)
		assert(place.load(data.data(), data.size(), 1.0, 320, 320, 200, error));
		place.layObjects({}, false, false);
		assert(at(4, 4) == sceneColor(30) && at(13, 11) == sceneColor(1));
	}
	std::puts("PASS: objects drawn again in their game's order (over what is under them as it is now; hidden; the other order; opaque; nothing until shown)");

	// Spots for people: inside the boxes, spread out.
	for (int n : {1, 4, 12}) {
		const std::vector<Point> spots = scene.spots(n);
		assert((int)spots.size() == n);
		for (const Point &p : spots) assert(inSomeBox(scene.boxes(), p));
		for (int i = 0; i < n && n <= 4; ++i)
			for (int j = i + 1; j < n; ++j) assert(std::hypot(spots[i].x - spots[j].x, spots[i].y - spots[j].y) > 30);
	}
	assert(scene.spots(0).empty());
	// Only where the picture is (not beside it, below it or at its very
	// top), on boxes with room to stand (not a line or a point), where
	// there are such; in a group asked, its boxes only; a group's boxes
	// counted, its nearest point.
	{
		std::vector<World::SourceBox> edges = {box(10, 100, 160, 140), box(300, 100, 400, 140), box(200, 0, 260, 4), box(60, 60, 60, 60),
			box(200, 140, 260, 180), box(260, 20, 300, 40)};
		const std::vector<uint8_t> edgeData = sceneBytes(w, h, pixels, edges);
		Scene edge;
		assert(edge.load(edgeData.data(), edgeData.size(), 1.2, 320, 1280, 720, error) && edge.boxes().size() == 6);
		for (int n : {1, 6, 24}) {
			const std::vector<Point> spots = edge.spots(n);
			assert((int)spots.size() == n);
			for (const Point &p : spots) {
				assert(inSomeBox(edge.boxes(), p) && p.x >= 0 && p.x < w && p.y >= h / 25.0 && p.y <= h);
				assert(!(near(p.x, 60) && near(p.y, 60)));
			}
		}
		const int lone = edge.groupAt({280, 30}), floorGroup = edge.groupAt({50, 120});
		assert(lone >= 0 && floorGroup >= 0 && lone != floorGroup && edge.groupSize(lone) == 1 && edge.groupSize(-5) == 0);
		for (const Point &p : edge.spots(6, floorGroup)) assert(edge.groupAt(p) == floorGroup);
		for (const Point &p : edge.spots(6, lone)) assert(edge.groupAt(p) == lone);
		Point c;
		assert(edge.closestIn(floorGroup, {200, 120}, c) && near(c.x, 160) && near(c.y, 120) && !edge.closestIn(99, {0, 0}, c));
		// (Nothing in the picture: as found.)
		std::vector<World::SourceBox> outside = {box(330, 100, 400, 140)};
		const std::vector<uint8_t> outsideData = sceneBytes(w, h, pixels, outside);
		Scene off;
		assert(off.load(outsideData.data(), outsideData.size(), 1.2, 320, 1280, 720, error) && off.spots(3).size() == 3 && inSomeBox(off.boxes(), off.spots(1)[0]));
	}
	std::puts("PASS: spots (in the boxes, spread out; in the picture, room to stand, in a group asked)");

	// A second picture of the place (The Dig's tram car parked): only where
	// it differs, shown, slid out of view, half slid, dissolved; the scene's
	// own colours (a colour the scene lacks: its nearest); not the same size,
	// or no difference, refused. Someone hidden is not drawn.
	{
		std::vector<uint8_t> plain((size_t)320 * 200, 9), parked = plain;
		for (int y = 40; y < 60; ++y) for (int x = 100; x < 140; ++x) parked[(size_t)y * 320 + x] = 12;
		const std::vector<uint8_t> plainData = sceneBytes(320, 200, plain, {box(0, 100, 320, 190)});
		std::vector<uint8_t> parkedData = sceneBytes(320, 200, parked, {box(0, 100, 320, 190)});
		Scene place;
		assert(place.load(plainData.data(), plainData.size(), 1.0, 320, 320, 200, error));
		std::vector<uint32_t> out((size_t)320 * 200);
		auto at = [&](int x, int y) { place.render(out.data(), 320); return out[(size_t)y * 320 + x]; };
		assert(at(120, 50) == sceneColor(9));
		const std::vector<uint8_t> smaller = sceneBytes(160, 200, std::vector<uint8_t>((size_t)160 * 200, 12), {});
		assert(!place.mountPicture(smaller.data(), smaller.size(), error) && !place.pictureMounted());
		assert(!place.mountPicture(plainData.data(), plainData.size(), error)); // (nothing differs)
		assert(place.mountPicture(parkedData.data(), parkedData.size(), error) && place.pictureMounted() && place.pictureWidth() == 40);
		assert(at(120, 50) == sceneColor(9)); // (not shown yet)
		place.showPicture(0, 256);
		assert(at(100, 40) == sceneColor(12) && at(139, 59) == sceneColor(12) && at(99, 50) == sceneColor(9) && at(140, 50) == sceneColor(9));
		place.showPicture(40, 256); // (slid out of its rectangle: hidden)
		assert(at(120, 50) == sceneColor(9) && at(139, 59) == sceneColor(9));
		place.showPicture(20, 256); // (half: in from the left of its rectangle)
		assert(at(110, 50) == sceneColor(9) && at(130, 50) == sceneColor(12));
		place.showPicture(0, 0);
		assert(at(120, 50) == sceneColor(9));
		place.showPicture(0, 128);
		int shownHalf = 0, rowsShown = 0;
		for (int y = 40; y < 60; ++y) {
			int inRow = 0;
			for (int x = 100; x < 140; ++x) inRow += at(x, y) == sceneColor(12);
			shownHalf += inRow;
			rowsShown += inRow > 0 && inRow < 40;
		}
		int columnsMixed = 0;
		for (int x = 100; x < 140; ++x) {
			int inColumn = 0;
			for (int y = 40; y < 60; ++y) inColumn += at(x, y) == sceneColor(12);
			columnsMixed += inColumn > 0 && inColumn < 20;
		}
		// (Scattered, not in stripes either way: about half, every row and
		// nearly every column part shown.)
		assert(shownHalf > 800 * 3 / 10 && shownHalf < 800 * 7 / 10 && rowsShown == 20 && columnsMixed >= 36);
		// (A colour the scene lacks: its nearest of the scene's. The car's 12 is
		// the scene's 40 exactly; the rest a little off.)
		for (int c = 0; c < 256; ++c) {
			parkedData[12 + c * 3] = (uint8_t)c; parkedData[12 + c * 3 + 1] = (uint8_t)(255 - c); parkedData[12 + c * 3 + 2] = (uint8_t)(c / 2 ^ 1);
		}
		parkedData[12 + 12 * 3] = 40; parkedData[12 + 12 * 3 + 1] = 215; parkedData[12 + 12 * 3 + 2] = 20;
		assert(place.mountPicture(parkedData.data(), parkedData.size(), error));
		place.showPicture(0, 256);
		assert(at(120, 50) == sceneColor(40) && at(99, 50) == sceneColor(9));
		// A new place: no picture.
		assert(place.load(plainData.data(), plainData.size(), 1.0, 320, 320, 200, error) && !place.pictureMounted());
		// An object shown in another picture under the car's rectangle: the
		// place under it as the object is now, the car still over it.
		{
			World::SourceObject lamp;
			lamp.id = 7; lamp.x = 90; lamp.y = 30; lamp.width = 20; lamp.height = 10; lamp.walkX = 100; lamp.walkY = 120; lamp.state = 0;
			lamp.name = "lamp"; lamp.shown = 0; lamp.pictureX = 90; lamp.pictureY = 30; lamp.pictureWidth = 20; lamp.pictureHeight = 20;
			lamp.pictures = {std::vector<uint8_t>(400, 9), std::vector<uint8_t>(400, 77)};
			const std::vector<uint8_t> lit = scene5Bytes(320, 200, plain, {box(0, 100, 320, 190)}, {lamp}, {0}, {});
			std::vector<uint8_t> litParked = parked;
			const std::vector<uint8_t> litCar = scene5Bytes(320, 200, litParked, {box(0, 100, 320, 190)}, {lamp}, {0}, {});
			assert(place.load(lit.data(), lit.size(), 1.0, 320, 320, 200, error));
			assert(place.mountPicture(litCar.data(), litCar.size(), error));
			place.showPicture(0, 256);
			assert(place.showObject(0, 1));
			assert(at(95, 35) == sceneColor(77) && at(105, 45) == sceneColor(12)); // (the lamp outside the car, the car over it)
			place.showPicture(40, 256); // (the car gone: the lamp lit where it was)
			assert(at(105, 45) == sceneColor(77) && at(120, 50) == sceneColor(9));
			place.showPicture(0, 256);
			assert(place.showObject(0, 0)); // (out again under the car)
			place.showPicture(40, 256);
			assert(at(105, 45) == sceneColor(9));
		}
		assert(place.load(plainData.data(), plainData.size(), 1.0, 320, 320, 200, error));
		// Someone hidden: not drawn, no rectangle; shown again.
		const std::vector<uint8_t> rider = spriteBytes({{2, 0, 0, -10, -40, 20, 40, 30}});
		const int n = place.addActor(rider.data(), rider.size(), 1, 1.0, error);
		place.place(n, {160, 150});
		int a0, b0, a1, b1;
		assert(place.drawnRect(n, a0, b0, a1, b1));
		place.hide(n, true);
		assert(!place.drawnRect(n, a0, b0, a1, b1) && at(160, 140) == sceneColor(9));
		place.hide(n, false);
		assert(place.drawnRect(n, a0, b0, a1, b1));
	}
	std::puts("PASS: a second picture of the place (shown, slid, dissolved, its nearest colours; refused when not the same size or the same); someone hidden");
	// A prop (the Shuttle Bug parked): in its own colours (none where it is
	// left out), as tall as asked at full scale and smaller where people are
	// smaller, its pixels as much taller than wide as asked, on its bottom
	// centre; in front of those further, behind the nearer, in front of no
	// one on its row; its rectangle; gone with a new place.
	{
		const std::vector<uint8_t> plain(320 * 200, 9);
		const std::vector<uint8_t> d = sceneBytes(320, 200, plain, {box(0, 100, 320, 190, 0, 128, 255)});
		Scene place;
		assert(place.load(d.data(), d.size(), 1.0, 320, 320, 200, error));
		std::vector<uint32_t> shown(320 * 200);
		auto at = [&](int x, int y) { place.render(shown.data(), 320); return shown[(size_t)y * 320 + x]; };
		uint8_t palette[768];
		for (int c = 0; c < 256; ++c) { palette[c * 3] = (uint8_t)(255 - c); palette[c * 3 + 1] = 0; palette[c * 3 + 2] = (uint8_t)c; }
		auto propColor = [](int c) { return 0xFF000000u | (uint32_t)(255 - c) << 16 | (uint32_t)c; };
		std::vector<uint8_t> van(20 * 10, 5);
		for (int y = 0; y < 10; ++y) van[y * 20] = 255; // (its left column left out)
		assert(place.addProp(van.data(), 0, 10, 255, palette, {160, 190}, 40, 2.0) < 0);
		const std::vector<uint8_t> none(20 * 10, 255);
		assert(place.addProp(none.data(), 20, 10, 255, palette, {160, 190}, 40, 2.0) < 0 && place.propCount() == 0);
		const int p = place.addProp(van.data(), 20, 10, 255, palette, {160, 190}, 40, 2.0);
		assert(p == 0 && place.propCount() == 1);
		assert(place.propRect(p, x0, y0, x1, y1) && x0 == 140 && x1 == 180 && y0 == 150 && y1 == 190);
		assert(at(141, 170) == sceneColor(9) && at(150, 170) == propColor(5) && at(150, 149) == sceneColor(9));
		// (Hit where drawn, not where left out, nor outside it.)
		assert(place.propHit(p, 150, 170) && !place.propHit(p, 141, 170) && !place.propHit(p, 150, 149) && !place.propHit(p, 181, 170) && !place.propHit(5, 150, 170));
		assert(near(place.depthAt({160, 190}), 1) && near(place.depthAt({160, 100}), 128 / 255.0));
		// (Further back, smaller: 40 rows at full scale, about 30 halfway.)
		const int q = place.addProp(van.data(), 20, 10, 255, palette, {60, 145}, 40, 2.0);
		assert(q == 1 && place.propRect(q, x0, y0, x1, y1) && y1 == 145 && std::abs((y1 - y0) - 30) <= 1);
		// Someone further than the van: behind it; on its row: in front.
		const std::vector<uint8_t> passer = spriteBytes({{2, 0, 0, -10, -40, 20, 40, 30}});
		const int n = place.addActor(passer.data(), passer.size(), 1, 1.0, error);
		place.place(n, {160, 175});
		assert(at(160, 160) == propColor(5));
		place.place(n, {160, 190});
		assert(at(160, 175) == spriteColor(30));
		// (Off screen: no rectangle.)
		const int far = place.addProp(van.data(), 20, 10, 255, palette, {-200, 190}, 40, 2.0);
		assert(far == 2 && !place.propRect(far, x0, y0, x1, y1) && !place.propRect(3, x0, y0, x1, y1));
		// The lights off: the place and the props black, the passer all in the
		// dark grey (or the colour asked), the rest as before; on again, as
		// before; lit again with a new place.
		place.setDark(true);
		assert(place.dark() && at(10, 10) == 0xFF000000u && at(145, 185) == 0xFF000000u && at(160, 175) == Scene::kDarkColor && at(175, 189) == 0xFF000000u);
		assert(place.drawnRect(n, x0, y0, x1, y1) && place.propRect(p, x0, y0, x1, y1));
		place.setDark(true, 0xFF102030u);
		assert(at(160, 175) == 0xFF102030u);
		place.setDark(false);
		assert(!place.dark() && at(10, 10) == sceneColor(9) && at(160, 175) == spriteColor(30) && at(145, 185) == propColor(5));
		place.setDark(true);
		assert(place.load(d.data(), d.size(), 1.0, 320, 320, 200, error) && place.propCount() == 0 && !place.dark() && at(10, 10) == sceneColor(9));
		// A flashlight in the dark: the place in 48 x 32 round the point (its
		// left on a multiple of 8, its top of 2), its corners rounded, the
		// rest black; kept inside the place; off, all dark; gone with a new
		// place.
		place.setDark(true);
		place.setFlashlight(true, {101, 61});
		int bx, by, bw, bh;
		assert(place.flashlight(bx, by, bw, bh) && bx == 72 && by == 44 && bw == 48 && bh == 32);
		assert(at(90, 60) == sceneColor(9) && at(71, 60) == 0xFF000000u && at(120, 60) == 0xFF000000u && at(90, 43) == 0xFF000000u && at(90, 76) == 0xFF000000u);
		assert(at(72, 60) == sceneColor(9) && at(119, 75 - 4) == sceneColor(9) && at(72, 44) == 0xFF000000u && at(73, 45) == 0xFF000000u && at(76, 48) == sceneColor(9));
		place.setFlashlight(true, {2, 199});
		assert(place.flashlight(bx, by, bw, bh) && bx == 0 && by == 200 - 32);
		place.setFlashlight(false);
		assert(!place.flashlight(bx, by, bw, bh) && at(10, 190) == 0xFF000000u);
		place.setFlashlight(true, {101, 61});
		assert(place.load(d.data(), d.size(), 1.0, 320, 320, 200, error) && !place.flashlight(bx, by, bw, bh));
	}
	std::puts("PASS: a prop among the people (its colours, size, depth, order, rectangle, where it is hit; gone with the place)");
	// (From 0198) A piece of the place's own picture as a prop (a plane
	// seat's front over the one sitting in it): the pixels where it was cut,
	// drawn pixel for pixel where asked; in front of those whose feet are
	// above its bottom row (or the row asked), behind those below it;
	// refused outside the place. Someone seated stays exactly where asked,
	// not moved into the walk boxes as someone placed is.
	{
		std::vector<uint8_t> picture(320 * 200, 9);
		for (int y = 120; y < 160; ++y) for (int x = 40; x < 80; ++x) picture[y * 320 + x] = (uint8_t)(20 + (x - 40) / 10); // (a striped seat front)
		const std::vector<uint8_t> d = sceneBytes(320, 200, picture, {box(0, 160, 320, 190)});
		Scene place;
		assert(place.load(d.data(), d.size(), 1.0, 320, 320, 200, error));
		std::vector<uint32_t> shown(320 * 200);
		auto at = [&](int x, int y) { place.render(shown.data(), 320); return shown[(size_t)y * 320 + x]; };
		assert(place.addPiece(-1, 0, 10, 10, 0, 0) < 0 && place.addPiece(315, 0, 10, 10, 0, 0) < 0 && place.addPiece(0, 0, 10, 10, 0, 195) < 0 &&
			place.addPiece(0, 0, 0, 10, 0, 0) < 0 && place.addPiece(0, 0, 10, 10, -1, 0) < 0 && place.propCount() == 0);
		const int front = place.addPiece(40, 120, 40, 40, 200, 120);
		assert(front == 0 && place.propRect(front, x0, y0, x1, y1) && x0 == 200 && x1 == 240 && y0 == 120 && y1 == 160);
		assert(at(205, 130) == sceneColor(20) && at(235, 150) == sceneColor(23) && at(199, 130) == sceneColor(9) && at(45, 130) == sceneColor(20));
		const std::vector<uint8_t> sitter = spriteBytes({{2, 0, 0, -10, -60, 20, 60, 30}});
		const int n = place.addActor(sitter.data(), sitter.size(), 1, 1.0, error);
		place.place(n, {220, 150});
		assert(place.actor(n).at.y == 160);
		place.seat(n, {220, 150});
		assert(place.actor(n).at.x == 220 && place.actor(n).at.y == 150 && !place.actor(n).moving);
		// (Behind it: their top over the picture above it, the rest behind.)
		assert(at(220, 100) == spriteColor(30) && at(220, 130) == sceneColor(22) && at(220, 149) == sceneColor(22));
		// (Below its row: in front of it.)
		place.seat(n, {220, 170});
		assert(at(220, 130) == spriteColor(30));
		// A piece drawn among the people by another row: behind one whose
		// feet are below that row though above its bottom.
		const int low = place.addPiece(40, 120, 40, 40, 100, 120, 140);
		assert(low == 1 && at(105, 130) == sceneColor(20));
		place.seat(n, {120, 150});
		assert(at(120, 130) == spriteColor(30));
		place.seat(n, {120, 130});
		assert(at(120, 125) == sceneColor(22));
		// Made smaller (too big for a seat): drawn half as tall, as wide.
		place.seat(n, {220, 150});
		int h0, h1, w0, w1;
		assert(place.drawnRect(n, w0, h0, w1, h1) && h1 - h0 == 60 && w1 - w0 == 20);
		place.resize(n, 0.5);
		assert(place.drawnRect(n, w0, h0, w1, h1) && h1 - h0 == 30 && w1 - w0 == 10 && h1 == 150);
		place.resize(n, 0);
		assert(place.drawnRect(n, w0, h0, w1, h1) && h1 - h0 == 30);
		// (Fitted to a seat: twice as tall, four times as wide.)
		place.resize(n, 2, 4);
		assert(place.drawnRect(n, w0, h0, w1, h1) && h1 - h0 == 60 && w1 - w0 == 40 && h1 == 150);
	}
	std::puts("PASS: a piece of the place's picture among the people (where it is cut and drawn, in front of those behind it, by the row asked; refused outside); someone seated exactly where asked, made smaller, fitted (taller, wider)");
	std::puts("PASS: the lights off (the place and props black, everyone in one colour; on again; lit in a new place); a flashlight in the dark (its rectangle, rounded, kept inside, off, gone with the place)");
	// Something lit (Sith Ewok 2's saber): lighting it up, its ignite frames
	// in turn while standing (8 ticks each), then its lit poses (standing,
	// walking); putting it out, the ignite frames backwards, then its own;
	// at once when not played; walking ends the frames. Those without
	// ignite frames light nothing. A glow's light is added to what is behind
	// it (in the dark too); a lit blade shows in the dark.
	{
		const std::vector<uint8_t> plain(320 * 200, 9);
		const std::vector<uint8_t> d = sceneBytes(320, 200, plain, {box(0, 100, 320, 190)});
		Scene place;
		assert(place.load(d.data(), d.size(), 1.0, 320, 320, 200, error));
		std::vector<uint32_t> shown(320 * 200);
		auto at = [&](int x, int y) { place.render(shown.data(), 320); return shown[(size_t)y * 320 + x]; };
		std::vector<Frame> frames = {{2, World::kGuestStand, 0, -10, -40, 20, 40, 30}, {2, World::kGuestWalk, 0, -10, -40, 20, 40, 31},
			{2, World::kGuestLitStand, 0, -10, -40, 20, 40, 50}, {2, World::kGuestLitWalk, 0, -10, -40, 20, 40, 51}, {0, World::kGuestWalk, 0, -10, -40, 20, 40, 32}};
		for (int i = 0; i < 3; ++i) frames.push_back({2, World::kGuestIgnite, i, -10, -40, 20, 40, (uint8_t)(40 + i)});
		std::vector<uint8_t> bytes = spriteBytes(frames);
		// (The lit standing frame's top rows a glow, (50, 50, 205) added; the
		// next rows a lit blade. Lit walking, facing the viewer only: so
		// walking either way.)
		size_t lit = 4 + 4 + 768;
		for (int f = 0; f < 2; ++f) lit += 12 + 2 * 20 * 40;
		for (int i = 0; i < 20 * 5; ++i) bytes[lit + 12 + 20 * 40 + 20 + i] = 2;
		for (int i = 0; i < 20 * 5; ++i) bytes[lit + 12 + 20 * 40 + 20 * 6 + i] = 3;
		const std::vector<uint8_t> plainOne = spriteBytes({{2, 0, 0, -10, -40, 20, 40, 30}});
		const int n = place.addActor(bytes.data(), bytes.size(), 1, 1.0, error), other = place.addActor(plainOne.data(), plainOne.size(), 1, 1.0, error);
		place.place(n, {160, 180}); place.place(other, {40, 180});
		assert(place.canLight(n) && !place.canLight(other) && !place.light(other, true) && !place.canLight(7));
		assert(place.shownKind(n) == World::kGuestStand && !place.actor(n).lit);
		assert(place.light(n, true) && place.actor(n).lit && place.shownKind(n) == World::kGuestIgnite && at(160, 170) == spriteColor(40));
		place.update(kIgniteTicks); assert(at(160, 170) == spriteColor(41));
		place.update(kIgniteTicks); assert(at(160, 170) == spriteColor(42));
		place.update(kIgniteTicks); assert(place.shownKind(n) == World::kGuestLitStand && at(160, 170) == spriteColor(50));
		// (The glow over the place's colour 9, (9, 246, 4): (59, 255, 209); the
		// blade as drawn.)
		assert(at(160, 142) == 0xFF000000u + (59u << 16) + (255u << 8) + 209u && at(160, 147) == spriteColor(50));
		assert(place.light(n, true) && place.shownKind(n) == World::kGuestLitStand); // (lit already)
		place.walkTo(n, {260, 180}); place.update(1);
		assert(place.shownKind(n) == World::kGuestLitWalk && at((int)place.actor(n).at.x, 170) == spriteColor(51));
		place.stop(n);
		assert(place.light(n, false) && !place.actor(n).lit && place.shownKind(n) == World::kGuestIgnite);
		const int x = (int)place.actor(n).at.x;
		assert(at(x, 170) == spriteColor(42));
		place.update(kIgniteTicks); assert(at(x, 170) == spriteColor(41));
		place.walkTo(n, {60, 180}); place.update(1);
		assert(place.actor(n).switching == 0 && place.shownKind(n) == World::kGuestWalk && at((int)place.actor(n).at.x, 170) == spriteColor(32));
		place.stop(n);
		assert(place.shownKind(n) == World::kGuestStand);
		assert(place.light(n, true, false) && place.shownKind(n) == World::kGuestLitStand);
		// (Turned back halfway: from the frame shown, the other way; lit
		// talking with no frames of its own, as lit standing.)
		assert(place.light(n, false, false) && place.light(n, true));
		place.update(kIgniteTicks);
		assert(at(x0n(place, n), 170) == spriteColor(41) && place.light(n, false) && at(x0n(place, n), 170) == spriteColor(41));
		place.update(kIgniteTicks); assert(at(x0n(place, n), 170) == spriteColor(40));
		place.update(kIgniteTicks); assert(place.shownKind(n) == World::kGuestStand && place.actor(n).switching == 0);
		assert(place.light(n, true));
		place.update(2 * kIgniteTicks); assert(at(x0n(place, n), 170) == spriteColor(42) && place.light(n, false) && at(x0n(place, n), 170) == spriteColor(42));
		place.update(kIgniteTicks); assert(at(x0n(place, n), 170) == spriteColor(41) && place.light(n, true) && at(x0n(place, n), 170) == spriteColor(41));
		place.update(2 * kIgniteTicks); assert(place.shownKind(n) == World::kGuestLitStand);
		place.talk(n, true); assert(place.shownKind(n) == World::kGuestLitStand && at(x0n(place, n), 170) == spriteColor(50));
		place.talk(n, false);
		// (In the dark: the glow added to black, the blade as drawn, the rest
		// dark.)
		place.setDark(true);
		const int y = (int)place.actor(n).at.y, cx = (int)place.actor(n).at.x;
		assert(at(cx, y - 38) == 0xFF000000u + (50u << 16) + (50u << 8) + 205u && at(cx, y - 33) == spriteColor(50) && at(cx, y - 10) == Scene::kDarkColor);
		place.setDark(false);
	}
	// (From 0200) Taken up first and put away after (Sith Ewok 3: a force
	// grab, then the ignite frames from their second; the ignite frames back
	// to their second, then stowed), seen from the side; not turned back
	// halfway. Moves (a swing lit, force lightning): their frames in turn
	// standing, the lightning's last ones but the first again till its
	// time; walking ends them; a walk ends for one; seen from the side when
	// facing the viewer; none for those without frames for them. Posed lit
	// and seated: seated (no move or grab frame).
	{
		const std::vector<uint8_t> plain(320 * 200, 9);
		const std::vector<uint8_t> d = sceneBytes(320, 200, plain, {box(0, 100, 320, 190)});
		Scene place;
		assert(place.load(d.data(), d.size(), 1.0, 320, 320, 200, error));
		std::vector<uint32_t> shown(320 * 200);
		auto at = [&](int x, int y) { place.render(shown.data(), 320); return shown[(size_t)y * 320 + x]; };
		auto colour = [&](int n) { return at(x0n(place, n), (int)place.actor(n).at.y - 10); };
		std::vector<Frame> frames = {{1, World::kGuestStand, 0, -10, -40, 20, 40, 30}, {2, World::kGuestStand, 0, -10, -40, 20, 40, 29},
			{1, World::kGuestWalk, 0, -10, -40, 20, 40, 31}, {1, World::kGuestLitStand, 0, -10, -40, 20, 40, 50}, {1, World::kGuestLitWalk, 0, -10, -40, 20, 40, 51}};
		for (int i = 0; i < 3; ++i) frames.push_back({1, World::kGuestIgnite, i, -10, -40, 20, 40, (uint8_t)(40 + i)});
		for (int i = 0; i < 2; ++i) frames.push_back({1, World::kGuestGrab, i, -10, -40, 20, 40, (uint8_t)(60 + i)});
		for (int i = 0; i < 2; ++i) frames.push_back({1, World::kGuestStow, i, -10, -40, 20, 40, (uint8_t)(70 + i)});
		for (int i = 0; i < 3; ++i) frames.push_back({1, World::kGuestSwing, i, -10, -40, 20, 40, (uint8_t)(80 + i)});
		for (int i = 0; i < 3; ++i) frames.push_back({1, World::kGuestZap, i, -10, -40, 20, 40, (uint8_t)(90 + i)});
		for (int i = 0; i < 2; ++i) frames.push_back({1, World::kGuestLitZap, i, -10, -40, 20, 40, (uint8_t)(95 + i)});
		const std::vector<uint8_t> bytes = spriteBytes(frames), plainOne = spriteBytes({{2, 0, 0, -10, -40, 20, 40, 33}});
		const int n = place.addActor(bytes.data(), bytes.size(), 1, 1.0, error), other = place.addActor(plainOne.data(), plainOne.size(), 1, 1.0, error);
		place.place(n, {160, 180}); place.place(other, {40, 180});
		assert(place.actor(n).dir == World::kGuestFront && colour(n) == spriteColor(29));
		// Taken up: from the front, seen from the side; grabbed, then lit from
		// the ignite frames' second.
		assert(place.light(n, true) && place.actor(n).dir == World::kGuestRight && place.shownKind(n) == World::kGuestGrab && colour(n) == spriteColor(60));
		assert(!place.light(n, false) && place.actor(n).lit); // (not turned back halfway)
		place.update(kIgniteTicks); assert(colour(n) == spriteColor(61));
		place.update(kIgniteTicks); assert(place.shownKind(n) == World::kGuestIgnite && colour(n) == spriteColor(41));
		place.update(kIgniteTicks); assert(colour(n) == spriteColor(42));
		place.update(kIgniteTicks); assert(place.shownKind(n) == World::kGuestLitStand && colour(n) == spriteColor(50) && place.actor(n).switching == 0);
		// A swing: its frames in turn, then lit standing again.
		assert(place.canAct(n, World::kGuestSwing) && !place.canAct(other, World::kGuestSwing) && !place.canAct(n, World::kGuestIgnite) && !place.canAct(9, World::kGuestSwing));
		assert(!place.act(other, World::kGuestZap) && !place.acting(other));
		assert(place.act(n, World::kGuestSwing) && place.acting(n) && place.shownKind(n) == World::kGuestSwing && colour(n) == spriteColor(80));
		place.update(kActTicks); assert(colour(n) == spriteColor(81));
		place.update(kActTicks); assert(colour(n) == spriteColor(82));
		place.update(kActTicks); assert(!place.acting(n) && place.shownKind(n) == World::kGuestLitStand);
		// Lightning lit: its two frames, the last again till its time.
		assert(place.act(n, World::kGuestLitZap, 4 * kActTicks) && colour(n) == spriteColor(95));
		place.update(kActTicks); assert(colour(n) == spriteColor(96));
		place.update(kActTicks); assert(colour(n) == spriteColor(96));
		place.update(2 * kActTicks); assert(!place.acting(n) && place.shownKind(n) == World::kGuestLitStand);
		// Put away: the ignite frames back to their second, then stowed.
		assert(place.light(n, false) && colour(n) == spriteColor(42));
		place.update(kIgniteTicks); assert(colour(n) == spriteColor(41));
		place.update(kIgniteTicks); assert(place.shownKind(n) == World::kGuestStow && colour(n) == spriteColor(70));
		place.update(kIgniteTicks); assert(colour(n) == spriteColor(71));
		place.update(kIgniteTicks); assert(place.shownKind(n) == World::kGuestStand && colour(n) == spriteColor(30) && !place.actor(n).lit);
		// Lightning without it: the wind-up, then the rest in a loop.
		assert(place.act(n, World::kGuestZap, 6 * kActTicks) && colour(n) == spriteColor(90));
		place.update(kActTicks); assert(colour(n) == spriteColor(91));
		place.update(kActTicks); assert(colour(n) == spriteColor(92));
		place.update(kActTicks); assert(colour(n) == spriteColor(91));
		place.update(kActTicks); assert(colour(n) == spriteColor(92));
		place.update(2 * kActTicks); assert(!place.acting(n) && place.shownKind(n) == World::kGuestStand);
		// Walking ends a move; a move ends a walk.
		assert(place.act(n, World::kGuestZap, 100));
		place.walkTo(n, {60, 180}); place.update(1);
		assert(!place.acting(n) && place.actor(n).moving && place.shownKind(n) != World::kGuestZap);
		assert(place.act(n, World::kGuestZap, 100) && !place.actor(n).moving && place.acting(n));
		place.update(200); assert(!place.acting(n));
		// (A move facing the viewer: from the side, the last one faced.)
		place.face(n, {160, 250});
		assert(place.actor(n).dir == World::kGuestFront && place.act(n, World::kGuestZap) && place.actor(n).dir == World::kGuestLeft);
		place.update(100);
		// (Lit at once, not played: not turned to a side.)
		place.face(n, {160, 250});
		assert(place.light(n, true, false) && place.actor(n).dir == World::kGuestFront && place.light(n, false, false));
		// (Posed lit and seated: seated, else standing; never a grab.)
		assert(place.light(n, true, false));
		place.pose(n, World::kGuestRight, World::kGuestSeated, 0);
		assert(place.shownKind(n) != World::kGuestGrab && place.shownKind(n) != World::kGuestStow);
		place.unpose(n);
	}
	// (Not turned during a move, a grab or a stow (a talker faced); posed
	// facing the viewer in its own pose meanwhile (a photo): still seen from
	// the side last faced, not the other side's frames nor the front's
	// ignite frames.)
	{
		const std::vector<uint8_t> plain(320 * 200, 9);
		const std::vector<uint8_t> d = sceneBytes(320, 200, plain, {box(0, 100, 320, 190)});
		Scene place;
		assert(place.load(d.data(), d.size(), 1.0, 320, 320, 200, error));
		std::vector<uint32_t> shown(320 * 200);
		auto colour = [&](int n) { place.render(shown.data(), 320); return shown[(size_t)((int)place.actor(n).at.y - 10) * 320 + x0n(place, n)]; };
		std::vector<Frame> frames;
		for (int dir = 0; dir < 3; ++dir) {
			frames.push_back({dir, World::kGuestStand, 0, -10, -40, 20, 40, (uint8_t)(10 + dir)});
			frames.push_back({dir, World::kGuestLitStand, 0, -10, -40, 20, 40, (uint8_t)(20 + dir)});
			for (int i = 0; i < 2; ++i) frames.push_back({dir, World::kGuestIgnite, i, -10, -40, 20, 40, (uint8_t)(30 + dir * 2 + i)});
		}
		for (int dir = 0; dir < 2; ++dir) {
			frames.push_back({dir, World::kGuestZap, 0, -10, -40, 20, 40, (uint8_t)(50 + dir)});
			frames.push_back({dir, World::kGuestGrab, 0, -10, -40, 20, 40, (uint8_t)(60 + dir)});
		}
		const std::vector<uint8_t> bytes = spriteBytes(frames);
		const int n = place.addActor(bytes.data(), bytes.size(), 1, 1.0, error);
		place.place(n, {160, 180});
		place.face(n, {0, 180});
		assert(place.act(n, World::kGuestZap, 50) && colour(n) == spriteColor(50));
		place.face(n, {300, 180}); place.face(n, {160, 260});
		assert(place.actor(n).dir == World::kGuestLeft && colour(n) == spriteColor(50));
		place.pose(n, World::kGuestFront, -1, 0);
		assert(colour(n) == spriteColor(50));
		place.unpose(n);
		place.update(60);
		place.face(n, {0, 180}); place.update(1);
		assert(place.light(n, true) && colour(n) == spriteColor(60));
		place.face(n, {160, 260}); place.face(n, {300, 180});
		assert(colour(n) == spriteColor(60) && place.actor(n).dir == World::kGuestLeft);
		place.pose(n, World::kGuestFront, -1, 0);
		assert(colour(n) == spriteColor(60));
		place.update(kIgniteTicks); assert(colour(n) == spriteColor(31)); // (the left's second ignite frame, not the front's)
		place.unpose(n);
		place.update(kIgniteTicks); assert(colour(n) == spriteColor(20)); // (then lit, still facing left)
	}
	std::puts("PASS: taken up first and put away after (a grab, then lit from the ignite frames' second; back to their second, then stowed; from the side; not turned back halfway; not turned at once); moves (a swing, lightning lit and not, its loop, walking ends them, a move ends a walk, from the side, kept to the side last faced when turned to the viewer); posed lit and seated, seated");
	// (The bridge: busy while lighting up, so the frames are drawn.)
	{
		const std::vector<uint8_t> plain(320 * 200, 9);
		const std::vector<uint8_t> d = sceneBytes(320, 200, plain, {box(0, 100, 320, 190)});
		std::vector<Frame> frames = {{2, World::kGuestStand, 0, -10, -40, 20, 40, 30}, {2, World::kGuestLitStand, 0, -10, -40, 20, 40, 50}};
		for (int i = 0; i < 3; ++i) frames.push_back({2, World::kGuestIgnite, i, -10, -40, 20, 40, (uint8_t)(40 + i)});
		const std::vector<uint8_t> bytes = spriteBytes(frames);
		char problem[128];
		assert(StageBridge::load(d.data(), d.size(), 1.0, 320, 320, 200, problem, sizeof(problem)));
		const int n = StageBridge::addActor(bytes.data(), bytes.size(), 1, 1.0, problem, sizeof(problem));
		assert(n == 0 && StageBridge::canLight(n) && !StageBridge::busy());
		assert(StageBridge::light(n, true, true) && StageBridge::lit(n) && StageBridge::busy() && StageBridge::shownKind(n) == StageBridge::kPoseIgnite);
		StageBridge::update(3 * kIgniteTicks - 1); assert(StageBridge::busy());
		// (Lit, standing: busy still, its crackle drawn in turn; from 0210.)
		StageBridge::update(1); assert(StageBridge::busy() && StageBridge::shownKind(n) == StageBridge::kPoseLitStand);
		assert(StageBridge::light(n, false, true) && StageBridge::busy() && !StageBridge::lit(n));
	}
	std::puts("PASS: something lit (its ignite frames in turn, its lit poses, put out backwards, at once, turned back halfway, walking ends them; lit talking as lit standing; none without ignite frames; busy while lighting); a glow's light added, a lit blade in the dark");
	// (From 0200) A leg lifted (Crispy 2's pee), from the side. Art points:
	// art pixels from the feet in the place, mirrored facing left, as big as
	// drawn there. Marks on the floor: a puddle spreading (yellow over the
	// floor), drying to a stain (the floor tinted), under everyone, not in
	// the dark, the oldest let go past kMarks, gone with the place; the
	// bridge busy while one spreads or dries.
	{
		const std::vector<uint8_t> plain(320 * 200, 9);
		const std::vector<uint8_t> d = sceneBytes(320, 200, plain, {box(0, 100, 320, 190)});
		Scene place;
		assert(place.load(d.data(), d.size(), 1.0, 320, 320, 200, error));
		std::vector<uint32_t> shown(320 * 200);
		auto at = [&](int x, int y) { place.render(shown.data(), 320); return shown[(size_t)y * 320 + x]; };
		auto red = [](uint32_t c) { return (int)((c >> 16) & 255); };
		std::vector<Frame> frames = {{1, World::kGuestStand, 0, -10, -40, 20, 40, 30}, {0, World::kGuestStand, 0, -10, -40, 20, 40, 31}};
		for (int i = 0; i < 3; ++i) frames.push_back({1, World::kGuestPee, i, -10, -40, 20, 40, (uint8_t)(100 + i)});
		const std::vector<uint8_t> bytes = spriteBytes(frames);
		const int n = place.addActor(bytes.data(), bytes.size(), 1, 1.0, error);
		place.place(n, {160, 180});
		const auto colour = [&]() { return at(x0n(place, n), (int)place.actor(n).at.y - 10); };
		assert(place.canAct(n, World::kGuestPee) && place.act(n, World::kGuestPee, 6 * kActTicks) && place.shownKind(n) == World::kGuestPee && colour() == spriteColor(100));
		place.update(kActTicks); assert(colour() == spriteColor(101));
		place.update(kActTicks); assert(colour() == spriteColor(102));
		place.update(kActTicks); assert(colour() == spriteColor(101));
		place.update(3 * kActTicks); assert(!place.acting(n) && place.shownKind(n) == World::kGuestStand);
		Point p;
		double per;
		place.face(n, {300, 180});
		assert(place.artPoint(n, -8, -2, p, per) && near(per, 1) && near(p.x, 152) && near(p.y, 178));
		place.face(n, {0, 180});
		assert(place.artPoint(n, -8, 0, p, per) && near(p.x, 168) && !place.artPoint(5, 0, 0, p, per));
		// A puddle: small at first, spreading, yellow over the floor.
		const uint32_t floor = sceneColor(9);
		place.addMark({100, 150}, 20, 0, 60);
		assert(place.drying() && at(100, 150) != floor && red(at(100, 150)) > 120 && at(106, 150) == floor);
		place.update(30);
		assert(red(at(106, 150)) > 120 && at(100, 140) == floor);
		// Dried: a stain, smaller, the floor tinted.
		place.update(30 + kPuddleTicks);
		assert(!place.drying() && at(100, 150) != floor && red(at(100, 150)) > 30 && red(at(100, 150)) < 70 && at(109, 150) == floor);
		// Not yet there while its age is below 0.
		place.addMark({200, 150}, 20, -5, 10);
		assert(at(200, 150) == floor);
		place.update(5); assert(at(200, 150) != floor);
		// Cut short: as big as it got, drying from then; not yet there, gone;
		// none there, -1.
		place.addMark({260, 150}, 20, 0, 100);
		place.update(10);
		const double cut = place.endMark({260, 150});
		assert(near(cut, 20 * (0.3 + 0.7 * 0.2)) && place.mark(place.markCount() - 1).grow == 10 && place.drying());
		place.addMark({280, 150}, 20, -5, 100);
		const int before = place.markCount();
		assert(place.endMark({280, 150}) == 0 && place.markCount() == before - 1 && place.endMark({1, 1}) == -1);
		// Under everyone; not in the dark.
		place.place(n, {100, 152});
		assert(at(100, 150) == spriteColor(31));
		place.setDark(true); assert(at(200, 150) == 0xFF000000u); place.setDark(false);
		// The oldest let go past kMarks; gone with the place.
		for (int i = 0; i < kMarks; ++i) place.addMark({20.0 + i * 20, 120}, 10, 1 << 20, 0);
		assert(place.markCount() == kMarks && place.mark(0).at.y == 120);
		assert(place.load(d.data(), d.size(), 1.0, 320, 320, 200, error) && place.markCount() == 0);
		// (The bridge: busy while one spreads or dries; its marks read back.)
		char problem[128];
		assert(StageBridge::load(d.data(), d.size(), 1.0, 320, 320, 200, problem, sizeof(problem)) && !StageBridge::busy() && StageBridge::markCount() == 0);
		StageBridge::addMark(50, 150, 12, -3, 20);
		double mx, my, mw;
		int age, grow;
		assert(StageBridge::busy() && StageBridge::mark(0, mx, my, mw, age, grow) && mx == 50 && my == 150 && mw == 12 && age == -3 && grow == 20 && !StageBridge::mark(1, mx, my, mw, age, grow));
		StageBridge::update(23 + kPuddleTicks); assert(!StageBridge::busy());
	}
	std::puts("PASS: a leg lifted (from the side, its frames in turn); art points in the place (mirrored facing left); marks on the floor (a puddle spreading, drying to a stain, under everyone, not in the dark, the oldest let go, gone with the place; busy while drying)");
	return 0;
}
