	if (!_scummverseRoaming) { warning("SCUMMVERSE_FLIGHT_JOIN_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;

 scummverseTravel(3);
 Actor *zak=derefActor(24,"late passenger"), *annie=derefActor(20,"other airport");
 zak->putActor(25,60,53); annie->putActor(20,60,60);
 _scummVars[733]=7; scummverseBoard();
 if(_currentRoom!=56 || _scummVars[724]!=7) error("Initial flight failed");
 unsigned original=_scummVars[725];
 if(!scummverseSwitchActor(24)) error("Cannot select late passenger");
 _scummVars[ProbeCatalog::travellerDestinationKey(24)]=10;
 scummverseBoard();
 if(_currentRoom!=53 || _scummVars[725]!=original || _scummVars[724]!=7 ||
    _scummVars[ProbeCatalog::travellerDestinationKey(24)]!=10) error("Wrong destination changed active flight");
 if(!scummverseSwitchActor(20)) error("Cannot select other airport");
 _scummVars[ProbeCatalog::travellerDestinationKey(20)]=7;
 scummverseBoard();
 if(_currentRoom!=60 || _scummVars[725]!=original || _scummVars[726]!=53) error("Wrong origin joined flight");
 if(!scummverseSwitchActor(24)) error("Cannot return to late passenger");
 derefActor(21,"joining companion")->putActor(22,60,53); _scummVars[791]=24;
 _scummVars[ProbeCatalog::travellerDestinationKey(24)]=7;
 scummverseBoard();
 if(_currentRoom!=56 || derefActor(3,"first passenger")->_room!=56 ||
    derefActor(21,"joining companion")->_room!=56 || _scummVars[727]!=3 ||
    _scummVars[726]!=53 || _scummVars[724]!=7) error("Matching passenger did not join existing flight");
 if(_scummVars[ProbeCatalog::travellerDestinationKey(24)]) error("Joined booking not consumed");
 unsigned joined=_scummVars[725]; scummverseBoard();
 if(_scummVars[725]!=joined) error("Repeated boarding changed manifest");
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 Common::String file;_saveLoadDescription="Joined flight";
 if(!saveState(10,false,file) || !loadState(10,false)) error("Joined flight save failed");
 for(int id : {3,21,24}) if(derefActor(id,"restored passenger")->_room!=56) error("Saved flight split party");
 scummverseArrive();
 for(int id : {3,21,24}) if(derefActor(id,"arrived passenger")->_room!=57) error("Joined flight split arrivals");
 if(annie->_room!=60 || _scummVars[724] || _scummVars[725]) error("Arrival changed rejected passenger or retained flight");
 // A player-selected booking survives after switching control to someone else.
 Actor *leslie=derefActor(22,"booked NPC");leslie->putActor(20,60,57);
 _scummVars[792]=0;_scummVars[ProbeCatalog::travellerDestinationKey(22)]=3;
 _scummverseRoamers[22].room=57;_scummverseNpcDestination[22]=10;
 _scummverseNpcBoarding[22]=500;
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummverseUpdateRoaming(0);
 if(_scummverseNpcDestination[22]!=3) error("NPC ignored selected booking");
 _scummVars[ProbeCatalog::travellerDestinationKey(24)]=3;scummverseBoard();
 if(leslie->_room!=57) error("Distant NPC boarded before reaching gate");
 _scummverseNpcBoarding[22]=0;
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummverseUpdateRoaming(0);
 if(leslie->_room!=56 || !(_scummVars[725]&(1u<<22)) ||
    _scummVars[ProbeCatalog::travellerDestinationKey(22)]) error("Matching NPC skipped active plane");
 scummverseArrive();
 if(leslie->_room!=53) error("NPC joining flight missed arrival");
 warning("SCUMMVERSE_FLIGHT_JOIN_PASS enabled=1");quitGame();
