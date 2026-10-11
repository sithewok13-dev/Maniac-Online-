	// Test-only injection into a temporary translation unit; never in an IPA.
	const bool safe = _scummverseExplorationSafety;
	auto clearScripts = [&]() {
		for (int s = 0; s < NUM_SCRIPT_SLOT; ++s) {
			vm.slot[s].status = ssDead;
			vm.slot[s].freezeCount = 0;
		}
		_currentScript = 0xFF;
		vm.numNestedScripts = 0;
		stopTalk();
	};
	auto setup = [&](int room) {
		clearScripts();
		VAR(VAR_EGO) = 3;
		startScene(room, nullptr, 0);
		clearScripts();
		for (int a = 1; a <= 7; ++a)
			derefActor(a, "safety probe")->putActor(0, 0, 0);
		derefActor(3, "safety probe")->setActorCostume(3);
		derefActor(3, "safety probe")->putActor(160, 120, room);
		VAR(VAR_ACTOR_RANGE_MIN) = 1;
		VAR(VAR_ACTOR_RANGE_MAX) = 7;
		VAR(VAR_HAVE_MSG) = 0;
		_userPut = 1;
		_sound->processSound();
	};
	auto pump = [&](int frames) {
		for (int frame = 0; frame < frames; ++frame) {
			for (int s = 0; s < NUM_SCRIPT_SLOT; ++s) {
				if (vm.slot[s].status == ssPaused) {
					vm.slot[s].delay = 0;
					vm.slot[s].status = ssRunning;
				}
			}
			VAR(VAR_HAVE_MSG) = 0;
			runAllScripts();
			walkActors();
			_sound->processSound();
		}
	};
	auto check = [&](bool passed, const char *label) {
		if (!passed) error("Safety probe failed: %s (enabled=%d)", label, safe);
		warning("Safety probe passed: %s (enabled=%d)", label, safe);
	};

	// Reproduce the reported kitchen disappearance through its original scene.
	if (safe) {
		setup(7);
		derefActor(10, "kitchen probe")->putActor(62, 56, 7);
		derefActor(3, "kitchen probe")->putActor(60, 56, 7);
		VAR(VAR_CAMERA_POS_X) = 47;
		_scummVars[126] = 0;
		runScript(153, false, false, nullptr);
		pump(50);
		check(derefActor(10, "kitchen probe")->_room == 7 &&
			isScriptRunning(153) && !isScriptRunning(38) && _userPut == 1,
			"Edna stays during kitchen encounter");
		check(_scummVars[126] == 0, "kitchen wait does not set chase flag");
		startScene(10, nullptr, 0);
		pump(120);
		check(!isScriptRunning(153) && derefActor(10, "kitchen probe")->_room == 19,
			"Edna resumes original departure after kitchen exit");
	}

	// Walk across Green Tentacle's original hallway, including Bernard.
	for (int kid : {3, 5}) {
		setup(12);
		VAR(VAR_EGO) = kid;
		derefActor(3, "hallway probe")->putActor(0, 0, 0);
		Actor *player = derefActor(kid, "hallway probe");
		player->setActorCostume(kid);
		player->putActor(38, 52, 12);
		derefActor(11, "hallway probe")->putActor(5, 52, 26);
		_scummVars[98] = _scummVars[99] = _scummVars[105] = 0;
		runEntryScript();
		int x, y, dir;
		getObjectXYPos(457, x, y, dir);
		const AdjustBoxResult dest = player->adjustXYToBeInBox(x, y);
		player->startWalkActor(x, y, dir);
		pump(200);
		if (safe) {
			check(!isScriptRunning(51) && !isScriptRunning(161) && _userPut == 1 &&
				player->getPos().x == dest.x * V12_X_MULTIPLIER &&
				player->getPos().y == dest.y * V12_Y_MULTIPLIER &&
				derefActor(14, "hallway probe")->_room == 12,
				"kid passes visible Green Tentacle without food or drink");
			check(_scummVars[98] == 0 && _scummVars[99] == 0,
				"hallway bypass preserves food and drink puzzle state");
			VAR(VAR_ACTIVE_OBJECT1) = 457;
			runObjectScript(457, 13, false, false, nullptr);
			check(_currentRoom == 38 && player->_room == 38, "original upstairs transition");
			VAR(VAR_ACTIVE_OBJECT1) = 462;
			runObjectScript(462, 1, false, false, nullptr);
			runObjectScript(462, 13, false, false, nullptr);
			check(_currentRoom == 26 && player->_room == 26 && _userPut == 1,
				"original route reaches Weird Ed with controls");
		} else {
			check(isScriptRunning(51) && (player->getPos().x != dest.x * V12_X_MULTIPLIER || _userPut == 0),
				"original hallway gate remains when disabled");
		}
	}

	// Edna's real monitor with a kid within capture distance.
	setup(19);
	derefActor(10, "safety probe")->putActor(160, 120, 19);
	_scummVars[161] = 0;
	runScript(36, false, false, nullptr);
	check((_scummVars[126] == 0) == safe, "Edna target decision");
	if (safe) {
		pump(40);
		check(isScriptRunning(36) && !isScriptRunning(37) && _userPut == 1 &&
			derefActor(3, "safety probe")->_room == 19, "Edna monitor survives without capture");
	} else {
		pump(1);
		check(isScriptRunning(37), "original Edna capture still starts when disabled");
	}

	setup(26);
	derefActor(11, "safety probe")->putActor(160, 120, 26);
	_scummVars[92] = 0;
	runScript(91, false, false, nullptr);
	check((_scummVars[118] == 0) == safe, "Ed target decision");
	if (safe) {
		pump(40);
		check(isScriptRunning(91) && !isScriptRunning(88) && _userPut == 1 &&
			derefActor(3, "safety probe")->_room == 26, "Ed monitor survives without capture");
	}

	// A real pickup object starts 116 after resetting its permission variable.
	setup(26);
	derefActor(11, "safety probe")->putActor(160, 120, 26);
	VAR(VAR_ACTIVE_OBJECT1) = 34;
	_scummVars[123] = 34;
	_scummVars[175] = 0;
	putOwner(34, OF_OWNER_ROOM);
	runObjectScript(34, 14, false, false, nullptr);
	check((getOwner(34) == 3) == safe, "Ed guarded pickup");
	check(_scummVars[106] == 0, "pickup override does not persist permission");
	if (safe) check(_scummVars[175] == 0 && _userPut == 1, "pickup leaves controls usable");

	// Wrong contracts must never disable input before reaching the death guard.
	for (int contract = 1; contract <= 2; ++contract) {
		setup(23);
		VAR(VAR_ACTIVE_OBJECT1) = 60;
		VAR(VAR_ACTIVE_OBJECT2) = 14;
		_scummVars[101] = contract;
		runScript(110, false, false, nullptr);
		check((_userPut == 1) == safe, "wrong contract control state");
		check(_scummVars[101] == contract, "contract state remains unchanged");
	}


	// Purple Tentacle's original search/return still completes with a kid present.
	setup(8);
	runScript(48, false, false, nullptr);
	pump(500);
	if (safe) {
		check(!isScriptRunning(48) && !isScriptRunning(49) &&
			derefActor(13, "safety probe")->_room == 31 &&
			derefActor(3, "safety probe")->_room == 8 &&
			_currentRoom == 8 && VAR(VAR_EGO) == 3 && _userPut == 1,
			"Purple Tentacle search returns without imprisonment or ego switch");
	} else {
		check(derefActor(3, "safety probe")->_room == 4,
			"original Purple Tentacle search captures when disabled");
	}

	// The bad tape completes its ordinary dialogue and restores input/camera.
	setup(20);
	derefActor(14, "safety probe")->putActor(200, 116, 20);
	_scummVars[154] = 0;
	_scummVars[157] = 25;
	runScript(107, false, false, nullptr);
	pump(500);
	if (safe) {
		check(!isScriptRunning(107) && _currentRoom == 20 && _userPut == 1 &&
			derefActor(3, "safety probe")->_room == 20 &&
			derefActor(3, "safety probe")->_costume == 3,
			"bad tape finishes without death or room loss");
	} else {
		check(derefActor(3, "safety probe")->_costume == 0,
			"original bad tape is fatal when disabled");
	}
	check(_scummVars[157] == 25, "tape contents are not changed");

	if (safe) {
		setup(38);
		derefActor(10, "safety probe")->putActor(120, 104, 38);
		derefActor(11, "safety probe")->putActor(40, 104, 26);
		_scummVars[161] = 0;
		runScript(39, false, false, nullptr);
		pump(120);
		check(derefActor(10, "safety probe")->_room == 19 &&
			_scummVars[125] == 0 && !isScriptRunning(37) && _userPut == 1,
			"Edna hallway-to-bedroom patrol completes");
	}


	if (safe) {
		// Actual microwave opening handler with radioactive water inside.
		setup(7);
		VAR(VAR_ACTIVE_OBJECT1) = 85;
		putState(85, 0);
		putState(83, kObjectStateIntrinsic);
		_scummVars[166] = 2;
		runScript(60, false, false, nullptr);
		runObjectScript(85, 1, false, false, nullptr);
		pump(10);
		check(_currentRoom == 7 && _userPut == 1 &&
			derefActor(3, "safety probe")->_costume == 3,
			"radioactive microwave caller preserves player");

		// Actual pool refill script tries every kid in the submerged room.
		setup(2);
		putState(66, 0);
		putState(157, kObjectStateIntrinsic);
		runScript(75, false, false, nullptr);
		pump(100);
		check(!isScriptRunning(75) && _currentRoom == 2 && _userPut == 1 &&
			derefActor(3, "safety probe")->_room == 2 &&
			derefActor(3, "safety probe")->_costume == 3,
			"pool refill completes without drowning");

		setup(2);
		VAR(VAR_ACTIVE_OBJECT1) = 288;
		runObjectScript(288, 9, false, false, nullptr);
		pump(5);
		check(_currentRoom == 2 && _userPut == 1 && !isScriptRunning(62),
			"reactor button cannot enter game over");
	}

	// Direct destructive entries, including every death reason, are inert.
	if (safe) {
		setup(1);
		const int hazards[] = {7,12,37,49,61,62,88,89,117,123,128};
		for (uint i = 0; i < ARRAYSIZE(hazards); ++i) {
			for (int reason = 1; reason <= 6; ++reason) {
				_scummVars[95] = reason;
				runScript(hazards[i], false, false, nullptr);
				check(!isScriptRunning(hazards[i]) && _currentRoom == 1 && _userPut == 1 &&
					derefActor(3, "safety probe")->_room == 1 &&
					derefActor(3, "safety probe")->_costume == 3, "destructive entry has no side effects");
			}
		}
	} else {
		setup(1);
		runScript(61, false, false, nullptr);
		check(isScriptRunning(61), "original death starts when disabled");
	}
	warning("SCUMMVERSE_SAFETY_PROBE_PASS enabled=%d", safe);
	quitGame();
