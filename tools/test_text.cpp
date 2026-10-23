// Portable speech wrapping: word boundaries, long words, explicit breaks,
// non-ASCII, font stand-ins and bounds. c++ -std=c++11 -Wall -Wextra -Werror
// -fsanitize=address,undefined -Iengine tools/test_text.cpp
#include "common/scummverse_text.h"
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
using Scummverse::wrapSpeech;

static std::string wrap(const char *in, int columns, int *lines = nullptr) {
	char out[512]; int n = wrapSpeech(in, out, sizeof(out), columns);
	if (lines) *lines = n;
	return out;
}

int main() {
	int lines = 0;
	// The device bug: a hard break inside "sight," at column 28.
	assert(wrap("Ah, the moon's a luring sight, but the shadows hold more secrets for us both.", 28, &lines) ==
	       "Ah, the moon's a luring\rsight, but the shadows hold\rmore secrets for us both.");
	assert(lines == 3);
	// No line exceeds the width and no word is split when it fits a line.
	const char *sample = "Hold still. That's a great shot of the haunted greenhouse at midnight!";
	std::string w = wrap(sample, 20);
	size_t start = 0;
	while (start <= w.size()) {
		size_t end = w.find('\r', start); if (end == std::string::npos) end = w.size();
		assert(end - start <= 20);
		start = end + 1;
	}
	// A word longer than a line is split into full-width pieces.
	assert(wrap("Supercalifragilistic", 8, &lines) == "Supercal\rifragili\rstic" && lines == 3);
	// Explicit breaks, collapsed spaces and dropped non-ASCII bytes.
	assert(wrap("one\ntwo   three", 28, &lines) == "one\rtwo three" && lines == 2);
	assert(wrap("caf\xc3\xa9 ok", 28) == "caf ok");
	assert(wrap("", 28, &lines).empty() && lines == 1);
	// Bytes the V1/V2 font draws as other glyphs (a copyright sign, arrows,
	// a pound sign...) are said in plain text, and lines count what is said.
	assert(wrap("2+2=4 ~ok~ a_b | c\\d `x`", 28) == "2+2-4 ok a-b c d 'x'");
	assert(wrap("It is 100% certain now", 12, &lines) == "It is 100\rpercent\rcertain now" && lines == 3);
	assert(wrap("%", 28) == "percent" && wrap("===", 28) == "---");
	// Output is bounded and terminated.
	char small[6]; wrapSpeech("abcdefghij", small, sizeof(small), 28);
	assert(std::strlen(small) == 5);
	wrapSpeech("%%%%", small, sizeof(small), 28);
	assert(std::string(small) == "perce");
	assert(wrapSpeech("x", small, 0, 28) == 0 && wrapSpeech(nullptr, small, 6, 28) == 0 && small[0] == 0);
	std::printf("PASS: speech wrapping (word boundaries, long words, breaks, ASCII, font stand-ins, bounds)\n");
}
