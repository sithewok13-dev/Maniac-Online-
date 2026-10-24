// SCUMMVERSE story differential (test only; tools/test_story_differential.py
// writes this into a temporary copy of backends/platform/null/null.cpp, the
// same in a stock build and in ours). The null backend, made repeatable:
// - a clock of its own: it moves only when something waits (delayMillis),
//   so a run is the same however fast the machine is, and nothing sleeps;
// - the sound mixed as that clock passes (not once per poll), its samples
//   folded into a running hash;
// - a screen that keeps what is drawn (pixels, palette, cursor, shake), for
//   the engine's side of the probe to read at each frame;
// - a fixed calendar date.
// A loop that reads the clock without ever waiting gets a millisecond every
// 100000 reads, so none can hang (counted; no game is known to need it).
// A game that never waits again (its scripts in a loop that never yields)
// is stopped after 30 seconds of real time with SCUMMVERSE_DIFF_HUNG.
// The main loop away for long (a film, a dialog or a question the game
// waits on, with nobody there to answer): every minute of the clock,
// Escape, then N and Return, as a player would; after 20 minutes, stopped
// with SCUMMVERSE_DIFF_STUCK.
#include "audio/mixer_intern.h"
#include "common/queue.h"
#include "common/textconsole.h"
#include "graphics/surface.h"

static uint32 g_diffNow = 0, g_diffSpins = 0, g_diffSpun = 0;
static uint64 g_diffMixed = 0;
static uint32 g_diffAudio = 2166136261u;

#ifdef POSIX
static void diffStop(const char *said, int code) {
	if (write(2, said, strlen(said)) < 0) {}
	_exit(code);
}
static void diffHung(int) {
	diffStop("WARNING: SCUMMVERSE_DIFF_HUNG\n", 3);
}
// (Each wait: 30 seconds more before the game is taken for hung.)
static void diffAlive() {
	static bool armed = false;
	if (!armed) {
		armed = true;
		signal(SIGALRM, diffHung);
	}
	alarm(30);
}
#else
static void diffStop(const char *said, int code) {}
static void diffAlive() {}
#endif

static uint32 diffFnv(uint32 hash, const void *data, uint size) {
	const byte *p = (const byte *)data;
	while (size--) {
		hash ^= *p++;
		hash *= 16777619u;
	}
	return hash;
}

class DiffGraphicsManager : public NullGraphicsManager {
public:
	Graphics::Surface screen;
	byte palette[768];
	uint32 cursor = 0;
	int shakeX = 0, shakeY = 0;
	bool cursorShown = false;

	DiffGraphicsManager() { memset(palette, 0, sizeof(palette)); }
	~DiffGraphicsManager() override { screen.free(); }

	void initSize(uint width, uint height, const Graphics::PixelFormat *format = nullptr) override {
		NullGraphicsManager::initSize(width, height, format);
		screen.free();
		screen.create(width, height, format ? *format : Graphics::PixelFormat::createFormatCLUT8());
	}
	void setPalette(const byte *colors, uint start, uint num) override {
		if (start < 256)
			memcpy(palette + 3 * start, colors, 3 * MIN<uint>(num, 256 - start));
	}
	void grabPalette(byte *colors, uint start, uint num) const override {
		if (start < 256)
			memcpy(colors, palette + 3 * start, 3 * MIN<uint>(num, 256 - start));
	}
	void copyRectToScreen(const void *buf, int pitch, int x, int y, int w, int h) override {
		Common::Rect r(x, y, x + w, y + h);
		r.clip(Common::Rect(screen.w, screen.h));
		if (r.isEmpty() || !screen.getPixels())
			return;
		const byte *src = (const byte *)buf + (r.top - y) * pitch + (r.left - x) * screen.format.bytesPerPixel;
		screen.copyRectToSurface(src, pitch, r.left, r.top, r.width(), r.height());
	}
	Graphics::Surface *lockScreen() override { return screen.getPixels() ? &screen : nullptr; }
	void fillScreen(uint32 col) override {
		if (screen.getPixels())
			screen.fillRect(Common::Rect(screen.w, screen.h), col);
	}
	void fillScreen(const Common::Rect &r, uint32 col) override {
		Common::Rect c(r);
		c.clip(Common::Rect(screen.w, screen.h));
		if (screen.getPixels() && !c.isEmpty())
			screen.fillRect(c, col);
	}
	void setShakePos(int x, int y) override { shakeX = x; shakeY = y; }
	bool showMouse(bool visible) override {
		const bool was = cursorShown;
		cursorShown = visible;
		return was;
	}
	void setMouseCursor(const void *buf, uint w, uint h, int hotspotX, int hotspotY, uint32 keycolor, bool dontScale, const Graphics::PixelFormat *format, const byte *mask) override {
		const uint bpp = format ? format->bytesPerPixel : 1;
		const int head[5] = {(int)w, (int)h, hotspotX, hotspotY, (int)keycolor};
		uint32 hash = diffFnv(2166136261u, head, sizeof(head));
		if (buf)
			hash = diffFnv(hash, buf, w * h * bpp);
		if (mask)
			hash = diffFnv(hash, mask, w * h);
		cursor = hash;
	}
	void setCursorPalette(const byte *colors, uint start, uint num) override {
		cursor = diffFnv(cursor ^ start, colors, 3 * num);
	}
};
static DiffGraphicsManager *g_diffScreen = nullptr;

