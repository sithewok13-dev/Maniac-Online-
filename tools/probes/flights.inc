	if (!_scummverseRoaming) { warning("SCUMMVERSE_FLIGHTS_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	Actor *player=derefActor(3,"flight probe");
	for(int dest=6;dest<=10;++dest) {
		if(!scummverseTravel(dest)) error("Import failed %d: %s",dest,_scummverseWorldNotice.c_str());
		if(_ENCD_offs || _EXCD_offs) error("Foreign scripts active");
		stopTalk(); VAR(VAR_HAVE_MSG)=0; _fullRedraw=true; scummLoop(4);
		Common::DumpFile shot; if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/flight-room-%d.ppm",_currentRoom)))) {
			Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); shot.write(header.c_str(),header.size());
			for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
		}
	}

	for(const auto &transition : {Common::Point(57,733),Common::Point(58,738),Common::Point(59,732),Common::Point(58,732)}) {
		scummverseTravel(transition.x-50); stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(4);
		int slot=getObjectIndex(transition.y); if(slot<1) error("Missing exit hotspot");
		_virtualMouse.x=_objs[slot].x_pos+_objs[slot].width/2; _virtualMouse.y=_objs[slot].y_pos+_objs[slot].height/2;
		bool found=false;
		for(int y=_objs[slot].y_pos;y<_objs[slot].y_pos+_objs[slot].height && !found;++y)
			for(int x=_objs[slot].x_pos;x<_objs[slot].x_pos+_objs[slot].width;++x)
				if(findObject(x,y)==transition.y) { _virtualMouse.x=x; _virtualMouse.y=y; found=true; break; }
		if(!found) error("Exit is completely obscured: %d",transition.y);
		VAR(VAR_VIRT_MOUSE_X)=_virtualMouse.x/8; VAR(VAR_VIRT_MOUSE_Y)=_virtualMouse.y/2; VAR(VAR_ACTIVE_VERB)=13;
		runInputScript(kSceneClickArea,0,1);
		for(int n=0;n<1200 && _currentRoom==transition.x;++n) scummLoop(4);
		if(_currentRoom==transition.x) error("Native exit click failed: room %d obj %d actor %d,%d",transition.x,transition.y,player->getRealPos().x,player->getRealPos().y);
	}
	scummverseTravel(3);
	Actor *zak=derefActor(24,"Zak passenger"), *ed=derefActor(11,"Ed passenger");
	zak->putActor(20,60,53); scummverseCompanionCommand(88);
	ed->putActor(2,60,53); _scummverseNpcDestination[11]=7; _scummverseNpcBoarding[11]=500;
	_scummVars[733]=7; scummverseBoard();
	if(_currentRoom!=56 || zak->_room!=56 || ed->_room!=56 || _scummVars[724]!=7) error("Manifest lost passengers");
	for(int n=0;n<2000;++n) { stopTalk(); VAR(VAR_HAVE_MSG)=0; scummverseUpdateRoaming(4); }
	if(_currentRoom!=56 || ed->_room!=56) error("Flight did not wait for Arrive");
	Common::String filename; _saveLoadDescription="Flight manifest";
	if(!saveState(7,false,filename) || !loadState(7,false) || _scummVars[724]!=7 || !(_scummVars[725] & (1u<<11))) error("Flight save/load failed");
	scummverseArrive();
	if(_currentRoom!=57 || zak->_room!=57 || ed->_room!=57) error("Flight arrival split passengers");
	runObjectScript(733,13,false,false,nullptr); if(_currentRoom!=58) error("Seattle outside failed");
	runObjectScript(738,13,false,false,nullptr); if(_currentRoom!=59) error("Rainier failed");
	runObjectScript(732,13,false,false,nullptr); if(_currentRoom!=58) error("Cave return failed");
	runObjectScript(732,13,false,false,nullptr); if(_currentRoom!=57) error("Airport return failed");
	_scummVars[733]=10; scummverseBoard(); scummverseArrive(); if(_currentRoom!=60) error("Miami failed");
	_scummVars[733]=3; scummverseBoard(); scummverseArrive(); if(_currentRoom!=53) error("SFO failed");
	scummverseTravel(5); player->putActor(92,59,55); _scummverseBusClock=240; scummverseWaitBus();
	for(int n=0;n<100;++n) scummverseServiceBus(4);
	if(_currentRoom!=55) error("Bus boarded before stopping");
	for(int n=0;n<50 && _currentRoom==55;++n) { scummverseServiceBus(4); stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(0); }
	if(_currentRoom!=53 || zak->_room!=53) error("Timed bus failed");
	scummverseTravel(5); player->putActor(92,59,55); scummverseWaitBus(); player->putActor(80,59,55); scummverseServiceBus(4);
	if(_scummverseBusEgo) error("Walking away did not cancel bus");
	warning("SCUMMVERSE_FLIGHTS_PASS enabled=1"); quitGame();
