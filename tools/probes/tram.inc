	// Mars tram between the landing site (79 = original 185) and the tram
	// station (184): boarding wait, countdown, ride, call button, NPC riders,
	// travel lock, save/load mid-ride, and the tram coming by itself to
	// whoever waits at a station.
	if (!_scummverseRoaming) { warning("SCUMMVERSE_TRAM_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	if (!scummverseTravel(1) || !_scummVars[763]) error("Sandbox not ready");
	// Park everyone so only the riders under test use the tram.
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	auto scratch=[&](int room,int original) { for(int i=0;i<33;++i) if(scummverseOriginalObject(room,732+i)==original) return 732+i; return 0; };
	Actor *me=derefActor(3,"tram player");
	auto run=[&](int ticks) { for(int n=0;n<ticks && _scummVars[797];++n) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	if (!scummverseTravel(29) || _currentRoom!=79) error("Cannot reach the landing site");
	const int tram=scratch(79,445), button=scratch(79,450);
	if (!tram || !button || scratch(184,445)!=tram) error("Tram objects missing");
	if (getState(tram)!=0 || (_scummVars[799]&1)) error("Tram not parked at the landing site: state %d",getState(tram));
	// Ride with the player: the tram waits while the player walks aboard.
	me->putActor(30,60,79); setCameraFollows(me); for(int n=0;n<8;++n) scummLoop(4);
	{ Common::DumpFile shot; if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/tram-%d.ppm",_currentRoom)))) {
		Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(header.c_str(),header.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);} } }
	me->putActor(30,60,79); runObjectScript(tram,13,false,false,nullptr);
	if (_scummVars[797]!=1 || !(_scummVars[798]&(1u<<3))) error("Boarding did not start");
	bool walked=false, hidden=false, announced=false, locked=false;
	for(int n=0;n<400 && _scummVars[797];++n) {
		const int phase=_scummVars[797];
		if (phase<=kTramBoarding && me->_moving) walked=true;
		if (phase>0 && phase<=kTramBoarding && VAR(VAR_HAVE_MSG)) announced=true;
		if (phase>kTramBoarding && _currentRoom==79) { hidden=hidden || !me->_visible; if (!locked) locked=!scummverseTravel(3) && _currentRoom==79; }
		if (phase>kTramBoarding+20 && phase<kTramBoarding+40) {
			Common::String file; _saveLoadDescription="Tram ride";
			if (!saveState(13,false,file) || !loadState(13,false) || !(_scummVars[798]&(1u<<3)) || _scummVars[797]<=kTramBoarding) error("Ride lost on load");
		}
		VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4);
	}
	if (_currentRoom!=184 || me->_room!=184 || !(_scummVars[799]&1) || _scummVars[797] || !walked || !hidden || !announced || !locked)
		error("Player ride failed: room %d station %d walked %d hidden %d announced %d locked %d",_currentRoom,_scummVars[799],walked,hidden,announced,locked);
	if (getState(tram)!=0) error("Tram not shown at the arrival station");
	for(int n=0;n<60;++n) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); }
	{ Common::DumpFile shot; if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/tram-%d.ppm",_currentRoom)))) {
		Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(header.c_str(),header.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);} } }

	// An NPC rides alone while the player stays at the station.
	Actor *annie=derefActor(20,"tram npc"); annie->stopActorMoving(); annie->putActor(15,60,184);
	scummverseTramRequest(20,true); run(400);
	if (annie->_room!=79 || !me->_visible || _currentRoom!=184 || (_scummVars[799]&1)) error("NPC ride failed: annie %d station %d",annie->_room,_scummVars[799]);
	if (getState(tram)!=10) error("Departed tram still drawn at 184");
	// Call it back with the button: it arrives empty.
	runObjectScript(button,13,false,false,nullptr); if (!(_scummVars[799]&2)) error("Call not accepted");
	run(400);
	if (!(_scummVars[799]&1) || getState(tram)!=0) error("Called tram did not arrive: station %d phase %d state %d annie %d room %d",_scummVars[799],_scummVars[797],getState(tram),annie->_room,_currentRoom);
	// Waiting at a station brings it over by itself, after a moment: to the
	// landing site, then back to the tram station by the pyramid (which has
	// no call button), and from there it rides back.
	auto waitFor=[&](int station) {
		bool sent=false, came=false;
		for(int n=0;n<300 && !came;++n) {
			VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4);
			sent=sent || _scummVars[797]>kTramBoarding;
			came=(_scummVars[799]&1)==station && !_scummVars[797];
		}
		if (!came || !sent || getState(tram)!=0) error("Tram did not come to station %d: at %d phase %d state %d",station,_scummVars[799],_scummVars[797],getState(tram));
	};
	if (!scummverseTravel(29) || _currentRoom!=79) error("Cannot return to the landing site");
	waitFor(0);
	if (!scummverseTravel(134) || _currentRoom!=184) error("Cannot reach the tram station");
	waitFor(1);
	me->putActor(30,60,184); runObjectScript(tram,13,false,false,nullptr);
	if (_scummVars[797]!=1) error("Boarding at the tram station did not start");
	run(600);
	if (_currentRoom!=79 || me->_room!=79 || (_scummVars[799]&1)) error("Ride back from the tram station failed: room %d station %d",_currentRoom,_scummVars[799]);
	warning("SCUMMVERSE_TRAM_PASS enabled=1"); quitGame();
