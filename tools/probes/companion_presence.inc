	if (!_scummverseRoaming) { warning("SCUMMVERSE_COMPANION_PRESENCE_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;


 scummverseTravel(3);
 for(int id=1;id<25;++id) _scummVars[770+id]=0;
 Actor *local=derefActor(24,"local companion"), *remote=derefActor(20,"remote companion");
 Actor *rider=derefActor(21,"bus companion");
 local->putActor(25,60,53); remote->putActor(25,60,60); rider->putActor(92,59,55);
 for(int id : {20,21,24}) _scummVars[770+id]=3;
 _scummVars[765]=kBusBoarding+20; _scummVars[766]=1u<<21; _scummVars[767]=21; rider->hideActor();
 _scummverseCompanionEgo=3; _scummverseCompanionRoom=53;
 scummverseUpdateCompanions();
 if(remote->_room!=60 || rider->_room!=55 || rider->_visible) error("Companion update teleported an absent or travelling actor");
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 Common::String filename;_saveLoadDescription="Companion presence";
 if(!saveState(11,false,filename) || !loadState(11,false)) error("Companion presence save failed");
 scummverseUpdateCompanions();
 if(remote->_room!=60 || rider->_room!=55 || rider->_visible) error("Reload recalled absent companion");
 _scummVars[733]=7;scummverseBoard();
 if(_currentRoom!=56 || local->_room!=56) error("Present companion missed flight");
 if(remote->_room!=60 || rider->_room!=55 || rider->_visible ||
    (_scummVars[725]&((1u<<20)|(1u<<21)))) error("Flight stole absent companion");
 scummverseArrive();
 if(local->_room!=57 || remote->_room!=60 || rider->_room!=55) error("Arrival moved absent companion");
 // A normal scene transition still carries companions from the departure room.
 _scummVars[765]=_scummVars[766]=_scummVars[767]=0;
 scummverseTravel(3);
 if(local->_room!=53 || remote->_room!=60 || rider->_room!=55) error("Ordinary transition did not respect presence");
 // A bus invitation cannot pull a follower out of another scene.
 scummverseTravel(5); local->putActor(90,59,55);
 remote->putActor(25,60,60); rider->putActor(25,60,60);
 scummverseWaitBus();
 for(int n=0;n<kBusBoarding/60+2 && _scummVars[765]<=kBusBoarding;++n) scummverseServiceBus(60);
 if(!(_scummVars[766]&(1u<<24)) || (_scummVars[766]&((1u<<20)|(1u<<21)))) error("Bus manifest ignored departure room");
 warning("SCUMMVERSE_COMPANION_PRESENCE_PASS enabled=1");quitGame();
