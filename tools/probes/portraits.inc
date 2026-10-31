	if(!_scummverseRoaming) { warning("SCUMMVERSE_PORTRAITS_PASS enabled=0");quitGame();return; }
	// Fresh boot must advance without clicking the original kid picker.
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	if(!_scummverseRoamingReady || !scummverseTravel(1) || !_scummVars[764]) error("Expanded cast failed ready=%d v763=%d v764=%d room=%d reason=%s",_scummverseRoamingReady,_scummVars[763],_scummVars[764],_currentRoom,_scummverseWorldNotice.c_str());

 // Zak remains in cave box 7 while the gallery opens in a three-box jungle.
 // Portrait rendering must never resolve that box against the displayed room.
 scummverseTravel(9);
 derefActor(24,"offscreen portrait actor")->putActor(43,45,59);
 scummverseTravel(12);
 scummverseRosterOffer();
 for(int id : {1,2,3,4,5,6,7,8,9,10,11,13,14,17,18,20,21,22,23,24}) {
  int count=0;
  for(int y=0;y<64;++y) for(int x=0;x<64;++x) {
   if(!FakeFaces::pixels[id][(y*64+x)*4+3]) continue;
   ++count;
   if(x<2 || y<2 || x>=62 || y>=62) error("Portrait touches frame: %d",id);
  }
  if(count<20) error("Portrait missing: %d",id);
 }
 warning("SCUMMVERSE_PORTRAITS_PASS enabled=1");quitGame();
