	// Zak's San Francisco on foot, tapped like a player: bedroom, living room,
	// 13th Avenue, the corner up to 14th Avenue, Lou's Loans and the Society
	// office, and back home; an NPC takes the corner offscreen; old saves in
	// rooms 99..109 (temple passages before patch 0073) land in the passages.
	if(!_scummverseRoaming) { warning("SCUMMVERSE_SF_PASS enabled=0");quitGame();return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.room=derefActor(id,"parked")->_room; r.wait=60000; r.speech=60000; }
	if(_scummVars[527]!=1 || _scummVars[528]!=5) error("New game scene schema %d/%d",_scummVars[527],_scummVars[528]);
	if(!scummverseTravel(1) || !_scummVars[764]) error("Zak not mounted: %s",_scummverseWorldNotice.c_str());
	Actor *player=derefActor(VAR(VAR_EGO),"San Francisco walker");
	auto shot=[&](int room) {
		Common::DumpFile f; if(!f.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/sf-%d.ppm",room)))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); }
	};
	auto tap=[&](int object,int destination) {
		stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
		const int from=_currentRoom;
		int slot=getObjectIndex(object); if(slot<1) error("Room %d has no doorway %d",from,object);
		bool found=false;
		for(int y=_objs[slot].y_pos;y<_objs[slot].y_pos+_objs[slot].height && !found;++y)
			for(int x=_objs[slot].x_pos;x<_objs[slot].x_pos+_objs[slot].width;++x)
				if(findObject(x,y)==object) { _virtualMouse.x=x;_virtualMouse.y=y;found=true;break; }
		if(!found) error("Doorway %d/%d cannot be tapped",from,object);
		VAR(VAR_VIRT_MOUSE_X)=_virtualMouse.x/8;VAR(VAR_VIRT_MOUSE_Y)=_virtualMouse.y/2;VAR(VAR_ACTIVE_VERB)=13;
		runInputScript(kSceneClickArea,0,1);
		for(int n=0;n<1500 && _currentRoom==from;++n) scummLoop(4);
		if(_currentRoom!=destination) error("Doorway %d/%d led to %d, not %d",from,object,_currentRoom,destination);
		for(int n=0;n<4;++n) scummLoop(4);
		if(player->_room!=destination) error("Player in %d, view %d",player->_room,destination);
		if(getBoxFlags(player->_walkbox)&(kBoxLocked|kBoxInvisible)) error("Room %d: player stands in closed box %d",destination,player->_walkbox);
		setCameraFollows(player); scummLoop(4);
	};
	// Home, the living room, the street, and up the corner to 14th Avenue.
	tap(655,102); shot(102);
	if(!(getBoxFlags(4)&kBoxInvisible)) error("Television box walkable");
	tap(735,55);
	tap(722,99); shot(99);
	// The Society door stands open: its stairs are drawn and walkable; the
	// diagonal sidewalk keeps its original facing hints.
	if(!(getState(742)&8) || getBoxFlags(14) || getBoxFlags(3)!=1) error("14th Avenue setup: door %d stairs box %d sidewalk %d",getState(742),getBoxFlags(14),getBoxFlags(3));
	{ const int stairs=getObjectIndex(741); bool shown=false;
	  for(int y=_objs[stairs].y_pos;y<_objs[stairs].y_pos+_objs[stairs].height && !shown;++y)
	   for(int x=_objs[stairs].x_pos;x<_objs[stairs].x_pos+_objs[stairs].width && !shown;++x) shown=findObject(x,y)==741;
	  if(!shown) error("Society stairs hidden"); }
	tap(740,100); shot(100);
	if(!(getBoxFlags(2)&kBoxInvisible)) error("Lou's counter walkable");
	tap(741,99);
	if(ABS(player->getRealPos().x-33)>3) error("Left Lou's away from his door: %d",player->getRealPos().x);
	tap(741,101); shot(101);
	{ Common::String file;_saveLoadDescription="Society office";
	  if(!saveState(13,false,file)||!loadState(13,false)) error("Society save failed");
	  if(_currentRoom!=101 || player->_room!=101) error("Society save landed in %d",_currentRoom); }
	tap(735,99);
	tap(739,55);
	tap(712,102);
	tap(734,54);
	// Another kid on the street, offscreen, takes the corner to 14th Avenue.
	Actor *walker=derefActor(5,"offscreen walker"); walker->putActor(92,59,55);
	// Passage 84 is the corner (the last row; checked by its arrival point).
	{ int x=0,y=0; if(!scummverseRoutePoint(84,true,x,y) || x!=5 || y!=58) error("Corner passage moved: %d,%d",x,y); }
	{ Roamer &r=_scummverseRoamers[5]; r=Roamer(); r.room=55; r.exit=84; r.elapsed=10000; r.speech=60000; }
	_scummVars[775]=0;
	scummverseUpdateRoaming(4);
	if(walker->_room!=99) error("Offscreen walker stayed in %d",walker->_room);
	// Retired IDs are refused; the temple passages are logical scenes now.
	for(int room=103;room<=109;++room) if(scummverseTravel(room-50)) error("Retired room %d accepted",room);
	// The Shuttle Bug's door leads back out beside the van, not to the tram end.
	if(!scummverseTravel(81-50)) error("Cannot board the Shuttle Bug");
	runObjectScript(739,13,false,false,nullptr);
	if(_currentRoom!=79 || ABS(player->getRealPos().x-104)>4) error("Left the Shuttle Bug to %d at %d",_currentRoom,player->getRealPos().x);
	// A save from before patch 0073 (scene schema 4): rooms 99..109 were
	// temple passages 157..167. The player in old 100 and a visitor in old 101
	// stand in passages 158 and 159 after loading.
	if(!scummverseTravel(100-50)) error("Cannot enter Lou's");
	walker->putActor(109,44,101);
	_scummVars[528]=4;
	{ Common::String file;_saveLoadDescription="Before the fold";
	  if(!saveState(14,false,file)||!loadState(14,false)) error("Legacy save failed"); }
	if(_scummVars[528]!=5 || _currentRoom!=158 || player->_room!=158 || walker->_room!=159 || walker->getRealPos().x!=109 || walker->getRealPos().y!=44 || _resourceMapper[158&0x7F]!=88)
		error("Legacy save: schema %d view %d player %d visitor %d at %d,%d",_scummVars[528],_currentRoom,player->_room,walker->_room,walker->getRealPos().x,walker->getRealPos().y);
	warning("SCUMMVERSE_SF_PASS enabled=1");
	quitGame();
	return;
