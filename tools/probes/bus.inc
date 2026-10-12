	if (!_scummverseRoaming) { if (_numRooms != 55) error("Disabled sandbox expanded rooms"); warning("SCUMMVERSE_BUS_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for (int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for (uint i=0;i<NUM_SCRIPT_SLOT;++i) if (vm.slot[i].status==ssPaused) { vm.slot[i].delay=0; vm.slot[i].status=ssRunning; }
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for (uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	if (_numRooms != 61 || !scummverseTravel(1)) error("Bus room capacity or apartment import failed");
	Actor *player=derefActor(3,"bus passenger");
	Common::Point oldPos=player->getRealPos();
	_scummverseStreetMounted=false; _scummverseStreetRoom.clear(); _scummVars[762]=0;
	ConfMan.setPath("scummverse_zak_path",Common::Path("@BAD_ZAK@"));
	if (scummverseTravel(5) || _currentRoom!=54 || player->getRealPos()!=oldPos || _scummVars[762]) error("Missing bus data changed location");
	int routeX=0,routeY=0; if (scummverseRoutePoint(77,false,routeX,routeY)) error("NPC used unavailable street");
	ConfMan.removeKey("scummverse_zak_path",ConfMan.getActiveDomainName());
	byte owners[650]; memcpy(owners,_objectOwnerTable,sizeof(owners));
	for (int kid=1;kid<=7;++kid) {
		VAR(VAR_EGO)=kid; _scummverseLastEgo=kid;
		if (!scummverseTravel(1)) error("Cannot start apartment trip");
		runObjectScript(655,13,false,false,nullptr);
		if (_currentRoom!=55 || _numObjectsInRoom!=20 || _ENCD_offs || _EXCD_offs || !_scummVars[762]) error("Apartment door bypassed street");
		for (int i=1;i<_numLocalObjects;++i) if (_objs[i].obj_nr && (_objs[i].obj_nr<712 || _objs[i].obj_nr>731)) error("Street object namespace collision");
		player=derefActor(kid,"bus queue"); player->putActor(92,59,55); _scummverseBusClock=156;
		runObjectScript(724,13,false,false,nullptr); scummverseServiceBus(4);
		if (_currentRoom!=53) error("Bus failed for kid %d",kid);
		runObjectScript(685,13,false,false,nullptr);
		if (_currentRoom!=55) error("Airport return bus failed");
		player->putActor(92,59,55); _scummverseBusClock=156;
		runObjectScript(723,11,false,false,nullptr); scummverseServiceBus(4);
		if (_currentRoom!=53) error("CashCard reader required payment");
		scummverseWorldRequest(((53*32+kid)<<8)|5); scummverseUpdateRoaming(4);
		if (_currentRoom!=55) error("Airport menu bus failed");
		runObjectScript(712,13,false,false,nullptr);
		if (_currentRoom!=54 || memcmp(owners,_objectOwnerTable,sizeof(owners))) error("Round trip changed inventory");
	}
	VAR(VAR_EGO)=3; _scummverseLastEgo=3; scummverseTravel(5); player=derefActor(3,"bus save");
	for (int id : {1,2,4,5,6,7,9,10,11,13,14,23,24}) {
		Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.room=derefActor(id,"park")->_room; r.wait=60000; r.speech=60000;
		derefActor(id,"park")->stopActorMoving();
	}
	_scummverseBusClock=80; player->putActor(90,59,55); setCameraAt(player->getPos().x,player->getPos().y);
	stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(4);
	Common::String shotPath("@SNAPSHOT@");
	if (!shotPath.empty()) {
		Common::DumpFile shot; if (!shot.open(Common::Path(shotPath))) error("Cannot write bus snapshot");
		Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); shot.write(header.c_str(),header.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); shot.write(_currentPalette+3*c,3); }
	}
	// Use native mouse/verb input to board the visible bus, not just a direct
	// adapter call. SCUMM V1 uses x/8 and y/2 virtual coordinates.
	if (findObject(800,100)!=724) error("Bus is not selectable");
	_virtualMouse.x=800; _virtualMouse.y=100;
	VAR(VAR_VIRT_MOUSE_X)=100; VAR(VAR_VIRT_MOUSE_Y)=50; VAR(VAR_ACTIVE_VERB)=13;
	runInputScript(kSceneClickArea,0,1);
	for(int n=0;n<1500 && _currentRoom==55;++n) scummLoop(4);
	if (_currentRoom!=53) error("Native bus click could not board: verb=%d obj=%d pos=%d,%d moving=%d script=%d", VAR(VAR_ACTIVE_VERB),VAR(VAR_ACTIVE_OBJECT1),player->getRealPos().x,player->getRealPos().y,player->_moving,_currentScript);
	scummverseTravel(5); stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(4);
	_virtualMouse.x=340; _virtualMouse.y=40;
	VAR(VAR_VIRT_MOUSE_X)=42; VAR(VAR_VIRT_MOUSE_Y)=20; VAR(VAR_ACTIVE_VERB)=13;
	runInputScript(kSceneClickArea,0,1);
	for(int n=0;n<1200 && _currentRoom==55;++n) scummLoop(4);
	if (_currentRoom!=54) error("Native stairs click could not reach apartment");
	scummverseTravel(5); stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(4);
	Common::String filename; _saveLoadDescription="Free bus probe";
	if (!saveState(2,false,filename)) error("Bus save failed");
	scummverseTravel(4); _scummverseStreetMounted=false; _scummverseStreetRoom.clear();
	if (!loadState(2,false) || _currentRoom!=55 || player->_room!=55 || player->_costume!=3 || _virtscr[0].h!=128) error("Bus save reload failed");
	player=derefActor(VAR(VAR_EGO),"bus queue"); player->putActor(92,59,55); _scummverseBusClock=156;
		runObjectScript(724,13,false,false,nullptr); scummverseServiceBus(4);
	if (_currentRoom!=53 || memcmp(owners,_objectOwnerTable,sizeof(owners))) error("Reloaded bus not usable");
	warning("SCUMMVERSE_BUS_PASS enabled=1"); quitGame();
