// Scummverse: the phone's restore point read (common/scummverse_restore.h):
// the file the iPhone's backend writes as the app is put away, damaged and
// odd ones. Build: c++ -std=c++11 -Wall -Wextra -Werror
//   -fsanitize=address,undefined -Iengine tools/test_restore.cpp
//   engine/common/scummverse_restore.cpp
#include "common/scummverse_restore.h"

#include <cassert>
#include <cstdio>
#include <cstring>
#include <random>
#include <string>
#include <vector>

namespace Restore = Scummverse::Restore;

// (Copied into a buffer of its own size: a read past it is caught.)
static bool parse(const std::string &text, std::string &target, int &slot, int capacity = 64) {
	std::vector<char> copy(text.begin(), text.end());
	std::vector<char> name(capacity > 0 ? capacity : 1, 'x');
	const bool whole = Restore::parse(copy.empty() ? "" : copy.data(), copy.size(), name.data(), capacity, slot);
	if (capacity > 0) {
		assert(std::memchr(name.data(), 0, name.size()));
		target = name.data();
	}
	assert(whole ? slot >= 0 && slot <= Restore::kMostSlot && !target.empty() : slot == -1 && (capacity <= 0 || target.empty()));
	return whole;
}

static bool names(const std::string &text, const char *target, int slot) {
	std::string t;
	int s = -2;
	return parse(text, t, s) && t == target && s == slot;
}

static bool refused(const std::string &text) {
	std::string t;
	int s = -2;
	return !parse(text, t, s);
}

// What the backend writes (ScummVM's INIFile::saveToStream: the section,
// then each key=value, each line ended with \n).
static std::string written(const std::string &target, const std::string &slot) {
	return "[state]\nrestore_target=" + target + "\nrestore_slot=" + slot + "\n";
}

