	if (!_scummverseRoaming) {
		warning("SCUMMVERSE_AI_ENCOUNTER_PASS enabled=0"); quitGame(); return;
	}
	for (uint n = 0; n < NUM_SCRIPT_SLOT; ++n) vm.slot[n].status = ssDead;
	_currentScript = 0xFF;
	VAR(VAR_EGO) = 3;
	startScene(7, nullptr, 0);
	_scummverseRoamingReady = true; _scummverseLastEgo = 3; _userPut = 1;
	Actor *player = derefActor(3, "AI test"); player->setActorCostume(3); player->putActor(30, 56, 7);
	Actor *edna = derefActor(10, "AI test"); edna->setActorCostume(10); edna->putActor(31, 56, 7);
	auto encounter = [&]() {
		stopTalk(); VAR(VAR_HAVE_MSG) = 0;
		_scummverseRoamers[10] = Roamer();
		scummverseUpdateRoaming(4);
	};
	// No model: immediately use the existing line, without allocating a request.
	FakeAI::accept = false; encounter();
	if (_scummverseAIActor || getTalkingActor() != 10) error("Missing-model fallback failed");
	FakeAI::accept = true; encounter();
	if (_scummverseAIActor != 10 || edna->_moving) error("AI encounter was not submitted");
	Common::Point position = player->getPos(), cameraPosition = camera._cur;
	FakeAI::complete = true; scummverseUpdateDialogue(4);
	if (_scummverseAIActor || getTalkingActor() != 10 || player->getPos() != position || camera._cur != cameraPosition || !_userPut)
		error("Generated response stole control or failed to display");
	// Deadline uses a classic line and cancels the worker.
	encounter(); int cancels = FakeAI::cancels;
	scummverseUpdateDialogue(360);
	if (_scummverseAIActor || getTalkingActor() != 10 || FakeAI::cancels != cancels + 1)
		error("Deadline fallback failed");
	// A result arriving after the player leaves cannot speak in another room.
	encounter(); FakeAI::complete = true;
	startScene(10, nullptr, 0); player->putActor(20, 60, 10);
	scummverseUpdateDialogue(4);
	if (_scummverseAIActor || FakeAI::complete) error("Stale-room response was not cancelled");
	// Changing player identity also invalidates the pending greeting.
	startScene(7, nullptr, 0); player->putActor(30, 56, 7); encounter();
	VAR(VAR_EGO) = 2; derefActor(2, "AI test")->putActor(30, 56, 7);
	FakeAI::complete = true; scummverseUpdateDialogue(4);
	if (_scummverseAIActor || FakeAI::complete) error("Stale-player response was not cancelled");
	// Explicit conversations pause only the selected NPC and render on the game thread.
	VAR(VAR_EGO) = 3; _scummverseLastEgo = 3; stopTalk(); VAR(VAR_HAVE_MSG) = 0;
	FakeAI::talk = 10; edna->startWalkActor(40,56,-1);
	_scummverseRoamers[10].walking = true; FakeAI::reply = true;
	position = player->getPos(); cameraPosition = camera._cur;
	scummverseUpdateRoaming(4);
	if (!(FakeAI::roster & (1u<<10)) || (FakeAI::roster & (1u<<3)) || edna->_moving ||
		_scummverseRoamers[10].walking || getTalkingActor() != 10 ||
		player->getPos() != position || camera._cur != cameraPosition || !_userPut)
		error("Talk roster/pause/speech/control isolation failed");
	FakeAI::talk = 0; stopTalk(); VAR(VAR_HAVE_MSG) = 0;
	_scummverseRoamers[10].wait = 0; _scummverseRoamers[10].exit = -1;
	scummverseUpdateRoaming(4);
	if (_scummverseRoamers[10].exit < 0) error("Closing Talk did not resume roaming");
	warning("SCUMMVERSE_AI_ENCOUNTER_PASS enabled=1");
	quitGame();