// For the engine's side (story_differential.inc): what the screen holds now.
bool scummverseDiffScreen(const byte *&pixels, int &w, int &h, int &pitch, int &bpp, const byte *&palette, uint32 &cursor, int &shake, bool &cursorShown) {
	if (!g_diffScreen || !g_diffScreen->screen.getPixels())
		return false;
	const Graphics::Surface &s = g_diffScreen->screen;
	pixels = (const byte *)s.getPixels();
	w = s.w;
	h = s.h;
	pitch = s.pitch;
	bpp = s.format.bytesPerPixel;
	palette = g_diffScreen->palette;
	cursor = g_diffScreen->cursor;
	shake = g_diffScreen->shakeX * 1000 + g_diffScreen->shakeY;
	cursorShown = g_diffScreen->cursorShown;
	return true;
}
// The sound mixed since the last call (a hash of its samples).
uint32 scummverseDiffAudio() {
	const uint32 hash = g_diffAudio;
	g_diffAudio = 2166136261u;
	return hash;
}
uint32 scummverseDiffNow() { return g_diffNow; }
uint32 scummverseDiffSpun() { return g_diffSpun; }

// The main loop's frames (story_differential.inc), and the keys pressed for
// a player when it is away for long.
static uint32 g_diffFrameAt = 0;
static int g_diffNudges = 0;
static Common::Queue<Common::Event> g_diffKeys;
void scummverseDiffFrame() {
	g_diffFrameAt = g_diffNow;
	g_diffNudges = 0;
}
static bool scummverseDiffNudge(Common::Event &event) {
	if (g_diffNow - g_diffFrameAt >= 20 * 60000u)
		diffStop("WARNING: SCUMMVERSE_DIFF_STUCK\n", 4);
	if (g_diffKeys.empty() && g_diffNow - g_diffFrameAt >= 60000u * (g_diffNudges + 1)) {
		++g_diffNudges;
		warning("SCUMMVERSE_DIFF_NUDGE %u", g_diffNow);
		const Common::KeyState keys[] = {Common::KeyState(Common::KEYCODE_ESCAPE, Common::ASCII_ESCAPE), Common::KeyState(Common::KEYCODE_n, 'n'),
			Common::KeyState(Common::KEYCODE_RETURN, Common::ASCII_RETURN)};
		for (const Common::KeyState &key : keys) {
			Common::Event press;
			press.kbd = key;
			press.type = Common::EVENT_KEYDOWN;
			g_diffKeys.push(press);
			press.type = Common::EVENT_KEYUP;
			g_diffKeys.push(press);
		}
	}
	if (g_diffKeys.empty())
		return false;
	event = g_diffKeys.pop();
	return true;
}

// The sound up to now on the clock, in fixed steps.
static void scummverseDiffMix(MixerManager *manager) {
	Audio::MixerImpl *mixer = manager ? (Audio::MixerImpl *)manager->getMixer() : nullptr;
	if (!mixer)
		return;
	static byte buffer[256 * 4];
	const uint64 due = (uint64)g_diffNow * mixer->getOutputRate() / 1000;
	while (g_diffMixed + 256 <= due) {
		mixer->mixCallback(buffer, sizeof(buffer));
		g_diffAudio = diffFnv(g_diffAudio, buffer, sizeof(buffer));
		g_diffMixed += 256;
	}
}
