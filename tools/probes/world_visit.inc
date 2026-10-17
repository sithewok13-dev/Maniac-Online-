	// Other worlds: visit every exported scene through the real engine.
	if (!_scummverseRoaming) { warning("SCUMMVERSE_WORLD_VISIT_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	Actor *me=derefActor(3,"world visitor");
	byte maniacColors[48]; memcpy(maniacColors,_currentPalette,48);
	auto shot=[&](const Common::String &name) {
		Common::DumpFile f; if(!f.open(Common::Path("/workspace/Maniac-Online/build/"+name))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); }
	};
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	int visited=0, walked=0, edges=0;
	for (int k=0;k<scummverseWorldSceneCount();++k) {
		const int room=kScummverseWorldFirstRoom+k;
		scummverseWorldRequest(((_currentRoom*32+3)<<8)|(160+k)); scummverseUpdateRoaming(4);
		if (_currentRoom!=room) { warning("WORLD scene %d not visited: %s",k,_scummverseWorldNotice.c_str()); continue; }
		++visited;
		if (_roomResource!=ScummverseContent::kForeignRoom || me->_room!=room || !me->_visible) error("Scene %d not mounted: resource %d",k,_roomResource);
		const byte *rgb=::Scummverse::WorldBridge::palette();
		if (memcmp(_currentPalette+3*16,rgb,3*::Scummverse::WorldBridge::slotCount())) error("Scene %d palette not applied",k);
		if (memcmp(_currentPalette,maniacColors,48)) error("Scene %d changed the 16 V1 colors",k);
		settle(6); shot(Common::String::format("world-visit-%d.ppm",k));
		// Walk inside the scene's own boxes.
		if (getNumBoxes()>0) {
			const Common::Point from=me->getRealPos();
			AdjustBoxResult goal=me->adjustXYToBeInBox(from.x>20 ? from.x-12 : from.x+12, from.y);
			me->startWalkActor(goal.x,goal.y,-1); for(int n=0;n<200 && me->_moving;++n) settle(1);
			if (me->getRealPos()!=from) ++walked;
		}
	}
	if (!visited) error("No exported scenes were visited");
	// Side exits: from a scene whose boxes reach the right side, walk on.
	for (int k=0;k<scummverseWorldSceneCount()-1;++k) {
		int scene=0, count=0; scummverseWorldPlace(k,scene,count);
		if (scene+1>=count || !scummverseTravelWorld(kScummverseWorldFirstRoom+k) || ::Scummverse::WorldBridge::rightX()<0) continue;
		me->putActor(::Scummverse::WorldBridge::rightX(),::Scummverse::WorldBridge::rightY(),_currentRoom); _scummverseTransitArmed=true;
		scummverseWorldEdges();
		if (_currentRoom!=kScummverseWorldFirstRoom+k+1) error("Side exit from scene %d reached %d",k,_currentRoom);
		++edges; if (edges>=3) break;
	}
	// Save and load inside a scene keep the scene and its picture.
	scummverseTravelWorld(kScummverseWorldFirstRoom); settle(4);
	Common::Array<byte> before; before.resize(_screenWidth*_virtscr[0].h);
	for(int y=0;y<_virtscr[0].h;++y) memcpy(&before[y*_screenWidth],_virtscr[0].getPixels(0,y),_screenWidth);
	Common::String file; _saveLoadDescription="Other world";
	if (!saveState(14,false,file) || !loadState(14,false)) error("World save/load failed");
	settle(4);
	if (_currentRoom!=kScummverseWorldFirstRoom || _roomResource!=ScummverseContent::kForeignRoom) error("World lost on load: room %d",_currentRoom);
	for(int y=0;y<_virtscr[0].h;++y) if (memcmp(&before[y*_screenWidth],_virtscr[0].getPixels(0,y),_screenWidth)) error("World picture changed on load (row %d)",y);
	// A missing cache: travel refuses with a reason; a save inside it loads at the airport.
	const Common::Path cache=scummverseWorldCache();
	ConfMan.setPath("scummverse_worlds_path",Common::Path("/nonexistent-worlds"));
	_scummverseWorldRoom=0;
	if (scummverseTravelWorld(kScummverseWorldFirstRoom+1) || _scummverseWorldNotice.find("isn't installed")==Common::String::npos) error("Missing scene not refused: %s",_scummverseWorldNotice.c_str());
	if (!loadState(14,false)) error("Load without cache failed");
	if (_currentRoom!=53) error("Stranded visitor not moved to the airport: %d",_currentRoom);
	ConfMan.setPath("scummverse_worlds_path",cache);
	// Home again: the Maniac colors are intact.
	scummverseTravelWorld(kScummverseWorldFirstRoom+2); scummverseTravel(2); settle(4);
	if (_currentRoom>=53 || memcmp(_currentPalette,maniacColors,48)) error("Return home failed: room %d",_currentRoom);
	warning("WORLD visited %d walked %d edges %d",visited,walked,edges);
	warning("SCUMMVERSE_WORLD_VISIT_PASS enabled=1"); quitGame();
