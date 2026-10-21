	// The basement's water valve through the original scripts (DOS V1): what
	// opening or turning it on, and closing or turning it off, changes (the
	// new engine's kManiacFollows and kManiacDoorNeeds follow this). Object
	// states: 8 the second picture; 2 untouchable.
	const bool safe = _scummverseExplorationSafety;
	auto clearScripts = [&]() {
		for (int s = 0; s < NUM_SCRIPT_SLOT; ++s) { vm.slot[s].status = ssDead; vm.slot[s].freezeCount = 0; }
		_currentScript = 0xFF; vm.numNestedScripts = 0; stopTalk();
	};
	auto setup = [&](int room) {
		clearScripts(); VAR(VAR_EGO) = 3; startScene(room, nullptr, 0); clearScripts();
		for (int a = 1; a <= 7; ++a) derefActor(a, "pool probe")->putActor(0, 0, 0);
		derefActor(3, "pool probe")->setActorCostume(3);
		derefActor(3, "pool probe")->putActor(160, 120, room);
		VAR(VAR_ACTOR_RANGE_MIN) = 1; VAR(VAR_ACTOR_RANGE_MAX) = 7; VAR(VAR_HAVE_MSG) = 0; _userPut = 1;
	};
	auto pump = [&](int frames) {
		for (int frame = 0; frame < frames; ++frame) {
			for (int s = 0; s < NUM_SCRIPT_SLOT; ++s) if (vm.slot[s].status == ssPaused) { vm.slot[s].delay = 0; vm.slot[s].status = ssRunning; }
			VAR(VAR_HAVE_MSG) = 0; runAllScripts(); walkActors(); _sound->processSound();
		}
	};
	// Open (1) and turn on (4) drain; close (2) and turn off (5) fill.
	const int verbs[4][2] = {{1, 1}, {2, 0}, {4, 1}, {5, 0}};
	setup(29);
	for (const auto &v : verbs) {
		VAR(VAR_ACTIVE_OBJECT1) = 66;
		runObjectScript(66, v[0], false, false, nullptr);
		pump(300);
		const bool drained = v[1];
		if (getState(66) != (drained ? 8 : 0) || getState(139) != (drained ? 8 : 0) || getState(172) != (drained ? 0 : 2))
			error("Pool valve probe: verb %d left valve %d, pool %d, ladder %d", v[0], getState(66), getState(139), getState(172));
		warning("Pool valve probe: verb %d: valve %d, pool %d, ladder %d", v[0], getState(66), getState(139), getState(172));
	}
	warning("SCUMMVERSE_POOL_VALVE_PASS enabled=%d", safe);
	quitGame();
