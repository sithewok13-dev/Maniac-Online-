// Scummverse: a person's or a shop's conversation as its game's scripts play
// it (common/scummverse_talks.h, from 0302): the talks file read and written
// (damaged ones refused), its talks begun by the value read and the money
// carried, their menus and choices played to their ends (a talk that comes
// back to its questions), the engine's bridge and the export's builder, and
// the catalog's rows (Monkey Island 2's), with talks made up here (no game
// text). From 0304 ("SVQ2") a talk begun by several values it reads, and a
// step that takes the one played to another place.
// Build: c++ -std=c++11 -Wall -Wextra -Werror -Wshadow -fsanitize=address,undefined
//   -Iengine tools/test_talks.cpp engine/common/scummverse_talks.cpp -lpthread
// (and with -fsanitize=thread).
#include "common/scummverse_talks.h"
#include "common/scummverse_talks_engine.h"
#include "common/scummverse_world_catalog.h"

#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <thread>
#include <vector>

using namespace Scummverse::Talks;
namespace Bridge = Scummverse::TalksBridge;

static Line said(int speaker, int costume, int color, const char *text) {
	Line l;
	l.speaker = speaker; l.costume = costume; l.color = color; l.text = text;
	return l;
}

static Choice choice(int id, const char *text, int next) {
	Choice c;
	c.id = id; c.text = text; c.step.next = next;
	c.step.lines.push_back(said(kSpeakerPlayed, 0, -1, text));
	return c;
}

