	if (!_scummverseRoaming) { warning("SCUMMVERSE_FLIGHTS_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	Actor *player=derefActor(3,"flight probe");
 // Expanded cast must retain independent computer selections after switching.
 scummverseTravel(3);
 derefActor(24,"Zak booking")->putActor(25,60,53);
 derefActor(20,"Annie booking")->putActor(28,60,53);
 if(!scummverseSwitchActor(24)) error("Cannot select Zak");
 scummverseWorldRequest(((_currentRoom*32+24)<<8)|42); scummverseUpdateRoaming(0);
 if(!scummverseSwitchActor(20)) error("Cannot select Annie");
 scummverseWorldRequest(((_currentRoom*32+20)<<8)|43); scummverseUpdateRoaming(0);
 Common::String bookingSave; _saveLoadDescription="Independent flight choices";
 stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(0);
 if(!saveState(6,false,bookingSave) || !loadState(6,false)) error("Booking save/load failed");
 if(!scummverseSwitchActor(24)) error("Cannot return to Zak");
 scummverseBoard();
 if(_currentRoom!=56 || _scummVars[724]!=7) error("Annie overwrote Zak's selected flight");
 scummverseArrive();
 if(!scummverseSwitchActor(20)) error("Cannot return to Annie");
 scummverseBoard();
 if(_currentRoom!=56 || _scummVars[724]!=10) error("Zak consumed Annie's selected flight");
 scummverseArrive();
 // Exercise old-save migration, including idempotence and legacy kid state.
 _scummVars[399]=0; _scummVars[700]=10; _scummVars[701]=20; _scummVars[702]=60;
 _scummVars[730]=7; _scummVars[740]=53; _scummVars[750]=1u<<24;
 _scummVars[733]=10;
 stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(0);
 if(!saveState(6,false,bookingSave) || !loadState(6,false)) error("Legacy booking load failed");
 if(_scummVars[ProbeCatalog::travellerReturnKey(20)]!=10 || _scummVars[ProbeCatalog::travellerDestinationKey(20)]!=7 ||
    _scummVars[ProbeCatalog::travellerDestinationKey(24)] || _scummVars[733]!=10) error("Legacy booking migration failed");
 _scummVars[ProbeCatalog::travellerDestinationKey(24)]=3;
 scummverseMigrateTravelRecords();
 if(_scummVars[ProbeCatalog::travellerDestinationKey(24)]!=3) error("Migration repeated");
 bool used[800]={};
 for(int id=1;id<=24;++id) {
  int keys[]={ProbeCatalog::travellerReturnKey(id),ProbeCatalog::travellerReturnKey(id)+1,ProbeCatalog::travellerReturnKey(id)+2,
    ProbeCatalog::travellerDestinationKey(id),ProbeCatalog::travellerOriginKey(id),ProbeCatalog::travellerPartyKey(id)};
  for(int key : keys) { if(key<256 || key>=800 || used[key]) error("Overlapping travel records"); used[key]=true; }
 }
 // Return points must belong to the actor, not to the last expanded traveller.
 derefActor(20,"Annie return")->putActor(20,60,10);
 derefActor(24,"Zak return")->putActor(20,60,16);
 if(!scummverseSwitchActor(20) || !scummverseTravel(3)) error("Annie departure failed");
 if(!scummverseSwitchActor(24) || !scummverseTravel(3)) error("Zak departure failed");
 if(!scummverseSwitchActor(20) || !scummverseTravel(2) || _currentRoom!=10) error("Zak overwrote Annie's mansion return");
 if(!scummverseSwitchActor(24) || !scummverseTravel(2) || _currentRoom!=16) error("Zak return failed room=%d saved=%d actorRoom=%d leader=%d",_currentRoom,_scummVars[ProbeCatalog::travellerReturnKey(24)],derefActor(24,"return failure")->_room,_scummVars[794]);
 if(!scummverseSwitchActor(3)) error("Cannot restore original player");

	for(int dest=6;dest<=10;++dest) {
		if(!scummverseTravel(dest)) error("Import failed %d: %s",dest,_scummverseWorldNotice.c_str());
		if(_ENCD_offs || _EXCD_offs) error("Foreign scripts active");
		stopTalk(); VAR(VAR_HAVE_MSG)=0; _fullRedraw=true; scummLoop(4);
		Common::DumpFile shot; if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/flight-room-%d.ppm",_currentRoom)))) {
			Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); shot.write(header.c_str(),header.size());
			for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
		}
	}

	for(const auto &transition : {Common::Point(57,734),Common::Point(58,737),Common::Point(59,732),Common::Point(58,732)}) {
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
	// Seattle uses the original big terminal (patch 0043): its exit is the door.
	runObjectScript(734,13,false,false,nullptr); if(_currentRoom!=58) error("Seattle outside failed");
	if(!(getState(737)&8)) error("Seattle cave opening is covered");
	runObjectScript(738,13,false,false,nullptr); if(_currentRoom!=58) error("Mountain scenery incorrectly enters cave");
	player->putActor(38,60,58);scummverseUpdateTransit(4);
	if(_currentRoom!=58) error("Forest edge incorrectly enters cave");
	runObjectScript(737,13,false,false,nullptr); if(_currentRoom!=59) error("Rainier failed");
	runObjectScript(732,13,false,false,nullptr); if(_currentRoom!=58) error("Cave return failed");
	runObjectScript(732,13,false,false,nullptr); if(_currentRoom!=57) error("Airport return failed");
	_scummVars[733]=10; scummverseBoard(); scummverseArrive(); if(_currentRoom!=60) error("Miami failed");
	_scummVars[733]=3; scummverseBoard(); scummverseArrive(); if(_currentRoom!=53) error("SFO failed");
	scummverseTravel(5); player->putActor(92,59,55);
	for(int n=0;n<500;++n) scummverseServiceBus(4);
	if(_currentRoom!=55 || _scummVars[765]) error("Sleeping bus left without request");
	scummverseWaitBus(); scummverseServiceBus(4);
	if(_currentRoom!=55) error("Bus skipped boarding");
	for(int n=0;n<40;++n) scummverseServiceBus(4);
	if(_currentRoom!=53 || zak->_room!=53) error("Requested bus failed");
	warning("SCUMMVERSE_FLIGHTS_PASS enabled=1"); quitGame();
