// Sandbox verb panel (common/scummverse_panel.cpp) with synthetic panels and
// scenes (no game data): the file read whole or not at all, where it goes
// under the scene and what a tap is on, drawing (a verb lit, the sentence
// line, things carried as names or pictures, arrows when there is more),
// the game's lettering (widths, wrapping, speech at the scene's scale),
// the plain rules for each verb, and things carried from a scene.
// c++ -std=c++11 -Wall -Wextra -Werror -Wshadow -fsanitize=address,undefined -Iengine
//   tools/test_panel.cpp engine/common/scummverse_panel.cpp engine/common/scummverse_world.cpp
#include "common/scummverse_panel.h"
#include "common/scummverse_panel_engine.h"
#include "common/scummverse_world.h"
#include <cassert>
#include <cmath>
#include <cstdio>
#include <cstring>
using namespace Scummverse;
using namespace Scummverse::Panel;

static void put16(std::vector<uint8_t> &v, int x) { v.push_back((uint8_t)(x & 255)); v.push_back((uint8_t)((x >> 8) & 255)); }
static void put(std::vector<uint8_t> &v, std::initializer_list<int> bytes) { for (int b : bytes) v.push_back((uint8_t)b); }

// A test panel 64x16 (palette c = (c, 2c, 255-c)): two verbs (Open at 2,2
// 12x5 lit in 200; a walk verb only named), the sentence centred at 32,0 in
// colour 9, slots 4 of 8x4 at x 40..56 in two rows (names in colour 7, or
// pictures), arrows (up 34,6 4x4, down 34,11 4x4), talk colour 11; two fonts
// of 5 rows: 'A' 3 wide (advance 4: ink, one pixel colour 50), 'B' 2 wide.
struct Spec { int slotKind = 1; bool trailing = false; int verbX = 2; int slotW = 8, slotH = 4; bool twiceA = false; bool emptySlot = false; };
static std::vector<uint8_t> panelBytes(const Spec &s = Spec()) {
	const int W = 64, rows = 16;
	std::vector<uint8_t> d = {'S', 'V', 'I', '1'};
	for (int f : {W, 200, 184, rows}) put16(d, f);
	for (int c = 0; c < 256; ++c) put(d, {c, (2 * c) & 255, 255 - c});
	for (int i = 0; i < W * rows; ++i) d.push_back((uint8_t)(i % 5 + 1));
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
	std::puts("PASS: more than the slots: a row at a time, the arrows only when there is more");

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
	std::puts("PASS: things carried from a scene (only the thing itself), kept panel to panel and without one, cleared");
	return 0;
}
