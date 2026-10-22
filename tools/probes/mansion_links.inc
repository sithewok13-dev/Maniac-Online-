	// What the mansion's things do to other things, through the original
	// scripts (DOS V1): the new engine's kManiacSets, kManiacOpenedBy,
	// kManiacTogether and kManiacShutsBehind follow this (from 0155 the things
	// file records it all for every thing; see test_sandbox_engine.py).
	// Object states: 8 the second picture, 2 untouchable (no picture).
	const bool safe = _scummverseExplorationSafety;
	auto clearScripts = [&]() {
		for (int s = 0; s < NUM_SCRIPT_SLOT; ++s) { vm.slot[s].status = ssDead; vm.slot[s].freezeCount = 0; }
		_currentScript = 0xFF; vm.numNestedScripts = 0; _sentenceNum = 0; stopTalk(); _sound->stopAllSounds();
	};
	auto setup = [&](int room) {
		clearScripts(); VAR(VAR_EGO) = 3; startScene(room, nullptr, 0); clearScripts();
		for (int a = 1; a <= 7; ++a) derefActor(a, "links probe")->putActor(0, 0, 0);
		derefActor(3, "links probe")->setActorCostume(3);
		derefActor(3, "links probe")->putActor(160, 120, room);
		VAR(VAR_ACTOR_RANGE_MIN) = 1; VAR(VAR_ACTOR_RANGE_MAX) = 7; VAR(VAR_HAVE_MSG) = 0; _userPut = 1;
	};
	auto pump = [&](int frames) {
		for (int frame = 0; frame < frames; ++frame) {
			for (int s = 0; s < NUM_SCRIPT_SLOT; ++s) if (vm.slot[s].status == ssPaused) { vm.slot[s].delay = 0; vm.slot[s].status = ssRunning; }
			VAR(VAR_HAVE_MSG) = 0; runAllScripts(); walkActors(); _sound->processSound();
		}
	};
	// (room, thing, verb, the other thing, its state after: in turn, each
	// from the state the one before left; a room of 0 goes on in the same.)
	// Verbs: 1 open, 2 close, 4 turn on, 5 turn off, 9 push, 10 pull, 13 walk.
	const int steps[][5] = {
		{1, 276, 1, 50, 8}, {0, 276, 2, 50, 0},        // the mailbox
		{22, 380, 1, 209, 8}, {0, 380, 2, 209, 0},     // the desk
		{6, 138, 1, 108, 8}, {0, 138, 2, 108, 0},      // the gate, seen from the garage
		{6, 138, 1, 143, 8}, {0, 138, 2, 143, 0},      // and from the other side
		{10, 69, 1, 69, 0},                            // the hall's secret door: no handle
		{0, 351, 9, 69, 8},                            // the gargoyle pushed opens it
		{0, 351, 10, 69, 8}, {0, 69, 2, 69, 8},        // pulled, still open; no handle to close it
		{0, 69, 13, 69, 0},                            // down its stairs, it shuts behind
		{10, 351, 10, 69, 8},                          // pulled, the gargoyle opens it too
		{6, 138, 1, 143, 8}, {0, 138, 9, 108, 0},      // the gate as one: opened, all open; pushed, all shut
		{0, 138, 9, 138, 0}, {0, 138, 10, 108, 8},     // (pushed shut, nothing); pulled, all open
		{0, 138, 10, 138, 8}, {0, 138, 2, 143, 0},     // (pulled open, nothing); closed, all shut
		{16, 143, 10, 138, 8}, {0, 143, 9, 138, 0},    // from the garage: that side and the deck's
		{0, 143, 10, 108, 0}, {0, 143, 9, 143, 0},     // (the other side left; shut again)
		{52, 108, 10, 138, 8}, {0, 108, 9, 138, 0},    // from the other side: the same
		{0, 108, 10, 143, 0},
		{24, 116, 1, 115, 2}, {0, 116, 1, 117, 2},     // the shower curtain as one: opened, all aside
		{0, 279, 2, 117, 8}, {0, 279, 2, 115, 8},      // closed from its gathered end, all back
		{0, 279, 10, 116, 2}, {0, 115, 2, 115, 8},     // pulled, aside; closed by a part, back
		{0, 253, 4, 253, 0}, {0, 253, 5, 253, 8},      // the sink runs without its second picture
		{0, 118, 4, 118, 8}, {0, 118, 5, 118, 8},      // the shower's tap: no handle; off, nothing
	};
	// (The lines said.)
	struct Line { int thing, verb; const char *line; };
	const Line lines[] = {{69, 1, "There's no handle here!"}, {69, 2, "There's no handle here!"}, {118, 4, "The handle's missing."}};
	for (const auto &s : steps) {
		if (s[0]) setup(s[0]);
		VAR(VAR_ACTIVE_OBJECT1) = s[1];
		_charsetBuffer[0] = 0;
		runObjectScript(s[1], s[2], false, false, nullptr);
		pump(1);
		const Common::String said((const char *)_charsetBuffer);
		pump(300);
		if (getState(s[3]) != s[4]) error("Mansion links probe: %d verb %d left %d at %d (not %d)", s[1], s[2], s[3], getState(s[3]), s[4]);
		for (const Line &l : lines) if (l.thing == s[1] && l.verb == s[2] && said != l.line) error("Mansion links probe: %d verb %d says '%s'", s[1], s[2], said.c_str());
		warning("Mansion links probe: %d verb %d: %d at %d", s[1], s[2], s[3], getState(s[3]));
	}
	warning("SCUMMVERSE_MANSION_LINKS_PASS enabled=%d", safe);
	quitGame();
