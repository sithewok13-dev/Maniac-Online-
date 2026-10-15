	if (!_scummverseRoaming) { warning("SCUMMVERSE_SEATING_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;


 scummverseTravel(3);
 for(int id : {1,2,3,4,5,6,7,9,10,11,13,14,23,24,20,21,22,8,17,18,19}) if(id!=3) derefActor(id,"isolate roster")->putActor(0,0,0);
 Actor *zak=derefActor(24,"seated Zak");zak->putActor(20,60,53);_scummVars[794]=3;
 _scummVars[733]=7;scummverseBoard();
 int zakSeat=_scummVars[525], daveSeat=_scummVars[504];
 if(!scummverseSeated(24) || !scummverseSeated(3) || zakSeat==daveSeat) error("First party not seated");
 // Four more local passengers join without changing existing reservations.
 for(int id : {20,21,22,23}) {
  derefActor(id,"joining rider")->putActor(20,60,53);
  if(!scummverseSwitchActor(id)) error("Cannot select joiner");
  _scummVars[ProbeCatalog::travellerDestinationKey(id)]=7;scummverseBoard();
  if(_currentRoom!=56 || !scummverseSeated(id)) error("Joiner not seated");
 }
 if(_scummVars[525]!=zakSeat || _scummVars[504]!=daveSeat) error("Joining reassigned seats");
 unsigned used=0;
 for(int id : {3,20,21,22,23,24}) {
  int slot=_scummVars[501+id];
  Actor *a=derefActor(id,"seat pose");
  if(slot<1 || slot>6 || (used&(1u<<slot)) || a->getRealPos().y!=52 || a->getElevation()!=-4 || a->getFacing()!=90)
   error("Invalid or duplicate seat for %d slot=%d pose=%d,%d elev=%d facing=%d",id,slot,a->getRealPos().x,a->getRealPos().y,a->getElevation(),a->getFacing());
  used|=1u<<slot;
 }
 Actor *extra=derefActor(11,"seventh passenger");extra->putActor(20,60,53);
 scummverseSwitchActor(11);_scummVars[ProbeCatalog::travellerDestinationKey(11)]=7;
 unsigned manifest=_scummVars[725];scummverseBoard();
 if(_currentRoom!=53 || _scummVars[725]!=manifest || _scummVars[ProbeCatalog::travellerDestinationKey(11)]!=7)
  error("Full plane changed rejected booking");
 scummverseSwitchActor(24);
 _scummverseNpcDestination[11]=7;_scummverseNpcBoarding[11]=0;_scummverseRoamers[11].room=53;
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummverseUpdateRoaming(0);
 if(extra->_room!=53 || _scummVars[725]!=manifest) error("NPC overbooked flight");
 // Switching, saving and load preserve occupied chairs.
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 Common::String save;_saveLoadDescription="Six seated passengers";
 if(!saveState(10,false,save) || !loadState(10,false)) error("Seat persistence failed");
 if(_scummVars[525]!=zakSeat || _scummVars[504]!=daveSeat || !scummverseSeated(24)) error("Load moved reservations");
 for(int x : {200,504,664}) {
  setCameraAtEx(x);_fullRedraw=true;stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
  Common::DumpFile shot;
  if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/seated-%d.ppm",x)))) {
   Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
   for(int y=0;y<_virtscr[0].h;++y) for(int px=0;px<_screenWidth;++px) {byte c=*_virtscr[0].getPixels(px,y);shot.write(_currentPalette+3*c,3);}
  }
 }
 zak->startWalkActor(65,55,-1);
 if(scummverseSeated(24) || _scummVars[525]!=-zakSeat || zak->getElevation()) error("Cannot leave seat");
 scummverseRestoreSeats();if(scummverseSeated(24)) error("Standing passenger reseated automatically");
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 if(!saveState(10,false,save) || !loadState(10,false) || _scummVars[525]!=-zakSeat || scummverseSeated(24))
  error("Standing reservation did not survive save/load");
 runObjectScript(753,11,false,false,nullptr);
 if(!scummverseSeated(24) || _scummVars[525]!=zakSeat) error("Use seat did not return to reservation");
 scummverseArrive();
 for(int id : {3,20,21,22,23,24}) if(derefActor(id,"landed rider")->_room!=57 || derefActor(id,"landed rider")->getElevation() || _scummVars[501+id]) error("Arrival left seating state");

 // Saves predating seat allocation acquire reservations without losing riders.
 scummverseTravel(6);_scummVars[724]=7;_scummVars[725]=1u<<24;_scummVars[727]=3;
 derefActor(3,"legacy owner")->putActor(40,55,56);
 zak->putActor(45,55,56);_scummVars[526]=0;
 scummverseRestoreSeats();
 if(!scummverseSeated(3) || !scummverseSeated(24)) error("Legacy seats not migrated");
 scummverseArrive();
 // Seven-person legacy flights remain intact; capacity never deletes a rider.
 scummverseTravel(6);_scummVars[724]=7;_scummVars[725]=0;_scummVars[727]=24;_scummVars[526]=0;
 for(int id : {3,5,20,21,22,23,24}) {
  derefActor(id,"legacy overflow")->putActor(30+id%6,55,56);_scummVars[725]|=1u<<id;
 }
 scummverseRestoreSeats();
 for(int id : {3,5,20,21,22,23,24}) if(derefActor(id,"legacy rider")->_room!=56 || _scummVars[501+id]) error("Legacy overflow lost rider");
 scummverseArrive();
 for(int id : {3,5,20,21,22,23,24}) if(derefActor(id,"legacy landing")->_room!=57) error("Legacy overflow arrival failed");
 // Every available source costume can be seated and rendered in isolation.
 const int cast[]={1,2,3,4,5,6,7,9,10,11,13,14,23,24,20,21,22,8,17,18,19};
 scummverseTravel(6);
 for(int id : cast) derefActor(id,"clear cabin")->putActor(0,0,0);
 for(int id : cast) {
  for(int n=1;n<25;++n) _scummVars[501+n]=0;
  _scummVars[724]=7;_scummVars[725]=1u<<id;_scummVars[727]=id;
  Actor *a=derefActor(id,"cast seating");a->putActor(63,52,56);
  VAR(VAR_EGO)=id;_scummverseLastEgo=id;_scummVars[501+id]=1;_scummVars[526]=1;
  scummverseRestoreSeats();setCameraFollows(a);setCameraAtEx(504);
  stopTalk();VAR(VAR_HAVE_MSG)=0;_fullRedraw=true;scummLoop(0);
  if(!a->_visible || a->_bottom<=a->_top || a->getElevation()!=-4) error("Cast seating failed %d",id);
  Common::DumpFile shot;
  if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/seated-cast-%d.ppm",id)))) {
   Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
   for(int y=0;y<_virtscr[0].h;++y) for(int px=0;px<_screenWidth;++px) {byte c=*_virtscr[0].getPixels(px,y);shot.write(_currentPalette+3*c,3);}
  }
  a->putActor(0,0,0);
 }
 warning("SCUMMVERSE_SEATING_PASS enabled=1");quitGame();
