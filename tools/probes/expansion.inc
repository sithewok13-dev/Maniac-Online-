	if(!_scummverseRoaming) { warning("SCUMMVERSE_EXPANSION_PASS enabled=0");quitGame();return; }
	// Fresh boot must advance without clicking the original kid picker.
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	if(!_scummverseRoamingReady || !scummverseTravel(1) || !_scummVars[764]) error("Expanded cast failed ready=%d v763=%d v764=%d room=%d reason=%s",_scummverseRoamingReady,_scummVars[763],_scummVars[764],_currentRoom,_scummverseWorldNotice.c_str());
	for(int room=56;room<=98;++room) {
		if(!scummverseTravel(room-50)) error("Room mount failed %d: %s",room,_scummverseWorldNotice.c_str());
		stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
		Common::DumpFile shot; if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/expanded-room-%d.ppm",room)))) {
			Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(header.c_str(),header.size());
			for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
		}
	}
	const int cast[]={1,2,3,4,5,6,7,8,9,10,11,13,14,17,18,19,20,21,22,23,24};
	for(int id:cast) {
		if(!scummverseSwitchActor(id)) error("Cannot switch actor %d room=%d costume=%d user=%d bus=%d ego=%d",id,derefActor(id,"switch failure")->_room,derefActor(id,"switch failure")->_costume,_userPut,_scummVars[765],VAR(VAR_EGO));
		if(scummverseOnBus()) for(int tick=0;tick<4;++tick) scummverseServiceBus(60);
		if(!scummverseTravel(3) || VAR(VAR_EGO)!=id) error("Actor cannot travel %d",id);
		Actor *a=derefActor(id,"switch test"); int x=a->getRealPos().x;
		_currentScript=1;if(scummverseOwnsActor(id)) error("Player commands blocked");_currentScript=0xFF;
		// Invalid scene clicks must not start scripts, travel or index graphics strips.
		const auto before=a->getPos();
		for(const auto &bad : {Common::Point(-8,120),Common::Point(-1,120),Common::Point(_roomWidth,120),Common::Point(0,-1),Common::Point(0,_roomHeight)}) {
			_virtualMouse=bad;runInputScript(kSceneClickArea,0,1);
			if(a->getPos()!=before || _currentRoom!=53) error("Invalid scene click mutated player %d",id);
		}
		int targetX=x>=3 ? x-3 : x+3;
		_virtualMouse.x=targetX*8;_virtualMouse.y=120;VAR(VAR_VIRT_MOUSE_X)=targetX;VAR(VAR_VIRT_MOUSE_Y)=60;VAR(VAR_ACTIVE_VERB)=13;
		runInputScript(kSceneClickArea,0,1);for(int n=0;n<100;++n) scummLoop(4);
		if(a->getRealPos().x==x) error("Player cannot walk %d",id);
		_scummVars[730+(id<=7?id:0)]=27;scummverseBoard();
		if(_currentRoom!=56) error("Cannot board as %d",id);
		scummverseArrive();if(_currentRoom!=77) error("Cannot arrive London as %d",id);
	}
	scummverseRosterOffer();
	for(int id:cast) {
		int count=0;for(int p=0;p<64*64;++p) if(FakeFaces::pixels[id][p*4+3]) ++count;
		if(count<20) error("Empty portrait %d",id);
		Common::DumpFile face; if(face.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/portrait-%d.ppm",id)))) {
			const char *header="P6\n64 64\n255\n";face.write(header,strlen(header));
			for(int p=0;p<64*64;++p) face.write(FakeFaces::pixels[id]+p*4,3);
		}
	}
	for(const auto &link:ProbeCatalog::zakLinks) {
		if(link.room<61) continue;
		if(!scummverseTravel(link.room-50)) error("Cannot prepare link");
		stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
		int slot=getObjectIndex(link.object);if(slot<1) error("Missing exit %d/%d",link.room,link.object);
		bool found=false;
		for(int y=_objs[slot].y_pos;y<_objs[slot].y_pos+_objs[slot].height && !found;++y)
			for(int x=_objs[slot].x_pos;x<_objs[slot].x_pos+_objs[slot].width;++x)
				if(findObject(x,y)==link.object) { _virtualMouse.x=x;_virtualMouse.y=y;found=true;break; }
		if(!found) error("Unselectable exit %d/%d",link.room,link.object);
		VAR(VAR_VIRT_MOUSE_X)=_virtualMouse.x/8;VAR(VAR_VIRT_MOUSE_Y)=_virtualMouse.y/2;VAR(VAR_ACTIVE_VERB)=13;
		runInputScript(kSceneClickArea,0,1);
		for(int n=0;n<1200 && _currentRoom==link.room;++n) scummLoop(4);
		if(_currentRoom!=link.destination) error("Exit failed %d/%d -> %d, actual %d",link.room,link.object,link.destination,_currentRoom);
	}
	// Every original pad hotspot opens the travel menu; Mars is immediately reachable.
	for(const auto &pad : {Common::Point(92,734),Common::Point(89,734),Common::Point(98,734),Common::Point(84,745),Common::Point(69,734),Common::Point(65,734),Common::Point(76,747)}) {
		scummverseTravel(pad.x-50);int before=FakeAI::airportOffers;
		runObjectScript(pad.y,11,false,false,nullptr);if(FakeAI::airportOffers!=before+1) error("Pad not active");
	}
	scummverseWorldRequest(((_currentRoom*32+VAR(VAR_EGO))<<8)|53);scummverseUpdateRoaming(0);
	if(_currentRoom!=84) error("Mars teleport failed");
	if(!scummverseTravel(5)) error("Street failed");
	for(int n=0;n<300;++n) scummverseServiceBus(4);
	if(_scummVars[765] || _currentRoom!=55) error("Bus departed without request");
	scummverseWaitBus();if(!_scummVars[765]) error("Bus ignored request");
	for(int n=0;n<20;++n) scummverseServiceBus(4);
	if(derefActor(VAR(VAR_EGO),"boarded rider")->_visible) error("Passenger drawn outside moving bus");
	for(int n=0;n<20;++n) scummverseServiceBus(4);
	if(_currentRoom!=53 || _scummVars[765]) error("Bus did not deliver passenger");
	// Switching to an NPC already aboard must follow its bus to the airport.
	_scummVars[765]=70;_scummVars[766]=1u<<18;_scummVars[767]=0;derefActor(18,"NPC bus rider")->putActor(103,61,55);
	if(!scummverseSwitchActor(18) || _currentRoom!=55 || _scummVars[767]!=18) error("Cannot take over bus passenger");
	scummverseServiceBus(60);scummverseServiceBus(60);
	if(_currentRoom!=53 || !scummverseSwitchActor(24)) error("Passenger takeover lost bus arrival");
	Common::String filename;_saveLoadDescription="Expanded worlds";
	if(!saveState(8,false,filename)||!loadState(8,false)) error("Expanded save failed");
	if(VAR(VAR_EGO)!=24 || !_scummVars[764]) error("Saved roster lost");
	warning("SCUMMVERSE_EXPANSION_PASS enabled=1");quitGame();
