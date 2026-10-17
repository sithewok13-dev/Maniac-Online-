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
	int visited=0, walked=0, edges=0, guests=0;
	// Pixels of the guest's palette slots on screen inside its drawn extent.
	auto guestPixels=[&](Actor *g) {
		int n=0; if (g->_top>=g->_bottom) return 0;
		for(int y=g->_top;y<g->_bottom;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); if(c>=192) ++n; }
		return n;
	};
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
		// The scene's characters: guest actors 25.., named, drawn from their frames.
		{
			const ::Scummverse::WorldCatalog::WorldGame *game=nullptr; int scene=0;
			int index=k; for (const auto &g : ::Scummverse::WorldCatalog::kWorldGames) { if (index<g.sceneCount) { game=&g; scene=index; break; } index-=g.sceneCount; }
			int present=0;
			for (int slot=0;slot<5;++slot) {
				const ::Scummverse::WorldCatalog::WorldGuest *g=game->scenes[scene].guests[slot];
				Actor *guest=derefActor(25+slot,"world guest");
				if (!g) { if (guest->_room) error("Scene %d slot %d has an unexpected guest",k,slot); continue; }
				if (guest->_room!=room || scummverseGuestSlot(guest)!=slot) error("Guest %s not placed (room %d)",g->name,guest->_room);
				if (strcmp((const char *)getObjOrActorName(25+slot),g->name)) error("Guest name %s",(const char *)getObjOrActorName(25+slot));
				if (!(scummverseGuestMask() & (1u<<(25+slot)))) error("Guest %s missing from the talk roster",g->name);
				guest->_needRedraw=true; settle(1);
				const int drawn=guestPixels(guest);
				if (drawn<30) error("Guest %s not drawn (%d pixels, extent %d..%d)",g->name,drawn,guest->_top,guest->_bottom);
				warning("WORLD guest %s pixels %d height %d",g->name,drawn,guest->_bottom-guest->_top);
				++guests; ++present;
			}
			if (present && memcmp(_currentPalette+3*192,::Scummverse::WorldBridge::guestPalette(),3*::Scummverse::WorldBridge::guestSlotCount())) error("Scene %d guest palette not applied",k);
			if (_scummVars[768]==room || derefActor(15,"resident")->_room==room) error("Scene %d borrowed the resident actor",k);
		}
		// Walk inside the scene's own boxes.
		if (getNumBoxes()>0) {
			const Common::Point from=me->getRealPos();
			AdjustBoxResult goal=me->adjustXYToBeInBox(from.x>20 ? from.x-12 : from.x+12, from.y);
			me->startWalkActor(goal.x,goal.y,-1); for(int n=0;n<200 && me->_moving;++n) settle(1);
			if (me->getRealPos()!=from) ++walked;
		}
	}
	if (!visited) error("No exported scenes were visited");
	// Guest behaviour in the first scene that has several.
	for (int k=0;k<scummverseWorldSceneCount();++k) {
		if (!::Scummverse::WorldCatalog::worldGuestInRoom(kScummverseWorldFirstRoom+k,1) || !scummverseTravelWorld(kScummverseWorldFirstRoom+k)) continue;
		const ::Scummverse::WorldCatalog::WorldGuest *g=::Scummverse::WorldCatalog::worldGuestInRoom(_currentRoom,0);
		Actor *guest=derefActor(25,"world guest"), *second=derefActor(26,"second guest");
		if (scummverseGuestSlot(guest)<0 || scummverseGuestSlot(second)<0) error("Guests not placed for behaviour");
		// One greeting when the player walks up.
		for (bool &greeted : _scummverseGuestGreeted) greeted=true;
		_scummverseGuestGreeted[0]=false; VAR(VAR_HAVE_MSG)=0; stopTalk();
		me->putActor(guest->getRealPos().x+3,guest->getRealPos().y,_currentRoom);
		scummverseUpdateGuests(4,0);
		if (!_scummverseGuestGreeted[0] || getTalkingActor()!=25) error("Guest %s did not greet",g->name);
		// Talking frames are drawn while the line is shown.
		for(int i=0;i<12;++i) { _talkDelay=100; scummLoop(4); }
		if (guestPixels(guest)<30) error("Talking guest not drawn");
		stopTalk(); VAR(VAR_HAVE_MSG)=0;
		// Chatting holds a guest still.
		second->startWalkActor(second->getRealPos().x+4,second->getRealPos().y,-1);
		scummverseUpdateGuests(4,1u<<26);
		if (second->_moving) error("Chatting guest kept walking");
		// A stroll: walking frames follow the actor.
		const Common::Point from=guest->getPos();
		AdjustBoxResult goal=guest->adjustXYToBeInBox(guest->getRealPos().x>20 ? guest->getRealPos().x-10 : guest->getRealPos().x+10,guest->getRealPos().y);
		guest->startWalkActor(goal.x,goal.y,-1);
		int walkingFrames=0;
		for(int n=0;n<200 && guest->_moving;++n) { scummLoop(4); if (guest->_moving && guestPixels(guest)>=30) ++walkingFrames; }
		if (getNumBoxes()>0 && guest->getPos()!=from && !walkingFrames) error("Guest %s not drawn while walking",g->name);
		shot("world-guest.ppm");
		// Saves keep only Maniac's 25 actors; loading places the guests again.
		Common::String file; _saveLoadDescription="Guests";
		if (!saveState(15,false,file) || !loadState(15,false)) error("Guest save/load failed");
		settle(2); guest->_needRedraw=true; settle(1);
		if (scummverseGuestSlot(guest)<0 || guestPixels(guest)<30) error("Guests lost on load");
		// Leaving sends them away.
		scummverseTravel(2); settle(2);
		for (int slot=0;slot<5;++slot) if (derefActor(25+slot,"guest")->_room) error("Guest actor %d stayed after leaving",25+slot);
		if (scummverseGuestMask()) error("Guests left in the talk roster");
		warning("WORLD guest behaviour %s walked frames %d",g->name,walkingFrames);
		break;
	}
	// A save from patch 0058 lent actor 15 to a world character: it is returned.
	{
		Actor *resident=derefActor(15,"resident");
		const int costume=resident->_costume;
		scummverseTravelWorld(kScummverseWorldFirstRoom);
		_scummVars[768]=_currentRoom; _scummVars[769]=costume; resident->putActor(10,50,_currentRoom);
		scummverseUpdateResident();
		if (_scummVars[768] || resident->_room) error("0058 world resident not returned: 768=%d room %d",_scummVars[768],resident->_room);
	}
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
	warning("WORLD visited %d walked %d edges %d guests %d",visited,walked,edges,guests);
	warning("SCUMMVERSE_WORLD_VISIT_PASS enabled=1"); quitGame();
