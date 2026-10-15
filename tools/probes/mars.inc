	if (!_scummverseRoaming) { warning("SCUMMVERSE_MARS_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;



 auto capture=[&](int logical) {
  for(int id=1;id<25;++id) derefActor(id,"Mars background")->hideActor();
  stopTalk();VAR(VAR_HAVE_MSG)=0;setCameraAtEx(VAR(VAR_CAMERA_MIN_X));cameraMoved();updateObjectStates();_fullRedraw=true;scummLoop_handleDrawing();
  Common::DumpFile shot;
  if(!shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/mars-sandbox-%d.ppm",logical)))) error("Cannot write Mars reference");
  Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
  for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
 };
 @SCENE_CHECKS@
 // Reproduce an older save with the machine-room player on the unused half.
 if(!scummverseTravel(43)) error("Machine restore setup failed");
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 Actor *oldPlayer=derefActor(VAR(VAR_EGO),"old machine occupant");
 oldPlayer->stopActorMoving();oldPlayer->putActor(20,60,93);
 VAR(VAR_CAMERA_MIN_X)=160;VAR(VAR_CAMERA_MAX_X)=480;
 Common::String oldFile;_saveLoadDescription="Old machine room pose";
 if(!saveState(15,false,oldFile)||!loadState(15,false)) error("Machine legacy-state restore failed");
 oldPlayer=derefActor(VAR(VAR_EGO),"restored machine occupant");
 if(_currentRoom!=93 || VAR(VAR_CAMERA_MIN_X)!=480 || oldPlayer->getRealPos().x<40)
  error("Machine occupant remained in unused half after load");
 warning("SCUMMVERSE_MARS_PASS enabled=1");quitGame();
