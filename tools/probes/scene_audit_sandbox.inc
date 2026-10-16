	// Capture every imported sandbox room actor-free at its camera minimum.
	if (!_scummverseRoaming) { warning("SCUMMVERSE_SCENE_SANDBOX_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	_scummverseRosterPending=false;
	Common::String report="{\"rooms\":[";
	for(int room=56;room<ScummverseContent::kRoomCount;++room) {
		if(!scummverseTravel(room-50)) error("Scene audit cannot enter %d: %s",room,_scummverseWorldNotice.c_str());
		stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
		for(int id=1;id<25;++id) derefActor(id,"scene audit")->hideActor();
		stopTalk();VAR(VAR_HAVE_MSG)=0;setCameraAtEx(VAR(VAR_CAMERA_MIN_X));cameraMoved();updateObjectStates();_fullRedraw=true;scummLoop_handleDrawing();
		report+=Common::String::format("%s{\"room\":%d,\"resource\":%d,\"camera\":[%d,%d],\"palette\":[%d,%d,%d]}",room==56?"":",",
			room,ScummverseContent::importedRoom(room)?ProbeCatalog::zakPlaces[room-56].file:0,VAR(VAR_CAMERA_MIN_X),VAR(VAR_CAMERA_MAX_X),_roomPalette[0],_roomPalette[1],_roomPalette[2]);
		Common::DumpFile shot;
		if(!shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/scene-audit/sbx-%d.ppm",room)))) error("Cannot write scene audit");
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte p=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*p,3);}
	}
	report+="]}\n";Common::DumpFile out;
	if(!out.open(Common::Path("/workspace/Maniac-Online/build/scene-audit/sandbox.json"))) error("Cannot write scene audit report");
	out.write(report.c_str(),report.size());out.close();
	warning("SCUMMVERSE_SCENE_SANDBOX_PASS enabled=1");quitGame();
