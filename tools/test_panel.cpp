// Sandbox verb panel (common/scummverse_panel.cpp) with synthetic panels and
// scenes (no game data): the file read whole or not at all, where it goes
// under the scene and what a tap is on, drawing (a verb lit, the sentence
// line, things carried as names or pictures, arrows when there is more),
// the game's lettering (widths, wrapping, speech at the scene's scale),
// the plain rules for each verb, things carried from a scene, what a
// thing's own script answers (the things files, SVO1 to SVO9), controls
// over the scene (Sam & Max's box, button and pointer), Full Throttle's
// coin and box, and Loom's distaff.
// c++ -std=c++11 -Wall -Wextra -Werror -Wshadow -fsanitize=address,undefined -Iengine
//   tools/test_panel.cpp engine/common/scummverse_panel.cpp engine/common/scummverse_world.cpp
#include "common/scummverse_panel.h"
#include "common/scummverse_panel_engine.h"
#include "common/scummverse_world.h"
#include "common/scummverse_world_catalog.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <functional>
using namespace Scummverse;
using namespace Scummverse::Panel;

// (The panel's verb kinds are the catalog's, passed through the bridge.)
static_assert((int)kWalk == (int)WorldCatalog::kWorldVerbWalk && (int)kWhatIs == (int)WorldCatalog::kWorldVerbWhatIs &&
	(int)kTakeOff == (int)WorldCatalog::kWorldVerbTakeOff && (int)kAct == (int)WorldCatalog::kWorldVerbAct &&
	(int)kHand == (int)WorldCatalog::kWorldVerbHand && (int)kNote == (int)WorldCatalog::kWorldVerbNote, "verb kinds");

static void put16(std::vector<uint8_t> &v, int x) { v.push_back((uint8_t)(x & 255)); v.push_back((uint8_t)((x >> 8) & 255)); }
static void put(std::vector<uint8_t> &v, std::initializer_list<int> bytes) { for (int b : bytes) v.push_back((uint8_t)b); }

// A test panel 64x16 (palette c = (c, 2c, 255-c)): two verbs (Open at 2,2
// 12x5 lit in 200; a walk verb only named), the sentence centred at 32,0 in
// colour 9, slots 4 of 8x4 at x 40..56 in two rows (names in colour 7, or
// pictures), arrows (up 34,6 4x4, down 34,11 4x4), talk colour 11; two fonts
// of 5 rows: 'A' 3 wide (advance 4: ink, one pixel colour 50), 'B' 2 wide.
// (plainArrows: the arrows' rectangles one colour, 4, as the games' panels
// are exported with nothing carried.)
struct Spec { int slotKind = 1; bool trailing = false; int verbX = 2; int slotW = 8, slotH = 4; bool twiceA = false; bool emptySlot = false; bool plainArrows = false; };
static std::vector<uint8_t> panelBytes(const Spec &s = Spec()) {
	const int W = 64, rows = 16;
	std::vector<uint8_t> d = {'S', 'V', 'I', '1'};
	for (int f : {W, 200, 184, rows}) put16(d, f);
	for (int c = 0; c < 256; ++c) put(d, {c, (2 * c) & 255, 255 - c});
	for (int i = 0; i < W * rows; ++i) {
		const int x = i % W, y = i / W;
		d.push_back((uint8_t)(s.plainArrows && x >= 34 && x < 38 && ((y >= 6 && y < 10) || (y >= 11 && y < 15)) ? 4 : i % 5 + 1));
	}
	d.push_back(2);
	put(d, {kOpen}); put16(d, 1); for (int f : {s.verbX, 2, 12, 5}) put16(d, f);
	d.push_back(4); d.insert(d.end(), {'O', 'p', 'e', 'n'});
	for (int i = 0; i < 12 * 5; ++i) d.push_back(200);
	put(d, {kWalk}); put16(d, 10); for (int f : {0, 0, 0, 0}) put16(d, f);
	d.push_back(7); d.insert(d.end(), {'W', 'a', 'l', 'k', ' ', 't', 'o'});
	put16(d, 32); put16(d, 0); put(d, {1, 9});
	put(d, {s.slotKind, 7, 13, 4});
	for (int k = 0; k < 4; ++k) {
		const bool none = s.emptySlot && k == 0;
		for (int f : {none ? 0 : 40 + (k % 2) * 8, none ? 0 : 6 + (k / 2) * 5, none ? 0 : s.slotW, none ? 0 : s.slotH}) put16(d, f);
	}
	for (int f : {34, 6, 4, 4, 34, 11, 4, 4}) put16(d, f);
	d.push_back(11);
	for (int font = 0; font < 2; ++font) {
		put(d, {5, 77, 255, s.twiceA ? 3 : 2});
		auto glyph = [&](int code, int adv, int w) {
			put(d, {code, adv, 0, 0, w, 5});
			for (int i = 0; i < w * 5; ++i) d.push_back((uint8_t)(i == 0 ? 50 : i % 2 ? 77 : 255));
		};
		glyph('A', 4, 3); glyph('B', 3, 2);
		if (s.twiceA) glyph('A', 4, 3);
	}
	if (s.trailing) d.push_back(0);
	return d;
}
static uint32_t rgb(int c) { return 0xFF000000u | (uint32_t)c << 16 | (uint32_t)((2 * c) & 255) << 8 | (uint32_t)(255 - c); }

// An "SVW5" scene 32x16 with one object 50 at 4,4 8x6: pictures 0 (index 3
// everywhere) and 1 (a 2x2 block of 9 in the middle, else 3), shown `shown`.
static std::vector<uint8_t> sceneBytes(int shown, bool pictures = true) {
	const int w = 32, h = 16;
	std::vector<uint8_t> d = {'S', 'V', 'W', '5'};
	put16(d, 7); put16(d, w); put16(d, h); d.push_back(0); d.push_back(0);
	for (int c = 0; c < 256; ++c) put(d, {c, 255 - c, c / 2});
	for (int i = 0; i < w * h; ++i) d.push_back(3);
	put16(d, 1);
	for (int f : {50, 4, 4, 8, 6, 8, 12, 1}) put16(d, f);
	d.push_back(0); // no cycles (and, without boxes, no box connections)
	d.push_back(3); d.insert(d.end(), {'m', 'u', 'g'});
	if (!pictures) { d.push_back(0); return d; }
	d.push_back(2); d.push_back((uint8_t)shown);
	for (int f : {4, 4, 8, 6}) put16(d, f);
	for (int i = 0; i < 48; ++i) d.push_back(3);
	for (int y = 0; y < 6; ++y) for (int x = 0; x < 8; ++x) d.push_back((uint8_t)(x >= 3 && x < 5 && y >= 2 && y < 4 ? 9 : 3));
	return d;
}

// Controls over the scene ("SVI2", Sam & Max's way): a box 32x20 from row
// 0 of a 32x20 screen, drawn (mask 1) at x 4..27, y 2..17; a walk verb only
// named, look and use icons at 6,3 and 14,3 (6x4, lit 200 and 201), two
// cells 6x4 at 6,10 and 14,10, the icon that shuts it at 22,3 4x4; each
// verb's pointer 3x2 (hot spot 1,1, its top left left clear, colour 60 +
// verb); the button 4x4 at 0,16 in colour 90.
struct OverSpec { int pointerVerb = 2; bool twice = false; int buttonY = 16; int closeX = 22; bool trailing = false; int maskValue = 1; bool shaded = false; };
static std::vector<uint8_t> overBytes(const OverSpec &o = OverSpec()) {
	const int W = 32, rows = 20;
	std::vector<uint8_t> d = {'S', 'V', 'I', '2'};
	for (int f : {W, 20, 0, rows}) put16(d, f);
	for (int c = 0; c < 256; ++c) put(d, {c, (2 * c) & 255, 255 - c});
	for (int i = 0; i < W * rows; ++i) d.push_back((uint8_t)(i % 5 + 1));
	// (Shaded: its bottom rows, 14..17, darken the scene, The Dig's way.)
	for (int y = 0; y < rows; ++y) for (int x = 0; x < W; ++x)
		d.push_back((uint8_t)(x >= 4 && x < 28 && y >= 2 && y < 18 ? (o.shaded && y >= 14 ? 2 : (x == 4 && y == 2 ? o.maskValue : 1)) : 0));
	d.push_back(3);
	put(d, {kWalk}); put16(d, 7); for (int f : {0, 0, 0, 0}) put16(d, f); d.push_back(0);
	put(d, {kLook}); put16(d, 4); for (int f : {6, 3, 6, 4}) put16(d, f); d.push_back(0);
	for (int i = 0; i < 24; ++i) d.push_back(200);
	put(d, {kUse}); put16(d, 5); for (int f : {14, 3, 6, 4}) put16(d, f); d.push_back(0);
	for (int i = 0; i < 24; ++i) d.push_back(201);
	put16(d, 0); put16(d, 0); put(d, {0, 0});
	put(d, {2, 0, 0, 2});
	for (int f : {6, 10, 6, 4, 14, 10, 6, 4}) put16(d, f);
	for (int f = 0; f < 8; ++f) put16(d, 0);
	d.push_back(11);
	for (int font = 0; font < 2; ++font) {
		put(d, {5, 77, 255, 1});
		put(d, {'A', 4, 0, 0, 3, 5});
		for (int i = 0; i < 15; ++i) d.push_back(77);
	}
	d.push_back(o.twice ? 4 : 3);
	for (int k = 0; k < (o.twice ? 4 : 3); ++k) {
		d.push_back((uint8_t)(k == 2 ? o.pointerVerb : k % 3));
		put16(d, 1); put16(d, 1); put16(d, 3); put16(d, 2);
		for (int i = 0; i < 6; ++i) d.push_back((uint8_t)(60 + k));
		for (int i = 0; i < 6; ++i) d.push_back(i ? 1 : 0);
	}
	put16(d, 0); put16(d, o.buttonY); put16(d, 4); put16(d, 4);
	for (int i = 0; i < 16; ++i) d.push_back(90);
	for (int i = 0; i < 16; ++i) d.push_back(1);
	for (int f : {o.closeX, 3, 4, 4}) put16(d, f);
	d.push_back(128); // (a shaded pixel keeps half its brightness)
	if (o.trailing) d.push_back(0);
	return d;
}

// A coin game's controls ("SVI3", 32x20 as overBytes): the box at 4..27 x
// 2..17 with no button (a right click opens it), two cells in one row at
// 8,10 and 14,10 (6x4), its arrows (up 5,4 3x2 in 150; down 20,4 in 151);
// one pointer (3x2 in 60, hot spot 1,1); a coin 12x10 (anchor 6,5; pixels
// 100..102, a hole at 4..7 x 6..8 and its corner clear), two verbs on it:
// look at 2,1 6x4 lit in 200 (its first pixel clear), the hand at 1,0
// 10x8 lit in 201 (around look); the name centred at 6,7 in colour 33.
// (As The Curse's: the name on a line of its own, centred at 16,18; a box
// with no arrows.)
struct CoinSpec { bool trailing = false; int lookX = 2, handWidth = 10, handHeight = 8, coinWidth = 12, lookKind = kLook; bool line = false, arrows = true; };
static std::vector<uint8_t> coinBytes(const CoinSpec &o = CoinSpec()) {
	const int W = 32, rows = 20;
	std::vector<uint8_t> d = {'S', 'V', 'I', '3'};
	for (int f : {W, 20, 0, rows}) put16(d, f);
	for (int c = 0; c < 256; ++c) put(d, {c, (2 * c) & 255, 255 - c});
	for (int i = 0; i < W * rows; ++i) d.push_back((uint8_t)(i % 5 + 1));
	for (int y = 0; y < rows; ++y) for (int x = 0; x < W; ++x) d.push_back((uint8_t)(x >= 4 && x < 28 && y >= 2 && y < 18));
	d.push_back(2);
	put(d, {o.lookKind}); put16(d, 8); for (int f : {o.lookX, 1, 6, 4}) put16(d, f); d.push_back(0);
	for (int i = 0; i < 24; ++i) d.push_back(200);
	put(d, {kHand}); put16(d, 9); for (int f : {1, 0, o.handWidth, o.handHeight}) put16(d, f); d.push_back(0);
	for (int i = 0; i < o.handWidth * o.handHeight; ++i) d.push_back(201);
	put16(d, o.line ? 16 : 0); put16(d, o.line ? 18 : 0); put(d, {o.line ? 1 : 0, o.line ? 33 : 0});
	put(d, {2, 0, 0, 2});
	for (int f : {8, 10, 6, 4, 14, 10, 6, 4}) put16(d, f);
	for (int f : {5, 4, 3, 2, 20, 4, 3, 2}) put16(d, o.arrows ? f : 0);
	d.push_back(11);
	for (int font = 0; font < 2; ++font) {
		put(d, {5, 77, 255, 1});
		put(d, {'A', 4, 0, 0, 3, 5});
		for (int i = 0; i < 15; ++i) d.push_back(77);
	}
	d.push_back(1);
	d.push_back(0); put16(d, 1); put16(d, 1); put16(d, 3); put16(d, 2);
	for (int i = 0; i < 6; ++i) d.push_back(60);
	for (int i = 0; i < 6; ++i) d.push_back(1);
	for (int f : {0, 0, 0, 0}) put16(d, f); // (no button)
	for (int f : {0, 0, 0, 0}) put16(d, f);
	d.push_back(255);
	put16(d, 6); put16(d, 5); put16(d, o.coinWidth); put16(d, 10);
	for (int i = 0; i < o.coinWidth * 10; ++i) d.push_back((uint8_t)(100 + i % 3));
	for (int y = 0; y < 10; ++y) for (int x = 0; x < o.coinWidth; ++x) d.push_back((uint8_t)!((x >= 4 && x < 8 && y >= 6 && y < 9) || (!x && !y)));
	put16(d, 6); put16(d, 7); d.push_back(33);
	for (int i = 0; i < 24; ++i) d.push_back(i ? 1 : 0);
	for (int i = 0; i < o.handWidth * o.handHeight; ++i) d.push_back(1);
	for (int k = 0; k < 2 && o.arrows; ++k) { for (int i = 0; i < 6; ++i) d.push_back((uint8_t)(150 + k)); for (int i = 0; i < 6; ++i) d.push_back(1); }
	if (o.trailing) d.push_back(0);
	return d;
}

// Loom's distaff ("SVI4", 64x16 under the scene from row 184, as
// panelBytes): three notes, c (id 0) at 2,2, e (2) at 10,2 and g (4) at
// 18,2, 6x4 each, lit in 200, 201, 202; no slots; the thing chosen shown at
// 40,4 16x8; three drafts: Opening g c g e, Sleep c e e c (the same both
// ways), Calm c c c e.
struct DistaffSpec { bool trailing = false; int noteId = 0, noteKind = kNote, iconX = 40, draftBits = 0; bool asPanel = false; };
static std::vector<uint8_t> distaffBytes(const DistaffSpec &o = DistaffSpec()) {
	const int W = 64, rows = 16;
	std::vector<uint8_t> d = {'S', 'V', 'I', (uint8_t)(o.asPanel ? '1' : '4')};
	for (int f : {W, 200, 184, rows}) put16(d, f);
	for (int c = 0; c < 256; ++c) put(d, {c, (2 * c) & 255, 255 - c});
	for (int i = 0; i < W * rows; ++i) d.push_back((uint8_t)(i % 5 + 1));
	d.push_back(3);
	const int ids[3] = {o.noteId, 2, 4};
	for (int k = 0; k < 3; ++k) {
		put(d, {o.noteKind}); put16(d, ids[k]); for (int f : {2 + 8 * k, 2, 6, 4}) put16(d, f);
		d.push_back(1); d.push_back((uint8_t)"ceg"[k]);
		for (int i = 0; i < 24; ++i) d.push_back((uint8_t)(200 + k));
	}
	put16(d, 0); put16(d, 0); put(d, {0, 9});
	put(d, {2, 0, 0, 0});
	for (int f = 0; f < 8; ++f) put16(d, 0);
	d.push_back(11);
	for (int font = 0; font < 2; ++font) {
		put(d, {5, 77, 255, 1});
		put(d, {'A', 4, 0, 0, 3, 5});
		for (int i = 0; i < 15; ++i) d.push_back(77);
	}
	if (!o.asPanel) {
		for (int f : {o.iconX, 4, 16, 8}) put16(d, f);
		d.push_back(3);
		const char *names[3] = {"Opening", "Sleep", "Calm"};
		const int notes[3][4] = {{4, 0, 4, 2}, {0, 2, 2, 0}, {0, 0, 0, 2}};
		for (int i = 0; i < 3; ++i) {
			d.push_back((uint8_t)std::strlen(names[i])); for (const char *c = names[i]; *c; ++c) d.push_back((uint8_t)*c);
			put16(d, notes[i][0] | notes[i][1] << 3 | notes[i][2] << 6 | notes[i][3] << 9 | (i ? 0 : o.draftBits));
		}
	}
	if (o.trailing) d.push_back(0);
	return d;
}

