	// Selection is staged at the computer and committed only at the gate.
	VAR(VAR_EGO)=3; scummverseTravel(3); _scummVars[733]=0;
	runObjectScript(683,13,false,false,nullptr);
	if (_currentRoom!=53) error("Unselected gate departed");
	scummverseWorldRequest(((53*32+5)<<8)|20); scummverseUpdateRoaming(4);
	if (_scummVars[733]) error("Stale computer selected for a different kid");
	scummverseWorldRequest(((53*32+3)<<8)|20); scummverseUpdateRoaming(4);
	if (_currentRoom!=53 || _scummVars[733]!=4) error("Computer travelled before boarding");
	Actor *zak=derefActor(24,"companion test"); zak->putActor(28,60,53);
	scummverseCompanionCommand(88);
	if (_scummVars[794]!=3) error("Companion did not join");
	runObjectScript(683,13,false,false,nullptr);
	if (_currentRoom!=1 || zak->_room!=1 || _scummVars[733] || _scummVars[743]!=53 || !(_scummVars[753] & (1u<<24))) error("Boarding lost companion or arrival facts");
	for (int destination : {3,5,1,5,3,4}) {
		if (!scummverseTravel(destination) || zak->_room!=_currentRoom) error("Companion lost across worlds/bus");
	}
	// Natural mansion door transition follows the same selected leader.
	player->putActor(20,60,10); startScene(10,player,0); scummverseUpdateCompanions();
	if (zak->_room!=10) error("Companion lost at mansion door");
	VAR(VAR_EGO)=5; scummverseTravel(1); scummverseUpdateCompanions();
	if (zak->_room!=10) error("Companion switched leaders without consent");
	VAR(VAR_EGO)=3; scummverseTravel(3);
	player->putActor(18,60,53); zak->putActor(28,60,53);
	stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(4);
	_saveLoadDescription="Companion and destination"; _scummVars[733]=5;
	if (!saveState(3,false,filename)) error("Companion save failed");
	_scummVars[794]=0; _scummVars[733]=0;
	if (!loadState(3,false) || _scummVars[794]!=3 || _scummVars[733]!=5) error("Save lost companions/destination");
	scummverseUpdateCompanions();
	scummverseCompanionCommand(120);
	if (_scummVars[794]) error("Companion could not be dismissed");
	// Render both directions and screen edges; ASAN catches clipping mistakes.
	for (int x : {0,18,39}) for (int facing : {90,270}) {
		zak->putActor(x,60,53); zak->setDirection(facing); zak->startAnimActor(zak->_standFrame);
		stopTalk(); VAR(VAR_HAVE_MSG)=0; _fullRedraw=true; scummLoop(4);
	}
	zak->putActor(28,60,53); zak->setDirection(270); player->putActor(18,60,53);
	for (int id : {1,2,4,5,6,7,9,10,11,13,14,23,24}) { _scummverseRoamers[id].wait=60000; _scummverseRoamers[id].speech=60000; derefActor(id,"park")->stopActorMoving(); }
	stopTalk(); VAR(VAR_HAVE_MSG)=0; _fullRedraw=true; scummLoop(4);
	warning("SCALE Dave=%d Zak=%d",player->_bottom-player->_top,zak->_bottom-zak->_top);
	if (zak->_bottom-zak->_top<35 || zak->_bottom-zak->_top>90) error("Zak scale is implausible");
	Common::DumpFile shot;
	if (shot.open(Common::Path("@COMPARE@"))) {
		Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); shot.write(header.c_str(),header.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); shot.write(_currentPalette+3*c,3); }
	}
