// Sandbox stage (common/scummverse_stage.cpp) with synthetic scenes and
// characters (no game data): the view at any screen size, walk boxes and
// paths, scales, drawing in true colour, walking, the camera, spots.
// c++ -std=c++11 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//   tools/test_stage.cpp engine/common/scummverse_stage.cpp engine/common/scummverse_world.cpp
#include "common/scummverse_stage.h"
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
	std::puts("PASS: doors (under before near, the smallest, only those asked)");

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
	}
	std::puts("PASS: object pictures (the render as with the picture in the scene; middle and edge; small and large screens)");

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
