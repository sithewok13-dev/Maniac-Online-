	if (!_scummverseRoaming) { warning("SCUMMVERSE_CHAMBER_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;



 // Seattle chamber 92 shares resource 14 with Mexico chamber 89 (logical 129/130).
 scummverseTravel(42);
 int untouched[21];for(int i=0;i<21;++i) untouched[i]=getState(732+i);
 if(!scummverseTravel(39)) error("Mexico chamber failed to load");
 // Reference assertions are supplied from Zak's independently executed entry.
 @REFERENCE_CHECKS@
 for(int box : {12,13}) if(!(getBoxFlags(box)&128)) error("Mexico nonwalking box unlocked");
 for(int id=1;id<25;++id) derefActor(id,"background audit")->hideActor();
 stopTalk();VAR(VAR_HAVE_MSG)=0;setCameraAtEx(160);cameraMoved();updateObjectStates();_fullRedraw=true;scummLoop_handleDrawing();
 Common::DumpFile shot;
 if(shot.open(Common::Path("/workspace/Maniac-Online/build/chamber-sandbox.ppm"))) {
  Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
  for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
 }
 shot.close();
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 // Emulate an older save's raw object states and unlocked walking zones.
 for(int i=0;i<21;++i) putState(732+i,untouched[i]);
 setBoxFlags(12,0);setBoxFlags(13,0);
 Common::String file;_saveLoadDescription="Legacy Mexico chamber";
 if(!saveState(11,false,file) || !loadState(11,false)) error("Chamber load repair failed");
 @REFERENCE_CHECKS@
 for(int box : {12,13}) if(!(getBoxFlags(box)&128)) error("Saved Mexico navigation not repaired");
 runObjectScript(732,13,false,false,nullptr);
 if(_currentRoom!=108) error("Chamber return exit failed");
 if(!scummverseTravel(42)) error("Shared chamber reload failed");
 for(int i=0;i<21;++i) if(getState(732+i)!=untouched[i]) error("Mexico setup leaked into another chamber");
 warning("SCUMMVERSE_CHAMBER_PASS enabled=1");quitGame();