int main() {
	// The backend's own file: the mansion, its autosave slot; a story; others.
	assert(names(written("maniac", "0"), "maniac", 0));
	assert(names(written("scummverse-story-tentacle", "0"), "scummverse-story-tentacle", 0));
	assert(names(written("maniac-1", "7"), "maniac-1", 7));
	assert(names(written("my_game", "999"), "my_game", 999));
	assert(names(written("maniac", "00"), "maniac", 0));
	std::printf("PASS: the backend's own restore points\n");

	// As ScummVM's reader lets them be: \r\n, spaces, a byte-order mark,
	// comments, blank lines, other sections and keys, the keys in another
	// order or case, the last line's end then spaces.
	assert(names("[state]\r\nrestore_target=maniac\r\nrestore_slot=0\r\n", "maniac", 0));
	assert(names("  [state]  \n  restore_target  =  maniac  \n\trestore_slot\t=\t0\t\n", "maniac", 0));
	assert(names("\xEF\xBB\xBF[state]\nrestore_target=maniac\nrestore_slot=0\n", "maniac", 0));
	assert(names("# put away\n; again\n// and\n(odd)\n\n[state]\n\nrestore_target=maniac\n# here\nrestore_slot=0\n\n", "maniac", 0));
	assert(names("[other]\nrestore_target=zak\nrestore_slot=3\n[state]\nrestore_slot=0\nrestore_target=maniac\n[after]\nx=y\n", "maniac", 0));
	assert(names("[STATE]\nRestore_Target=maniac\nRESTORE_SLOT=4\n", "maniac", 4));
	assert(names("[state]\nrestore_target=maniac\nrestore_slot=0\n   \t", "maniac", 0));
	// (After ']': ignored, as there; no ']' after its letters: there, the app stops.)
	assert(names("[state] here\nrestore_target=maniac\nrestore_slot=0\n", "maniac", 0));
	assert(refused("[state here\nrestore_target=maniac\nrestore_slot=0\n"));
	// (The first of each counts, in the first state section, as ScummVM's getKey.)
	assert(names("[state]\nrestore_target=maniac\nrestore_target=zak\nrestore_slot=1\nrestore_slot=2\n", "maniac", 1));
	assert(names("[state]\nrestore_target=maniac\nrestore_slot=1\n[state]\nrestore_target=zak\nrestore_slot=2\n", "maniac", 1));
	assert(refused("[state]\nrestore_target=maniac\n[state]\nrestore_slot=2\n"));
	std::printf("PASS: as ScummVM's INI reader takes it (line ends, spaces, a byte-order mark, comments, other sections, case, the first of each)\n");

	// Missing or empty: nothing, either key, either value; keys elsewhere.
	assert(refused(""));
	assert(refused("\n\n"));
	assert(refused("[state]\n"));
	assert(refused("[state]\nrestore_target=maniac\n"));
	assert(refused("[state]\nrestore_slot=0\n"));
	assert(refused(written("", "0")));
	assert(refused(written("maniac", "")));
	assert(refused("[other]\nrestore_target=maniac\nrestore_slot=0\n"));
	std::printf("PASS: missing keys or values refused\n");

	// Damaged: every cut of a whole one, at every length (the app stopped as
	// it wrote, or a disk full): refused, a slot or target cut short
	// included.
	for (const std::string &whole : {written("maniac", "0"), written("maniac", "12"), written("scummverse-story-dig", "105"),
			std::string("[state]\r\nrestore_target=maniac\r\nrestore_slot=34\r\n")}) {
		std::string t;
		int s;
		assert(parse(whole, t, s));
		for (size_t n = 0; n < whole.size(); ++n) assert(refused(whole.substr(0, n)));
	}
	std::printf("PASS: every cut of a whole restore point refused (none names a slot or target cut short)\n");

	// Damaged inside: a NUL byte, a broken section, a key outside one, junk,
	// a bad key name, a target ScummVM cannot name, a slot not a number.
	{
		std::string withNul = written("maniac", "0");
		withNul[withNul.find("maniac") + 3] = 0;
		assert(refused(withNul));
		std::string nulAtEnd = written("maniac", "0");
		nulAtEnd.push_back(0);
		assert(refused(nulAtEnd));
		// (Even where nothing is read: ScummVM's reader would cut the line there.)
		std::string nulInComment = "# put\n" + written("maniac", "0");
		nulInComment[3] = 0;
		assert(refused(nulInComment));
		std::string nulAtEndOfLine = written("maniac", "0");
		nulAtEndOfLine.insert(nulAtEndOfLine.size() - 1, 1, '\0');
		assert(refused(nulAtEndOfLine));
	}
	assert(refused("[stat\nrestore_target=maniac\nrestore_slot=0\n"));
	assert(refused("[]\nrestore_target=maniac\nrestore_slot=0\n"));
	assert(refused("[st/ate]\nrestore_target=maniac\nrestore_slot=0\n"));
	assert(refused("restore_target=maniac\nrestore_slot=0\n"));
	assert(refused("restore_target=maniac\n[state]\nrestore_target=maniac\nrestore_slot=0\n"));
	assert(refused("[state]\nrestore_target=maniac\njunk\nrestore_slot=0\n"));
	assert(refused("[state]\nrestore_target=maniac\n=0\nrestore_slot=0\n"));
	assert(refused("[state]\nrestore_target=maniac\nre/store=1\nrestore_slot=0\n"));
	assert(refused("[state]\nrestore_target=maniac\nr\xC3\xA9=1\nrestore_slot=0\n"));
	for (const char *target : {"mani ac", "../maniac", "maniac/x", "man.iac", "maniac\xC3\xA9", "\xFF", "[maniac]", "maniac=1", "-"}) {
		const bool ok = std::string(target) == "-";
		assert(ok ? names(written(target, "0"), target, 0) : refused(written(target, "0")));
	}
	for (const char *slotText : {"-1", "+1", "0x1", "1a", "1 2", "1.0", "1000", "99999999999999999999", "\xEF\xBC\x91", " "})
		assert(refused(written("maniac", slotText)));
	std::printf("PASS: damaged inside refused (NUL bytes, sections, keys outside one, junk, names, targets, slots)\n");

	// Sizes: at most kMostBytes; a target only if it fits whole.
	{
		std::string padded = written("maniac", "0");
		padded += std::string(Restore::kMostBytes - padded.size() - 1, '\n') + "\n";
		assert(padded.size() == Restore::kMostBytes && names(padded, "maniac", 0));
		assert(refused(padded + "\n"));
		std::string t;
		int s;
		assert(parse(written("maniac", "0"), t, s, 7) && t == "maniac" && s == 0);
		assert(!parse(written("maniac", "0"), t, s, 6));
		assert(!parse(written("maniac", "0"), t, s, 1));
		const std::string longName(200, 'm');
		assert(!parse(written(longName, "0"), t, s, 64) && parse(written(longName, "0"), t, s, 201) && t == longName);
		// (No buffer at all, or none to write in: refused, nothing written.)
		int s2 = 5;
		char one = 'x';
		assert(!Restore::parse(nullptr, 0, &one, 1, s2) && one == 0 && s2 == -1);
		s2 = 5;
		assert(!Restore::parse("[state]\n", 8, nullptr, 64, s2) && s2 == -1);
		one = 'x';
		assert(!Restore::parse("[state]\n", 8, &one, 0, s2) && one == 'x');
	}
	std::printf("PASS: sizes (at most %d bytes; a target only whole in its buffer)\n", (int)Restore::kMostBytes);

	// Random damage: bytes flipped, dropped and added in whole ones, and
	// random text: never a crash, a read past the end or a name or slot
	// that could not be (each checked in parse above).
	std::mt19937 random(20261024);
	const std::string base = written("maniac", "42");
	int whole = 0, total = 0;
	for (int round = 0; round < 300000; ++round) {
		std::string text = base;
		const int edits = 1 + random() % 4;
		for (int e = 0; e < edits; ++e) {
			const size_t at = random() % (text.size() + 1);
			switch (random() % 3) {
			case 0: if (at < text.size()) text[at] = (char)(random() % 256); break;
			case 1: if (at < text.size()) text.erase(at, 1); break;
			default: text.insert(text.begin() + at, (char)(random() % 256)); break;
			}
		}
		if (round % 10 == 0) {
			text.clear();
			const size_t n = random() % 80;
			static const char letters[] = "[]=\n\r #;/(statergoS_0123maniac-";
			for (size_t i = 0; i < n; ++i) text.push_back(letters[random() % (sizeof(letters) - 1)]);
		}
		std::string t;
		int s;
		total++;
		if (parse(text, t, s)) {
			whole++;
			for (char c : t) assert((c >= '0' && c <= '9') || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '-' || c == '_');
		}
	}
	std::printf("PASS: %d damaged or random files read safely (%d still a restore point)\n", total, whole);
	return 0;
}