// (A shop's sale: without enough money its line, nothing more; with it, a
// choice of two, the first the thing given and the price paid. A person's
// talk: three questions, two of them back to the questions (one set aside
// once asked), the third its end; and a chain asking again until given.)
static Data data() {
	Data d;
	d.money.var = 305; d.money.room = 9; d.money.object = 76;
	d.money.one = "one coin"; d.money.manyBefore = "a purse of "; d.money.manyAfter = " coins";
	Talk sale;
	sale.room = 48; sale.object = 540; sale.kind = 3;
	Opening poor;
	poor.moneyFrom = 0; poor.moneyTo = 24;
	poor.step.lines.push_back(said(kSpeakerPlayed, 0, -1, "May I buy this?"));
	poor.step.lines.push_back(said(kSpeakerSomeone, 40, 12, "Not with that purse."));
	Opening rich;
	rich.moneyFrom = 25;
	rich.step = poor.step;
	rich.step.lines[1].text = "That will be twenty-five.";
	rich.step.next = 0;
	sale.openings.push_back(poor);
	sale.openings.push_back(rich);
	Menu buy;
	buy.choices.push_back(choice(120, "Yes, please.", kEnd));
	buy.choices.push_back(choice(121, "No, thanks.", kEnd));
	Step &yes = buy.choices[0].step;
	yes.money = -25;
	Given saw;
	saw.room = 48; saw.object = 540; saw.name = "saw";
	yes.given.push_back(saw);
	yes.pictures.push_back(std::make_pair(517, 1));
	yes.leaves.push_back(std::make_pair(0x8000 + 86, 1));
	sale.menus.push_back(buy);
	d.talks.push_back(sale);
	Talk person;
	person.room = 14; person.object = 127; person.kind = 10; person.costume = 23;
	Opening hello;
	hello.step.lines.push_back(said(kSpeakerSomeone, 23, 11, "Yes?"));
	hello.step.next = 0;
	person.openings.push_back(hello);
	Menu questions; // (menu 0: all three; menu 1: the first asked, set aside)
	questions.choices.push_back(choice(120, "Who are you?", 1));
	questions.choices.push_back(choice(121, "Nice weather.", 0));
	questions.choices.push_back(choice(122, "Bye.", kEnd));
	Menu after;
	after.choices.push_back(choice(121, "Nice weather.", 1));
	after.choices.push_back(choice(122, "Bye.", kEnd));
	after.choices[1].step.taken.push_back(111);
	person.menus.push_back(questions);
	person.menus.push_back(after);
	d.talks.push_back(person);
	Talk bucket;
	bucket.room = 14; bucket.object = 124; bucket.kind = 3; bucket.reads = 0x8000 + 367;
	for (int value = 0; value < 2; ++value) {
		Opening o;
		o.value = value;
		o.step.lines.push_back(said(kSpeakerNone, 0, 7, value ? "Again?" : "Hands off."));
		o.step.next = 0;
		bucket.openings.push_back(o);
	}
	for (int k = 0; k < 4; ++k) {
		Menu m;
		m.choices.push_back(choice(120, "Please?", k < 3 ? k + 1 : kEnd));
		m.choices.push_back(choice(121, "Never mind.", kEnd));
		if (k == 3) {
			Given b;
			b.room = 14; b.object = 124;
			m.choices[0].step.given.push_back(b);
		}
		bucket.menus.push_back(m);
	}
	d.talks.push_back(bucket);
	// (From 0304 a person's talk read by three values: by the first and the
	// second its two ways, the third read but not told apart (0 either way);
	// its job taken pays and takes the one played elsewhere, the talk over.)
	Talk bar;
	bar.room = 9; bar.object = 73; bar.kind = 10; bar.costume = 17; bar.reads = 0x8000 + 74;
	bar.also.push_back(0x8000 + 71); bar.also.push_back(0x8000 + 77);
	for (int fired = 0; fired < 2; ++fired) {
		Opening o;
		o.value = 1; o.also.push_back(fired); o.also.push_back(0);
		o.step.lines.push_back(said(kSpeakerSomeone, 17, 187, fired ? "Still keen?" : "Something new?"));
		o.step.next = fired;
		bar.openings.push_back(o);
	}
	Opening plain;
	plain.value = 0; plain.also.push_back(0); plain.also.push_back(0);
	plain.step.lines.push_back(said(kSpeakerSomeone, 17, 187, "Evening."));
	bar.openings.push_back(plain);
	for (int k = 0; k < 2; ++k) {
		Menu m;
		m.choices.push_back(choice(120, "Count me in.", kEnd));
		m.choices.push_back(choice(121, "Not today.", kEnd));
		Step &hired = m.choices[0].step;
		hired.money = 420;
		hired.leaves.push_back(std::make_pair(0x8000 + 77, 1));
		if (!k) hired.leaves.push_back(std::make_pair(0x8000 + 71, 1));
		hired.goesRoom = 11; hired.goesX = 274; hired.goesY = 114; hired.goesFacing = 0;
		bar.menus.push_back(m);
	}
	d.talks.push_back(bar);
	return d;
}

static bool same(const Data &a, const Data &b) { return write(a) == write(b); }

