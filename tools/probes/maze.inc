	// Zak's pyramids and the Sphinx maze, walked like a player: every step taps
	// a doorway, and each cell arrives as its own original scene (camera, walk
	// boxes, doorways) on the shared corridor resource.
	if(!_scummverseRoaming) { warning("SCUMMVERSE_MAZE_PASS enabled=0");quitGame();return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	// A new game uses the current layout: rooms 200+ are Zak scenes, never
	// other-world places of old saves.
	if(_scummVars[608]!=1) error("New game layout variable is %d",_scummVars[608]);
	if(!_scummverseRoamingReady || !scummverseTravel(1) || !_scummVars[764]) error("Zak not mounted: %s",_scummverseWorldNotice.c_str());
	Actor *player=derefActor(VAR(VAR_EGO),"maze walker");
	int cells=0;
	auto shot=[&](int room) {
		Common::DumpFile f; if(!f.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/maze-%d.ppm",room)))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); }
	};
	auto arrived=[&](int room) {
		if(_currentRoom!=room || player->_room!=room) error("Expected to be in %d, view %d player %d",room,_currentRoom,player->_room);
		if(room>=128 && _resourceMapper[room&0x7F]!=ProbeCatalog::zakSceneSlotRoom(room))
			error("Room %d maps to %d, not %d",room,_resourceMapper[room&0x7F],ProbeCatalog::zakSceneSlotRoom(room));
		if(const auto *scene=ProbeCatalog::zakSceneSetup(room)) {
			if(VAR(VAR_CAMERA_MIN_X)!=scene->cameraMin || VAR(VAR_CAMERA_MAX_X)!=scene->cameraMax)
				error("Room %d camera %d..%d, original %d..%d",room,VAR(VAR_CAMERA_MIN_X),VAR(VAR_CAMERA_MAX_X),scene->cameraMin,scene->cameraMax);
			for(int b=0;b<scene->boxCount;++b) if(getBoxFlags(b)!=scene->boxes[b]) error("Room %d box %d flags %d, original %d",room,b,getBoxFlags(b),scene->boxes[b]);
			for(int i=0;i<scene->objectCount;++i) if(getState(732+i)!=scene->objects[i].state)
				error("Room %d object %d state %d, setup %d",room,scene->objects[i].id,getState(732+i),scene->objects[i].state);
		}
		if(getBoxFlags(player->_walkbox)&(kBoxLocked|kBoxInvisible)) error("Room %d: player stands in closed box %d",room,player->_walkbox);
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
		for(int n=0;n<1200 && _currentRoom==from;++n) scummLoop(4);
		if(_currentRoom!=destination) error("Doorway %d/%d led to %d, not %d",from,object,_currentRoom,destination);
		for(int n=0;n<4;++n) scummLoop(4);
		arrived(destination);
		if(destination>=207 && destination<=220) ++cells;
	};
	// Through the Sphinx's secret entryway, every cell of the maze (the dead
	// end and the map room included), and out through the leg.
	if(!scummverseTravel(72-50)) error("Cannot reach the Sphinx");
	const int walk[][2]={{733,207},{736,208},{734,209},{732,210},{733,211},{733,212},{734,213},
		{735,214},{736,219},{738,220},{738,219},{733,214},{735,215},{732,216},{734,217},{736,218},
		{738,152},{732,218},{733,216},{733,215},{733,214},{733,213},{733,210},{733,211},{732,207},
		{732,73},{732,72}};
	for(const auto &step : walk) {
		tap(step[0],step[1]);
		if(step[1]==207 || step[1]==213 || step[1]==220) { setCameraFollows(player); scummLoop(4); shot(step[1]); }
		if(step[1]==213 && cells<8) {
			// Saved and loaded inside the maze: the same cell, mapping and setup.
			Common::String file;_saveLoadDescription="Sphinx maze";
			if(!saveState(13,false,file)||!loadState(13,false)) error("Maze save failed");
			arrived(213);
		}
	}
	if(cells<20) error("Walked only %d maze cells",cells);
	// The other leg, then the Egypt pyramid: corridor, sarcophagus chamber and
	// the stairs to the crystal chamber, and back.
	const int egypt[][2]={{735,139},{732,72},{732,135},{735,74},{738,75},{739,76},{732,75},{740,74},{732,135}};
	for(const auto &step : egypt) tap(step[0],step[1]);
	// Mars: the pyramid entrance's door, the corridor, the sarcophagus chamber
	// and the crystal room upstairs, and back out.
	if(!scummverseTravel(71-50)) error("Cannot reach the Mars pyramid");
	const int mars[][2]={{735,187},{738,186},{739,84},{742,186},{740,187},{732,71}};
	for(const auto &step : mars) {
		tap(step[0],step[1]);
		if(step[1]==187) { setCameraFollows(player); scummLoop(4); shot(187); }
	}
	// A save from patches 0057..0061 (layout unset) standing in room 207 was in
	// an other-world place; loading it leaves the maze for that place (or the
	// airport when the place is not installed) and marks the layout.
	if(!scummverseTravel(72-50)) error("Cannot return to the Sphinx");
	tap(733,207);
	_scummVars[608]=0;
	{ Common::String file;_saveLoadDescription="Legacy layout";
	  if(!saveState(14,false,file)||!loadState(14,false)) error("Legacy save failed"); }
	if(_currentRoom==207 || player->_room==207 || _scummVars[608]!=1) error("Legacy save stayed in the maze: view %d player %d layout %d",_currentRoom,player->_room,_scummVars[608]);
	warning("MAZE walked %d cells; legacy save left for room %d",cells,_currentRoom);
	warning("SCUMMVERSE_MAZE_PASS enabled=1");
	quitGame();
	return;
