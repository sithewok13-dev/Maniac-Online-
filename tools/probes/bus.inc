	if (!_scummverseRoaming) { if (_numRooms != 55) error("Disabled sandbox expanded rooms"); warning("SCUMMVERSE_BUS_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for (int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for (uint i=0;i<NUM_SCRIPT_SLOT;++i) if (vm.slot[i].status==ssPaused) { vm.slot[i].delay=0; vm.slot[i].status=ssRunning; }
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for (uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	if (_numRooms != ScummverseContent::kForeignRoom + 1 || !scummverseTravel(1)) error("Bus room capacity or apartment import failed");
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
		if (_currentRoom!=102) error("Apartment door did not reach the living room");
		runObjectScript(735,13,false,false,nullptr);
		if (_currentRoom!=55 || _numObjectsInRoom!=20 || _ENCD_offs || _EXCD_offs || !_scummVars[762]) error("Apartment door bypassed street");
		for (int i=1;i<_numLocalObjects;++i) if (_objs[i].obj_nr && (_objs[i].obj_nr<712 || _objs[i].obj_nr>731)) error("Street object namespace collision");
		player=derefActor(kid,"bus queue"); player->putActor(92,59,55); _scummverseBusClock=156;
		runObjectScript(724,13,false,false,nullptr); for(int tick=0;tick<120;++tick) scummverseServiceBus(4);
		if (_currentRoom!=53) error("Bus failed for kid %d",kid);
		runObjectScript(685,13,false,false,nullptr);
		if (_currentRoom!=55) error("Airport return bus failed");
		player->putActor(92,59,55); _scummverseBusClock=156;
		runObjectScript(723,11,false,false,nullptr); for(int tick=0;tick<120;++tick) scummverseServiceBus(4);
		if (_currentRoom!=53) error("CashCard reader required payment");
		scummverseWorldRequest(((53*32+kid)<<8)|5); scummverseUpdateRoaming(4);
		if (_currentRoom!=55) error("Airport menu bus failed");
		runObjectScript(712,13,false,false,nullptr);
		if (_currentRoom!=102) error("Street stairs did not reach the living room");
		runObjectScript(734,13,false,false,nullptr);
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
	// The parked cab has a direct click target even with its baked driver image.
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
	if (_currentRoom!=102) error("Native stairs click could not reach the living room");
	scummverseTravel(5); stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(4);
	Common::String filename; _saveLoadDescription="Free bus probe";
	if (!saveState(2,false,filename)) error("Bus save failed");
	scummverseTravel(4); _scummverseStreetMounted=false; _scummverseStreetRoom.clear();
	if (!loadState(2,false) || _currentRoom!=55 || player->_room!=55 || player->_costume!=3 || _virtscr[0].h!=128) error("Bus save reload failed");
	// Loading resets transient roaming timers; keep bystanders parked so the
	// bus is free for this check.
	// (A roamer whose room differs from its actor's starts afresh there: a
	// short wait, or the longer one it was given.)
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.room=derefActor(id,"parked bystander")->_room; r.wait=60000; r.speech=60000; }
	_scummVars[765]=_scummVars[766]=_scummVars[767]=0;
	player=derefActor(VAR(VAR_EGO),"bus queue"); player->putActor(92,59,55); _scummverseBusClock=156;
		runObjectScript(724,13,false,false,nullptr); for(int tick=0;tick<120;++tick) scummverseServiceBus(4);
	if (_currentRoom!=53 || memcmp(owners,_objectOwnerTable,sizeof(owners))) error("Reloaded bus not usable");
	// While the bus drives away, hidden riders must not be drawn anywhere: the
	// rendered frame equals a background-only redraw (no other actors present).
	if (!scummverseTravel(5)) error("Cannot return to street");
	for (int id=1;id<_numActors;++id) if (id!=VAR(VAR_EGO) && derefActor(id,"street bystander")->_room==55) derefActor(id,"street bystander")->putActor(0,0,0);
	player=derefActor(VAR(VAR_EGO),"ghost check"); player->putActor(92,59,55); scummverseWaitBus();
	for (int tick=0;tick<400 && _currentRoom==55;++tick) {
		VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4);
		if (_scummVars[765]<=kBusBoarding || _currentRoom!=55) continue;
		Common::Array<byte> rendered; rendered.resize(_screenWidth*_virtscr[0].h);
		for (int y=0;y<_virtscr[0].h;++y) memcpy(&rendered[y*_screenWidth],_virtscr[0].getPixels(0,y),_screenWidth);
		_fullRedraw=true; scummLoop_handleDrawing();
		for (int y=0;y<_virtscr[0].h;++y) if (memcmp(&rendered[y*_screenWidth],_virtscr[0].getPixels(0,y),_screenWidth))
			{ Common::String who; for (int id=1;id<_numActors;++id) { Actor *a=derefActor(id,"ghost"); if (a->_room==55) who+=Common::String::format(" %d:%d@%d,%d",id,a->_visible,a->getRealPos().x,a->getRealPos().y); }
			error("Hidden bus rider drawn at phase %d row %d riders %x actors%s",_scummVars[765],y,_scummVars[766],who.c_str()); }
	}
	if (_currentRoom!=53) error("Ghost check ride did not arrive");
	// The bus waits several seconds: the caller walks to the door and steps
	// in, and a character who heads for the stop during the wait still rides.
	{
		if (!scummverseTravel(5)) error("Cannot return to street for boarding");
		for (int id=1;id<_numActors;++id) if (id!=VAR(VAR_EGO) && derefActor(id,"street bystander")->_room==55) derefActor(id,"street bystander")->putActor(0,0,0);
		player=derefActor(VAR(VAR_EGO),"walking rider"); player->putActor(70,59,55); scummverseWaitBus();
		Actor *late=derefActor(9,"late rider"); _scummVars[779]=0;
		bool walkedAboard=false, lateAboard=false, departedEarly=false, lateSent=false;
		for (int tick=0;tick<1200 && _currentRoom==55;++tick) {
			VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4);
			const int phase=_scummVars[765];
			if (phase>0 && phase<=kBusBoarding && (_scummverseBusBoarded & (1u<<VAR(VAR_EGO)))) walkedAboard=true;
			if (phase>40 && phase<kBusBoarding/2 && !lateSent) {
				lateSent=true; late->stopActorMoving(); late->putActor(50,59,55); Roamer &r=_scummverseRoamers[9]; r=Roamer(); r.room=55; r.exit=78; r.wait=0;
			}
			if (phase>0 && phase<=kBusBoarding && (_scummverseBusBoarded & (1u<<9))) lateAboard=true;
			if (phase>kBusBoarding && phase<kBusBoarding+8 && player->_room==55 && !(_scummVars[766] & (1u<<VAR(VAR_EGO)))) departedEarly=true;
		}
		if (_currentRoom!=53 || !walkedAboard || !lateAboard || departedEarly || late->_room!=53)
			error("Bus boarding wait failed: room %d walked %d late %d early %d lateRoom %d",_currentRoom,walkedAboard,lateAboard,departedEarly,late->_room);
	}
	// NPCs ride on their own: an NPC at the stop calls the bus, rides hidden
	// and arrives at the airport while the player watches from there.
	{
		Actor *rider=derefActor(10,"independent rider"); rider->stopActorMoving(); rider->putActor(92,59,55); _scummVars[780]=0;
		Roamer &r=_scummverseRoamers[10]; r=Roamer(); r.room=55; r.exit=78; r.elapsed=100000;
		bool rode=false;
		for (int tick=0;tick<400 && rider->_room!=53;++tick) {
			VAR(VAR_HAVE_MSG)=0; stopTalk(); scummverseUpdateRoaming(4);
			if (_scummVars[766] & (1u<<10)) rode=true;
		}
		if (!rode || rider->_room!=53 || _currentRoom!=53) error("NPC did not ride the bus: rode %d room %d phase %d",rode,rider->_room,_scummVars[765]);
	}
	warning("SCUMMVERSE_BUS_PASS enabled=1"); quitGame();
