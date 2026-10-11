	if (!_scummverseRoaming) { warning("SCUMMVERSE_AIRPORT_PASS enabled=0"); quitGame(); return; }
	ConfMan.setPath("scummverse_zak_path", Common::Path("@BAD_ZAK@"));
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for (int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for (uint i=0;i<NUM_SCRIPT_SLOT;++i) if (vm.slot[i].status==ssPaused) { vm.slot[i].delay=0; vm.slot[i].status=ssRunning; }
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for (uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	Actor *player=derefActor(3,"airport probe");
	Common::Point original=player->getRealPos(); int originalRoom=_currentRoom;
	byte owners[650]; memcpy(owners,_objectOwnerTable,sizeof(owners));
	if (scummverseTravel(3) || _currentRoom!=originalRoom || player->getRealPos()!=original || _scummVars[761])
		error("Invalid airport changed game state");
	ConfMan.removeKey("scummverse_zak_path",ConfMan.getActiveDomainName());
	if (!scummverseTravel(3) || _currentRoom!=53 || _virtscr[0].h!=128 || _numObjectsInRoom!=29 || _ENCD_offs || _EXCD_offs)
		error("Airport resource import failed");
	for (int i=1;i<_numLocalObjects;++i) if (_objs[i].obj_nr && (_objs[i].obj_nr<683 || _objs[i].obj_nr>711)) error("Airport object collision");
	auto freezeOthers = [&]() {
		for (int id : {1,2,3,4,5,6,7,9,10,11,13,14,23,24}) if (id!=VAR(VAR_EGO)) {
			Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.room=derefActor(id,"park NPC")->_room; r.wait=60000; r.speech=60000;
			derefActor(id,"park NPC")->stopActorMoving();
		}
	};
	scummverseMountStreet(); scummverseInitVisitors();
	freezeOthers(); stopTalk(); VAR(VAR_HAVE_MSG)=0;
	// Render the real room and exercise the existing floor-click input script.
	_mouse.x=160; _mouse.y=136; _virtualMouse.x=160; _virtualMouse.y=120;
	VAR(VAR_VIRT_MOUSE_X)=20; VAR(VAR_VIRT_MOUSE_Y)=60; VAR(VAR_ACTIVE_VERB)=13;
	runInputScript(kSceneClickArea,0,1);
	for(int n=0;n<300;++n) { scummLoop(4); if (player->getRealPos().x==20 && !player->_moving) break; }
	if (player->getRealPos().x!=20) error("Airport floor input cannot walk");
	Common::String shotPath("@SNAPSHOT@");
	if (!shotPath.empty()) {
		Common::DumpFile shot;
		if (!shot.open(Common::Path(shotPath))) error("Cannot write requested snapshot");
		Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); shot.write(header.c_str(),header.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); shot.write(_currentPalette+3*c,3); }
	}
	// Both outer property edges, with the original yard/driveway link retained.
	for(int side=0;side<2;++side) {
		int room=side ? 44 : 1;
		player->putActor(side ? 30 : 8,64,room); startScene(room,player,0); scummverseUpdateTransit(4);
		player->startWalkActor(side ? 37 : 0,64,-1);
		for(int n=0;n<300 && _currentRoom==room;++n) scummLoop(4);
		if (_currentRoom!=53 || player->_costume!=3) error("Mansion outer edge failed: %d",side);
		for(int n=0;n<20;++n) scummLoop(4);
		if (_currentRoom!=53 || FakeAI::airportOffers) error("Arrival bounced or opened a flight automatically");
	}
	// Free destinations have no ticket, cash, item, or inventory dependency.
	int offers=FakeAI::airportOffers;
	runObjectScript(688,11,false,false,nullptr);
	if (FakeAI::airportOffers!=offers+1 || _currentRoom!=53) error("Reservations terminal did not offer free travel");
	scummverseWorldRequest(((53*32+3)<<8)|1); scummverseUpdateRoaming(4);
	if (_currentRoom!=54) error("Free apartment selection failed");
	runObjectScript(655,13,false,false,nullptr);
	if (_currentRoom!=55) error("Apartment door did not reach the bus street");
	runObjectScript(724,13,false,false,nullptr);
	if (_currentRoom!=53) error("Free bus did not reach airport");
	scummverseWorldRequest(((53*32+5)<<8)|4); scummverseUpdateRoaming(4);
	if (_currentRoom!=53) error("Stale passenger selection moved another kid");
	runObjectScript(683,13,false,false,nullptr);
	scummverseWorldRequest(((53*32+3)<<8)|4); scummverseUpdateRoaming(4);
	if (_currentRoom!=1 || player->getRealPos().x<4 || memcmp(owners,_objectOwnerTable,sizeof(owners))) error("Free mansion return changed inventory or landed on an exit");
	// Visible NPCs walk to each connection; they never move the player's camera.
	const int routes[][3]={{73,1,53},{74,44,53},{75,53,1},{76,53,55},{77,54,55},{78,55,53},{79,55,54}};
	for(const auto &route : routes) for(int actorId : {1,2,4,5,6,7,9,10,11,13,14,23,24}) {
		player->putActor(20,60,route[1]); startScene(route[1],player,0); freezeOthers();
		Actor *zak=derefActor(actorId,"travelling NPC"); zak->putActor(20,60,route[1]);
		Roamer &r=_scummverseRoamers[actorId]; r=Roamer(); r.room=route[1]; r.exit=route[0]; r.speech=60000;
		Common::Point playerPos=player->getRealPos(), cameraPos=camera._cur, zakPos=zak->getRealPos(); bool walked=false;
		for(int n=0;n<2000 && zak->_room==route[1];++n) {
			stopTalk(); VAR(VAR_HAVE_MSG)=0; scummverseUpdateRoaming(4); walkActors();
			walked |= zak->getRealPos()!=zakPos;
			if (_currentRoom!=route[1] || player->getRealPos()!=playerPos || camera._cur!=cameraPos || !_userPut) error("NPC travel stole player control");
		}
		if (!walked || zak->_room!=route[2] || zak->_costume!=(actorId==24 ? 34 : actorId)) error("Visible NPC %d route failed: %d -> %d",actorId,route[1],route[2]);
	}
	// Random airport planning may choose either connected destination, even the
	// place an NPC just left. Offscreen travel must not load a scene or walkbox.
	player->putActor(30,56,7); startScene(7,player,0); freezeOthers();
	Actor *zak=derefActor(24,"random passenger"); unsigned visited=0;
	_rnd.setSeed(12345);
	for(int round=0;round<40;++round) {
		zak->putActor(20,60,53); Roamer &r=_scummverseRoamers[24]; r=Roamer(); r.room=53; r.previousRoom=1;
		Common::Point cameraPos=camera._cur, playerPos=player->getRealPos();
		scummverseUpdateRoaming(4); r.elapsed=10000; scummverseUpdateRoaming(4);
		if (_currentRoom!=7 || camera._cur!=cameraPos || player->getRealPos()!=playerPos) error("Offscreen flight stole scene");
		if (zak->_room==1) visited|=1; else if(zak->_room==55) visited|=2; else error("Random flight did not reach a connected destination");
	}
	if (visited!=3) error("Random airport routing omitted a destination");
	// A group conversation prevents departures, including the new actor.
	scummverseTravel(3); zak->putActor(15,60,53); Actor *edna=derefActor(10,"airport group"); edna->putActor(18,60,53);
	for(int id : {10,24}) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.room=53; r.elapsed=10000; }
	FakeAI::group=(1u<<10)|(1u<<24);
	for(int n=0;n<100;++n) { scummverseUpdateRoaming(4); walkActors(); }
	if (zak->_room!=53 || edna->_room!=53 || zak->_moving || edna->_moving) error("Airport group did not pause travel");
	FakeAI::group=0; stopTalk(); VAR(VAR_HAVE_MSG)=0;
	// Saves retain airport location and Zak's independent position. Resource
	// caches and transient route/edge state must be safely recreated on load.
	freezeOthers(); scummLoop(4); _saveLoadDescription="Airport probe"; Common::String filename;
	if(!saveState(2,false,filename)) error("Airport save failed");
	scummverseTravel(4); _scummverseAirportMounted=false; _scummverseAirportRoom.clear();
	_scummverseZakMounted=false; _scummverseZakRoom.clear(); _scummverseZakCostume.clear();
	if(!loadState(2,false) || _currentRoom!=53 || zak->_room!=53 || zak->_costume!=34 || _virtscr[0].h!=128) error("Airport reload failed");
	if(!scummverseTravel(4) || _currentRoom!=1 || _virtscr[0].h!=136 || memcmp(owners,_objectOwnerTable,sizeof(owners))) error("Airport save return failed");
	Common::String oldSave("@OLD_SAVE@");
	if (!oldSave.empty()) {
		{
			Common::File source; if(!source.open(Common::FSNode(Common::Path(oldSave)))) error("Cannot read previous-build save");
			Common::Array<byte> bytes; bytes.resize(source.size()); source.read(bytes.data(),bytes.size());
			Common::OutSaveFile *copy=_saveFileMan->openForSaving("maniac.s03",false); if(!copy) error("Cannot stage previous-build save");
			copy->write(bytes.data(),bytes.size()); copy->finalize(); delete copy;
		}
		if(!loadState(3,false) || _currentRoom!=54 || !_scummVars[760] || _scummVars[761]) error("Previous-build save did not load");
		Common::Point savedZak=zak->getRealPos(); int savedZakRoom=zak->_room;
		scummverseUpdateTransit(4);
		if(!_scummVars[761] || zak->getRealPos()!=savedZak || zak->_room!=savedZakRoom) error("Airport migration reset saved Zak");
		if(!scummverseTravel(3) || _currentRoom!=53) error("Previous-build save cannot use airport");
	}
	warning("SCUMMVERSE_AIRPORT_PASS enabled=1"); quitGame();
