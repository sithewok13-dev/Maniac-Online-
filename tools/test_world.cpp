// Other-worlds scene loader with synthetic scenes (no game data).
// c++ -std=c++14 -Wall -Wextra -Werror -fsanitize=address,undefined -Iengine
//   tools/test_world.cpp engine/common/scummverse_world.cpp
#include "common/scummverse_world.h"
#include <cassert>
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

int main() {
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
	std::printf("PASS: color budget, invalid targets, width limit, narrow padding\n");
}
