	// The mansion's padlocked door (room 4, 160; its padlocks 161 and 162;
	// the key 141 from the pit under the pool), through the original
	// scripts (DOS V1), as a player does it: the door locked (state 4) until
	// both padlocks are unlocked (8), the second clearing its lock; then Open
	// opens it (8). The new engine's kManiacPadlocks follows this (the things
	// file has each padlock alone). Numbers only; no line is kept.
	const bool safe = _scummverseExplorationSafety;
	auto clearScripts = [&]() {
		for (int s = 0; s < NUM_SCRIPT_SLOT; ++s) { vm.slot[s].status = ssDead; vm.slot[s].freezeCount = 0; }
		_currentScript = 0xFF; vm.numNestedScripts = 0; _sentenceNum = 0; stopTalk(); _sound->stopAllSounds();
	};
	auto pump = [&](int frames) {
		for (int frame = 0; frame < frames; ++frame) {
			for (int s = 0; s < NUM_SCRIPT_SLOT; ++s) if (vm.slot[s].status == ssPaused) { vm.slot[s].delay = 0; vm.slot[s].status = ssRunning; }
			VAR(VAR_HAVE_MSG) = 0; runAllScripts(); walkActors(); _sound->processSound();
		}
	};
	clearScripts(); VAR(VAR_EGO) = 3; startScene(4, nullptr, 0); clearScripts();
	for (int a = 1; a <= 7; ++a) derefActor(a, "locks probe")->putActor(0, 0, 0);
	derefActor(3, "locks probe")->setActorCostume(3);
	derefActor(3, "locks probe")->putActor(160, 120, 4);
	VAR(VAR_ACTOR_RANGE_MIN) = 1; VAR(VAR_ACTOR_RANGE_MAX) = 7; VAR(VAR_HAVE_MSG) = 0; _userPut = 1;
	addObjectToInventory(141, 2); putOwner(141, 3);
	// (verb, thing, the thing with it, then the door's and each padlock's state.)
	// Verbs: 1 open, 8 unlock.
	const int steps[][6] = {
		{1, 160, 0, 4, 0, 0},     // locked: Open says so
		{8, 161, 141, 4, 8, 0},   // one padlock unlocked: still locked
		{1, 160, 0, 4, 8, 0},
		{8, 162, 141, 0, 8, 8},   // both: the door unlocked
		{1, 160, 0, 8, 8, 8},     // and opened
	};
	if (getState(160) != 4 || getState(161) || getState(162)) error("Mansion locks probe: start %d %d %d", getState(160), getState(161), getState(162));
	for (const auto &s : steps) {
		VAR(VAR_ACTIVE_VERB) = s[0]; VAR(VAR_ACTIVE_OBJECT1) = s[1]; VAR(VAR_ACTIVE_OBJECT2) = s[2];
		_charsetBuffer[0] = 0;
		runObjectScript(s[1], s[0], false, false, nullptr);
		pump(300);
		if (getState(160) != s[3] || getState(161) != s[4] || getState(162) != s[5] || _currentRoom != 4)
			error("Mansion locks probe: verb %d on %d: %d %d %d in room %d", s[0], s[1], getState(160), getState(161), getState(162), _currentRoom);
		warning("Mansion locks probe: verb %d on %d: %d %d %d", s[0], s[1], getState(160), getState(161), getState(162));
	}
	warning("SCUMMVERSE_MANSION_LOCKS_PASS enabled=%d", safe);
	quitGame();
