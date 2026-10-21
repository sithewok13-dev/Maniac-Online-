	// What the mansion's things do to other things, through the original
	// scripts (DOS V1): the new engine's kManiacSets and kManiacOpenedBy
	// follow this. Object states: 8 the second picture.
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
	// Verbs: 1 open, 2 close, 9 push, 10 pull.
	const int steps[][5] = {
		{1, 276, 1, 50, 8}, {0, 276, 2, 50, 0},        // the mailbox
		{22, 380, 1, 209, 8}, {0, 380, 2, 209, 0},     // the desk
		{6, 138, 1, 108, 8}, {0, 138, 2, 108, 0},      // the gate, seen from the garage
		{6, 138, 1, 143, 8}, {0, 138, 2, 143, 0},      // and from the other side
		{10, 69, 1, 69, 0},                            // the hall's secret door: no handle
		{0, 351, 9, 69, 8},                            // the gargoyle pushed opens it
	};
	for (const auto &s : steps) {
		if (s[0]) setup(s[0]);
		VAR(VAR_ACTIVE_OBJECT1) = s[1];
		_charsetBuffer[0] = 0;
		runObjectScript(s[1], s[2], false, false, nullptr);
		pump(1);
		const Common::String said((const char *)_charsetBuffer);
		pump(300);
		if (getState(s[3]) != s[4]) error("Mansion links probe: %d verb %d left %d at %d (not %d)", s[1], s[2], s[3], getState(s[3]), s[4]);
		if (s[1] == 69 && said != "There's no handle here!") error("Mansion links probe: the secret door says '%s'", said.c_str());
		warning("Mansion links probe: %d verb %d: %d at %d", s[1], s[2], s[3], getState(s[3]));
	}
	warning("SCUMMVERSE_MANSION_LINKS_PASS enabled=%d", safe);
	quitGame();
