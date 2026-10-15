	if (!_scummverseRoaming) { warning("SCUMMVERSE_TEMPLE_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;



 auto capture=[&](int logical) {
  for(int id=1;id<25;++id) derefActor(id,"temple background")->hideActor();
  stopTalk();VAR(VAR_HAVE_MSG)=0;setCameraAtEx(160);cameraMoved();updateObjectStates();_fullRedraw=true;scummLoop_handleDrawing();
  Common::DumpFile shot;
  if(!shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/temple-sandbox-%d.ppm",logical)))) error("Cannot write temple reference");
  Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
  for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
 };
 @LEGACY_CHECKS@
 @SCENE_CHECKS@
 @ROUTE_CHECKS@
 // Three distinct original exterior entrances, not one generic edge.
 for(int i=0;i<3;++i) {
  scummverseTravel(37);runObjectScript(i==0?733:i==1?735:736,13,false,false,nullptr);
  if(_currentRoom!=(i==0?88:98+i)) error("Exterior temple entrance");
  Actor *a=derefActor(VAR(VAR_EGO),"temple entrant");
  if(a->getRealPos().x<110) error("Temple entrant did not use original arrival doorway");
 }
 scummverseTravel(39);
 Actor *visitor=derefActor(8,"offscreen temple visitor");visitor->putActor(20,60,88);
 _scummVars[778]=0;
 auto &roamer=_scummverseRoamers[8];roamer.room=88;roamer.wait=0;roamer.walking=true;
 for(uint i=0;i<sizeof(ProbeCatalog::zakLinks)/sizeof(ProbeCatalog::zakLinks[0]);++i)
  if(ProbeCatalog::zakLinks[i].room==88 && ProbeCatalog::zakLinks[i].destination==99) roamer.exit=i;
 scummverseUpdateRoaming(4);
 if(_currentRoom!=89 || visitor->_room!=99 || visitor->getRealPos().x!=109 || visitor->getRealPos().y!=44)
  error("Offscreen temple arrival lost logical doorway: room=%d actorroom=%d pos=%d,%d wait=%d exit=%d",_currentRoom,visitor->_room,visitor->getRealPos().x,visitor->getRealPos().y,roamer.wait,roamer.exit);
 if(!scummverseSwitchActor(8) || _currentRoom!=99 || visitor->getRealPos().x<100) error("Temple visitor switching failed");
 if(!scummverseSwitchActor(3) || _currentRoom!=89) error("Temple actors lost distinct rooms");
 if(scummverseTravel(ScummverseContent::kRoomCount-50)) error("Unregistered room accepted");
 warning("SCUMMVERSE_TEMPLE_PASS enabled=1");quitGame();