int main() {
	// ---- Read as written, written as read. ----
	const Data d = data();
	const std::vector<uint8_t> bytes = write(d);
	Data back;
	std::string error;
	assert(parse(bytes.data(), bytes.size(), back, error) && same(d, back));
	assert(back.talks.size() == 4 && back.talks[0].menus[0].choices[0].step == d.talks[0].menus[0].choices[0].step);
	assert(back.talks[1].menus[1].choices[1].step.taken.size() == 1 && back.talks[0].menus[0].choices[0].step.money == -25);
	assert(back.talks[0].openings[1].moneyTo == kNoMost && back.talks[2].reads == 0x8000 + 367);
	assert(back.talks[3].also.size() == 2 && back.talks[3].also[1] == 0x8000 + 77 && back.talks[3].openings[1].also[0] == 1 && back.talks[0].also.empty());
	assert(back.talks[3].menus[0].choices[0].step.goesRoom == 11 && back.talks[3].menus[0].choices[0].step.goesX == 274 && back.talks[3].menus[1].choices[1].step.goesRoom == 0);
	assert(bytes.size() > 4 && !std::memcmp(bytes.data(), "SVQ2", 4));
	std::puts("PASS: a talks file read as written (money, four talks, their openings by one value or by three, menus, choices and steps, one taking the one played elsewhere)");
	// ---- Damaged files refused. ----
	{
		// (Cut short anywhere, or one byte more: refused, nothing kept.)
		for (size_t n = 0; n < bytes.size(); ++n) {
			Data out;
			assert(!parse(bytes.data(), n, out, error) && out.talks.empty() && !out.money.var);
		}
		std::vector<uint8_t> longer = bytes;
		longer.push_back(0);
		assert(!parse(longer.data(), longer.size(), back, error) && error == "longer than it says" && back.talks.empty());
		std::vector<uint8_t> magic = bytes;
		magic[3] = '1'; // (0302's "SVQ1": none now, its game exported again)
		assert(!parse(magic.data(), magic.size(), back, error));
		// (Each byte flipped: refused, or read back as something it writes
		// again byte for byte; never a crash, never half a file.)
		int refused = 0;
		for (size_t at = 4; at < bytes.size(); ++at)
			for (int bit = 0; bit < 8; ++bit) {
				std::vector<uint8_t> flipped = bytes;
				flipped[at] ^= (uint8_t)(1 << bit);
				Data out;
				std::string why;
				if (!parse(flipped.data(), flipped.size(), out, why)) { ++refused; assert(out.talks.empty() && !why.empty()); continue; }
				const std::vector<uint8_t> again = write(out);
				Data twice;
				assert(parse(again.data(), again.size(), twice, why) && same(out, twice));
				for (const Talk &t : out.talks) {
					for (const Opening &o : t.openings) assert(o.step.next >= kEnd && o.step.next < (int)t.menus.size());
					for (const Menu &m : t.menus) for (const Choice &c : m.choices) assert(c.step.next >= kEnd && c.step.next < (int)t.menus.size());
				}
			}
		assert(refused > 0);
		// (Made so: each is refused.)
		auto refuses = [&](Data x, const char *why) {
			const std::vector<uint8_t> b = write(x);
			Data out;
			std::string e;
			const bool ok = parse(b.data(), b.size(), out, e);
			if (ok) std::printf("not refused: %s\n", why);
			assert(!ok && out.talks.empty());
		};
		Data x = data();
		x.talks[1].menus[0].choices[0].step.next = 2;
		refuses(x, "a menu led to that is none");
		x = data();
		x.talks[1].openings[0].step.next = -2;
		refuses(x, "a menu below none");
		x = data();
		x.talks[1].menus[0].choices[1].id = 120;
		refuses(x, "a choice's number twice in a menu");
		x = data();
		x.talks[0].openings[0].moneyTo = 30;
		refuses(x, "ways of beginning that overlap");
		x = data();
		x.talks[0].openings[1].moneyTo = 3;
		refuses(x, "money to below money from");
		x = data();
		x.talks[0].openings[0].step.lines[0].speaker = 2;
		refuses(x, "a line by no one known");
		x = data();
		x.talks[0].openings[0].step.lines[1].costume = 0;
		refuses(x, "someone's line with no costume");
		x = data();
		x.talks[1].menus[0].choices[0].text.clear();
		refuses(x, "a choice with no text");
		x = data();
		x.talks[1].menus[0].choices[0].text = std::string("a\0b", 3);
		refuses(x, "a text holding a zero");
		x = data();
		x.talks[2].openings.clear();
		refuses(x, "a talk that never begins");
		x = data();
		x.talks[1].menus[0].choices.clear();
		refuses(x, "a menu with no choice");
		x = data();
		for (int k = 0; k <= kMostChoices; ++k) x.talks[1].menus[0].choices.push_back(choice(200 + k, "more", kEnd));
		refuses(x, "a menu past its most");
		x = data();
		x.talks.push_back(x.talks[1]);
		refuses(x, "a talk twice");
		x = data();
		x.talks[0].menus[0].choices[0].step.leaves.push_back(std::make_pair(0x8000 + 86, 2));
		refuses(x, "a value left twice");
		x = data();
		x.money.object = 0;
		refuses(x, "money with no thing");
		x = data();
		x.talks[0].kind = 0;
		refuses(x, "a talk of no verb");
		// (From 0304.)
		x = data();
		x.talks[3].also[1] = x.talks[3].also[0];
		refuses(x, "a further value read twice");
		x = data();
		x.talks[3].also[0] = x.talks[3].reads;
		refuses(x, "a further value its first");
		x = data();
		x.talks[3].also[1] = 0;
		refuses(x, "a further value none");
		x = data();
		for (int k = 0; k < kMostAlso; ++k) x.talks[3].also.push_back(0x8000 + 600 + k);
		refuses(x, "further values past their most");
		x = data();
		x.talks[3].openings[2].also[0] = 1;
		x.talks[3].openings[2].value = 1;
		refuses(x, "ways of beginning by the same values that overlap");
		x = data();
		x.talks[3].menus[0].choices[0].step.next = 1;
		refuses(x, "a step that goes on to a menu and elsewhere");
		x = data();
		x.talks[3].menus[0].choices[0].step.goesFacing = 4;
		refuses(x, "a way facing none of four");
		x = data();
		x.talks[3].menus[0].choices[1].step.goesX = 5;
		refuses(x, "a spot with no place");
		// (Past its most menus: the builder's written() gives none.)
		Bridge::fileBegin(0, 0, 0, "", "", "");
		const int t = Bridge::fileTalk(1, 2, 3, 0, 0);
		int menus = 0;
		while (Bridge::fileMenu(t) >= 0) ++menus;
		assert(menus == kMostMenus);
	}
	std::puts("PASS: damaged talks files refused (cut short, longer, flipped, a menu that is none, choices twice, overlapping openings, lines by no one, past their most; from 0304 further values twice or none, a way facing none of four, a step going on and elsewhere)");
	// ---- Played: begun by the money carried, chosen to their ends. ----
	{
		Play p;
		const Talk &sale = d.talks[0];
		assert(p.begin(sale, 0, 0) && p.step()->lines[1].text == "Not with that purse." && !p.menu() && p.menuIndex() == kEnd);
		assert(p.begin(sale, 0, 24) && !p.menu());
		assert(p.begin(sale, 0, 25) && p.menu() && p.menu()->choices.size() == 2);
		assert(!p.begin(sale, 1, 99)); // (no way of beginning with that value)
		assert(p.begin(sale, 0, 99999) && p.choose(0) && p.step()->money == -25 && p.step()->given[0].object == 540 && !p.menu());
		assert(!p.choose(0)); // (over)
		const Talk &person = d.talks[1];
		assert(p.begin(person, 0, 0) && p.menu() == &person.menus[0]);
		assert(p.choose(1) && p.menuIndex() == 0); // (back to its questions)
		assert(p.choose(0) && p.menuIndex() == 1 && p.menu()->choices.size() == 2); // (the first set aside once asked)
		for (int k = 0; k < 50; ++k) assert(p.choose(0) && p.menuIndex() == 1); // (a loop, as long as one likes)
		assert(!p.choose(2) && !p.choose(-1));
		assert(p.choose(1) && !p.menu() && p.step()->taken[0] == 111 && p.active());
		p.end();
		assert(!p.active() && !p.step());
		const Talk &bucket = d.talks[2];
		assert(p.begin(bucket, 1, 0) && p.step()->lines[0].text == "Again?");
		int asked = 0;
		while (p.menu()) { assert(p.choose(0)); ++asked; }
		assert(asked == 4 && p.step()->given.size() == 1 && p.step()->given[0].object == 124);
		assert(d.find(14, 999, 10, 23) == 1 && d.find(14, 124, 3, 0) == 2 && d.find(14, 125, 3, 0) == -1 && d.find(48, 540, 4, 0) == -1);
		assert(d.money.name(1) == "one coin" && d.money.name(25) == "a purse of 25 coins" && d.money.name(0).empty());
		// (From 0304 by its further values too: those not given read as 0;
		// a way of beginning by none of them, none.)
		const Talk &bar = d.talks[3];
		assert(p.begin(bar, 1, std::vector<int>{0, 0}, 0) && p.step()->lines[0].text == "Something new?" && p.menuIndex() == 0);
		assert(p.begin(bar, 1, std::vector<int>{1, 0}, 0) && p.step()->lines[0].text == "Still keen?" && p.menuIndex() == 1);
		assert(p.begin(bar, 1, std::vector<int>{1}, 0) && p.menuIndex() == 1 && p.begin(bar, 0, 0) && p.step()->lines[0].text == "Evening." && !p.menu());
		assert(!p.begin(bar, 1, std::vector<int>{1, 1}, 0) && !p.begin(bar, 0, std::vector<int>{0, 1}, 0) && p.begin(bar, 1, 0) && p.menuIndex() == 0);
		assert(p.begin(bar, 1, std::vector<int>{0, 0}, 0) && p.choose(0) && p.step()->money == 420 && p.step()->goesRoom == 11 && p.step()->leaves.size() == 2 && !p.menu());
	}
	std::puts("PASS: talks played (by the money carried and the value read, from 0304 by several, their choices to their ends, back to their questions, a chain asked again)");
	// ---- The engine's bridge and the export's builder. ----
	{
		char why[64], text[64];
		assert(Bridge::load(1, bytes.data(), bytes.size(), why, sizeof(why)) && Bridge::loaded(1) && !Bridge::loaded(0) && Bridge::count(1) == 4);
		int var, room, object;
		assert(Bridge::money(1, var, room, object) && var == 305 && room == 9 && object == 76 && !Bridge::money(0, var, room, object));
		assert(Bridge::moneyName(1, 7, text, sizeof(text)) && !strcmp(text, "a purse of 7 coins") && !Bridge::moneyName(1, 0, text, sizeof(text)));
		assert(Bridge::find(1, 48, 540, 3, 0) == 0 && Bridge::find(1, 14, 0, 10, 23) == 1 && Bridge::find(1, 14, 0, 10, 24) == -1);
		int kind, costume, reads;
		assert(Bridge::talk(1, 2, room, object, kind, costume, reads) && reads == 0x8000 + 367 && Bridge::talk(1, 3, room, object, kind, costume, reads) && reads == 0x8000 + 74 && !Bridge::talk(1, 4, room, object, kind, costume, reads));
		assert(!Bridge::begin(1, 0, 1, 0) && !Bridge::active());
		assert(Bridge::begin(1, 0, 0, 30) && Bridge::active() && Bridge::stepLines() == 2 && Bridge::menuUp() && Bridge::choices() == 2);
		int speaker, color, id;
		assert(Bridge::stepLine(1, speaker, costume, color, text, sizeof(text)) && speaker == kSpeakerSomeone && costume == 40 && color == 12);
		assert(Bridge::choice(1, id, text, sizeof(text)) && id == 121 && !Bridge::choice(2, id, text, sizeof(text)));
		assert(Bridge::choose(0) && Bridge::stepMoney() == -25 && Bridge::stepGiven() == 1 && !Bridge::menuUp());
		char name[16];
		assert(Bridge::stepGive(0, room, object, name, sizeof(name)) && room == 48 && object == 540 && !strcmp(name, "saw"));
		int picture;
		assert(Bridge::stepPictures() == 1 && Bridge::stepPicture(0, object, picture) && object == 517 && picture == 1);
		assert(Bridge::stepLeaves() == 1 && Bridge::stepLeave(0, var, picture) && var == 0x8000 + 86 && picture == 1);
		// (A text cut to its room, never past it.)
		char small[5];
		assert(Bridge::stepLine(0, speaker, costume, color, small, sizeof(small)) && !strcmp(small, "Yes,"));
		int place, goesX, goesY, facing;
		assert(!Bridge::stepGoes(place, goesX, goesY, facing));
		// (From 0304 a talk's further values, a talk begun by them, and a step's way.)
		assert(Bridge::talkAlso(1, 3, 0) == 0x8000 + 71 && Bridge::talkAlso(1, 3, 1) == 0x8000 + 77 && !Bridge::talkAlso(1, 3, 2) && !Bridge::talkAlso(1, 0, 0) && !Bridge::talkAlso(1, 9, 0));
		const int fired[] = {1, 1, 0}, hired[] = {1, 1, 1};
		assert(!Bridge::begin(1, 3, hired, 3, 0) && Bridge::begin(1, 3, fired, 3, 0) && Bridge::menuIndex() == 1 && Bridge::begin(1, 3, fired, 1, 0) && Bridge::menuIndex() == 0);
		assert(Bridge::choose(0) && Bridge::stepMoney() == 420 && Bridge::stepGoes(place, goesX, goesY, facing) && place == 11 && goesX == 274 && goesY == 114 && facing == 0 && !Bridge::menuUp());
		Bridge::end();
		assert(!Bridge::active() && !Bridge::menuUp() && Bridge::stepLines() == 0);
		// (A damaged file drops the one before; a talk under way of its game ends.)
		assert(Bridge::begin(1, 1, 0, 0) && Bridge::active());
		assert(!Bridge::load(1, bytes.data(), bytes.size() - 1, why, sizeof(why)) && !Bridge::loaded(1) && !Bridge::active() && Bridge::find(1, 48, 540, 3, 0) == -1);
		// (The builder: the same file as the module writes.)
		Bridge::fileBegin(305, 9, 76, "one coin", "a purse of ", " coins");
		for (const Talk &t : d.talks) {
			const int ti = t.also.empty() ? Bridge::fileTalk(t.room, t.object, t.kind, t.costume, t.reads) : Bridge::fileTalk(t.room, t.object, t.kind, t.costume, t.reads, t.also.data(), (int)t.also.size());
			for (size_t m = 0; m < t.menus.size(); ++m) assert(Bridge::fileMenu(ti) == (int)m);
			auto build = [&](const Step &s) {
				Bridge::stepNew();
				for (const Line &l : s.lines) Bridge::stepAddLine(l.speaker, l.costume, l.color, l.text.c_str());
				for (const auto &l : s.leaves) Bridge::stepAddLeave(l.first, l.second);
				Bridge::stepSetMoney(s.money);
				for (const Given &g : s.given) Bridge::stepAddGiven(g.room, g.object, g.name.c_str());
				for (int k : s.taken) Bridge::stepAddTaken(k);
				for (const auto &x : s.pictures) Bridge::stepAddPicture(x.first, x.second);
				Bridge::stepSetNext(s.next);
				if (s.goesRoom) Bridge::stepSetGoes(s.goesRoom, s.goesX, s.goesY, s.goesFacing);
			};
			for (const Opening &o : t.openings) {
				build(o.step);
				assert(o.also.empty() ? Bridge::fileOpening(ti, o.value, o.moneyFrom, o.moneyTo) : Bridge::fileOpening(ti, o.value, o.also.data(), (int)o.also.size(), o.moneyFrom, o.moneyTo));
			}
			for (size_t m = 0; m < t.menus.size(); ++m)
				for (const Choice &c : t.menus[m].choices) {
					const int ci = Bridge::fileChoice(ti, (int)m, c.id, c.text.c_str());
					build(c.step);
					assert(ci >= 0 && Bridge::fileChoiceStep(ti, (int)m, ci));
				}
		}
		const int size = Bridge::written(nullptr, 0);
		assert(size == (int)bytes.size());
		std::vector<uint8_t> out(size);
		assert(Bridge::written(out.data(), size) == size && out == bytes);
		// (Not a whole file: none.)
		Bridge::stepNew();
		Bridge::stepSetNext(7);
		assert(Bridge::fileOpening(0, 5, 0, kNoMost) && Bridge::written(nullptr, 0) == 0);
		assert(Bridge::fileTalk(1, 1, 1, 0, 0) >= 0 && Bridge::fileChoice(0, 99, 1, "x") == -1 && !Bridge::fileChoiceStep(0, 99, 0));
		const int many[] = {1, 2, 3, 4};
		assert(Bridge::fileTalk(2, 2, 2, 0, 5, many, kMostAlso + 1) == -1 && Bridge::fileTalk(2, 2, 2, 0, 5, many, -1) == -1); // (from 0304: past their most)
		Bridge::clear();
		assert(!Bridge::loaded(1));
	}
	std::puts("PASS: the bridge (a file loaded per game, a talk under way step by step, a damaged file dropping the one before) and the builder (the same bytes)");
	// ---- Read at once on several threads (the module's own reading keeps
	// nothing of its own). ----
	{
		std::vector<std::thread> threads;
		std::vector<int> fine(4, 0);
		for (int k = 0; k < 4; ++k)
			threads.push_back(std::thread([&, k]() {
				for (int n = 0; n < 50; ++n) {
					Data out;
					std::string e;
					fine[k] += parse(bytes.data(), bytes.size(), out, e) && same(out, d);
				}
			}));
		for (std::thread &t : threads) t.join();
		for (int f : fine) assert(f == 50);
	}
	std::puts("PASS: talks files read on four threads at once");
	// ---- The catalog's rows (from 0302). ----
	{
		using namespace Scummverse::WorldCatalog;
		const int games = worldGameCount();
		assert(kWorldTalkAlso <= kMostAlso);
		for (const WorldTalk &t : kWorldTalks) {
			assert(t.game >= 0 && t.game < games && !worldHome(t.game) && worldTalkChoices(t.game) && t.object > 0 && t.kind >= kWorldVerbWalk && t.kind < 32);
			assert(!t.reads || worldKeptValue(t.game, t.reads));
			// (From 0304 its further values: kept, after its first, each once, none
			// after a none.)
			for (int k = 0; k < kWorldTalkAlso; ++k) {
				assert(!t.also[k] || (t.reads && worldKeptValue(t.game, t.also[k]) && t.also[k] != t.reads && (!k || t.also[k - 1])));
				for (int j = 0; j < k; ++j) assert(!t.also[k] || t.also[j] != t.also[k]);
			}
			const WorldTalkChoices *c = worldTalkChoices(t.game);
			assert(c->first > 0 && c->last >= c->first && c->last - c->first < kMostChoices && c->choice > 0);
			// (A person's: of its game's cast in that place.)
			bool cast = !t.costume;
			for (const WorldCastGuest &g : kWorldCast) cast = cast || (g.game == t.game && g.room == t.room && g.guest.costume == t.costume);
			assert(cast);
			int same = 0;
			for (const WorldTalk &o : kWorldTalks) same += o.game == t.game && o.room == t.room && o.kind == t.kind && o.costume == t.costume && (t.costume || o.object == t.object);
			assert(same == 1 && (!t.gives || worldTalkGives(t.game, t.gives)));
		}
		assert(sizeof(kWorldTalks) / sizeof(kWorldTalks[0]) <= (size_t)kMostTalks);
		for (const WorldMoney &m : kWorldMoneys) {
			assert(m.game >= 0 && m.game < games && m.var > 0 && m.object > 0 && m.names > 0 && worldMoney(m.game) == &m && worldMoneyValue(m.game, m.var));
			assert(!worldKeptValue(m.game, m.var) && !worldKeptCount(m.game, m.var) && !worldDuelValue(m.game, m.var));
		}
		for (const WorldDoorValue &v : kWorldDoorValues) {
			assert(v.game >= 0 && v.game < games && worldKeptValue(v.game, v.var) && worldKeptValue(v.game, v.sets) && v.value && v.var != v.sets);
			const WorldLink *link = worldLinkFrom(v.game, v.room, v.door);
			assert(link);
		}
		for (const WorldEntryValue &v : kWorldEntryValues) assert(v.game >= 0 && v.game < games && worldKeptValue(v.game, v.var));
		// (Monkey Island 2's: the saw's sale, the bucket, the dealer; the pieces
		// of eight; the peg leg sawn, kept as its class, its way out calling the
		// woodsmith away, as 0301's rows read it; the mud in the bucket.)
		int mi2 = -1;
		for (int g = 0; g < games; ++g) if (sameId(kWorldGames[g].gameid, "monkey2")) mi2 = g;
		assert(mi2 == 1 && worldExportVersion("monkey2") >= 40 && worldTalks(mi2) && !worldTalks(0));
		// (From 0304 the bartender's talk by the rat in the soup, the cook
		// fired and the job taken, each kept; the job offered kept too.)
		int bar = 0;
		for (const WorldTalk &t : kWorldTalks)
			bar += t.game == mi2 && t.room == 9 && t.kind == kWorldVerbTalk && t.costume == 17 && t.reads == 0x8000 + 74 && t.also[0] == 0x8000 + 71 && t.also[1] == 0x8000 + 77 && !t.also[2] && !t.gives;
		assert(bar == 1 && worldKeptValue(mi2, 0x8000 + 94) && worldKeptValueAs(mi2, 0x8000 + 77, 1) == 1 && worldKeptValueAs(mi2, 0x8000 + 77, 2) == -1);
		assert(worldTalkGives(mi2, 540) && worldTalkGives(mi2, 124) && !worldTalkGives(mi2, 76));
		const WorldMoney *money = worldMoney(mi2);
		assert(money && money->var == 305 && money->object == 76 && !worldMoney(0));
		const WorldKeptClass *leg = worldKeptClass(mi2, kWorldClassValue + 1);
		assert(leg && leg->object == 130 && leg->cls == 6 && worldKeptValue(mi2, kWorldClassValue + 1));
		int sawn = 0, mud = 0;
		for (const WorldValueReader &v : kWorldValueReaders) {
			sawn += v.game == mi2 && v.room == 14 && v.object == 130 && v.kind == kWorldVerbUse && v.with == 540 && v.reads == kWorldClassValue + 1;
			mud += v.game == mi2 && v.room == 20 && v.kind == kWorldVerbUse && v.with == 124 && v.reads == 0x8000 + 367;
		}
		assert(sawn == 1 && mud == 3);
		bool away = false, cleared = false;
		for (const WorldDoorValue &v : kWorldDoorValues) away = away || (v.game == mi2 && v.room == 14 && v.door == 126 && v.var == 166 && v.sets == 0x8000 + 361 && v.to == 1);
		for (const WorldEntryValue &v : kWorldEntryValues) cleared = cleared || (v.game == mi2 && v.room == 14 && v.var == 166 && v.value == 0);
		assert(away && cleared);
		// (Its start's scroll script let go elsewhere; Fate of Atlantis's left as
		// it is, its export as before; from 0307 Fate of Atlantis's let go too,
		// its export version 34 on.)
		int atlantis = -1;
		for (int g = 0; g < games; ++g) if (sameId(kWorldGames[g].gameid, "atlantis")) atlantis = g;
		assert(worldScrollStart(mi2) && atlantis >= 0 && worldScrollStart(atlantis) && worldExportVersion("atlantis") >= 34 && !worldScrollStart(0));
	}
	std::puts("PASS: the catalog's talks, money, doors' and entries' values (Monkey Island 2's sale of the saw, its bucket, its antique dealer, from 0304 its bartender by three values, its pieces of eight, its peg leg sawn and its way out)");
	return 0;
}
