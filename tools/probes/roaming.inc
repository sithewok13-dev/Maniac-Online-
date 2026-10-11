	// Finish the real boot/character-selection script, including its cleanup.
	if (!_scummverseRoaming) {
		if (_scummverseRoamingReady) error("Sandbox enabled despite config");
		warning("SCUMMVERSE_ROAMING_PROBE_PASS enabled=0");
		quitGame();
		return;
	}
	_scummVars[47] = 3; _scummVars[48] = 2; _scummVars[49] = 5;
	_scummVars[110] = 1; _scummVars[111] = 3;
	auto tick = [&]() {
		for (uint n = 0; n < NUM_SCRIPT_SLOT; ++n) {
			if (vm.slot[n].status == ssPaused) { vm.slot[n].delay = 0; vm.slot[n].status = ssRunning; }
		}
		VAR(VAR_HAVE_MSG) = 0;
		_talkDelay = 0;
		runAllScripts();
		scummverseUpdateRoaming(4);
		walkActors();
		_sound->processSound();
	};
	for (int n = 0; n < 100 && !_scummverseRoamingReady; ++n) tick();
	if (!_scummverseRoamingReady || _currentRoom != 44 || !_userPut || isScriptRunning(131) || isScriptRunning(120))
		error("Sandbox boot/intro replacement failed: room=%d ready=%d control=%d", _currentRoom, _scummverseRoamingReady, _userPut);
	// Original entry scripts cannot teleport Edna/Green/Fred/Sandy home.
	for (int id : {9, 10, 14, 23}) derefActor(id, "probe")->putActor(20, 60, 3);
	startScene(7, nullptr, 0); startScene(12, nullptr, 0); startScene(30, nullptr, 0);
	for (int id : {9, 10, 14, 23})
		if (derefActor(id, "probe")->_room != 3) error("Room entry reset roaming actor %d", id);
	// Every audited cinematic is rejected without allocating a slot or moving
	// the camera, even when invoked directly by a timer/object script.
	for (int script = 2; script < 176; ++script) {
		if (!scummverseBlocksScript(script)) continue;
		runScript(script, false, false, nullptr);
		if (isScriptRunning(script) || _currentRoom != 30 || !_userPut)
			error("Story script %d escaped sandbox guard", script);
	}
	// The radiation suit's object script is also an ending handoff, even
	// though it does not contain a cutscene opcode.
	int team[] = {_scummVars[47], _scummVars[48], _scummVars[49]};
	runObjectScript(269, 11, false, false, nullptr);
	if (VAR(VAR_EGO) != 3 || !_userPut || _scummVars[47] != team[0] || _scummVars[48] != team[1] || _scummVars[49] != team[2])
		error("Suit ending handoff removed player/team");
	startScene(7, nullptr, 0);
	Actor *player = derefActor(3, "probe");
	player->putActor(30, 56, 7);
	Actor *edna = derefActor(10, "probe");
	edna->putActor(60, 56, 7);
	const Common::Point before = edna->getPos(), playerBefore = player->getPos();
	const Common::Point cameraBefore = camera._cur;
	bool moved = false, exited = false;
	for (int n = 0; n < 2500; ++n) {
		tick();
		moved |= edna->getPos() != before;
		exited |= edna->_room != 7;
		if (_currentRoom != 7 || player->getPos() != playerBefore || camera._cur != cameraBefore || VAR(VAR_EGO) != 3 || !_userPut)
			error("Roaming changed player/camera/control");
	}
	if (!moved || !exited) error("Edna did not walk out of kitchen");
	// A fresh encounter speaks once; staying nearby does not flood the screen.
	edna->putActor(31, 56, 7);
	_scummverseRoamers[10] = Roamer();
	stopTalk(); VAR(VAR_HAVE_MSG) = 0;
	scummverseUpdateRoaming(4);
	if (_scummverseRoamers[10].lastLine < 0 || _scummverseRoamers[10].speech <= 0)
		error("No encounter dialogue");
	int cooldown = _scummverseRoamers[10].speech;
	scummverseUpdateRoaming(4);
	if (_scummverseRoamers[10].speech != cooldown - 4) error("Dialogue cooldown reset/spam");
	// Switching to a moving kid cancels only that kid's autonomous route.
	Actor *kid = derefActor(2, "probe");
	kid->putActor(50, 56, 7); kid->startWalkActor(60, 56, -1);
	VAR(VAR_EGO) = 2;
	scummverseUpdateRoaming(4);
	if (kid->_moving || _scummverseRoamers[2].exit != -1) error("Switched kid kept roaming");
	VAR(VAR_EGO) = 3;
	const int routes[][4] = {
		{1, 53, 29, 234},
		{1, 61, 10, 67},
		{1, 257, 44, 258},
		{2, 171, 6, 172},
		{3, 71, 10, 70},
		{3, 126, 5, 135},
		{4, 159, 8, 155},
		{4, 163, 31, 166},
		{5, 135, 3, 126},
		{6, 137, 36, 125},
		{6, 138, 16, 143},
		{6, 172, 2, 171},
		{7, 81, 10, 68},
		{7, 82, 37, 95},
		{8, 154, 10, 69},
		{8, 155, 4, 159},
		{9, 217, 19, 231},
		{10, 67, 1, 61},
		{10, 68, 7, 81},
		{10, 69, 8, 154},
		{10, 70, 3, 71},
		{10, 230, 11, 179},
		{11, 179, 10, 230},
		{11, 180, 14, 197},
		{11, 181, 17, 185},
		{11, 182, 13, 193},
		{12, 456, 13, 194},
		{12, 457, 38, 229},
		{12, 458, 23, 459},
		{13, 193, 11, 182},
		{13, 194, 12, 456},
		{13, 195, 22, 208},
		{13, 196, 18, 201},
		{14, 197, 11, 180},
		{15, 223, 27, 102},
		{16, 59, 51, 177},
		{16, 143, 6, 138},
		{17, 185, 11, 181},
		{18, 201, 13, 196},
		{19, 103, 38, 461},
		{19, 231, 9, 217},
		{20, 213, 21, 235},
		{21, 235, 20, 213},
		{21, 465, 38, 460},
		{22, 208, 13, 195},
		{23, 459, 12, 458},
		{24, 113, 25, 112},
		{25, 109, 38, 463},
		{25, 112, 24, 113},
		{26, 39, 38, 462},
		{27, 99, 38, 464},
		{27, 102, 15, 223},
		{27, 232, 28, 252},
		{28, 252, 27, 232},
		{29, 234, 1, 53},
		{30, 255, 51, 267},
		{31, 166, 4, 163},
		{36, 124, 37, 98},
		{36, 125, 6, 137},
		{37, 95, 7, 82},
		{37, 98, 36, 124},
		{38, 229, 12, 457},
		{38, 460, 21, 465},
		{38, 461, 19, 103},
		{38, 462, 26, 39},
		{38, 463, 25, 109},
		{38, 464, 27, 99},
		{44, 258, 1, 257},
		{51, 177, 16, 59},
		{51, 267, 30, 255},
		{52, 108, 6, 138},
		{31, 168, 30, 169},
		{30, 169, 31, 168},
	};
	for (const auto &route : routes) {
		int x, y;
		if (!scummverseDoorPoint(route[0], route[1], x, y) || !scummverseDoorPoint(route[2], route[3], x, y))
			error("Missing passage resource %d/%d -> %d/%d", route[0], route[1], route[2], route[3]);
		startScene(route[0], nullptr, 0);
		player->putActor(20, 56, route[0]);
		if (!scummversePassage(route[1], 13) || _currentRoom != route[2] || player->_room != route[2] || !_userPut)
			error("Passage failed %d/%d -> %d", route[0], route[1], route[2]);
		_sound->processSound();
	}

	// Every cast member can use actual V1 walking, not just room teleports.
	const int cast[] = {1, 2, 4, 5, 6, 7, 9, 10, 11, 13, 14, 23};
	startScene(7, nullptr, 0); player->putActor(10, 60, 7);
	for (int id : cast) {
		Actor *a = derefActor(id, "cast walking probe");
		a->putActor(50, 56, 7);
		_scummverseRoamers[id] = Roamer();
		_scummverseRoamers[id].speech = 60000;
		bool walked = false;
		Common::Point origin = a->getPos();
		for (int n = 0; n < 2000 && a->_room == 7; ++n) {
			tick(); walked |= a->getPos() != origin;
		}
		if (!walked || a->_room == 7) error("Actor %d failed real walking/exit", id);
	}
	// Check visible traversal from each room: no NPC calls startScene().
	for (uint index = 0; index < ARRAYSIZE(routes); ++index) {
		const auto &route = routes[index];
		startScene(route[0], nullptr, 0);
		player->putActor(20, 60, route[0]);
		int x, y;
		scummverseDoorPoint(route[0], route[1], x, y);
		edna->putActor(x > 8 ? x - 8 : x + 8, y, route[0]);
		Roamer &r = _scummverseRoamers[10];
		r = Roamer(); r.room = route[0]; r.exit = index; r.speech = 60000;
		for (int n = 0; n < 2000 && edna->_room == route[0]; ++n) tick();
		if (edna->_room != route[2] || _currentRoom != route[0])
			error("Visible NPC route failed %d/%d -> %d; actor in %d", route[0], route[1], route[2], edna->_room);
	}
	// Normal serialization keeps NPC positions; transient routes reset on load.
	startScene(7, nullptr, 0); player->putActor(30, 56, 7);
	edna->putActor(30, 56, 10);
	setCameraAt(player->getPos().x, player->getPos().y);
	setCameraFollows(player);
	scummLoop(4);
	_saveLoadDescription = "Sandbox probe";
	Common::String saveFilename;
	if (!saveState(1, false, saveFilename)) error("Sandbox save failed");
	edna->putActor(40, 56, 3);
	if (!loadState(1, false) || !_scummverseRoamingReady || edna->_room != 10)
		error("Sandbox reload failed");
	for (int n = 0; n < 2000 && edna->_room == 10; ++n) tick();
	if (edna->_room == 10) error("Roaming did not resume after reload");
	warning("SCUMMVERSE_ROAMING_PROBE_PASS enabled=1");
	quitGame();
