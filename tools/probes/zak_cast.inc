	if (!_scummverseRoaming) { warning("SCUMMVERSE_ZAK_CAST_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;

	if (!scummverseTravel(1) || !_scummVars[763]) error("Zak cast failed to initialize");
	for(int id=20;id<=22;++id) {
		Actor *a=derefActor(id,"cast probe");
		if(a->_costume!=id+15 || a->_room!=54) error("Wrong cast resource/spawn %d",id);
		_currentScript=1; if(!scummverseOwnsActor(id)) error("Original scripts can alter guest"); _currentScript=0xFF;
	}
	// Isolate authentic costumes and all four facing directions for rendering.
	for(int id=1;id<25;++id) if(id!=3 && (id<20 || id>22)) derefActor(id,"isolate")->putActor(0,0,0);
	for(int direction : {0,90,180,270}) {
		for(int id=20;id<=22;++id) {
			Actor *a=derefActor(id,"guest draw"); a->putActor(23+(id-20)*7,56,54); a->setDirection(direction); a->startAnimActor(a->_standFrame);
		}
		stopTalk(); VAR(VAR_HAVE_MSG)=0; _fullRedraw=true; scummLoop(0);
		Common::DumpFile shot; if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/zak-cast-%d.ppm",direction)))) {
			Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(header.c_str(),header.size());
			for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
		}
	}
	for(int id=20;id<=22;++id) {
		Actor *a=derefActor(id,"walk guest"); const int before=a->getRealPos().x;
		a->startWalkActor(before-3,56,-1);
		for(int n=0;n<80;++n) {walkActors(); processActors();}
		if(a->getRealPos().x==before) error("Guest cannot walk %d",id);
		scummverseCompanionCommand(64+id); if(_scummVars[770+id]!=3) error("Cannot recruit guest");
	}
	if(!scummverseTravel(3)) error("Airport failed");
	_scummVars[733]=7; scummverseBoard();
	for(int id=20;id<=22;++id) if(derefActor(id,"passenger")->_room!=56 || !(_scummVars[725]&(1u<<id))) error("Missing guest passenger");
	Common::String filename;_saveLoadDescription="Zak cast flight";
	if(!saveState(8,false,filename) || !loadState(8,false)) error("Cast save/load failed");
	scummverseArrive();
	for(int id=20;id<=22;++id) {
		Actor *a=derefActor(id,"arrival"); if(a->_room!=57 || a->_costume!=id+15 || _scummVars[770+id]!=3) error("Saved guest lost identity");
		scummverseCompanionCommand(96+id); if(_scummVars[770+id]) error("Cannot release guest");
		_scummverseRoamers[id].room=57; _scummverseNpcDestination[id]=4; _scummverseNpcBoarding[id]=0;
	}
	stopTalk(); VAR(VAR_HAVE_MSG)=0; scummverseUpdateRoaming(4);
	for(int id=20;id<=22;++id) if(derefActor(id,"independent travel")->_room!=1) error("Guest cannot travel independently");
	warning("SCUMMVERSE_ZAK_CAST_PASS enabled=1");quitGame();