int main() {
	std::string error;
	// The file whole or not at all.
	{
		const std::vector<uint8_t> data = panelBytes();
		Source s;
		assert(parse(data.data(), data.size(), s, error));
		assert(s.screenWidth == 64 && s.screenHeight == 200 && s.top == 184 && s.rows == 16 && s.pixels.size() == 64 * 16);
		assert(s.verbs.size() == 2 && s.verbs[0].kind == kOpen && s.verbs[0].name == "Open" && s.verbs[0].rect.width == 12 && s.verbs[0].lit.size() == 60);
		assert(s.verbs[1].kind == kWalk && s.verbs[1].rect.width == 0 && s.verbs[1].name == "Walk to");
		assert(s.sentenceX == 32 && s.sentenceCentred && s.sentenceColor == 9 && s.slotKind == 1 && s.slotColor == 7 && s.slots.size() == 4);
		assert(s.up.x == 34 && s.down.y == 11 && s.talkColor == 11);
		assert(s.fonts[0].has['A'] && s.fonts[0].glyphs['A'].advance == 4 && s.fonts[1].has['B'] && !s.fonts[1].has['C']);
		for (size_t cut = 1; cut < data.size(); cut += 37) assert(!parse(data.data(), data.size() - cut, s, error));
		Spec trailing; trailing.trailing = true;
		Spec outside; outside.verbX = 60;
		Spec wide; wide.slotW = 30;
		Spec kind; kind.slotKind = 3;
		Spec twice; twice.twiceA = true;
		Spec flat; flat.slotH = 0; // (a slot with width but no height)
		for (const Spec &bad : {trailing, outside, wide, kind, twice, flat}) {
			const std::vector<uint8_t> b = panelBytes(bad);
			assert(!parse(b.data(), b.size(), s, error));
		}
		std::vector<uint8_t> tag = data; tag[3] = '2';
		assert(!parse(tag.data(), tag.size(), s, error) && !parse(nullptr, 0, s, error));
	}
	std::puts("PASS: the panel file (read whole; cut short, left over, outside, bad kinds and doubled letters refused)");

	// Under the scene: its rows at the scene's scale, its columns centred;
	// what a tap is on.
	{
		const std::vector<uint8_t> data = panelBytes();
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error));
		assert(p.rowsAt(3.0) == 48);
		p.layout(400, 1000, 100, 3.0, 2.5); // 64 columns 160 wide, from 120
		assert(p.top() == 100 && p.screenRows() == 48);
		assert(p.hit(10, 99).panel == false && p.hit(10, 148).panel == false && p.hit(10, 100).panel && p.hit(10, 100).verb < 0);
		// Open at 2..14 x 2..7: screen 125..155, 106..121; a few pixels off
		// (6 panel pixels: 15 across, 18 down) still for it, farther not.
		assert(p.hit(140, 112).verb == 0 && p.hit(124, 112).verb == 0 && p.hit(156 + 12, 112).verb == 0);
		assert(p.hit(140, 100 + 12 * 3).verb == 0 && p.hit(140, 100 + 13 * 3).verb < 0 && p.hit(120 + 22 * 2.5, 112).verb < 0);
		// Arrows; slots only where something is carried.
		assert(p.hit(120 + 35 * 2.5, 100 + 7 * 3).arrow == -1 && p.hit(120 + 35 * 2.5, 100 + 12 * 3).arrow == 1);
		assert(p.hit(120 + 42 * 2.5, 100 + 7 * 3).item == -1);
		std::vector<Item> items(3);
		items[0].name = "AB"; items[1].name = "B"; items[2].name = "BA";
		p.setItems(items);
		assert(p.hit(120 + 42 * 2.5, 100 + 7 * 3).item == 0 && p.hit(120 + 50 * 2.5, 100 + 7 * 3).item == 1);
		assert(p.hit(120 + 42 * 2.5, 100 + 12 * 3).item == 2 && p.hit(120 + 50 * 2.5, 100 + 12 * 3).item == -1);
		// Where a verb is on screen holds the taps for it.
		const Rect r = p.onScreen(p.source().verbs[0].rect);
		assert(p.hit(r.x, r.y).verb == 0 && p.hit(r.x + r.width - 1, r.y + r.height - 1).verb == 0);
		assert(p.walkVerb() == 1 && p.verbName(-1) == "Walk to" && p.verbName(0) == "Open" && p.kindOf(-1) == kWalk);
	}
	std::puts("PASS: under the scene at its scale, columns centred; taps on verbs (and near them), arrows, things carried");

	// Where each verb is on screen is exactly where taps are for it, at any
	// scale (its corners are for it, not a neighbour); rows kept on screen.
	{
		const std::vector<uint8_t> data = panelBytes();
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error));
		for (double rs = 1.0; rs < 6.0; rs += 0.0137)
			for (double cs : {rs / 1.2, rs, rs * 0.9}) {
				p.layout(1000, 2000, 37, rs, cs);
				const Rect r = p.onScreen(p.source().verbs[0].rect);
				assert(r.width > 0 && r.height > 0);
				for (int x : {r.x, r.x + r.width - 1}) for (int y : {r.y, r.y + r.height - 1}) assert(p.hit(x, y).verb == 0);
				const Rect slot = p.onScreen(p.source().slots[3]);
				std::vector<Item> four(4);
				p.setItems(four);
				for (int x : {slot.x, slot.x + slot.width - 1}) for (int y : {slot.y, slot.y + slot.height - 1}) assert(p.hit(x, y).item == 3);
			}
		p.layout(400, 120, 100, 3.0, 2.5);
		assert(p.screenRows() == 20); // (48 rows, 20 left on screen)
	}
	std::puts("PASS: where verbs and slots are on screen holds exactly their taps at any scale; rows kept on screen");

	// Drawing: the panel as the game drew it; a verb lit; the sentence line
	// centred; names in their slots (cut at the slot), pictures fitted.
	{
		const std::vector<uint8_t> data = panelBytes();
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error));
		std::vector<uint32_t> canvas;
		p.compose(canvas);
		for (size_t i = 0; i < canvas.size(); ++i) assert(canvas[i] == rgb(p.source().pixels[i]));
		p.select(0);
		p.compose(canvas);
		assert(canvas[2 * 64 + 2] == rgb(200) && canvas[6 * 64 + 13] == rgb(200) && canvas[7 * 64 + 2] == rgb(p.source().pixels[7 * 64 + 2]));
		p.select(-1);
		p.setSentence("AB");
		assert(p.textWidth(0, "AB") == 7 && p.textWidth(0, "ABC") == 7);
		p.compose(canvas);
		// Centred at 32: from 32 - 3 = 29; 'A' at 29..31, ink (77) in colour 9, its own colour 50 kept.
		assert(canvas[0 * 64 + 29] == rgb(50) && canvas[0 * 64 + 30] == rgb(9) && canvas[0 * 64 + 31] == rgb(p.source().pixels[31]));
		assert(canvas[1 * 64 + 29] == rgb(9));
		p.setSentence("");
		std::vector<Item> items(1);
		items[0].name = "ABABAB"; // 4*3+3*3 = 21 wide: cut at the slot's 8
		p.setItems(items);
		p.compose(canvas);
		assert(canvas[6 * 64 + 40] == rgb(50) && canvas[6 * 64 + 41] == rgb(7));
		for (int y = 6; y < 10; ++y) for (int x = 48; x < 56; ++x) assert(canvas[y * 64 + x] == rgb(p.source().pixels[y * 64 + x]));
		// Pictures: a 16x8 one halved into its 8x4 slot; a 2x2 one 1:1 in the middle; see-through left alone.
		Spec pictureSlots; pictureSlots.slotKind = 2;
		const std::vector<uint8_t> pictureData = panelBytes(pictureSlots);
		assert(p.load(pictureData.data(), pictureData.size(), error));
		assert(p.items().size() == 1); // (carried on from panel to panel)
		std::vector<Item> pictures(2);
		pictures[0].width = 16; pictures[0].height = 8;
		for (int i = 0; i < 128; ++i) pictures[0].picture.push_back(0xFF000000u | (uint32_t)(i % 16));
		pictures[1].width = 2; pictures[1].height = 2;
		pictures[1].picture = {0xFF123456u, 0u, 0xFF123456u, 0xFF123456u};
		p.setItems(pictures);
		p.compose(canvas);
		for (int x = 0; x < 8; ++x) assert(canvas[6 * 64 + 40 + x] == (0xFF000000u | (uint32_t)(x * 2)));
		assert(canvas[7 * 64 + 51] == 0xFF123456u && canvas[7 * 64 + 52] == rgb(p.source().pixels[7 * 64 + 52]) && canvas[8 * 64 + 52] == 0xFF123456u);
	}
	// A slot the panel has none of: nothing drawn there, nothing hit.
	{
		Spec gap; gap.slotKind = 2; gap.emptySlot = true;
		const std::vector<uint8_t> data = panelBytes(gap);
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error));
		std::vector<Item> pictures(2);
		for (Item &item : pictures) { item.width = 3; item.height = 3; item.picture.assign(9, 0xFF00FF00u); }
		p.setItems(pictures);
		std::vector<uint32_t> canvas;
		p.compose(canvas);
		int green = 0;
		for (uint32_t c : canvas) green += c == 0xFF00FF00u;
		assert(green == 9); // (only the second, in slot 1)
		p.layout(64, 16, 0, 1.0, 1.0);
		assert(p.hit(0, 0).item == -1 && p.hit(50, 7).item == 1);
	}
	std::puts("PASS: drawn as the game drew it; a verb lit, the sentence centred, names cut at their slot, pictures fitted; no slot, nothing");

	// More than the slots: a row at a time, arrows (drawn for names lists
	// only when there is more).
	{
		const std::vector<uint8_t> data = panelBytes();
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error));
		std::vector<Item> items(7);
		for (size_t i = 0; i < items.size(); ++i) items[i].name = std::string(1 + i % 2, 'A');
		p.setItems(items);
		std::vector<uint32_t> canvas;
		p.compose(canvas);
		const uint32_t ink = rgb(7);
		auto arrow = [&](const Rect &a) { int n = 0; for (int y = 0; y < a.height; ++y) for (int x = 0; x < a.width; ++x) n += canvas[(a.y + y) * 64 + a.x + x] == ink; return n; };
		assert(p.firstItem() == 0 && arrow(p.source().up) == 0 && arrow(p.source().down) > 0);
		p.scroll(1); p.compose(canvas);
		assert(p.firstItem() == 2 && arrow(p.source().up) > 0 && arrow(p.source().down) > 0);
		p.scroll(5); p.compose(canvas);
		assert(p.firstItem() == 4 && arrow(p.source().down) == 0 && arrow(p.source().up) > 0);
		p.scroll(-9);
		assert(p.firstItem() == 0);
		p.setItems(std::vector<Item>(2)); p.compose(canvas);
		assert(arrow(p.source().up) == 0 && arrow(p.source().down) == 0);
	}
	// (Pictures carried, the arrows' places plain as exported (Monkey Island
	// 2's, Day of the Tentacle's): an arrow drawn there, in the sentence's
	// colour, where there is more; none where the art has its own.)
	{
		Spec pictures; pictures.slotKind = 2; pictures.plainArrows = true;
		const std::vector<uint8_t> data = panelBytes(pictures);
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error));
		std::vector<Item> items(7);
		for (Item &i : items) { i.width = 2; i.height = 2; i.picture.assign(4, 0xFF00FF00u); }
		p.setItems(items);
		std::vector<uint32_t> canvas;
		p.compose(canvas);
		const uint32_t ink = rgb(9);
		auto arrow = [&](const Rect &a) { int n = 0; for (int y = 0; y < a.height; ++y) for (int x = 0; x < a.width; ++x) n += canvas[(a.y + y) * 64 + a.x + x] == ink; return n; };
		assert(arrow(p.source().up) == 0 && arrow(p.source().down) > 0);
		p.scroll(5); p.compose(canvas);
		assert(arrow(p.source().up) > 0 && arrow(p.source().down) == 0);
		Spec drawn; drawn.slotKind = 2;
		const std::vector<uint8_t> art = panelBytes(drawn);
		Panel::Panel q;
		assert(q.load(art.data(), art.size(), error));
		q.setItems(items); q.compose(canvas);
		assert(arrow(q.source().down) == 0);
	}
	std::puts("PASS: more than the slots: a row at a time, the arrows only when there is more (drawn where the panel's places for them are plain)");

	// On screen: each row and column from the panel's own, black either side.
	{
		const std::vector<uint8_t> data = panelBytes();
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error));
		p.select(0); p.setSentence("BA");
		const int sw = 300, sh = 200, top = 140;
		p.layout(sw, sh, top, 3.7, 3.1);
		std::vector<uint32_t> screen((size_t)sw * sh, 0x12345678u), canvas;
		p.render(screen.data(), sw, sh);
		p.compose(canvas);
		const int columns = (int)std::lround(64 * 3.1), left = (sw - columns) / 2;
		for (int y = 0; y < sh; ++y)
			for (int x = 0; x < sw; ++x) {
				const uint32_t got = screen[(size_t)y * sw + x];
				if (y < top || y >= top + p.screenRows()) { assert(got == 0x12345678u); continue; }
				if (x < left || x >= left + columns) { assert(got == 0xFF000000u); continue; }
				const int cy = std::min(15, (int)((y - top) / 3.7)), cx = std::min(63, (int)((x - left) / 3.1));
				assert(got == canvas[(size_t)cy * 64 + cx]);
			}
	}
	std::puts("PASS: on screen at the scene's scale, rows and columns from the panel's own, black either side");

	// Lettering: lines wrapped at a width; speech scaled, centred, kept on
	// screen and off the panel's rows.
	{
		const std::vector<uint8_t> data = panelBytes();
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error));
		const std::vector<std::string> lines = p.wrap(1, "AB AB AB", 15); // 7 + space(0) ...
		assert(lines.size() == 2 && lines[0] == "AB AB" && lines[1] == "AB");
		assert(p.wrap(1, "ABABABAB", 5).size() == 1); // (a word longer than a line stays whole)
		const int sw = 200, limit = 100;
		std::vector<uint32_t> screen((size_t)sw * 140, 0);
		p.say(screen.data(), sw, sw, limit, "AB", 100, 60, 2.0, 2.0, 0xFFABCDEFu);
		int inked = 0, own = 0, x0 = sw, x1 = 0, y0 = 140, y1 = 0;
		for (int y = 0; y < 140; ++y)
			for (int x = 0; x < sw; ++x) {
				const uint32_t c = screen[(size_t)y * sw + x];
				if (!c) continue;
				inked += c == 0xFFABCDEFu; own += c == rgb(50);
				x0 = std::min(x0, x); x1 = std::max(x1, x + 1); y0 = std::min(y0, y); y1 = std::max(y1, y + 1);
			}
		// Width 7 at 2: 14 across, centred on 100 (93..107); 5 rows at 2 ending at 60.
		assert(x0 == 93 && x1 <= 107 && y0 == 50 && y1 == 60 && inked > 0 && own == 8);
		std::fill(screen.begin(), screen.end(), 0);
		p.say(screen.data(), sw, sw, limit, "AB", 2, 104, 2.0, 2.0, 0xFFABCDEFu); // at the left edge, under the limit
		for (int y = limit; y < 140; ++y) for (int x = 0; x < sw; ++x) assert(!screen[(size_t)y * sw + x]);
		int left = sw;
		for (int y = 0; y < limit; ++y) for (int x = 0; x < sw; ++x) if (screen[(size_t)y * sw + x]) left = std::min(left, x);
		assert(left == 0);
	}
	std::puts("PASS: lettering: widths, wrapping, speech scaled, centred, on screen and off the panel");

	// The plain rules.
	{
		Thing door; door.door = true; door.pictures = 2; door.shown = 0; door.differs = true; door.width = 20; door.height = 40;
		Thing mug; mug.pictures = 2; mug.shown = 1; mug.differs = true; mug.width = 8; mug.height = 6;
		Thing big = mug; big.width = 120; big.height = 80;
		Thing hidden = mug; hidden.shown = 0;
		Thing plain; plain.width = 30; plain.height = 30;
		Thing three = mug; three.pictures = 3; three.shown = 2;
		Outcome o = decide(kLook, mug, "mug");
		assert(o.result == kSay && o.say == "Mug.");
		assert(decide(kWhatIs, mug, "grog?").say == "Grog?" && decide(kLook, mug, "").say == "Nothing special.");
		o = decide(kPickUp, mug, "mug");
		assert(o.result == kTake && o.picture == 0);
		for (const Thing &t : {door, big, hidden, plain}) assert(decide(kPickUp, t, "x").result == kSay && decide(kPickUp, t, "x").say == "I can't pick that up.");
		assert(decide(kOpen, door, "door").result == kShow && decide(kOpen, door, "door").picture == 1);
		Thing open = door; open.shown = 1;
		assert(decide(kOpen, open, "door").say == "It's already open." && decide(kClose, open, "door").picture == 0);
		assert(decide(kClose, door, "door").say == "It's already closed." && decide(kOpen, plain, "x").say == "It doesn't open.");
		assert(decide(kTurnOn, door, "lamp").picture == 1 && decide(kTurnOff, open, "lamp").picture == 0 && decide(kTurnOn, plain, "x").say == "It doesn't turn on.");
		// (Two pictures: there and not; more: through those showing it.)
		Thing none3 = three; none3.shown = 0;
		assert(decide(kPush, three, "x").picture == 1 && decide(kPull, mug, "x").picture == 0 && decide(kPush, plain, "x").say == "It won't budge.");
		assert(decide(kPush, none3, "x").picture == 1 && decide(kPull, hidden, "x").picture == 1);
		assert(decide(kUse, mug, "x").say == "That doesn't seem to work." && decide(kGive, mug, "x").result == kSay && decide(kTalk, mug, "x").result == kSay);
		assert(decide(kWalk, mug, "x").result == kNothing);
		// Where the game's script is known: only what it answers.
		Thing pirate = mug; pirate.answers = 1 << kTalk | 1 << kLook;
		Thing grog = mug; grog.answers = 1 << kPickUp;
		Thing hatch = door; hatch.answers = 1 << kClose; // (either of open and close will do)
		assert(decide(kPickUp, pirate, "pirate").say == "I can't pick that up." && decide(kPickUp, grog, "mug").result == kTake);
		assert(decide(kOpen, hatch, "hatch").picture == 1 && decide(kOpen, pirate, "x").say == "It doesn't open.");
		assert(decide(kPush, pirate, "x").say == "It won't budge." && decide(kTurnOn, pirate, "x").say == "It doesn't turn on.");
		assert(decide(kLook, pirate, "pirate").say == "Pirate." && decide(kUse, grog, "x").result == kSay);
		// Its catch-all entry alone: not known (all will do); with its own: those.
		Thing any = mug; any.answers = PanelBridge::kThingAnswersAny;
		Thing pirateAny = pirate; pirateAny.answers |= PanelBridge::kThingAnswersAny;
		Thing grogAny = grog; grogAny.answers |= PanelBridge::kThingAnswersAny | PanelBridge::kThingAway;
		assert(decide(kPickUp, any, "x").result == kTake && decide(kOpen, any, "x").say == "It's already open.");
		assert(decide(kPickUp, pirateAny, "x").say == "I can't pick that up." && decide(kPickUp, grogAny, "x").result == kTake);
		Thing nothing = mug; nothing.answers = 0;
		assert(decide(kPickUp, nothing, "x").say == "I can't pick that up." && decide(kPush, nothing, "x").say == "It won't budge.");
		// The oldest games' own verbs: read names it, unlock opens, the rest said.
		assert(decide(kRead, mug, "note").say == "Note." && decide(kUnlock, door, "door").picture == 1);
		assert(decide(kUnlock, plain, "x").say == "It isn't locked." && decide(kUnlock, open, "door").say == "It's already open.");
		assert(decide(kFix, mug, "x").result == kSay && decide(kPutOn, mug, "x").result == kSay && decide(kTakeOff, mug, "x").result == kSay);
		assert(decide(kNewKid, mug, "x").result == kNothing);
		// Their things are there in picture 0 and taken in 1 ("on").
		Thing old = mug; old.takenShown = true; old.shown = 0;
		o = decide(kPickUp, old, "key");
		assert(o.result == kTake && o.picture == 1);
		Thing oldGone = old; oldGone.shown = 1;
		assert(decide(kPickUp, oldGone, "key").say == "I can't pick that up.");
	}
	std::puts("PASS: the plain rules (look names, pick up small shown things, open, close, on, off, push, pull; the rest said; what the game's script answers; the oldest games' verbs and their way of taking)");

	// Where a game puts things: per room each object's picture and what it
	// answers; read whole or not at all; kept per game.
	{
		std::vector<uint8_t> d = {'S', 'V', 'O', '1'};
		put16(d, 2);
		put16(d, 28); put16(d, 2); put16(d, 373); d.push_back(1); put16(d, 1 << kPickUp); put16(d, 341); d.push_back(1); put16(d, 1 << kTalk);
		put16(d, 33); put16(d, 0);
		GameThings things;
		assert(parseThings(d.data(), d.size(), things, error) && things.rooms.size() == 2);
		const GameThing *mug = things.find(28, 373);
		assert(mug && mug->picture == 1 && mug->answers == 1 << kPickUp && !things.find(28, 999) && !things.find(33, 373));
		for (size_t cut = 1; cut < d.size() - 4; ++cut) assert(!parseThings(d.data(), d.size() - cut, things, error));
		std::vector<uint8_t> extra = d; extra.push_back(0);
		assert(!parseThings(extra.data(), extra.size(), things, error) && things.rooms.empty());
		char problem[64];
		int picture = -1, answers = -1;
		assert(PanelBridge::loadThings(0, d.data(), d.size(), problem, sizeof(problem)) && PanelBridge::thingsLoaded(0) && !PanelBridge::thingsLoaded(1));
		assert(PanelBridge::gameThing(0, 28, 341, picture, answers) && picture == 1 && answers == 1 << kTalk && !PanelBridge::gameThing(1, 28, 341, picture, answers));
		// (One that cannot be read: kept as none, not read again.)
		assert(!PanelBridge::loadThings(0, extra.data(), extra.size(), problem, sizeof(problem)) && PanelBridge::thingsLoaded(0));
		assert(!PanelBridge::gameThing(0, 28, 341, picture, answers) && std::strlen(problem) > 0);
		PanelBridge::clearThings();
		assert(!PanelBridge::thingsLoaded(0));
		// In any order in the file; a room only once; at most so many.
		std::vector<uint8_t> mixed = {'S', 'V', 'O', '1'};
		put16(mixed, 3);
		put16(mixed, 90); put16(mixed, 1); put16(mixed, 7); mixed.push_back(2); put16(mixed, PanelBridge::kThingAway);
		put16(mixed, 12); put16(mixed, 3);
		for (int id : {30, 10, 20}) { put16(mixed, id); mixed.push_back((uint8_t)(id / 10)); put16(mixed, 1 << kLook); }
		put16(mixed, 50); put16(mixed, 0);
		assert(parseThings(mixed.data(), mixed.size(), things, error) && things.rooms.size() == 3);
		assert(things.rooms[0].first == 12 && things.rooms[2].first == 90);
		for (int id : {10, 20, 30}) assert(things.find(12, id) && things.find(12, id)->picture == id / 10);
		assert(things.find(90, 7)->answers == PanelBridge::kThingAway && !things.find(50, 7) && !things.find(11, 10) && !things.find(91, 7));
		std::vector<uint8_t> twice = {'S', 'V', 'O', '1'};
		put16(twice, 2);
		put16(twice, 28); put16(twice, 0); put16(twice, 28); put16(twice, 0);
		assert(!parseThings(twice.data(), twice.size(), things, error) && things.rooms.empty());
		std::vector<uint8_t> rooms = {'S', 'V', 'O', '1'};
		put16(rooms, kMostThingRooms + 1);
		for (int i = 0; i <= kMostThingRooms; ++i) { put16(rooms, i); put16(rooms, 0); }
		assert(!parseThings(rooms.data(), rooms.size(), things, error) && error == "too many rooms");
		std::vector<uint8_t> crowd = {'S', 'V', 'O', '1'};
		put16(crowd, 1); put16(crowd, 1); put16(crowd, kMostThings + 1);
		for (int i = 0; i <= kMostThings; ++i) { put16(crowd, i); crowd.push_back(0); put16(crowd, 0); }
		assert(!parseThings(crowd.data(), crowd.size(), things, error) && error == "too many things" && things.rooms.empty());
	}
	std::puts("PASS: where a game puts things (read whole or not at all, any order, a room once, at most so many; per room and object, kept per game)");

	// What a thing's own script does to a verb ("SVO2"): from a picture, its
	// picture after, the others it changes, its line; looked up whatever the
	// file's order; read whole or not at all; "SVO1" has none.
	{
		std::vector<uint8_t> d = {'S', 'V', 'O', '2'};
		put16(d, 1); put16(d, 24); put16(d, 1); put16(d, 115); d.push_back(1); put16(d, 1 << kOpen | 1 << kClose);
		put16(d, 3);
		put16(d, 24); put16(d, 253); d.push_back(kTurnOn); d.push_back(1); d.push_back(0); d.push_back(0); d.push_back(0);
		put16(d, 24); put16(d, 115); d.push_back(kOpen); d.push_back(1); d.push_back(0); d.push_back(2);
		put16(d, 24); put16(d, 116); d.push_back(0); put16(d, 6); put16(d, 139); d.push_back(1);
		const std::string line = "Not now.";
		d.push_back((uint8_t)line.size()); d.insert(d.end(), line.begin(), line.end());
		put16(d, 7); put16(d, 88); d.push_back(kClose); d.push_back(0); d.push_back(0); d.push_back(0); d.push_back(0);
		GameThings things;
		assert(parseThings(d.data(), d.size(), things, error) && things.effects.size() == 3 && things.find(24, 115));
		const ThingEffect *e = things.effect(24, 115, kOpen, 1);
		assert(e && e->after == 0 && e->others.size() == 2 && e->others[1].room == 6 && e->others[1].id == 139 && e->others[1].picture == 1 && e->line == line);
		assert(things.effect(24, 253, kTurnOn, 1) && things.effect(24, 253, kTurnOn, 1)->line.empty() && things.effect(7, 88, kClose, 0));
		assert(!things.effect(24, 115, kOpen, 0) && !things.effect(24, 115, kClose, 1) && !things.effect(25, 115, kOpen, 1));
		for (size_t cut = 1; cut < d.size() - 4; ++cut) assert(!parseThings(d.data(), d.size() - cut, things, error));
		std::vector<uint8_t> bad = d; bad[4 + 2 + 2 + 2 + 2 + 1 + 2 + 2 + 2 + 2 + 1 + 1] = 4; // (a picture past 1, not taken)
		assert(!parseThings(bad.data(), bad.size(), things, error) && error == "bad effect");
		// (From 0161: bit 1 of the picture after, taken by the one who used it.)
		std::vector<uint8_t> took = d; took[4 + 2 + 2 + 2 + 2 + 1 + 2 + 2 + 2 + 2 + 1 + 1] = 3;
		assert(parseThings(took.data(), took.size(), things, error) && things.effect(24, 253, kTurnOn, 1)->taken && things.effect(24, 253, kTurnOn, 1)->after == 1);
		assert(!things.effect(24, 115, kOpen, 1)->taken);
		char problem[64], said[16];
		int after = -1, others[6], count = -1, room, id, kind, from;
		assert(PanelBridge::loadThings(3, d.data(), d.size(), problem, sizeof(problem)) && PanelBridge::effectCount(3) == 3);
		bool taken = true;
		assert(PanelBridge::thingEffect(3, 24, 115, kOpen, 1, after, others, count, 2, said, sizeof(said), &taken) && after == 0 && !taken && count == 2 && others[3] == 6 && others[4] == 139 && others[5] == 1 && line == said);
		assert(PanelBridge::thingEffect(3, 24, 115, kOpen, 1, after, others, count, 1, said, sizeof(said)) && count == 1);
		assert(!PanelBridge::thingEffect(3, 24, 115, kOpen, 0, after, others, count, 2, said, sizeof(said)) && !PanelBridge::thingEffect(4, 24, 115, kOpen, 1, after, others, count, 2, said, sizeof(said)));
		assert(PanelBridge::effectAt(3, 0, room, id, kind, from) && room == 7 && id == 88 && kind == kClose && from == 0 && !PanelBridge::effectAt(3, 3, room, id, kind, from));
		// ("SVO3", from 0168: then what each thing is inside, and the
		// picture that one shows it in; looked up whatever the order; one
		// inside itself or listed twice refused.)
		std::vector<uint8_t> three = d;
		three[3] = '3';
		put16(three, 2);
		put16(three, 7); put16(three, 90); put16(three, 89); three.push_back(1);
		put16(three, 1); put16(three, 55); put16(three, 54); three.push_back(1);
		assert(parseThings(three.data(), three.size(), things, error) && things.parents.size() == 2 && things.effects.size() == 3);
		assert(things.parent(1, 55) && things.parent(1, 55)->parent == 54 && things.parent(7, 90)->picture == 1 && !things.parent(7, 89) && !things.parent(1, 90));
		for (size_t cut = 1; cut < 16; ++cut) assert(!parseThings(three.data(), three.size() - cut, things, error));
		std::vector<uint8_t> self = three;
		self[self.size() - 3] = 55; self[self.size() - 2] = 0; // (the key inside itself)
		assert(!parseThings(self.data(), self.size(), things, error) && error == "bad parent");
		std::vector<uint8_t> twice = d;
		twice[3] = '3';
		put16(twice, 2);
		for (int k = 0; k < 2; ++k) { put16(twice, 1); put16(twice, 55); put16(twice, 54); twice.push_back(1); }
		assert(!parseThings(twice.data(), twice.size(), things, error) && error == "a parent twice");
		// (From export version 23 every game's but the mansion's: "SVO3"
		// with no effects, then what each thing is inside.)
		std::vector<uint8_t> inside = {'S', 'V', 'O', '3'};
		put16(inside, 1); put16(inside, 2); put16(inside, 2);
		for (int id : {15, 92}) { put16(inside, id); inside.push_back(0); put16(inside, 0); }
		put16(inside, 0);
		put16(inside, 1); put16(inside, 2); put16(inside, 15); put16(inside, 92); inside.push_back(1);
		assert(parseThings(inside.data(), inside.size(), things, error) && things.effects.empty() && things.parents.size() == 1);
		assert(things.parent(2, 15) && things.parent(2, 15)->parent == 92 && things.parent(2, 15)->picture == 1 && things.find(2, 92));
		for (size_t cut = 1; cut < inside.size() - 4; ++cut) assert(!parseThings(inside.data(), inside.size() - cut, things, error));
		int parent = -1, parentPicture = -1;
		assert(PanelBridge::loadThings(3, three.data(), three.size(), problem, sizeof(problem)) && PanelBridge::thingParent(3, 7, 90, parent, parentPicture) && parent == 89 && parentPicture == 1);
		assert(!PanelBridge::thingParent(3, 7, 89, parent, parentPicture) && !PanelBridge::thingParent(4, 7, 90, parent, parentPicture));
		assert(parseThings(d.data(), d.size(), things, error) && things.parents.empty()); // ("SVO2": none)
		// ("SVO4", from 0171: each effect names its second thing (0 none,
		// 0xFFFF any other), its after's bits 2 and 3 the first or second
		// used up, an other's picture 2 one had then. Looked up: that second's
		// own, else the usual; single things as before.)
		{
			std::vector<uint8_t> four = {'S', 'V', 'O', '4'};
			put16(four, 1); put16(four, 1); put16(four, 1); put16(four, 50); four.push_back(0); put16(four, 0);
			put16(four, 3);
			auto effect = [&](int thing, int verb, int with, int bits, int otherPicture, const std::string &spoken) {
				put16(four, 1); put16(four, thing); four.push_back((uint8_t)verb); four.push_back(0); put16(four, with); four.push_back((uint8_t)bits);
				four.push_back(otherPicture >= 0 ? 1 : 0);
				if (otherPicture >= 0) { put16(four, 7); put16(four, 90); four.push_back((uint8_t)otherPicture); }
				four.push_back((uint8_t)spoken.size()); four.insert(four.end(), spoken.begin(), spoken.end());
			};
			effect(55, kUse, 50, 1 | 8, 2, "Click.");
			effect(55, kUse, 0xFFFF, 0, -1, "It doesn't work.");
			effect(55, kOpen, 0, 0, -1, "");
			put16(four, 0);
			assert(parseThings(four.data(), four.size(), things, error) && things.effects.size() == 3);
			const ThingEffect *own = things.effect(1, 55, kUse, 0, 50), *usual = things.effect(1, 55, kUse, 0, kAnyOther);
			assert(own && own->with == 50 && own->after == 1 && own->secondGone && !own->firstGone && !own->taken && own->others[0].picture == 2 && own->line == "Click.");
			assert(usual && usual->line == "It doesn't work." && things.effect(1, 55, kOpen, 0) && !things.effect(1, 55, kUse, 0));
			int flags;
			char reply[32];
			assert(PanelBridge::loadThings(5, four.data(), four.size(), problem, sizeof(problem)));
			assert(PanelBridge::pairEffect(5, 1, 55, kUse, 0, 50, after, others, count, 1, reply, sizeof(reply), flags) && flags == (4 | 8) && count == 1 && others[2] == 2 && std::string(reply) == "Click.");
			assert(PanelBridge::pairEffect(5, 1, 55, kUse, 0, 61, after, others, count, 1, reply, sizeof(reply), flags) && flags == 0 && count == 0 && std::string(reply) == "It doesn't work.");
			assert(!PanelBridge::pairEffect(5, 1, 55, kUnlock, 0, 50, after, others, count, 1, reply, sizeof(reply), flags));
			int with = -1;
			assert(PanelBridge::effectAt(5, 0, room, id, kind, from, &with) && kind == kOpen && with == 0);
			std::vector<uint8_t> badAfter = four;
			badAfter[4 + 2 + 2 + 2 + 2 + 1 + 2 + 2 + 2 + 2 + 1 + 1 + 2] = 16; // (an after past its bits)
			assert(!parseThings(badAfter.data(), badAfter.size(), things, error) && error == "bad effect");
			std::vector<uint8_t> asThree = four;
			asThree[3] = '3'; // (read as "SVO3": the seconds misread, refused whole)
			assert(!parseThings(asThree.data(), asThree.size(), things, error));
		}
		// ("SVO5", from 0195: then the main power, its picture off and the
		// places dark while it is off; found by game and place.)
		{
			// (Rooms 1 and 8, the power one of 8's things, in its picture 0.)
			std::vector<uint8_t> five = {'S', 'V', 'O', '5'};
			put16(five, 2); put16(five, 1); put16(five, 1); put16(five, 50); five.push_back(0); put16(five, 0);
			put16(five, 8); put16(five, 1); put16(five, 157); five.push_back(0); put16(five, 0);
			put16(five, 0); // (no effects)
			put16(five, 0); // (no parents)
			put16(five, 8); put16(five, 157); five.push_back(1);
			put16(five, 3); put16(five, 9); put16(five, 3); put16(five, 22);
			assert(parseThings(five.data(), five.size(), things, error) && things.powerRoom == 8 && things.powerId == 157 && things.powerOff == 1);
			assert(things.unpowered.size() == 3 && things.unpowered[0] == 3 && things.unpowered[2] == 22);
			assert(PanelBridge::loadThings(6, five.data(), five.size(), problem, sizeof(problem)));
			int off = 0;
			room = id = 0;
			assert(PanelBridge::mainPower(6, room, id, off) && room == 8 && id == 157 && off == 1);
			assert(PanelBridge::unpowered(6, 9) && PanelBridge::unpowered(6, 3) && !PanelBridge::unpowered(6, 1) && !PanelBridge::unpowered(7, 9) && !PanelBridge::mainPower(5, room, id, off));
			std::vector<uint8_t> cut(five.begin(), five.end() - 2); // (one place short)
			assert(!parseThings(cut.data(), cut.size(), things, error));
			std::vector<uint8_t> odd = five;
			odd[odd.size() - 9] = 2; // (an off picture past 1)
			assert(!parseThings(odd.data(), odd.size(), things, error) && error == "bad main power");
			std::vector<uint8_t> none = {'S', 'V', 'O', '5'};
			put16(none, 0); put16(none, 0); put16(none, 0); put16(none, 0); put16(none, 0); none.push_back(0); put16(none, 0);
			assert(parseThings(none.data(), none.size(), things, error) && !things.powerId && things.unpowered.empty());
			// (One that is none of its things, or starts in its picture off: read,
			// the power dropped, so nothing is dark from the start.)
			std::vector<uint8_t> stranger = five;
			stranger[stranger.size() - 11] = 158 & 0xFF; // (power object 158)
			assert(parseThings(stranger.data(), stranger.size(), things, error) && !things.powerId && things.unpowered.empty());
			std::vector<uint8_t> startsOff = five;
			startsOff[4 + 2 + 2 + 2 + 2 + 1 + 2 + 2 + 2 + 2] = 1; // (157 drawn in its picture 1 at the start)
			assert(parseThings(startsOff.data(), startsOff.size(), things, error) && !things.powerId && things.unpowered.empty());
			// ("SVO6", from 0240: then the close-ups a thing's script shows,
			// the mansion's wall safe's keypad: its verbs, the scene and the
			// part shown, the keys and their lines, the code, each answer.)
			std::vector<uint8_t> six = five;
			six[3] = '6';
			const size_t sixth = six.size();
			six.push_back(1);
			put16(six, 9); put16(six, 219); put16(six, 1 << kOpen | 1 << kUse); put16(six, 43); put16(six, 0);
			six.push_back(3);
			for (int key : {300, 429, 430}) { put16(six, key); six.push_back((uint8_t)(key % 10)); six.push_back(1); six.push_back((uint8_t)('0' + key % 10)); }
			six.push_back(4); put(six, {9, 0, 0, 0});
			six.push_back(1); six.push_back(0);
			six.push_back(0); six.push_back(4); put(six, {'N', 'o', 'p', 'e'});
			assert(parseThings(six.data(), six.size(), things, error) && things.closeUps.size() == 1 && things.powerId == 157);
			const CloseUp &safe = things.closeUps[0];
			assert(safe.room == 9 && safe.id == 219 && safe.closeUp == 43 && safe.keys.size() == 3 && safe.keys[1].id == 429 && safe.keys[1].value == 9 && safe.keys[1].line == "9");
			assert(safe.code.size() == 4 && safe.code[0] == 9 && safe.code[1] == 0 && safe.right == 1 && safe.rightLine.empty() && safe.wrong == 0 && safe.wrongLine == "Nope");
			assert(PanelBridge::loadThings(7, six.data(), six.size(), problem, sizeof(problem)) && PanelBridge::closeUpCount(7) == 1 && PanelBridge::closeUpCount(6) == 0);
			int kinds = 0, left = -1, keys = 0, presses = 0, picture = -1, value = -1;
			char shows[8];
			assert(PanelBridge::closeUpThing(7, 0, room, id, kinds) && room == 9 && id == 219 && kinds == (1 << kOpen | 1 << kUse) && !PanelBridge::closeUpThing(7, 1, room, id, kinds));
			assert(PanelBridge::closeUpScene(7, 0, room, left, keys, presses) && room == 43 && left == 0 && keys == 3 && presses == 4);
			assert(PanelBridge::closeUpKey(7, 0, 2, id, value, shows, sizeof(shows)) && id == 430 && value == 0 && std::string(shows) == "0" && !PanelBridge::closeUpKey(7, 0, 3, id, value, shows, sizeof(shows)));
			assert(PanelBridge::closeUpCode(7, 0, 0) == 9 && PanelBridge::closeUpCode(7, 0, 3) == 0 && PanelBridge::closeUpCode(7, 0, 4) == -1);
			assert(PanelBridge::closeUpAnswer(7, 0, true, picture, shows, sizeof(shows)) && picture == 1 && !*shows);
			assert(PanelBridge::closeUpAnswer(7, 0, false, picture, shows, sizeof(shows)) && picture == 0 && std::string(shows) == "Nope");
			for (size_t cut = 1; cut < six.size() - sixth; ++cut) {
				std::vector<uint8_t> shorter(six.begin(), six.end() - cut);
				assert(!parseThings(shorter.data(), shorter.size(), things, error));
			}
			std::vector<uint8_t> past = six;
			past[sixth + 1 + 10 + 1 + 3 * 5 + 1 + 1] = 7; // (a press no key gives)
			assert(!parseThings(past.data(), past.size(), things, error) && error == "bad close-up");
			std::vector<uint8_t> unseen = six;
			unseen[sixth + 1 + 4] = unseen[sixth + 1 + 5] = 0; // (shown by no verb)
			assert(!parseThings(unseen.data(), unseen.size(), things, error) && error == "bad close-up");
			std::vector<uint8_t> asFive = six;
			asFive[3] = '5'; // (read as "SVO5": the close-ups left over, refused whole)
			assert(!parseThings(asFive.data(), asFive.size(), things, error));
			std::vector<uint8_t> noneShown(five.begin(), five.end());
			noneShown[3] = '6'; noneShown.push_back(0);
			assert(parseThings(noneShown.data(), noneShown.size(), things, error) && things.closeUps.empty() && things.powerId == 157);
			// ("SVO7", from 0242: each close-up goes on with a view's turns, the
			// thing seen, its buttons and coins; a keypad has none, a view no
			// keys and no code: the mansion's telescope, turned by two buttons
			// a step at a time, a coin in its slot paying a turn, the part shown
			// at one turn following the painting.)
			const std::vector<uint8_t> keypad(six.begin() + sixth + 1, six.end());
			auto seven = [&](int start, int turnCount, int firstAfter, bool keypadTurns, int coins, bool coded) {
				std::vector<uint8_t> v = five;
				v[3] = '7';
				v.push_back(2);
				v.insert(v.end(), keypad.begin(), keypad.end());
				v.push_back(0); // (its start)
				if (keypadTurns) { put(v, {1, 0}); for (int k = 0; k < 6; ++k) put16(v, 0); } else v.push_back(0);
				put16(v, 0); put16(v, 0); put(v, {0, 0});
				put16(v, 28); put16(v, 413); put16(v, 1 << kUse); put16(v, 34); put16(v, 640);
				put(v, {0}); // (no keys)
				if (coded) put(v, {1, 1}); else v.push_back(0);
				put(v, {0, 0, 0, 0});
				put(v, {start, turnCount});
				static const int values[] = {1, 0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16};
				for (int t = 0; t < turnCount; ++t) {
					v.push_back(values[t]);
					for (int seen = 0; seen < 2; ++seen) { put16(v, values[t] ? 34 : 35); put16(v, values[t] == 2 && seen ? 0 : values[t] * 320 % 1280); put16(v, values[t] ? 240 : 120); }
				}
				put16(v, 9); put16(v, 218);
				v.push_back(2);
				put16(v, 411); v.push_back(kPush); put(v, {1, '<'});
				for (int t = 0; t < turnCount; ++t) v.push_back(t ? (t == 1 ? 1 : 0) : firstAfter);
				put16(v, 412); v.push_back(kPush); put(v, {1, '>'});
				for (int t = 0; t < turnCount; ++t) v.push_back(t == 0 ? 2 : t == 1 ? 0 : t);
				v.push_back(coins);
				for (int k = 0; k < coins; ++k) { put16(v, 414); put16(v, 36 + k); }
				return v;
			};
			std::vector<uint8_t> scope = seven(1, 3, 1, false, 1, false);
			assert(parseThings(scope.data(), scope.size(), things, error) && things.closeUps.size() == 2 && !things.closeUps[0].view() && things.closeUps[1].view());
			assert(things.closeUps[0].keys.size() == 3 && things.closeUps[0].turns.empty() && things.closeUps[1].turns.size() == 3 && things.closeUps[1].coins.size() == 1);
			assert(PanelBridge::loadThings(8, scope.data(), scope.size(), problem, sizeof(problem)) && PanelBridge::closeUpCount(8) == 2);
			int start = -1, turns = 0, seenRoom = 0, seen = 0, ticks = 0, verb = 0, next = -1, slot = 0, coin = 0;
			assert(!PanelBridge::closeUpView(8, 0, start, turns, seenRoom, seen) && PanelBridge::closeUpScene(8, 0, room, left, keys, presses) && keys == 3 && presses == 4);
			assert(PanelBridge::closeUpView(8, 1, start, turns, seenRoom, seen) && start == 1 && turns == 3 && seenRoom == 9 && seen == 218);
			assert(PanelBridge::closeUpThing(8, 1, room, id, kinds) && room == 28 && id == 413 && kinds == 1 << kUse);
			assert(PanelBridge::closeUpScene(8, 1, room, left, keys, presses) && room == 34 && left == 640 && keys == 0 && presses == 0);
			assert(PanelBridge::closeUpTurn(8, 1, 0, 0, value, room, left, ticks) && value == 1 && room == 34 && left == 320 && ticks == 240);
			assert(PanelBridge::closeUpTurn(8, 1, 1, 1, value, room, left, ticks) && value == 0 && room == 35 && left == 0 && ticks == 120);
			assert(PanelBridge::closeUpTurn(8, 1, 2, 0, value, room, left, ticks) && value == 2 && left == 640 && PanelBridge::closeUpTurn(8, 1, 2, 1, value, room, left, ticks) && left == 0);
			assert(!PanelBridge::closeUpTurn(8, 1, 3, 0, value, room, left, ticks) && !PanelBridge::closeUpTurn(8, 1, 0, 2, value, room, left, ticks) && !PanelBridge::closeUpTurn(8, 0, 0, 0, value, room, left, ticks));
			assert(PanelBridge::closeUpButtons(8, 1) == 2 && PanelBridge::closeUpButtons(8, 0) == 0);
			assert(PanelBridge::closeUpButton(8, 1, 0, 0, id, verb, next, shows, sizeof(shows)) && id == 411 && verb == kPush && next == 1 && std::string(shows) == "<");
			assert(PanelBridge::closeUpButton(8, 1, 1, 0, id, verb, next, shows, sizeof(shows)) && id == 412 && next == 2);
			assert(PanelBridge::closeUpButton(8, 1, 1, 2, id, verb, next, shows, sizeof(shows)) && next == 2); // (at its end)
			assert(!PanelBridge::closeUpButton(8, 1, 2, 0, id, verb, next, shows, sizeof(shows)) && !PanelBridge::closeUpButton(8, 1, 0, 3, id, verb, next, shows, sizeof(shows)));
			assert(PanelBridge::closeUpCoin(8, 1, 0, slot, coin) && slot == 414 && coin == 36 && !PanelBridge::closeUpCoin(8, 1, 1, slot, coin) && !PanelBridge::closeUpCoin(8, 0, 0, slot, coin));
			assert(PanelBridge::closeUpCode(8, 0, 0) == 9 && PanelBridge::closeUpCode(8, 1, 0) == -1);
			for (size_t less = 1; less < scope.size() - sixth; ++less) {
				std::vector<uint8_t> shorter(scope.begin(), scope.end() - less);
				assert(!parseThings(shorter.data(), shorter.size(), things, error));
			}
			std::vector<uint8_t> asSix = scope;
			asSix[3] = '6'; // (read as "SVO6": its turns left over, refused whole)
			assert(!parseThings(asSix.data(), asSix.size(), things, error));
			// (Refused: a start that is none of its turns; a turn after past its
			// turns; two turns of one value; a keypad with turns; a view with a
			// code; more turns or coins than a file holds. As many as it holds:
			// read.)
			for (const std::vector<uint8_t> &refused : {seven(4, 3, 1, false, 1, false), seven(1, 3, 3, false, 1, false), seven(1, 3, 1, true, 1, false), seven(1, 3, 1, false, 1, true),
				seven(1, PanelBridge::kMostTurns + 1, 1, false, 1, false), seven(1, 3, 1, false, PanelBridge::kMostCoins + 1, false)})
				assert(!parseThings(refused.data(), refused.size(), things, error) && error == "bad close-up");
			std::vector<uint8_t> again = scope;
			const size_t turnsAt = scope.size() - (1 + 4) - (1 + 2 * (2 + 1 + 2 + 3)) - 4 - 3 * 13; // (before the thing seen, the buttons, the coin)
			assert(scope[turnsAt] == 1 && scope[turnsAt + 13] == 0);
			again[turnsAt + 13] = 1; // (the second turn's value the first's)
			assert(!parseThings(again.data(), again.size(), things, error) && error == "bad close-up");
			std::vector<uint8_t> most = seven(1, PanelBridge::kMostTurns, 1, false, PanelBridge::kMostCoins, false);
			assert(parseThings(most.data(), most.size(), things, error) && things.closeUps[1].turns.size() == (size_t)PanelBridge::kMostTurns && things.closeUps[1].coins.size() == (size_t)PanelBridge::kMostCoins);
			PanelBridge::clearThings();
			assert(PanelBridge::closeUpCount(8) == 0);
			// ("SVO8", from 0248: each close-up goes on with a film (none: u16
			// 0), then the marks and the answers that read them. The mansion's
			// TV: on first a while, then its studio, the one there saying his
			// lines and the sign blinking, its mark left for the kid; the
			// typewriter's answers by the marks.)
			auto line = [](std::vector<uint8_t> &v, const char *text) { v.push_back((uint8_t)std::strlen(text)); for (const char *c = text; *c; ++c) v.push_back((uint8_t)*c); };
			struct Ev { int tick, id, picture; const char *line; };
			int leadTicks = 126;
			auto eight = [&](const std::vector<Ev> &evs, int length, int mark, int facing, int leadPicture, int markCount, std::initializer_list<int> answerMarks, bool keyedFilm) {
				std::vector<uint8_t> v = five;
				v[3] = '8';
				v.push_back(3);
				v.insert(v.end(), keypad.begin(), keypad.end());
				put(v, {0, 0}); put16(v, 0); put16(v, 0); put(v, {0, 0}); // (a keypad: no turns, nothing seen, no buttons, no coins)
				put16(v, 0); // (no film)
				put16(v, 28); put16(v, 413); put16(v, 1 << kUse); put16(v, 34); put16(v, 640);
				put(v, {0, 0, 0, 0, 0, 0}); // (no keys, no code, its answers none)
				put(v, {1, 1, 1}); for (int k = 0; k < 2; ++k) { put16(v, 34); put16(v, 640); put16(v, 240); }
				put16(v, 0); put16(v, 0); put(v, {0, 0});
				put16(v, 0); // (no film)
				put16(v, 17); put16(v, 190); put16(v, 1 << kTurnOn | 1 << kUse); put16(v, 40); put16(v, 0);
				if (keyedFilm) { v.push_back(1); put16(v, 300); v.push_back(0); line(v, "0"); put(v, {1, 0}); } else put(v, {0, 0});
				put(v, {0, 0, 0, 0});
				put(v, {0, 0}); put16(v, 0); put16(v, 0); put(v, {0, 0});
				put16(v, length); put16(v, leadTicks); v.push_back(leadPicture);
				put16(v, 17); put16(v, 136); put16(v, 104); v.push_back(facing); v.push_back(3);
				v.push_back(evs.size());
				for (const Ev &e : evs) { put16(v, e.tick); put16(v, e.id); v.push_back(e.picture); line(v, e.line); }
				put(v, {0, mark, 1}); line(v, "Off");
				v.push_back(markCount);
				for (int k = 0; k < markCount; ++k) v.push_back(k & 1);
				put16(v, answerMarks.size());
				int n = 0;
				for (int marks : answerMarks) {
					const bool mailbox = n++ == 2;
					put16(v, mailbox ? 1 : 27); put16(v, mailbox ? 276 : 416); put(v, {kUse, mailbox ? 1 : 0}); put16(v, 222); put16(v, mailbox ? 50 : 0); v.push_back(marks);
					if (mailbox) { put(v, {1 | 2, 1}); put16(v, 1); put16(v, 58); put(v, {1, 0}); line(v, "Taken"); }
					else { put(v, {0, 0, marks == 1 ? 2 : 0}); line(v, marks == 1 ? "Typed" : "No"); }
				}
				return v;
			};
			const std::vector<Ev> film = {{66, 0, 1, "Hi"}, {102, 266, 0, ""}, {168, 266, 1, ""}, {1308, 0, 0, ""}};
			std::vector<uint8_t> tv = eight(film, 1308, 0, 2, 1, 2, {0, 1, 2}, false);
			assert(parseThings(tv.data(), tv.size(), things, error) && things.closeUps.size() == 3 && things.closeUps[2].isFilm() && !things.closeUps[2].view());
			assert(!things.closeUps[0].isFilm() && !things.closeUps[1].isFilm() && things.closeUps[1].view() && things.marks.size() == 2 && things.marked.size() == 3);
			assert(PanelBridge::loadThings(9, tv.data(), tv.size(), problem, sizeof(problem)) && PanelBridge::closeUpCount(9) == 3);
			int length = 0, lead = 0, leadPicture = 0, costume = 0, fx = 0, fy = 0, facing = 0, color = 0, events = 0, filmAfter = -1, mark = -1, tick = 0, need = -1, flags = 0, sets = 0;
			bool powered = false;
			char offSaid[8], said[16];
			assert(PanelBridge::closeUpFilm(9, 2, length, lead, leadPicture, costume, fx, fy, facing, color, events, filmAfter, mark, powered, offSaid, sizeof(offSaid)));
			assert(length == 1308 && lead == 126 && leadPicture == 1 && costume == 17 && fx == 136 && fy == 104 && facing == 2 && color == 3 && events == 4 && filmAfter == 0 && mark == 0 && powered && std::string(offSaid) == "Off");
			assert(!PanelBridge::closeUpFilm(9, 0, length, lead, leadPicture, costume, fx, fy, facing, color, events, filmAfter, mark, powered, offSaid, sizeof(offSaid)) &&
				!PanelBridge::closeUpFilm(9, 1, length, lead, leadPicture, costume, fx, fy, facing, color, events, filmAfter, mark, powered, offSaid, sizeof(offSaid)) &&
				!PanelBridge::closeUpFilm(9, 3, length, lead, leadPicture, costume, fx, fy, facing, color, events, filmAfter, mark, powered, offSaid, sizeof(offSaid)));
			assert(!PanelBridge::closeUpView(9, 2, start, turns, seenRoom, seen) && PanelBridge::closeUpView(9, 1, start, turns, seenRoom, seen) && PanelBridge::closeUpCode(9, 2, 0) == -1);
			assert(PanelBridge::closeUpThing(9, 2, room, id, kinds) && room == 17 && id == 190 && kinds == (1 << kTurnOn | 1 << kUse));
			assert(PanelBridge::closeUpScene(9, 2, room, left, keys, presses) && room == 40 && keys == 0 && presses == 0);
			assert(PanelBridge::closeUpFilmEvent(9, 2, 0, tick, id, picture, said, sizeof(said)) && tick == 66 && id == 0 && picture == 1 && std::string(said) == "Hi");
			assert(PanelBridge::closeUpFilmEvent(9, 2, 2, tick, id, picture, said, sizeof(said)) && tick == 168 && id == 266 && picture == 1 && !*said);
			assert(PanelBridge::closeUpFilmEvent(9, 2, 3, tick, id, picture, said, sizeof(said)) && tick == 1308 && !id && !picture && !PanelBridge::closeUpFilmEvent(9, 2, 4, tick, id, picture, said, sizeof(said)));
			assert(PanelBridge::markCount(9) == 2 && PanelBridge::markKind(9, 0) == 0 && PanelBridge::markKind(9, 1) == 1 && PanelBridge::markKind(9, 2) == -1 && PanelBridge::markCount(8) == 0);
			assert(PanelBridge::markReader(9, 27, 416, kUse, 222, need) && need == 0 && PanelBridge::markReader(9, 1, 276, kUse, 222, need) && need == 50);
			assert(!PanelBridge::markReader(9, 27, 416, kUse, 221, need) && !PanelBridge::markReader(9, 27, 416, kOpen, 222, need) && !PanelBridge::markReader(8, 27, 416, kUse, 222, need));
			int others[3 * 4], count = 0;
			assert(PanelBridge::markedAnswer(9, 27, 416, kUse, 0, 222, 1, after, others, count, 4, said, sizeof(said), flags, sets) && std::string(said) == "Typed" && sets == 2 && !count && !flags && after == 0);
			assert(PanelBridge::markedAnswer(9, 27, 416, kUse, 0, 222, 0, after, others, count, 4, said, sizeof(said), flags, sets) && std::string(said) == "No" && sets == 0);
			assert(!PanelBridge::markedAnswer(9, 27, 416, kUse, 0, 222, 3, after, others, count, 4, said, sizeof(said), flags, sets)); // (not recorded so)
			assert(!PanelBridge::markedAnswer(9, 27, 416, kUse, 1, 222, 0, after, others, count, 4, said, sizeof(said), flags, sets));
			assert(PanelBridge::markedAnswer(9, 1, 276, kUse, 1, 222, 2, after, others, count, 4, said, sizeof(said), flags, sets) && after == 1 && flags == 1 && count == 1 &&
				others[0] == 1 && others[1] == 58 && others[2] == 1 && std::string(said) == "Taken");
			// (Any order of the answers: the same.)
			std::vector<uint8_t> reordered = eight(film, 1308, 0, 2, 1, 2, {1, 0, 2}, false);
			assert(parseThings(reordered.data(), reordered.size(), things, error) && things.marked[0].room == 1 && things.marked[1].marks == 0 && things.marked[2].marks == 1);
			// (No close-ups, no marks: read.)
			std::vector<uint8_t> bare = five;
			bare[3] = '8'; put(bare, {0, 0}); put16(bare, 0);
			assert(parseThings(bare.data(), bare.size(), things, error) && things.closeUps.empty() && things.marks.empty() && things.marked.empty() && things.powerId == 157);
			// (Cut short anywhere: refused whole; read as "SVO7", the film left over.)
			for (size_t less = 1; less < tv.size() - sixth; ++less) {
				std::vector<uint8_t> shorter(tv.begin(), tv.end() - less);
				assert(!parseThings(shorter.data(), shorter.size(), things, error));
			}
			std::vector<uint8_t> asSeven = tv;
			asSeven[3] = '7';
			assert(!parseThings(asSeven.data(), asSeven.size(), things, error));
			// (Refused: an event past its end, events out of order, a way past
			// four, a picture past 1 meanwhile, a mark past the marks, a film
			// with keys; marks past those a file holds, an answer's marks past
			// the marks, an answer twice; more events than a file holds.)
			for (const std::vector<uint8_t> &refused : {eight({{1400, 0, 1, "Hi"}}, 1308, 0, 2, 1, 2, {0, 1, 2}, false), eight({{168, 0, 1, "Hi"}, {66, 266, 0, ""}}, 1308, 0, 2, 1, 2, {0, 1, 2}, false),
				eight(film, 1308, 0, 4, 1, 2, {0, 1, 2}, false), eight(film, 1308, 0, 2, 2, 2, {0, 1, 2}, false), eight(film, 1308, 0, 2, 1, 2, {0, 1, 2}, true)})
				assert(!parseThings(refused.data(), refused.size(), things, error) && error == "bad close-up");
			for (const std::vector<uint8_t> &refused : {eight(film, 1308, 2, 2, 1, 2, {0, 1, 2}, false), eight(film, 1308, 0, 2, 1, PanelBridge::kMostMarks + 1, {0, 1, 2}, false), eight(film, 1308, 0, 2, 1, 1, {0, 1, 2}, false),
				eight(film, 1308, 0, 2, 1, 2, {0, 4, 2}, false)})
				assert(!parseThings(refused.data(), refused.size(), things, error) && error == "bad marks");
			// (From a review of 0248: its lead past its length, or past
			// kMostFilmLead (its thing shown, taps waiting, meanwhile): refused;
			// at the most, read.)
			for (int tooLong : {1309, PanelBridge::kMostFilmLead + 1, 65535}) {
				leadTicks = tooLong;
				std::vector<uint8_t> refused = eight(film, 2000, 0, 2, 1, 2, {0, 1, 2}, false);
				assert(!parseThings(refused.data(), refused.size(), things, error) && error == "bad close-up");
				refused = eight(film, 1308, 0, 2, 1, 2, {0, 1, 2}, false);
				assert(!parseThings(refused.data(), refused.size(), things, error) && error == "bad close-up");
			}
			leadTicks = PanelBridge::kMostFilmLead;
			std::vector<uint8_t> longest = eight(film, 1308, 0, 2, 1, 2, {0, 1, 2}, false);
			assert(parseThings(longest.data(), longest.size(), things, error) && things.closeUps[2].film.lead == PanelBridge::kMostFilmLead);
			leadTicks = 1308;
			longest = eight(film, 1308, 0, 2, 1, 2, {0, 1, 2}, false);
			assert(!parseThings(longest.data(), longest.size(), things, error) && error == "bad close-up");
			leadTicks = 126;
			std::vector<uint8_t> twice = eight(film, 1308, 0, 2, 1, 2, {0, 0, 2}, false);
			assert(!parseThings(twice.data(), twice.size(), things, error) && error == "an answer twice");
			// (As many events as a file holds: read; one more: refused.)
			std::vector<Ev> many;
			for (int k = 0; k <= PanelBridge::kMostFilmEvents; ++k) many.push_back({k, 266, k & 1, ""});
			std::vector<uint8_t> crowded = eight(many, 1308, 0, 2, 1, 2, {0, 1, 2}, false);
			assert(!parseThings(crowded.data(), crowded.size(), things, error) && error == "bad close-up");
			many.pop_back();
			crowded = eight(many, 1308, 0, 2, 1, 2, {0, 1, 2}, false);
			assert(parseThings(crowded.data(), crowded.size(), things, error) && things.closeUps[2].film.events.size() == (size_t)PanelBridge::kMostFilmEvents);
			PanelBridge::clearThings();
			assert(PanelBridge::markCount(9) == 0 && PanelBridge::closeUpCount(9) == 0);
		}
		// (From 0247, Sam & Max's: "SVO7" with one thing's answers only (no
		// second), no main power and no close-ups; one taken from its picture
		// 0, its place then in picture 1; one saying a line and giving
		// another (an other's picture 2) after setting its picture. Read whole
		// or not at all.)
		{
			std::vector<uint8_t> snm = {'S', 'V', 'O', '7'};
			put16(snm, 1); put16(snm, 20); put16(snm, 2);
			put16(snm, 205); snm.push_back(0); put16(snm, 1 << kUse | 1 << kPickUp);
			put16(snm, 209); snm.push_back(0); put16(snm, PanelBridge::kThingAway);
			put16(snm, 2);
			put16(snm, 20); put16(snm, 205); put(snm, {kUse, 0}); put16(snm, 0); put(snm, {1 | 2, 0, 5, 'M', 'i', 'n', 'e', '.'});
			put16(snm, 20); put16(snm, 205); put(snm, {kPickUp, 0}); put16(snm, 0); put(snm, {0, 2});
			put16(snm, 20); put16(snm, 209); snm.push_back(1); put16(snm, 20); put16(snm, 209); snm.push_back(2);
			put(snm, {5, 'H', 'e', 'r', 'e', '.'});
			put16(snm, 0); // (no parents)
			put16(snm, 0); put16(snm, 0); snm.push_back(0); put16(snm, 0); // (no main power)
			snm.push_back(0); // (no close-ups)
			assert(parseThings(snm.data(), snm.size(), things, error) && things.effects.size() == 2 && !things.powerId && things.unpowered.empty() && things.closeUps.empty());
			const ThingEffect *took = things.effect(20, 205, kUse, 0), *gave = things.effect(20, 205, kPickUp, 0);
			assert(took && took->taken && took->after == 1 && took->others.empty() && took->line == "Mine." && !things.effect(20, 205, kUse, 1));
			assert(gave && !gave->taken && gave->after == 0 && gave->others.size() == 2 && gave->others[0].picture == 1 && gave->others[1].picture == 2 && gave->line == "Here.");
			for (size_t cut = 1; cut < snm.size() - 4; ++cut) assert(!parseThings(snm.data(), snm.size() - cut, things, error));
			bool taken = false;
			assert(PanelBridge::loadThings(6, snm.data(), snm.size(), problem, sizeof(problem)) && PanelBridge::effectCount(6) == 2);
			assert(PanelBridge::thingEffect(6, 20, 205, kUse, 0, after, others, count, 2, said, sizeof(said), &taken) && taken && after == 1 && !count && std::string(said) == "Mine.");
			assert(PanelBridge::thingEffect(6, 20, 205, kPickUp, 0, after, others, count, 2, said, sizeof(said), &taken) && !taken && count == 2 && others[5] == 2);
			// (From 0258: read whole through the newer reader too: given, its
			// one line by the one played.)
			int afterOld = -1, flagsOld = -1, othersOld[4 * 2], countOld = -1, linesOld = -1;
			assert(PanelBridge::thingAnswer(6, 20, 205, kPickUp, 0, 0, afterOld, flagsOld, othersOld, countOld, 2, linesOld) && countOld == 2 && linesOld == 1 && !flagsOld);
			assert(othersOld[2] == 1 && !othersOld[3] && !othersOld[6] && othersOld[7] == 1);
			assert(PanelBridge::thingAnswer(6, 20, 205, kUse, 0, 0, afterOld, flagsOld, othersOld, countOld, 2, linesOld) && flagsOld == 1 && afterOld == 1 && linesOld == 1);
			PanelBridge::clearThings();
		// (From 0258, "SVO9": SVO8 with its answers whole. Sam & Max-shaped:
		// one answer from its thing's picture 3 to 4, taken, saying said3
		// lines (the one played's, Max's in his costume and colour, no one's
		// in its colour); another setting an other to its picture 3, giving
		// one from a place and one in no place (room 0), its line the one
		// played's; no marks; the two given's own inventory pictures. Every
		// version's lines and given filled; the bridge's older readers as
		// before (given: picture 2, one past 1 left out). Cut short anywhere,
		// or anything out of range: refused whole.)
		{
			auto text = [](std::vector<uint8_t> &v, const char *s) { v.push_back((uint8_t)std::strlen(s)); for (const char *c = s; *c; ++c) v.push_back((uint8_t)*c); };
			struct Said { int speaker, costume, color; const char *line; };
			struct Other { int room, id, picture, given; };
			struct Icon { int id; const char *name; int width, height, mask; };
			auto nine = [&](int flags, const std::vector<Said> &lines, const std::vector<Other> &others9, const std::vector<Icon> &icons, int iconCount = -1) {
				std::vector<uint8_t> v = {'S', 'V', 'O', '9'};
				put16(v, 1); put16(v, 20); put16(v, 2);
				put16(v, 205); v.push_back(3); put16(v, 1 << kUse | 1 << kPickUp);
				put16(v, 209); v.push_back(0); put16(v, 0);
				put16(v, 2);
				put16(v, 20); put16(v, 205); put(v, {kUse, 3}); put16(v, 0); put(v, {4, flags, 0});
				v.push_back((uint8_t)lines.size());
				for (const Said &s : lines) {
					v.push_back((uint8_t)s.speaker);
					if (s.speaker != 0 && s.speaker != 255) put16(v, s.costume);
					if (s.speaker != 0) v.push_back((uint8_t)s.color);
					text(v, s.line);
				}
				put16(v, 20); put16(v, 205); put(v, {kPickUp, 0}); put16(v, 0); put(v, {0, 0, (int)others9.size()});
				for (const Other &o : others9) { put16(v, o.room); put16(v, o.id); put(v, {o.picture, o.given}); }
				put(v, {1, 0}); text(v, "Here.");
				put16(v, 0);                                      // (no parents)
				put16(v, 0); put16(v, 0); v.push_back(0); put16(v, 0); // (no main power)
				v.push_back(0);                                   // (no close-ups)
				v.push_back(0); put16(v, 0);                      // (no marks, no answers by them)
				put16(v, iconCount >= 0 ? iconCount : (int)icons.size());
				for (const Icon &c : icons) {
					put16(v, c.id); text(v, c.name); put16(v, c.width); put16(v, c.height);
					for (int k = 0; k < c.width * c.height; ++k) v.push_back(k ? (uint8_t)c.mask : 1);
					for (int k = 0; k < c.width * c.height; ++k) put(v, {10 * k, 20, 30});
				}
				return v;
			};
			const std::vector<Said> said3 = {{0, 0, 0, "Mine."}, {3, 3, 15, "Me too!"}, {255, 0, 2, "Beep."}};
			const std::vector<Other> others9 = {{20, 209, 3, 0}, {22, 221, 0, 1}, {0, 547, 0, 1}};
			const std::vector<Icon> icons = {{547, "Plum", 3, 2, 1}, {221, "Torch", 2, 1, 0}};
			std::vector<uint8_t> whole = nine(1, said3, others9, icons);
			assert(parseThings(whole.data(), whole.size(), things, error) && things.effects.size() == 2 && things.icons.size() == 2 && !things.powerId);
			const ThingEffect *took9 = things.effect(20, 205, kUse, 3), *gave9 = things.effect(20, 205, kPickUp, 0);
			assert(took9 && took9->taken && !took9->firstGone && took9->after == 4 && took9->line == "Mine." && took9->lines.size() == 3);
			assert(took9->lines[0].speaker == kSpeakerPlayed && took9->lines[0].color == -1 && took9->lines[1].speaker == 3 && took9->lines[1].costume == 3 && took9->lines[1].color == 15 &&
				took9->lines[1].text == "Me too!" && took9->lines[2].speaker == kSpeakerNone && !took9->lines[2].costume && took9->lines[2].color == 2 && took9->lines[2].text == "Beep.");
			assert(gave9 && !gave9->taken && gave9->others.size() == 3 && gave9->others[0].picture == 3 && !gave9->others[0].given && gave9->others[1].given && gave9->others[1].room == 22 &&
				gave9->others[2].given && !gave9->others[2].room && gave9->lines.size() == 1 && gave9->line == "Here.");
			const ThingIcon *plum = things.icon(547), *torch = things.icon(221);
			assert(things.icons[0].id == 221 && plum && torch && !things.icon(209) && plum->name == "Plum" && plum->width == 3 && plum->height == 2 && plum->picture.size() == 6);
			assert(plum->picture[0] == 0xFF00141Eu && plum->picture[1] == (0xFF000000u | 10u << 16 | 20u << 8 | 30u) && torch->picture[0] >> 24 == 0xFF && !torch->picture[1]);
			// (Through the bridge: whole, its lines one by one, the given carried by
			// their icons; the older readers as before.)
			assert(PanelBridge::loadThings(6, whole.data(), whole.size(), problem, sizeof(problem)) && PanelBridge::effectCount(6) == 2);
			int after9 = -1, flags9 = -1, others4[4 * 4], count9 = -1, lines9 = -1, speaker = -1, costume = -1, color = 0;
			char line9[16];
			assert(PanelBridge::thingAnswer(6, 20, 205, kUse, 3, 0, after9, flags9, others4, count9, 4, lines9) && after9 == 4 && flags9 == 1 && !count9 && lines9 == 3);
			assert(PanelBridge::answerLine(6, 20, 205, kUse, 3, 0, 1, speaker, costume, color, line9, sizeof(line9)) && speaker == 3 && costume == 3 && color == 15 && std::string(line9) == "Me too!");
			assert(PanelBridge::answerLine(6, 20, 205, kUse, 3, 0, 2, speaker, costume, color, line9, sizeof(line9)) && speaker == PanelBridge::kSpeakerNone && color == 2);
			assert(!PanelBridge::answerLine(6, 20, 205, kUse, 3, 0, 3, speaker, costume, color, line9, sizeof(line9)) && !PanelBridge::thingAnswer(6, 20, 205, kUse, 1, 0, after9, flags9, others4, count9, 4, lines9));
			assert(PanelBridge::thingAnswer(6, 20, 205, kPickUp, 0, 0, after9, flags9, others4, count9, 4, lines9) && count9 == 3 && lines9 == 1 && !flags9);
			assert(others4[2] == 3 && !others4[3] && others4[4] == 22 && others4[5] == 221 && !others4[6] && others4[7] == 1 && !others4[8] && others4[9] == 547 && others4[11] == 1);
			assert(PanelBridge::thingAnswer(6, 20, 205, kPickUp, 0, 0, after9, flags9, others4, count9, 1, lines9) && count9 == 1); // (as many as asked)
			int others3[3 * 4];
			assert(PanelBridge::thingEffect(6, 20, 205, kPickUp, 0, after, others3, count, 4, said, sizeof(said), &taken) && count == 2 && others3[2] == 2 && !others3[3] && others3[5] == 2 && std::string(said) == "Here.");
			assert(PanelBridge::thingEffect(6, 20, 205, kUse, 3, after, others3, count, 4, said, sizeof(said), &taken) && taken && after == 4 && std::string(said) == "Mine.");
			PanelBridge::clearItems();
			char item[16];
			assert(PanelBridge::addIcon(6, 547, nullptr) && PanelBridge::itemCount() == 1 && PanelBridge::itemName(0, item, sizeof(item)) == 4 && !std::strcmp(item, "Plum"));
			assert(PanelBridge::addIcon(6, 221, "lamp") && PanelBridge::itemName(1, item, sizeof(item)) == 4 && !std::strcmp(item, "lamp"));
			assert(!PanelBridge::addIcon(6, 209, nullptr) && !PanelBridge::addIcon(7, 547, nullptr) && PanelBridge::itemCount() == 2);
			PanelBridge::clearItems();
			PanelBridge::clearThings();
			// (Every version fills lines and given: the SVO7 above, one line by
			// the one played, its picture 2 given.)
			assert(parseThings(snm.data(), snm.size(), things, error) && things.effect(20, 205, kUse, 0)->lines.size() == 1 && things.effect(20, 205, kUse, 0)->lines[0].speaker == kSpeakerPlayed &&
				things.effect(20, 205, kPickUp, 0)->others[1].given && !things.effect(20, 205, kPickUp, 0)->others[0].given && things.icons.empty());
			// (No lines, no others, no icons: read.)
			std::vector<uint8_t> bare9 = nine(0, {}, {}, {});
			assert(parseThings(bare9.data(), bare9.size(), things, error) && things.effect(20, 205, kUse, 3)->lines.empty() && things.effect(20, 205, kUse, 3)->line.empty() && things.icons.empty());
			// (Cut short anywhere: refused whole; read as SVO8: refused.)
			for (size_t cut = 1; cut < whole.size() - 4; ++cut) assert(!parseThings(whole.data(), whole.size() - cut, things, error) && things.effects.empty() && things.icons.empty());
			std::vector<uint8_t> asEight = whole;
			asEight[3] = '8';
			assert(!parseThings(asEight.data(), asEight.size(), things, error));
			// (Refused: lines past kMostLines, an empty line, flags past 7, a
			// given past 1, one given in a picture, one in no place not given;
			// an icon of no thing, none wide, wider than kMostIconSide, a mask
			// past 1, icons past kMostIcons, an icon twice.)
			std::vector<Said> many(PanelBridge::kMostLines + 1, Said{0, 0, 0, "x"});
			std::vector<uint8_t> lots = nine(1, many, others9, icons);
			assert(!parseThings(lots.data(), lots.size(), things, error) && error == "too many lines" && things.effects.empty());
			many.pop_back();
			lots = nine(1, many, others9, icons);
			assert(parseThings(lots.data(), lots.size(), things, error) && things.effect(20, 205, kUse, 3)->lines.size() == (size_t)PanelBridge::kMostLines);
			for (const std::vector<uint8_t> &refused : {nine(1, {{0, 0, 0, ""}}, others9, icons), nine(8, said3, others9, icons), nine(1, said3, {{22, 221, 0, 2}}, icons),
				nine(1, said3, {{22, 221, 1, 1}}, icons), nine(1, said3, {{0, 209, 1, 0}}, icons)})
				assert(!parseThings(refused.data(), refused.size(), things, error) && error == "bad effect" && things.effects.empty());
			for (const std::vector<uint8_t> &refused : {nine(1, said3, others9, {{0, "None", 1, 1, 0}}), nine(1, said3, others9, {{547, "Flat", 0, 1, 0}}),
				nine(1, said3, others9, {{547, "Wide", PanelBridge::kMostIconSide + 1, 1, 0}}), nine(1, said3, others9, {{547, "Odd", 2, 2, 2}}),
				nine(1, said3, others9, {}, PanelBridge::kMostIcons + 1)})
				assert(!parseThings(refused.data(), refused.size(), things, error) && error == "bad icons" && things.icons.empty());
			std::vector<uint8_t> twice9 = nine(1, said3, others9, {{547, "Plum", 1, 1, 0}, {547, "Plum", 1, 1, 0}});
			assert(!parseThings(twice9.data(), twice9.size(), things, error) && error == "an icon twice");
			std::vector<uint8_t> biggest = nine(1, said3, others9, {{547, "Big", PanelBridge::kMostIconSide, PanelBridge::kMostIconSide, 1}});
			assert(parseThings(biggest.data(), biggest.size(), things, error) && things.icon(547)->picture.size() == (size_t)(PanelBridge::kMostIconSide * PanelBridge::kMostIconSide));
		}
		}
		// (From 0251, The Dig's and Full Throttle's, the same "SVO7": the
		// answers by their own verbs' kinds, The Dig's tap and Full Throttle's
		// hand, look and kick; one taken from its picture 0 leaving it 0 (as
		// The Dig's leaves it), one opening another. Each found by its own
		// kind only, from its own picture only.)
		{
			std::vector<uint8_t> v7 = {'S', 'V', 'O', '7'};
			put16(v7, 1); put16(v7, 23); put16(v7, 2);
			put16(v7, 182); v7.push_back(0); put16(v7, 0);
			put16(v7, 154); v7.push_back(0); put16(v7, 0);
			put16(v7, 4);
			put16(v7, 23); put16(v7, 182); put(v7, {kAct, 0}); put16(v7, 0); put(v7, {2, 0, 3, 'R', 'o', 'd'});
			put16(v7, 23); put16(v7, 154); put(v7, {kAct, 0}); put16(v7, 0); put(v7, {1, 1}); put16(v7, 23); put16(v7, 155); v7.push_back(1); v7.push_back(0);
			put16(v7, 23); put16(v7, 154); put(v7, {kHand, 1}); put16(v7, 0); put(v7, {0, 0, 2, 'N', 'o'});
			put16(v7, 23); put16(v7, 154); put(v7, {kPush, 0}); put16(v7, 0); put(v7, {0, 0, 4, 'O', 'w', '!', '!'});
			put16(v7, 0); // (no parents)
			put16(v7, 0); put16(v7, 0); v7.push_back(0); put16(v7, 0); // (no main power)
			v7.push_back(0); // (no close-ups)
			assert(parseThings(v7.data(), v7.size(), things, error) && things.effects.size() == 4);
			const ThingEffect *rod = things.effect(23, 182, kAct, 0), *lid = things.effect(23, 154, kAct, 0), *hand = things.effect(23, 154, kHand, 1), *kick = things.effect(23, 154, kPush, 0);
			assert(rod && rod->taken && rod->after == 0 && rod->line == "Rod" && !things.effect(23, 182, kPickUp, 0) && !things.effect(23, 182, kAct, 1));
			assert(lid && !lid->taken && lid->after == 1 && lid->others.size() == 1 && lid->others[0].id == 155 && lid->others[0].picture == 1 && lid->line.empty());
			assert(hand && hand->line == "No" && !things.effect(23, 154, kHand, 0) && kick && kick->line == "Ow!!" && !things.effect(23, 154, kLook, 0));
			for (size_t cut = 1; cut < v7.size() - 4; ++cut) assert(!parseThings(v7.data(), v7.size() - cut, things, error));
			bool taken = false;
			assert(PanelBridge::loadThings(8, v7.data(), v7.size(), problem, sizeof(problem)) && PanelBridge::effectCount(8) == 4);
			assert(PanelBridge::thingEffect(8, 23, 182, kAct, 0, after, others, count, 2, said, sizeof(said), &taken) && taken && after == 0 && !count && std::string(said) == "Rod");
			assert(PanelBridge::thingEffect(8, 23, 154, kAct, 0, after, others, count, 2, said, sizeof(said), &taken) && !taken && after == 1 && count == 1 && others[1] == 155 && others[2] == 1);
			assert(!PanelBridge::thingEffect(8, 23, 154, kAct, 1, after, others, count, 2, said, sizeof(said), &taken));
			PanelBridge::clearThings();
		}
		// (From 0254, Monkey Island's, the same "SVO7": the answers by its
		// panel's verbs' kinds (turned on, opened, pulled, picked up; none for
		// giving or walking), one taken from its picture 0 leaving it in 1 (its
		// game's picture of the place without it), the same line from both
		// pictures, one saying nothing but setting another. Each found by its
		// kind and picture only.)
		{
			std::vector<uint8_t> mi = {'S', 'V', 'O', '7'};
			put16(mi, 1); put16(mi, 29); put16(mi, 2);
			put16(mi, 391); mi.push_back(0); put16(mi, 0);
			put16(mi, 392); mi.push_back(0); put16(mi, 0);
			put16(mi, 5);
			put16(mi, 29); put16(mi, 391); put(mi, {kPickUp, 0}); put16(mi, 0); put(mi, {1 | 2, 0, 4, 'M', 'i', 'n', 'e'});
			put16(mi, 29); put16(mi, 391); put(mi, {kTurnOn, 0}); put16(mi, 0); put(mi, {0, 0, 2, 'N', 'o'});
			put16(mi, 29); put16(mi, 391); put(mi, {kTurnOn, 1}); put16(mi, 0); put(mi, {1, 0, 2, 'N', 'o'});
			put16(mi, 29); put16(mi, 392); put(mi, {kOpen, 0}); put16(mi, 0); put(mi, {0, 0, 4, 'S', 't', 'u', 'b'});
			put16(mi, 29); put16(mi, 392); put(mi, {kPull, 0}); put16(mi, 0); put(mi, {1, 1}); put16(mi, 29); put16(mi, 391); mi.push_back(1); mi.push_back(0);
			put16(mi, 0); // (no parents)
			put16(mi, 0); put16(mi, 0); mi.push_back(0); put16(mi, 0); // (no main power)
			mi.push_back(0); // (no close-ups)
			assert(parseThings(mi.data(), mi.size(), things, error) && things.effects.size() == 5);
			const ThingEffect *chicken = things.effect(29, 391, kPickUp, 0), *on0 = things.effect(29, 391, kTurnOn, 0), *on1 = things.effect(29, 391, kTurnOn, 1);
			const ThingEffect *opened = things.effect(29, 392, kOpen, 0), *pulled = things.effect(29, 392, kPull, 0);
			assert(chicken && chicken->taken && chicken->after == 1 && chicken->line == "Mine" && !things.effect(29, 391, kPickUp, 1) && !things.effect(29, 391, kGive, 0));
			assert(on0 && on1 && on0->line == "No" && on1->line == "No" && on0->after == 0 && on1->after == 1 && !things.effect(29, 391, kTurnOff, 0));
			assert(opened && opened->line == "Stub" && !opened->taken && pulled && pulled->line.empty() && pulled->after == 1 && pulled->others.size() == 1 && pulled->others[0].id == 391);
			for (size_t cut = 1; cut < mi.size() - 4; ++cut) assert(!parseThings(mi.data(), mi.size() - cut, things, error));
			bool taken = false;
			assert(PanelBridge::loadThings(0, mi.data(), mi.size(), problem, sizeof(problem)) && PanelBridge::effectCount(0) == 5);
			assert(PanelBridge::thingEffect(0, 29, 391, kPickUp, 0, after, others, count, 2, said, sizeof(said), &taken) && taken && after == 1 && !count && std::string(said) == "Mine");
			assert(PanelBridge::thingEffect(0, 29, 392, kPull, 0, after, others, count, 2, said, sizeof(said), &taken) && !taken && after == 1 && count == 1 && others[0] == 29 && others[1] == 391 && others[2] == 1 && !*said);
			assert(!PanelBridge::thingEffect(0, 29, 392, kPush, 0, after, others, count, 2, said, sizeof(said), &taken));
			PanelBridge::clearThings();
		}
		// (From 0260, Day of the Tentacle's and both Monkey Islands' two
		// things, the same "SVO7": Use of a thing carried (210) with one here
		// (392, from each picture: its own answer to 210, its usual one to any
		// other; one using the thing carried up and setting another), and Give
		// to someone, filed under kWorldPersonThing and their costume (24): their
		// own answer to 210 (used up: given), their usual one to any other. Each
		// found by its key and second only; none by a lookup of one thing.)
		{
			const int person = WorldCatalog::kWorldPersonThing + 24;
			std::vector<uint8_t> two = {'S', 'V', 'O', '7'};
			put16(two, 1); put16(two, 29); put16(two, 2);
			put16(two, 392); two.push_back(0); put16(two, 0);
			put16(two, 210); two.push_back(0); put16(two, 0);
			put16(two, 6);
			put16(two, 29); put16(two, 392); put(two, {kUse, 0}); put16(two, 210); put(two, {1 | 8, 1}); put16(two, 29); put16(two, 391); two.push_back(1); put(two, {3, 'Y', 'e', 's'});
			put16(two, 29); put16(two, 392); put(two, {kUse, 0}); put16(two, 0xFFFF); put(two, {0, 0, 2, 'N', 'o'});
			put16(two, 29); put16(two, 392); put(two, {kUse, 1}); put16(two, 0xFFFF); put(two, {1, 0, 4, 'N', 'o', 'p', 'e'});
			put16(two, 29); put16(two, 392); put(two, {kOpen, 0}); put16(two, 0); put(two, {1, 0, 0});
			put16(two, 29); put16(two, person); put(two, {kGive, 0}); put16(two, 210); put(two, {8, 0, 6, 'T', 'h', 'a', 'n', 'k', 's'});
			put16(two, 29); put16(two, person); put(two, {kGive, 0}); put16(two, 0xFFFF); put(two, {0, 0, 7, 'N', 'o', ' ', 't', 'h', 'x', '.'});
			put16(two, 0); // (no parents)
			put16(two, 0); put16(two, 0); two.push_back(0); put16(two, 0); // (no main power)
			two.push_back(0); // (no close-ups)
			assert(parseThings(two.data(), two.size(), things, error) && things.effects.size() == 6);
			const ThingEffect *used = things.effect(29, 392, kUse, 0, 210), *usual0 = things.effect(29, 392, kUse, 0, kAnyOther), *usual1 = things.effect(29, 392, kUse, 1, kAnyOther);
			const ThingEffect *given = things.effect(29, person, kGive, 0, 210), *refused = things.effect(29, person, kGive, 0, kAnyOther);
			assert(used && used->secondGone && !used->firstGone && !used->taken && used->after == 1 && used->others.size() == 1 && used->others[0].id == 391 && used->line == "Yes");
			assert(usual0 && usual0->line == "No" && usual0->after == 0 && usual1 && usual1->line == "Nope" && usual1->after == 1 && !things.effect(29, 392, kUse, 1, 210));
			assert(given && given->secondGone && given->line == "Thanks" && refused && !refused->secondGone && refused->line == "No thx.");
			assert(!things.effect(29, 392, kUse, 0) && !things.effect(29, person, kGive, 0) && !things.effect(29, 210, kGive, 0, person) && things.effect(29, 392, kOpen, 0));
			for (size_t cut = 1; cut < two.size() - 4; ++cut) assert(!parseThings(two.data(), two.size() - cut, things, error));
			int flags = 0;
			bool alone = false;
			assert(PanelBridge::loadThings(5, two.data(), two.size(), problem, sizeof(problem)) && PanelBridge::effectCount(5) == 6);
			assert(PanelBridge::pairEffect(5, 29, 392, kUse, 0, 210, after, others, count, 2, said, sizeof(said), flags) && flags == (4 | 8) && after == 1 && count == 1 && others[1] == 391 && std::string(said) == "Yes");
			assert(PanelBridge::pairEffect(5, 29, 392, kUse, 0, 211, after, others, count, 2, said, sizeof(said), flags) && flags == 0 && after == 0 && !count && std::string(said) == "No");
			assert(PanelBridge::pairEffect(5, 29, 392, kUse, 1, 210, after, others, count, 2, said, sizeof(said), flags) && flags == 0 && after == 1 && std::string(said) == "Nope");
			assert(PanelBridge::pairEffect(5, 29, person, kGive, 0, 210, after, others, count, 2, said, sizeof(said), flags) && flags == (4 | 8) && std::string(said) == "Thanks");
			assert(PanelBridge::pairEffect(5, 29, person, kGive, 0, 391, after, others, count, 2, said, sizeof(said), flags) && flags == 0 && std::string(said) == "No thx.");
			assert(!PanelBridge::pairEffect(5, 29, WorldCatalog::kWorldPersonThing + 25, kGive, 0, 210, after, others, count, 2, said, sizeof(said), flags));
			assert(!PanelBridge::thingEffect(5, 29, 392, kUse, 0, after, others, count, 2, said, sizeof(said), &alone) && PanelBridge::thingEffect(5, 29, 392, kOpen, 0, after, others, count, 2, said, sizeof(said), &alone) && after == 1);
			PanelBridge::clearThings();
		}
		std::vector<uint8_t> plain = {'S', 'V', 'O', '1'};
		put16(plain, 0);
		assert(PanelBridge::loadThings(3, plain.data(), plain.size(), problem, sizeof(problem)) && PanelBridge::effectCount(3) == 0);
		PanelBridge::clearThings();
	}
	std::puts("PASS: what a thing's own script does to a verb (from a picture: its picture after, the others, its line; any order; whole or not at all); a close-up's keypad, view (its turns, buttons, coins) or film (its lead, the one there, its events on their ticks, its mark); the marks and the answers that read them; Sam & Max's (taken, a thing given; no power, no close-ups); The Dig's and Full Throttle's (by their own verbs' kinds); Monkey Island's (by its panel's verbs' kinds); from 0258 SVO9, its answers whole (pictures past the second, flags apart, each line with who says it, the things given with their own pictures; cut short or out of range: refused whole; older readers as before); two things of the later games (Use with one here, Give to someone, own and usual answers)");

	// Things carried from a scene (the bridge; its picture below): only what differs from the
	// place without it, through the scene's palette; kept panel to panel and
	// without a panel; cleared.
	{
		PanelBridge::clear();
		const std::vector<uint8_t> scene = sceneBytes(1), bare = sceneBytes(1, false);
		assert(!PanelBridge::addItem(bare.data(), bare.size(), 50, "mug") && !PanelBridge::addItem(scene.data(), scene.size(), 51, "mug"));
		assert(PanelBridge::addItem(scene.data(), scene.size(), 50, "mug") && PanelBridge::itemCount() == 1);
		char name[16];
		assert(PanelBridge::itemName(0, name, sizeof(name)) == 3 && !strcmp(name, "mug"));
		const std::vector<uint8_t> data = panelBytes();
		char problem[64];
		assert(PanelBridge::load(data.data(), data.size(), problem, sizeof(problem)) && PanelBridge::itemCount() == 1);
		std::vector<uint8_t> broken = data; broken.pop_back();
		assert(!PanelBridge::load(broken.data(), broken.size(), problem, sizeof(problem)) && !PanelBridge::loaded() && PanelBridge::itemCount() == 1);
		assert(PanelBridge::load(data.data(), data.size(), problem, sizeof(problem)));
		// A line in one of the panel's colours, else (none, or none of its
		// colours) in its talk colour.
		assert(PanelBridge::talkColor(-1) == rgb(11) && PanelBridge::talkColor(256) == rgb(11) && PanelBridge::talkColor(5) == rgb(5));
		for (int color : {5, -1}) {
			std::vector<uint32_t> said((size_t)200 * 140, 0);
			PanelBridge::say(said.data(), 200, 200, 100, "AB", 100, 60, 2.0, 2.0, color);
			int inked = 0, other = 0;
			for (uint32_t c : said) { inked += c == rgb(color < 0 ? 11 : color); other += c == rgb(color < 0 ? 5 : 11); }
			assert(inked > 0 && !other);
		}
		PanelBridge::unload();
		assert(!PanelBridge::loaded() && PanelBridge::itemCount() == 1);
		PanelBridge::clear();
		assert(PanelBridge::itemCount() == 0 && !PanelBridge::loaded());
		// (One shown as none: its last picture.)
		const std::vector<uint8_t> unshown = sceneBytes(0);
		assert(PanelBridge::addItem(unshown.data(), unshown.size(), 50, nullptr) && PanelBridge::itemName(0, name, sizeof(name)) == 3);
		PanelBridge::removeItem(0);
		assert(PanelBridge::itemCount() == 0);
		// (The oldest games' way: picture 0, against the place without it, 1.)
		assert(PanelBridge::addItem(scene.data(), scene.size(), 50, "key", 0, 1) && PanelBridge::itemCount() == 1);
		PanelBridge::removeItem(0);
		// The rules through the bridge.
		int picture; char say[64];
		assert(PanelBridge::decide(kOpen, true, 2, 0, true, 10, 10, -1, "door", picture, say, sizeof(say)) == kShow && picture == 1);
		assert(PanelBridge::decide(kLook, false, 0, 0, false, 0, 0, -1, "sign", picture, say, sizeof(say)) == kSay && !strcmp(say, "Sign."));
		assert(PanelBridge::decide(kOpen, true, 2, 0, true, 10, 10, 1 << kLook, "door", picture, say, sizeof(say)) == kSay && !strcmp(say, "It doesn't open."));
		assert(PanelBridge::decide(kPickUp, false, 2, 0, true, 8, 8, -1, "key", picture, say, sizeof(say), true) == kTake && picture == 1);
	}
	{
		// The picture itself (Panel side): through a scene parsed here.
		World::SourceScene source;
		const std::vector<uint8_t> scene = sceneBytes(1);
		assert(World::parseScene(scene.data(), scene.size(), source, error) && source.objects[0].shown == 1);
		PanelBridge::clear();
		assert(PanelBridge::addItem(scene.data(), scene.size(), 50, "mug"));
		Spec pictureSlots; pictureSlots.slotKind = 2;
		const std::vector<uint8_t> pictureData = panelBytes(pictureSlots);
		char problem[64];
		assert(PanelBridge::load(pictureData.data(), pictureData.size(), problem, sizeof(problem)));
		PanelBridge::layout(64, 16, 0, 1.0, 1.0);
		std::vector<uint32_t> screen(64 * 16, 0);
		PanelBridge::render(screen.data(), 64, 16);
		// Slot 0 at 40,6 8x4; the 8x6 picture fitted to 4 rows (2/3): 5x4 from 41,6.
		const uint32_t block = 0xFF000000u | 9u << 16 | 246u << 8 | 4u;
		int blocks = 0;
		for (int y = 6; y < 10; ++y) for (int x = 40; x < 48; ++x) blocks += screen[y * 64 + x] == block;
		assert(blocks > 0 && blocks <= 4);
		for (int y = 6; y < 10; ++y) for (int x = 40; x < 48; ++x)
			assert(screen[y * 64 + x] == block || screen[y * 64 + x] == rgb(pictureData[12 + 768 + y * 64 + x]));
		PanelBridge::clear();
	}
	{
		// (Its two pictures the same, as the mansion's garage's two: drawn
		// whole, not nothing.)
		std::vector<uint8_t> same = sceneBytes(1);
		for (size_t i = same.size() - 48; i < same.size(); ++i) same[i] = 3;
		PanelBridge::clear();
		assert(PanelBridge::addItem(same.data(), same.size(), 50, "box"));
		Spec pictureSlots; pictureSlots.slotKind = 2;
		const std::vector<uint8_t> pictureData = panelBytes(pictureSlots);
		char problem[64];
		assert(PanelBridge::load(pictureData.data(), pictureData.size(), problem, sizeof(problem)));
		PanelBridge::layout(64, 16, 0, 1.0, 1.0);
		std::vector<uint32_t> screen(64 * 16, 0);
		PanelBridge::render(screen.data(), 64, 16);
		const uint32_t plain = 0xFF000000u | 3u << 16 | 252u << 8 | 1u;
		int drawn = 0;
		for (int y = 6; y < 10; ++y) for (int x = 40; x < 48; ++x) drawn += screen[y * 64 + x] == plain && rgb(pictureData[12 + 768 + y * 64 + x]) != plain;
		assert(drawn > 0);
		PanelBridge::clear();
	}
	std::puts("PASS: things carried from a scene (only the thing itself; whole where its pictures are the same), kept panel to panel and without one, cleared");
	{
		// Controls over the scene (Sam & Max): the file whole or not at all.
		const std::vector<uint8_t> data = overBytes();
		Source s;
		assert(parse(data.data(), data.size(), s, error));
		assert(s.over && s.rows == 20 && s.mask.size() == 32 * 20 && s.mask[2 * 32 + 4] == 1 && s.mask[0] == 0);
		assert(s.verbs.size() == 3 && s.cursors.size() == 3 && s.cursors[1].rect.width == 3 && s.cursors[2].hotX == 1 && s.cursors[0].mask[0] == 0);
		assert(s.button.rect.x == 0 && s.button.rect.y == 16 && s.button.rect.width == 4 && s.close.x == 22 && s.slotKind == 2 && s.slots.size() == 2 && s.shade == 128);
		for (size_t cut = 1; cut < data.size(); cut += 29) assert(!parse(data.data(), data.size() - cut, s, error));
		OverSpec trailing; trailing.trailing = true;
		OverSpec badVerb; badVerb.pointerVerb = 3;
		OverSpec again; again.pointerVerb = 1;
		OverSpec low; low.buttonY = 18;
		OverSpec farClose; farClose.closeX = 30;
		OverSpec badMask; badMask.maskValue = 3;
		for (const OverSpec &bad : {trailing, badVerb, again, low, farClose, badMask}) {
			const std::vector<uint8_t> b = overBytes(bad);
			assert(!parse(b.data(), b.size(), s, error));
			// (Cut short anywhere, bad or not: refused, nothing written past.)
			for (size_t cut = bad.trailing ? 2 : 1; cut < b.size(); ++cut) assert(!parse(b.data(), b.size() - cut, s, error));
		}
		// (A panel under the scene is none of this.)
		const std::vector<uint8_t> under = panelBytes();
		assert(parse(under.data(), under.size(), s, error) && !s.over && s.cursors.empty());
		// Over a scene at twice the size: shut, only its button; open, every
		// tap the box's (off it or its icon that shuts it, shut).
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error) && p.over() && !p.isOpen());
		p.layout(64, 40, 0, 2.0, 2.0);
		const Rect b = p.buttonOnScreen();
		assert(b.x == 0 && b.y == 32 && b.width == 8 && b.height == 8);
		Panel::Panel::Hit h = p.hit(2, 34);
		assert(h.panel && h.button && h.verb < 0);
		h = p.hit(30, 20);
		assert(!h.panel && h.verb < 0 && !h.close);
		p.open(true);
		assert(p.isOpen());
		assert(p.hit(0, 0).close && !p.hit(0, 0).icon && p.hit(63, 39).close && p.hit(46, 8).close && p.hit(46, 8).icon);
		h = p.hit(14, 8);
		assert(h.verb == 1 && !h.close);
		assert(p.hit(30, 8).verb == 2 && p.hit(14, 22).item == -1 && !p.hit(14, 22).close);
		std::vector<Item> items(1);
		items[0].name = "rat"; items[0].width = 2; items[0].height = 2; items[0].picture.assign(4, 0xFF00FF00u);
		p.setItems(items);
		assert(p.hit(14, 22).item == 0 && p.hit(30, 22).item == -1);
		// The pointer: walking, look, use, then walking again.
		assert(p.pointerVerb() == 0);
		p.nextVerb(); assert(p.selected() == 1 && p.pointerVerb() == 1);
		p.nextVerb(); assert(p.selected() == 2);
		p.nextVerb(); assert(p.selected() == -1 && p.pointerVerb() == 0);
		// Drawn: the box only where it is drawn, only while open; the
		// button and the pointer (its hot spot where asked), not while open.
		std::vector<uint32_t> screen(64 * 40, 7);
		p.render(screen.data(), 64, 40);
		assert(screen[0] == 7 && screen[63 * 1] == 7 && screen[4 * 64 + 8] == rgb(data[12 + 768 + 2 * 32 + 4]));
		assert(screen[22 * 64 + 16] == 0xFF00FF00u && screen[22 * 64 + 14] != 0xFF00FF00u); // (the rat in the middle of its cell)
		p.open(false);
		std::fill(screen.begin(), screen.end(), 7);
		p.render(screen.data(), 64, 40);
		for (uint32_t c : screen) assert(c == 7);
		p.select(1);
		p.renderControls(screen.data(), 64, 64, 40, 20, 20, true);
		assert(screen[33 * 64 + 1] == rgb(90) && screen[39 * 64 + 7] == rgb(90));
		// (Look's pointer, 3x2 at twice the size, hot spot 1,1 on 20,20: from 18,18.)
		assert(screen[18 * 64 + 18] == 7 && screen[18 * 64 + 20] == rgb(61) && screen[21 * 64 + 23] == rgb(61) && screen[22 * 64 + 24] == 7);
		std::fill(screen.begin(), screen.end(), 7);
		p.renderControls(screen.data(), 64, 64, 40, 20, 20, false);
		assert(screen[18 * 64 + 20] == 7 && screen[33 * 64 + 1] == rgb(90));
		// Under the scene: no button, nothing drawn, never open.
		Panel::Panel under2;
		assert(under2.load(under.data(), under.size(), error) && !under2.over());
		under2.open(true);
		assert(!under2.isOpen() && under2.buttonOnScreen().width == 0);
		// The bridge's codes: 5 the button, 6 off the box, 7 its icon.
		char problem[64];
		int index;
		assert(PanelBridge::load(data.data(), data.size(), problem, sizeof(problem)) && PanelBridge::over());
		PanelBridge::layout(64, 40, 0, 2.0, 2.0);
		assert(PanelBridge::hit(2, 34, index) == 5);
		PanelBridge::open(true);
		assert(PanelBridge::isOpen() && PanelBridge::hit(0, 0, index) == 6 && PanelBridge::hit(46, 8, index) == 7);
		assert(PanelBridge::hit(14, 8, index) == 2 && index == 1);
		int x, y, w, hh;
		assert(PanelBridge::buttonRect(x, y, w, hh) && x == 0 && y == 32 && PanelBridge::closeRect(x, y, w, hh) && x == 44 && y == 6);
		PanelBridge::nextVerb();
		assert(PanelBridge::pointerVerb() == 1);
		PanelBridge::clear();
		// More carried than the box's cells (Sam & Max's, The Dig's): the last
		// cell turns the page (an arrow drawn there), the others show the
		// things on it; past the last page, the first again; as many as the
		// cells, none to turn.
		{
			Panel::Panel m;
			assert(m.load(data.data(), data.size(), error));
			m.layout(64, 40, 0, 2.0, 2.0);
			m.open(true);
			std::vector<Item> three(3, items[0]);
			m.setItems(three);
			assert(m.hit(14, 22).item == 0 && m.hit(30, 22).item == -1 && m.hit(30, 22).arrow == 1);
			std::vector<uint32_t> shown(64 * 40, 7);
			m.render(shown.data(), 64, 40);
			int white = 0;
			for (int y = 20; y < 28; ++y) for (int x = 28; x < 40; ++x) white += shown[y * 64 + x] == 0xFFFFFFFFu;
			assert(white > 0 && shown[22 * 64 + 16] == 0xFF00FF00u);
			m.scroll(1); assert(m.firstItem() == 1 && m.hit(14, 22).item == 1);
			m.scroll(1); assert(m.firstItem() == 2 && m.hit(14, 22).item == 2);
			m.scroll(1); assert(m.firstItem() == 0);
			m.scroll(-1); assert(m.firstItem() == 2);
			m.setItems(std::vector<Item>(2, items[0]));
			assert(m.firstItem() == 0 && m.hit(30, 22).item == 1 && m.hit(30, 22).arrow == 0);
		}
		// Shaded (The Dig's grid): the scene there darkened by the shade, a
		// thing carried in a cell drawn over it; a tap there is the box's.
		OverSpec shadedSpec; shadedSpec.shaded = true;
		const std::vector<uint8_t> grid = overBytes(shadedSpec);
		Panel::Panel q;
		assert(q.load(grid.data(), grid.size(), error));
		q.layout(64, 40, 0, 2.0, 2.0);
		q.open(true);
		std::vector<uint32_t> scene(64 * 40, 0xFF6040C8u);
		q.render(scene.data(), 64, 40);
		assert(scene[30 * 64 + 20] == (0xFF000000u | (0x60 * 128 / 255) << 16 | (0x40 * 128 / 255) << 8 | (0xC8 * 128 / 255)));
		assert(scene[0] == 0xFF6040C8u && scene[10 * 64 + 20] == rgb(grid[12 + 768 + 5 * 32 + 10]));
		assert(!q.hit(20, 30).close && q.hit(20, 30).panel);
	}
	{
		// One tap does what fits (The Dig's): what can be taken is, what is
		// shut opens, else it is looked at.
		Thing small; small.pictures = 2; small.shown = 1; small.differs = true; small.width = small.height = 10;
		Outcome o = decide(kAct, small, "rock");
		assert(o.result == kTake && o.picture == 0);
		Thing shut; shut.pictures = 2; shut.shown = 0; shut.differs = true; shut.width = shut.height = 100;
		o = decide(kAct, shut, "hatch");
		assert(o.result == kShow && o.picture == 1);
		Thing wall; wall.pictures = 0; wall.width = wall.height = 100;
		o = decide(kAct, wall, "space");
		assert(o.result == kSay && o.say == "Space.");
		// (No walking, the first verb the tap: the pointer is it.)
		std::vector<uint8_t> tapOnly = overBytes();
		tapOnly[4 + 8 + 768 + 2 * 32 * 20 + 1] = kAct;
		Panel::Panel t;
		assert(t.load(tapOnly.data(), tapOnly.size(), error) && t.walkVerb() == -1 && t.pointerVerb() == 0 && t.kindOf(0) == kAct);
	}
	std::puts("PASS: controls over the scene (a box from its button, shut off it or by its icon; the pointer round its verbs; drawn only where drawn, darkened where shaded; one tap doing what fits)");
	{
		// Full Throttle's coin ("SVI3"): the file whole or not at all.
		const std::vector<uint8_t> data = coinBytes();
		Source s;
		assert(parse(data.data(), data.size(), s, error));
		assert(s.coin && s.over && s.button.pixels.empty() && s.cursors.size() == 2 && s.cursors[0].rect.width == 3);
		assert(s.coinPicture.rect.width == 12 && s.coinPicture.rect.height == 10 && s.coinPicture.hotX == 6 && s.coinPicture.hotY == 5);
		assert(s.coinPicture.mask[0] == 0 && s.coinPicture.mask[1] == 1 && s.nameX == 6 && s.nameY == 7 && s.nameInk == 33);
		assert(s.verbs.size() == 2 && s.verbs[0].litMask.size() == 24 && s.verbs[0].litMask[0] == 0 && s.verbs[1].kind == kHand && s.verbs[1].litMask.size() == 80);
		assert(s.upPicture.rect.x == 5 && s.upPicture.pixels[0] == 150 && s.downPicture.rect.x == 20 && s.downPicture.pixels[5] == 151);
		for (size_t cut = 1; cut < data.size(); ++cut) assert(!parse(data.data(), data.size() - cut, s, error));
		CoinSpec trailing; trailing.trailing = true;
		CoinSpec off; off.lookX = 8; // (a part off the coin)
		CoinSpec none; none.handWidth = none.handHeight = 0; // (a part of nothing)
		CoinSpec big; big.coinWidth = 300;
		CoinSpec kind; kind.lookKind = kHand + 1;
		for (const CoinSpec &bad : {trailing, off, none, big, kind}) {
			const std::vector<uint8_t> b = coinBytes(bad);
			assert(!parse(b.data(), b.size(), s, error));
		}
		// (Sam & Max's controls are not a coin.)
		const std::vector<uint8_t> sam = overBytes();
		assert(parse(sam.data(), sam.size(), s, error) && !s.coin);
		Panel::Panel q;
		assert(q.load(sam.data(), sam.size(), error));
		q.layout(64, 40, 0, 2.0, 2.0);
		q.openCoin(32, 20, "rat");
		assert(!q.coin() && !q.coinOpen() && q.coinVerb(26, 14) == -1);
		// At twice the size: the pointer walks; no button.
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error) && p.coin() && p.over());
		p.layout(64, 40, 0, 2.0, 2.0);
		assert(p.pointerVerb() == -1 && p.buttonOnScreen().width == 0 && !p.hit(30, 20).panel);
		// Held at 32,20: its anchor there (its top left 20,10), the parts
		// under a point (the smaller where one lies in another), none off them.
		p.openCoin(32, 20, "A");
		assert(p.coinOpen() && p.coinLit() == -1);
		Rect c = p.coinOnScreen();
		assert(c.x == 20 && c.y == 10 && c.width == 24 && c.height == 20);
		assert(p.coinVerb(26, 14) == 0 && p.coinVerb(22, 24) == 1 && p.coinVerb(20, 28) == -1 && p.coinVerb(19, 14) == -1 && p.coinVerb(44, 14) == -1);
		const Rect part = p.partOnScreen(0);
		assert(part.x == 24 && part.y == 12 && part.width == 12 && part.height == 8 && p.partOnScreen(2).width == 0);
		// Kept on the screen near its edges.
		p.openCoin(0, 0, "A");
		assert(p.coinOnScreen().x == 0 && p.coinOnScreen().y == 0);
		p.openCoin(64, 40, "A");
		assert(p.coinOnScreen().x == 40 && p.coinOnScreen().y == 20);
		// Drawn over the scene: the coin where it is drawn, the scene through
		// its hole and corner; the part lit (the scene where its lit picture
		// is clear); the name in its colour over it.
		p.openCoin(32, 20, "A");
		std::vector<uint32_t> screen(64 * 40, 7);
		p.renderCoin(screen.data(), 64, 64, 40);
		assert(screen[10 * 64 + 20] == 7 && screen[10 * 64 + 22] == rgb(101) && screen[22 * 64 + 34] == 7 && screen[9 * 64 + 22] == 7);
		assert(screen[24 * 64 + 28] == rgb(33)); // (the name's 'A' at 4,7 of the coin)
		// (A long name past the coin's edges, not cut at them.)
		p.openCoin(32, 20, "AAAAAAAA");
		std::fill(screen.begin(), screen.end(), 7);
		p.renderCoin(screen.data(), 64, 64, 40);
		assert(screen[24 * 64 + 2] == rgb(33) && screen[24 * 64 + 60] == rgb(33));
		p.openCoin(32, 20, "A");
		p.lightCoin(0);
		assert(p.coinLit() == 0);
		std::fill(screen.begin(), screen.end(), 7);
		p.renderCoin(screen.data(), 64, 64, 40);
		assert(screen[12 * 64 + 24] == 7 && screen[12 * 64 + 26] == rgb(200) && screen[18 * 64 + 34] == rgb(200));
		p.lightCoin(5);
		assert(p.coinLit() == -1);
		p.shutCoin();
		std::fill(screen.begin(), screen.end(), 7);
		p.renderCoin(screen.data(), 64, 64, 40);
		for (uint32_t v : screen) assert(v == 7);
		assert(p.coinVerb(26, 14) == -1);
		p.lightCoin(0);
		assert(p.coinLit() == -1);
		// Its pointer is the one, wherever: drawn at its hot spot.
		p.renderControls(screen.data(), 64, 64, 40, 20, 20, true);
		assert(screen[18 * 64 + 18] == rgb(60) && screen[21 * 64 + 23] == rgb(60));
		// Its box: its arrows (not the coin's verbs) and cells; a thing at a
		// time each way; an arrow drawn only where there is more that way.
		p.open(true);
		Panel::Panel::Hit h = p.hit(12, 9);
		assert(h.arrow == -1 && !h.close && p.hit(42, 9).arrow == 1 && p.hit(12, 6).verb == -1 && p.hit(12, 6).arrow == 0 && !p.hit(12, 6).close && p.hit(0, 0).close);
		std::vector<Item> items(5);
		for (Item &i : items) { i.name = "rat"; i.width = 2; i.height = 2; i.picture.assign(4, 0xFF00FF00u); }
		p.setItems(items);
		assert(p.hit(18, 22).item == 0 && p.hit(30, 22).item == 1);
		std::fill(screen.begin(), screen.end(), 7);
		p.render(screen.data(), 64, 40);
		assert(screen[8 * 64 + 10] != rgb(150) && screen[8 * 64 + 40] == rgb(151));
		p.scroll(1);
		assert(p.firstItem() == 1 && p.hit(18, 22).item == 1);
		p.render(screen.data(), 64, 40);
		assert(screen[8 * 64 + 10] == rgb(150) && screen[8 * 64 + 40] == rgb(151));
		p.scroll(10);
		assert(p.firstItem() == 3);
		std::fill(screen.begin(), screen.end(), 7);
		p.render(screen.data(), 64, 40);
		assert(screen[8 * 64 + 10] == rgb(150) && screen[8 * 64 + 40] != rgb(151));
		p.scroll(-10);
		assert(p.firstItem() == 0);
		items.resize(2);
		p.setItems(items);
		std::fill(screen.begin(), screen.end(), 7);
		p.render(screen.data(), 64, 40);
		assert(screen[8 * 64 + 10] != rgb(150) && screen[8 * 64 + 40] != rgb(151));
		// The bridge: the coin, its parts, the box's arrows (code 4); its
		// parts are not on the panel.
		char problem[64];
		int index, x, y, w, hh;
		assert(PanelBridge::load(data.data(), data.size(), problem, sizeof(problem)) && PanelBridge::coin() && PanelBridge::over());
		PanelBridge::layout(64, 40, 0, 2.0, 2.0);
		assert(!PanelBridge::verbShown(0) && !PanelBridge::verbRect(0, x, y, w, hh) && PanelBridge::pointerVerb() == -1);
		assert(!PanelBridge::coinOpen() && !PanelBridge::coinRect(x, y, w, hh) && !PanelBridge::partRect(0, x, y, w, hh));
		PanelBridge::openCoin(32, 20, "rat");
		assert(PanelBridge::coinOpen() && PanelBridge::coinRect(x, y, w, hh) && x == 20 && y == 10 && w == 24 && hh == 20);
		assert(PanelBridge::partRect(1, x, y, w, hh) && x == 22 && y == 10 && w == 20 && hh == 16);
		assert(PanelBridge::coinVerb(26, 14) == 0 && PanelBridge::verbKind(1) == kHand);
		PanelBridge::lightCoin(1);
		assert(PanelBridge::coinLit() == 1);
		PanelBridge::shutCoin();
		assert(!PanelBridge::coinOpen() && PanelBridge::coinLit() == -1);
		PanelBridge::open(true);
		assert(PanelBridge::hit(12, 9, index) == 4 && index == -1 && PanelBridge::hit(42, 9, index) == 4 && index == 1 && PanelBridge::hit(0, 0, index) == 6);
		assert(PanelBridge::arrows());
		PanelBridge::clear();
		assert(!PanelBridge::coin());
		// The Curse's: the name on its own line at the bottom, wherever the
		// coin is (not on the coin); a box with no arrows to show or tap.
		CoinSpec curse; curse.line = true; curse.arrows = false;
		const std::vector<uint8_t> chest = coinBytes(curse);
		Panel::Panel k;
		assert(k.load(chest.data(), chest.size(), error) && k.coin() && !k.arrows());
		k.layout(64, 40, 0, 2.0, 2.0);
		k.openCoin(32, 20, "A");
		std::fill(screen.begin(), screen.end(), 7);
		k.renderCoin(screen.data(), 64, 64, 40);
		// ('A' 4 wide, 3 rows at twice the size: centred on 32, from row 36.)
		assert(screen[36 * 64 + 28] == rgb(33) && screen[24 * 64 + 28] != rgb(33));
		k.openCoin(10, 8, "A");
		std::fill(screen.begin(), screen.end(), 7);
		k.renderCoin(screen.data(), 64, 64, 40);
		assert(screen[36 * 64 + 28] == rgb(33));
		k.open(true);
		assert(k.hit(12, 9).arrow == 0 && k.hit(42, 9).arrow == 0);
		std::vector<Item> many(5);
		for (Item &i : many) { i.name = "rat"; i.width = 2; i.height = 2; i.picture.assign(4, 0xFF00FF00u); }
		k.setItems(many);
		std::fill(screen.begin(), screen.end(), 7);
		k.render(screen.data(), 64, 40);
		for (uint32_t v : screen) assert(v != rgb(150) && v != rgb(151));
		assert(PanelBridge::load(chest.data(), chest.size(), problem, sizeof(problem)) && !PanelBridge::arrows());
		PanelBridge::clear();
	}
	{
		// Full Throttle's hand: what can be taken is, what is shut opens, what
		// is open shuts, else it doesn't work.
		Thing small; small.pictures = 2; small.shown = 1; small.differs = true; small.width = small.height = 10;
		Outcome o = decide(kHand, small, "wrench");
		assert(o.result == kTake && o.picture == 0);
		Thing shut; shut.pictures = 2; shut.shown = 0; shut.differs = true; shut.width = shut.height = 100;
		o = decide(kHand, shut, "door");
		assert(o.result == kShow && o.picture == 1);
		shut.shown = 1;
		o = decide(kHand, shut, "door");
		assert(o.result == kShow && o.picture == 0);
		Thing wall; wall.pictures = 0; wall.width = wall.height = 100;
		o = decide(kHand, wall, "wall");
		assert(o.result == kSay && o.say == "That doesn't seem to work.");
	}
	std::puts("PASS: Full Throttle's coin (read whole; held over a thing where it is, kept on screen; the part under a point, the smaller in another; drawn with the scene through, a part lit, the name; its box's arrows a thing at a time, shown where there is more; its pointer; the hand; The Curse's name on its own line, its box without arrows)");
	{
		// Loom's distaff ("SVI4"): the file whole or not at all.
		const std::vector<uint8_t> data = distaffBytes();
		Source s;
		assert(parse(data.data(), data.size(), s, error));
		assert(s.distaff && !s.over && s.verbs.size() == 3 && s.verbs[1].kind == kNote && s.verbs[1].id == 2 && s.icon.x == 40 && s.icon.height == 8);
		assert(s.drafts.size() == 3 && s.drafts[0].name == "Opening" && s.drafts[0].notes[0] == 4 && s.drafts[0].notes[3] == 2 && s.drafts[1].notes[2] == 2);
		for (size_t cut = 1; cut < data.size(); ++cut) assert(!parse(data.data(), data.size() - cut, s, error));
		DistaffSpec trailing; trailing.trailing = true;
		DistaffSpec far; far.noteId = 8; // (no such note)
		DistaffSpec notNote; notNote.noteKind = kLook; // (a verb that is no note)
		DistaffSpec off; off.iconX = 60; // (its box off the panel)
		DistaffSpec bits; bits.draftBits = 0x1000;
		DistaffSpec panel; panel.asPanel = true; // (notes on a panel that is no distaff)
		for (const DistaffSpec &bad : {trailing, far, notNote, off, bits, panel}) {
			const std::vector<uint8_t> b = distaffBytes(bad);
			assert(!parse(b.data(), b.size(), s, error));
		}
		// Notes played: each lit; the fourth spins the draft they make (its
		// index; 16 more backwards; one the same both ways forwards; none -2).
		Panel::Panel p;
		assert(p.load(data.data(), data.size(), error) && p.distaff() && !p.coin() && !p.over());
		assert(p.play(2) == -1 && p.selected() == 2 && p.play(0) == -1 && p.play(2) == -1 && p.played() == 3);
		assert(p.play(1) == 0 && p.played() == 0);
		assert(p.play(1) == -1 && p.play(2) == -1 && p.play(0) == -1 && p.play(2) == 16);
		assert(p.play(0) == -1 && p.play(1) == -1 && p.play(1) == -1 && p.play(0) == 1);
		assert(p.play(1) == -1 && p.play(1) == -1 && p.play(1) == -1 && p.play(1) == -2 && p.played() == 0);
		assert(p.play(5) == -1 && p.play(-1) == -1 && p.played() == 0);
		p.play(0); p.clearPlayed();
		assert(p.played() == 0);
		// Drawn under the scene: the note lit; no sentence line; the thing
		// chosen fitted in its box, until let go.
		p.layout(64, 200, 184, 1.0, 1.0);
		p.select(1);
		p.setSentence("A");
		std::vector<uint32_t> screen(64 * 200, 7);
		p.render(screen.data(), 64, 200);
		assert(screen[186 * 64 + 10] == rgb(201) && screen[186 * 64 + 2] == rgb(data[12 + 768 + 2 * 64 + 2]) && screen[184 * 64] == rgb(data[12 + 768]));
		Item thing; thing.name = "leaf"; thing.width = thing.height = 2; thing.picture.assign(4, 0xFF00FF00u);
		p.choose(thing);
		assert(p.hasChosen());
		p.render(screen.data(), 64, 200);
		assert(screen[(184 + 7) * 64 + 47] == 0xFF00FF00u && screen[(184 + 4) * 64 + 40] != 0xFF00FF00u);
		p.unchoose();
		p.render(screen.data(), 64, 200);
		assert(!p.hasChosen() && screen[(184 + 7) * 64 + 47] != 0xFF00FF00u);
		// (Not a distaff: no notes played.)
		const std::vector<uint8_t> under = panelBytes();
		Panel::Panel q;
		assert(q.load(under.data(), under.size(), error) && !q.distaff() && q.play(0) == -1);
		// The bridge: its notes' verbs, drafts, the thing chosen from a scene.
		char problem[64], name[16];
		int verb, notes[4], x, y, w, h;
		assert(PanelBridge::load(data.data(), data.size(), problem, sizeof(problem)) && PanelBridge::distaff() && !PanelBridge::coin());
		PanelBridge::layout(64, 200, 184, 1.0, 1.0);
		assert(PanelBridge::draftCount() == 3 && PanelBridge::draftName(2, name, sizeof(name)) == 4 && !std::strcmp(name, "Calm"));
		assert(PanelBridge::draftNotes(1, notes) && notes[0] == 0 && notes[1] == 2 && !PanelBridge::draftNotes(3, notes));
		assert(PanelBridge::noteVerb(4, verb) && verb == 2 && !PanelBridge::noteVerb(7, verb));
		assert(PanelBridge::hit(12, 187, verb) == 2 && verb == 1 && PanelBridge::play(verb) == -1 && PanelBridge::playedNotes() == 1);
		PanelBridge::clearPlayed();
		assert(PanelBridge::playedNotes() == 0 && PanelBridge::iconRect(x, y, w, h) && x == 40 && y == 188 && w == 16 && h == 8);
		const std::vector<uint8_t> scene = sceneBytes(1);
		assert(!PanelBridge::choose(scene.data(), scene.size(), 51, "mug") && !PanelBridge::chosen());
		assert(PanelBridge::choose(scene.data(), scene.size(), 50, "mug") && PanelBridge::chosen());
		PanelBridge::unchoose();
		assert(!PanelBridge::chosen());
		// (One shown in its picture 0, a thing shut: drawn whole, centred.)
		const std::vector<uint8_t> shut = sceneBytes(0);
		assert(PanelBridge::choose(shut.data(), shut.size(), 50, "mug", 0) && PanelBridge::chosen());
		std::vector<uint32_t> box(64 * 200, 7);
		PanelBridge::render(box.data(), 64, 200);
		assert(box[192 * 64 + 48] == (0xFF000000u | 3u << 16 | 252u << 8 | 1u) && box[192 * 64 + 42] != (0xFF000000u | 3u << 16 | 252u << 8 | 1u));
		PanelBridge::unchoose();
		PanelBridge::clear();
		assert(!PanelBridge::distaff() && !PanelBridge::iconRect(x, y, w, h));
		// (A panel that is no distaff takes no thing chosen.)
		assert(PanelBridge::load(under.data(), under.size(), problem, sizeof(problem)) && !PanelBridge::choose(scene.data(), scene.size(), 50, "mug"));
		PanelBridge::clear();
	}
	std::puts("PASS: Loom's distaff (read whole; its notes lit, four spinning a draft forwards or backwards, or none; no sentence line; the thing chosen in its box)");

	// Where each draws (from 0243, the screen drawn in parts): every pixel
	// render, the coin, the controls and speech draw is inside the bounds
	// each says (drawn onto screens of one colour, three colours, so none is
	// missed), for panels under the scene (names and pictures), over it
	// (open and shut, the pointer anywhere, half off the screen), a coin
	// held anywhere and a distaff, at several scales; none when nothing is
	// drawn. The panel composed: as render composes it.
	{
		auto inside = [](const Rect &r, int W, int H, const std::function<void(uint32_t *)> &draw) {
			bool any = false;
			for (uint32_t fill : {0x00000000u, 0xFFFFFFFFu, 0x80123456u}) {
				std::vector<uint32_t> s((size_t)W * H, fill);
				draw(s.data());
				for (int y = 0; y < H; ++y)
					for (int x = 0; x < W; ++x)
						if (s[(size_t)y * W + x] != fill) { assert(r.contains(x, y)); any = true; }
			}
			return any;
		};
		Spec pictures; pictures.slotKind = 2;
		const std::vector<std::vector<uint8_t> > panels = {panelBytes(), panelBytes(pictures), overBytes(), coinBytes(), distaffBytes()};
		int drew = 0;
		for (size_t k = 0; k < panels.size(); ++k) {
			Panel::Panel p;
			std::string problem;
			assert(p.load(panels[k].data(), panels[k].size(), problem));
			std::vector<Item> items(5);
			for (size_t i = 0; i < items.size(); ++i) { items[i].name = "AB"; items[i].width = 3; items[i].height = 2; items[i].picture.assign(6, 0xFF0000FFu); }
			p.setItems(items);
			p.setSentence("ABBA");
			for (const double scale : {1.0, 2.0, 3.5}) {
				const int W = (int)(64 * scale) + 7, H = (int)(40 * scale) + 9;
				p.layout(W, H, p.over() ? 3 : H - p.rowsAt(scale), scale, scale / 1.2);
				for (int state = 0; state < 4; ++state) {
					p.select(state - 1);
					p.open(state & 1);
					if (p.coin()) { if (state) p.openCoin(state * W / 3, state * H / 3, "AAAAAAAAAAAA"); else p.shutCoin(); p.lightCoin(state - 1); }
					drew += inside(p.renderBounds(H), W, H, [&](uint32_t *s) { p.render(s, W, H); });
					drew += inside(p.coinBounds(W, H), W, H, [&](uint32_t *s) { p.renderCoin(s, W, W, H); });
					for (const int px : {-30, 5, W / 2, W - 2})
						drew += inside(p.controlsBounds(W, H, px, px / 2, state != 2), W, H, [&](uint32_t *s) { p.renderControls(s, W, W, H, px, px / 2, state != 2); });
					for (const int cx : {-40, 3, W / 2, W + 20}) {
						const int from = 5, across = W - 9, limit = H - 4 * state;
						Rect r = p.sayBounds(across, limit, "AB BA AAB BBA ABAB AB", cx, cx / 3 + 4, scale, scale / 1.2);
						r.x += from;
						drew += inside(r, W, H, [&](uint32_t *s) { p.say(s + from, W, across, limit, "AB BA AAB BBA ABAB AB", cx, cx / 3 + 4, scale, scale / 1.2, 0xFFABCDEFu); });
					}
				}
			}
			// (Shut over the scene, a coin not held: nothing, and no bounds.)
			if (p.over()) { p.open(false); assert(p.renderBounds(1000).width == 0); }
			if (p.coin()) { p.shutCoin(); assert(p.coinBounds(1000, 1000).width == 0); }
		}
		assert(drew > 100);
		// Through the bridge: the same, and the panel as composed.
		const std::vector<uint8_t> under = panelBytes();
		char problem[64];
		assert(PanelBridge::load(under.data(), under.size(), problem, sizeof(problem)));
		PanelBridge::layout(200, 100, 60, 2.0, 2.0);
		int x, y, w, h;
		assert(PanelBridge::renderBounds(100, x, y, w, h) && x == 0 && y == 60 && w == 200 && h == 32);
		assert(!PanelBridge::coinBounds(200, 100, x, y, w, h) && !PanelBridge::controlsBounds(200, 100, 10, 10, true, x, y, w, h));
		assert(PanelBridge::sayBounds(200, 60, "AB", 100, 50, 2.0, 2.0, x, y, w, h) && y + h <= 60 && x >= 0 && x + w <= 200);
		assert(!PanelBridge::sayBounds(200, 60, "", 100, 50, 2.0, 2.0, x, y, w, h));
		const int pixels = PanelBridge::composed(nullptr, 0);
		assert(pixels == PanelBridge::columns() * PanelBridge::rows());
		std::vector<unsigned int> canvas(pixels);
		assert(PanelBridge::composed(canvas.data(), pixels) == pixels);
		Panel::Panel same;
		std::string why;
		assert(same.load(under.data(), under.size(), why));
		std::vector<uint32_t> composed;
		same.compose(composed);
		assert(std::equal(composed.begin(), composed.end(), canvas.begin()));
		PanelBridge::clear();
	}
	std::puts("PASS: where each draws (the panel, its box over the scene, the coin, the controls, speech: every pixel drawn inside its bounds, at several scales, half off the screen; none when nothing is); the panel as composed");
	return 0;
}
