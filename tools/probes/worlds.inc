	if (!_scummverseRoaming) { warning("SCUMMVERSE_WORLDS_PASS enabled=0"); quitGame(); return; }
	ConfMan.setPath("scummverse_zak_path", Common::Path("/nonexistent/zak"));
	// Complete the original character picker so input variables are initialized.
	_scummVars[47] = 3; _scummVars[48] = 2; _scummVars[49] = 5;
	_scummVars[110] = 1; _scummVars[111] = 3;
	for (int n=0; n<100 && !_scummverseRoamingReady; ++n) {
		for (uint i=0;i<NUM_SCRIPT_SLOT;++i) if (vm.slot[i].status == ssPaused) { vm.slot[i].delay=0; vm.slot[i].status=ssRunning; }
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for (uint n = 0; n < NUM_SCRIPT_SLOT; ++n) vm.slot[n].status = ssDead;
	_currentScript = 0xFF; VAR(VAR_EGO) = 3; _userPut = 1;
	_scummverseRoamingReady = true; _scummverseLastEgo = 3;
	startScene(7, nullptr, 0);
	Actor *dave = derefActor(3,"world test"); dave->setActorCostume(3); dave->putActor(30,56,7);
	const Common::Point original = dave->getRealPos(); const int costume = dave->_costume;
	Common::Array<byte> owners; owners.resize(650); memcpy(owners.data(),_objectOwnerTable,650);
	// Missing/wrong files fail without changing world, player or inventory.
	ConfMan.setPath("scummverse_zak_path", Common::Path("/nonexistent/zak"));
	if (scummverseTravel(1) || _currentRoom != 7 || dave->getRealPos() != original) error("Missing-world transfer was not atomic");
	// Without Zak's files there is no airport (room 53 is made from them):
	// one nobody plays, left in another world's place, goes home to the
	// mansion's front lawn; one standing in the airport (a save made where
	// Zak's files were) is played from the front lawn too.
	{
		Roamer roamers[25];
		for (int id=0; id<25; ++id) roamers[id] = _scummverseRoamers[id];
		for (int id : {1,2,4,6,7,9,10,11,13,14,23}) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.room=derefActor(id,"held")->_room; r.wait=60000; r.speech=60000; }
		Actor *bernard = derefActor(5,"no airport");
		const int bernardRoom = bernard->_room, bernardCostume = bernard->_costume; const Common::Point bernardAt = bernard->getRealPos();
		bernard->setActorCostume(5);
		const int slot = _scummVars[600], leader = _scummVars[770+5];
		_scummVars[770+5] = 0; // (Following no one: on his own there.)
		_scummVars[600] = 34; // (A place of Monkey Island's in the first slot room, 192.)
		bernard->putActor(20,60,192); _scummverseRoamers[5] = Roamer();
		for (int n=0; n<200 && bernard->_room==192; ++n) scummverseUpdateRoaming(4);
		_scummVars[600] = slot;
		if (bernard->_room != 1) error("Left in another world without Zak's files: home to room %d (%d,%d)",bernard->_room,bernard->getRealPos().x,bernard->getRealPos().y);
		bernard->putActor(30,60,53);
		// (The scripts the rooms' entries start are not this probe's.)
		bool running[NUM_SCRIPT_SLOT];
		for (uint i=0; i<NUM_SCRIPT_SLOT; ++i) running[i] = vm.slot[i].status != ssDead;
		auto quiet = [&]() { for (uint i=0; i<NUM_SCRIPT_SLOT; ++i) if (!running[i]) vm.slot[i].status = ssDead; _currentScript = 0xFF; _userPut = 1; };
		if (!scummverseSwitchActor(5) || VAR(VAR_EGO) != 5 || _currentRoom != 1 || bernard->_room != 1)
			error("Played from Zak's airport without his files: room %d, Bernard in %d",_currentRoom,bernard->_room);
		quiet();
		if (!scummverseSwitchActor(3) || VAR(VAR_EGO) != 3 || _currentRoom != 7) error("Dave not played again: room %d",_currentRoom);
		quiet();
		dave->putActor(original.x,original.y,7);
		bernard->setActorCostume(bernardCostume); bernard->putActor(bernardAt.x,bernardAt.y,bernardRoom);
		for (int id=0; id<25; ++id) _scummverseRoamers[id] = roamers[id];
		_scummVars[770+5] = leader;
	}
	ConfMan.removeKey("scummverse_zak_path", ConfMan.getActiveDomainName());
	ConfMan.removeKey("scummverse_zak_path", Common::ConfigManager::kApplicationDomain);
	if (!scummverseTravel(1) || _currentRoom != 54 || dave->_room != 54 || dave->_costume != costume || VAR(VAR_EGO) != 3)
		error("Traveller identity/costume was not preserved");
	Actor *zak = derefActor(24,"world test");
	if (zak->_room != 54 || zak->_costume != 34 || strcmp((const char *)zak->getActorName(),"Zak McKracken")) error("Zak did not retain independent identity");
	if (_numObjectsInRoom != 33 || _ENCD_offs || _EXCD_offs) error("Foreign room scripts or objects incorrect");
	for (int i=1;i<_numLocalObjects;++i) if (_objs[i].obj_nr && (_objs[i].obj_nr < 650 || _objs[i].obj_nr > 682)) error("Foreign object namespace collision");
	if (memcmp(owners.data(),_objectOwnerTable,650)) error("Mansion inventory ownership changed");
	// Real walking and renderer, not just room assignment.
	const Common::Point start = dave->getRealPos();
	dave->startWalkActor(35,56,-1);
	for (int n=0;n<300;++n) { scummLoop(4); if (!dave->_moving) break; }
	if (dave->getRealPos()==start) error("Dave cannot walk in Zak's room");
	zak->startWalkActor(26,56,-1);
	for (int n=0;n<300;++n) { scummLoop(4); if (!zak->_moving) break; }
	if (zak->getRealPos().x==30) error("Imported Zak cannot walk");
	// Native input script receives a floor click and starts a real walk.
	stopTalk(); VAR(VAR_HAVE_MSG) = 0;
	_mouse.x = 160; _mouse.y = 128; _virtualMouse.x = 160; _virtualMouse.y = 112;
	VAR(VAR_VIRT_MOUSE_X) = 20; VAR(VAR_VIRT_MOUSE_Y) = 56;
	VAR(VAR_ACTIVE_VERB) = 13;
	runInputScript(kSceneClickArea, 0, 1);
	for (int n=0;n<300;++n) { scummLoop(4); if (dave->getRealPos().x == 20 && !dave->_moving) break; }
	if (dave->getRealPos().x != 20) error("Scene click did not reach its destination: %d",dave->getRealPos().x);
	// Foreign object interactions cannot execute scripts from either game.
	runObjectScript(650, 1, false, false, nullptr);
	if (_currentRoom != 54 || VAR(VAR_EGO) != 3) error("Foreign object script escaped isolation");
	// Zak is included in Talk and pauses while participating.
	stopTalk(); VAR(VAR_HAVE_MSG) = 0; FakeAI::talk = 24; FakeAI::reply = true;
	zak->startWalkActor(30,56,-1); scummverseUpdateRoaming(4);
	if (!(FakeAI::roster & (1u<<24)) || zak->_moving || getTalkingActor() != 24)
		error("Zak Talk roster/pause/speech failed");
	FakeAI::talk = 0; stopTalk(); VAR(VAR_HAVE_MSG) = 0;
	// A second kid can visit without replacing Dave; return points are per kid.
	Actor *bernard = derefActor(5,"second traveller");
	bernard->setActorCostume(5); bernard->putActor(25,56,7); VAR(VAR_EGO)=5; _scummverseLastEgo=5;
	startScene(7,bernard,0);
	if (!scummverseTravel(1) || dave->_room != 54) error("Second traveller replaced Dave");
	FakeAI::group=(1u<<3)|(1u<<24); scummverseUpdateRoaming(4);
	if ((FakeAI::roster & FakeAI::group) != FakeAI::group || zak->_moving || dave->_moving) error("Cross-world group roster/pause failed");
	FakeAI::group=0;
	if (!scummverseTravel(2) || bernard->getRealPos() != Common::Point(25,56) || dave->_room != 54)
		error("Per-kid return point failed");
	VAR(VAR_EGO)=3; _scummverseLastEgo=3; startScene(54,dave,0); scummLoop(4);
	_saveLoadDescription = "Cross-world probe"; Common::String filename;
	if (!saveState(2,false,filename)) error("World save failed");
	if (!scummverseTravel(2) || _currentRoom != 7 || dave->_costume != costume || dave->getRealPos() != original) error("Round trip did not restore departure point");
	_scummverseZakMounted = false; _scummverseZakRoom.clear(); _scummverseZakCostume.clear();
	if (!loadState(2,false) || _currentRoom != 54 || VAR(VAR_EGO)!=3) error("Cross-world save reload failed");
	if (!scummverseTravel(2) || _currentRoom!=7 || dave->getRealPos()!=original || memcmp(owners.data(),_objectOwnerTable,650)) error("Return after save reload failed");
	warning("SCUMMVERSE_WORLDS_PASS enabled=1"); quitGame();
