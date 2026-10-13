	if(!_scummverseRoaming) { warning("SCUMMVERSE_WALKBOX_PASS enabled=0");quitGame();return; }
	// Fresh boot must advance without clicking the original kid picker.
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	if(!_scummverseRoamingReady || !scummverseTravel(1) || !_scummVars[764]) error("Expanded cast failed ready=%d v763=%d v764=%d room=%d reason=%s",_scummverseRoamingReady,_scummVars[763],_scummVars[764],_currentRoom,_scummverseWorldNotice.c_str());

 if(!scummverseTravel(46)) error("Cannot enter Peru carving");
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 for(int id : {1,2,3,4,5,6,7,8,9,10,11,13,14,17,18,19,20,21,22,23,24}) {
  Actor *a=derefActor(id,"Peru walking cast");
  for(int box=6;box<=8;++box) if(getBoxFlags(box)!=0x80) error("Aerial box unlocked");
  // Original ground point remains available. Points in each aerial region
  // must project to ground even when this actor is not the selected player.
  auto ground=a->adjustXYToBeInBox(15,60);
  if(ground.x!=15 || ground.y!=60 || ground.box>=6) error("Ground lost");
  for(const auto &p : {Common::Point(10,10),Common::Point(25,10),Common::Point(65,10)}) {
   auto target=a->adjustXYToBeInBox(p.x,p.y);
   if(target.box>=6 || (target.x==p.x && target.y==p.y)) error("Walking actor reaches air %d",id);
  }
 }
 Actor *player=derefActor(VAR(VAR_EGO),"Peru player");
 player->putActor(15,60,96);player->startWalkActor(65,10,-1);
 for(int n=0;n<600 && player->_moving;++n) walkActors();
 auto end=player->getRealPos();
 if(end.y<46) error("Player walked into cliff air");
 // Simulate an older sandbox save with unlocked aerial boxes and a player in air.
 for(int box=6;box<=8;++box) setBoxFlags(box,0);
 player->putActor(65,10,96);
 Common::String filename;_saveLoadDescription="Legacy aerial position";
 if(!saveState(9,false,filename) || !loadState(9,false)) error("Walkbox save migration failed");
 if(getBoxFlags(8)!=0x80 || player->getRealPos().y<46) error("Old save kept aerial access");

 runObjectScript(732,13,false,false,nullptr);
 if(_currentRoom!=95) error("Peru jungle exit lost");
 scummverseTravel(8);
 if(getBoxFlags(4)!=64) error("Seattle branch restriction lost");
 runObjectScript(737,13,false,false,nullptr);if(_currentRoom!=59) error("Cave entry blocked");
 runObjectScript(732,13,false,false,nullptr);if(_currentRoom!=58 || getBoxFlags(4)!=64) error("Cave return lost restriction");
 warning("SCUMMVERSE_WALKBOX_PASS enabled=1");quitGame();
