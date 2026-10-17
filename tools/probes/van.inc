	// Melissa and Leslie's van, flown: boarded at its Mars landing site with a
	// companion, launched from the controls (countdown), flown with travel
	// locked (saved and loaded in flight), landed in San Francisco where it
	// stands drawn and boardable, flown on to another world when exported,
	// and home to Mars, where the original art shows it again.
	if(!_scummverseRoaming) { warning("SCUMMVERSE_VAN_PASS enabled=0");quitGame();return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	using namespace ::Scummverse::WorldCatalog;
	const bool otherWorld=@MONKEY@;
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	auto scratch=[&](int original) { for(int i=0;i<33;++i) if(scummverseOriginalObject(_currentRoom,732+i)==original) return 732+i; error("Room %d has no object %d",_currentRoom,original); return 0; };
	auto shot=[&](const char *name) {
		Common::DumpFile f; if(!f.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/%s.ppm",name)))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); }
	};
	auto site=[&](int game,int room) { for(int i=0;i<kWorldVanSiteCount;++i) if(kWorldVanSites[i].game==game && kWorldVanSites[i].room==room) return i; error("No van site %d:%d",game,room); return -1; };
	Actor *me=derefActor(3,"van pilot"), *friendly=derefActor(5,"van companion");
	// Fly from wherever the van is: board, take off, wait for liftoff.
	auto flyFrom=[&](bool atMars) {
		if(atMars) runObjectScript(scratch(452),13,false,false,nullptr);
		else { int x,y,w,h; if(!scummverseVanRect(x,y,w,h)) error("No van here"); if(!scummverseVanTap(x+w/2,y+h/2)) error("Van tap did not board"); }
		if(_currentRoom!=kVanCockpit) error("Not in the cockpit: %d",_currentRoom);
		settle(2);
		friendly->putActor(me->getRealPos().x-3,me->getRealPos().y,kVanCockpit); friendly->showActor();
		runObjectScript(scratch(490),13,false,false,nullptr);
		if(_scummVars[kVanPhaseVar]!=1) error("Controls did not start the countdown");
		if(scummverseTravel(2)) error("Left during the countdown");
		for(int n=0;n<400 && _currentRoom!=kVanFlightRoom;++n) settle(1);
		if(_currentRoom!=kVanFlightRoom || _scummVars[kVanSiteVar]!=-1 || me->_visible || friendly->_room!=kVanFlightRoom)
			error("No liftoff: view %d site %d visible %d companion %d",_currentRoom,_scummVars[kVanSiteVar],me->_visible,friendly->_room);
	};
	if(!scummverseTravel(1) || !_scummVars[764]) error("Zak not mounted: %s",_scummverseWorldNotice.c_str());
	if(!scummverseTravel(kVanLandingSite-50)) error("Cannot reach the landing site");
	settle(4);
	if(_scummverseVanSprite.empty() || _scummverseVanW<100) error("Van picture not taken (%d px wide)",_scummverseVanW);
	if(getState(scratch(454))&kObjectStateIntrinsic) error("Van not at its landing site at start");
	_scummVars[770+5]=3;
	flyFrom(true);
	settle(10); shot("van-flight");
	if(scummverseTravel(2)) error("Travel allowed in flight");
	{ Common::String file; _saveLoadDescription="Van in flight";
	  if(!saveState(15,false,file)||!loadState(15,false)) error("Van save failed");
	  settle(2);
	  if(_currentRoom!=kVanFlightRoom || _scummVars[kVanPhaseVar]!=kVanFlying || me->_visible) error("Flight lost on load: view %d phase %d",_currentRoom,_scummVars[kVanPhaseVar]); }
	// Land in San Francisco (the request the Arrive menu sends).
	const int sf=site(-1,55);
	scummverseWorldRequest(kWorldVanRequest+sf); scummverseUpdateRoaming(0); settle(4);
	if(_currentRoom!=55 || _scummVars[kVanSiteVar]!=sf || _scummVars[kVanPhaseVar] || !me->_visible || friendly->_room!=55) error("Landing failed: view %d site %d phase %d",_currentRoom,_scummVars[kVanSiteVar],_scummVars[kVanPhaseVar]);
	auto drawnHere=[&](const char *where) {
		int x,y,w,h; if(!scummverseVanRect(x,y,w,h)) error("No van rect in %s",where);
		setCameraAt(x+w/2,60); _fullRedraw=true; settle(2);
		VirtScreen &vs=_virtscr[0]; int match=0, opaque=0;
		for(int py=0;py<h;++py) for(int px=0;px<w;++px) {
			const byte c=_scummverseVanSprite[MIN(_scummverseVanH-1,py*_scummverseVanH/h)*_scummverseVanW+MIN(_scummverseVanW-1,px*_scummverseVanW/w)];
			const int sx=x+px-vs.xstart, sy=y+py;
			if(c==255 || sx<0 || sx>=_screenWidth || sy<0 || sy>=vs.h) continue;
			++opaque; match+=*(const byte *)vs.getBackPixels(sx,sy)==c;
		}
		if(opaque<200 || match<opaque*9/10) error("Van not drawn in %s: %d of %d pixels",where,match,opaque);
		warning("VAN drawn in %s: %d px",where,match);
	};
	drawnHere("San Francisco"); shot("van-sf");
	// The van's door leads back out here, not to Mars; Mars shows only sand.
	{ int x,y,w,h; scummverseVanRect(x,y,w,h); scummverseVanTap(x+w/2,y+h/2); }
	if(_currentRoom!=kVanCockpit) error("Tap did not board");
	runObjectScript(scratch(488),13,false,false,nullptr);
	if(_currentRoom!=55) error("Cockpit door led to %d, not where the van stands",_currentRoom);
	if(!scummverseTravel(kVanLandingSite-50)) error("Cannot return to Mars");
	settle(4);
	if(!(getState(scratch(454))&kObjectStateIntrinsic)) error("Van still drawn at Mars while parked in San Francisco");
	runObjectScript(scratch(454),13,false,false,nullptr);
	if(_currentRoom!=kVanLandingSite) error("Boarded a van that is not here");
	if(!scummverseTravel(5)) error("Cannot return to San Francisco");
	settle(2);
	if(otherWorld) {
		flyFrom(false);
		const int beach=site(0,20);
		scummverseWorldRequest(kWorldVanRequest+beach); scummverseUpdateRoaming(0); settle(4);
		int game,source; game=scummverseWorldGameOf(_currentRoom,source);
		if(game!=0 || source!=20 || _scummVars[kVanSiteVar]!=beach) error("Did not land on Monkey Island: %d:%d",game,source);
		drawnHere("Monkey Island"); shot("van-monkey");
		flyFrom(false);
	} else flyFrom(false);
	// Home to Mars: the original art shows it again.
	scummverseWorldRequest(kWorldVanRequest+0); scummverseUpdateRoaming(0); settle(4);
	if(_currentRoom!=kVanLandingSite || _scummVars[kVanSiteVar]!=0 || (getState(scratch(454))&kObjectStateIntrinsic)) error("Not home on Mars: view %d site %d",_currentRoom,_scummVars[kVanSiteVar]);
	warning("SCUMMVERSE_VAN_PASS enabled=1");
	quitGame();
	return;
