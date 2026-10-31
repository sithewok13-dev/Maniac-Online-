	// The Dig's tram, played: walking to the ledge of the Nexus station of the
	// map-spire line calls the car, which slides in; the player, a companion
	// and someone else on the ledge board during the wait, travel is locked on
	// the ride (saved and loaded halfway), and everyone steps off at the spire
	// station, where the car stays parked and opens at once.
	if(!_scummverseRoaming) { warning("SCUMMVERSE_DIG_TRAM_PASS enabled=0");quitGame();return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.room=derefActor(id,"parked")->_room; r.wait=60000; r.speech=60000; }
	using namespace ::Scummverse::WorldCatalog;
	const int dig=8;
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	auto place=[&](int &game,int &source) { game=scummverseWorldGameOf(_currentRoom,source); };
	auto ledgeOf=[&](int room,bool exit,int &x,int &y) {
		const WorldTramStop *stop=nullptr;
		for (const auto &l : kWorldTramLines) for (const auto &e : l.ends) if (e.room==room) stop=&e;
		if (!stop || !scummverseWorldUnits(dig,room,exit?stop->exitX:stop->ledgeX,exit?stop->exitY:stop->ledgeY,x,y)) error("No ledge for %d",room);
	};
	auto shot=[&](const char *name) {
		Common::DumpFile f; if(!f.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/%s.ppm",name)))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); }
	};
	Actor *me=derefActor(3,"tram player"), *friendly=derefActor(5,"tram companion"), *bystander=derefActor(6,"tram bystander"), *away=derefActor(7,"tram stayer");
	if(!scummverseTravelPlace(dig,80)) error("Cannot reach the Nexus tram station: %s",_scummverseWorldNotice.c_str());
	settle(2);
	if(!::Scummverse::WorldBridge::pictureMounted()) error("Tram car picture not mounted (export the game again)");
	if(_scummVars[609] || _scummVars[612]) error("Tram not idle at start: %d %d",_scummVars[609],_scummVars[612]);
	// The car picture is hidden until called: the background is the scene's own.
	const int width=::Scummverse::WorldBridge::width(), height=::Scummverse::WorldBridge::height();
	Common::Array<byte> empty; empty.resize(width*height); memcpy(empty.data(),::Scummverse::WorldBridge::pixels(),width*height);
	int lx,ly; ledgeOf(80,false,lx,ly);
	// A damaged save's tram on this very trip (a time no trip takes: before
	// its start, past its end): dropped first, so the ledge's call goes
	// through (not taken for that one under way).
	{
		const AdjustBoxResult on=me->adjustXYToBeInBox(lx,ly);
		me->putActor(on.x,on.y,_currentRoom); me->stopActorMoving();
		for (int phase : {-5,kDigTramDone+1,0x7FFFFFFF}) {
			_scummVars[609]=phase; _scummVars[610]=0; _scummVars[611]=1; _scummverseDigTramArmed=true;
			scummverseServiceDigTram(1);
			if(_scummVars[609]<1 || _scummVars[609]>kDigTramOpen || _scummVars[611]!=1)
				error("A damaged tram (phase %d) kept the ledge's call from going through: phase %d, trip %d",phase,_scummVars[609],_scummVars[611]);
			_scummVars[609]=_scummVars[610]=_scummVars[611]=_scummVars[612]=0;
		}
		_scummverseDigTramArmed=true; _scummverseDigTramBusySaid=false;
		scummverseServiceDigTram(1); VAR(VAR_HAVE_MSG)=0; stopTalk();
		warning("DIG TRAM a damaged save's phase on this trip dropped, the ledge's call through");
	}
	// Companion (follows Dave) and a bystander already on the ledge; Razor stays back.
	_scummVars[770+5]=3;
	const AdjustBoxResult start=me->adjustXYToBeInBox(lx-14,ly);
	me->putActor(start.x,start.y,_currentRoom); friendly->putActor(start.x-2,start.y,_currentRoom); friendly->showActor();
	const AdjustBoxResult at=me->adjustXYToBeInBox(lx,ly);
	bystander->putActor(at.x+1,at.y,_currentRoom); bystander->showActor();
	away->putActor(start.x-6,start.y,_currentRoom); away->showActor();
	settle(2);
	me->startWalkActor(at.x,at.y,-1);
	for(int n=0;n<600 && !_scummVars[609];++n) settle(1);
	if(!_scummVars[609] || _scummVars[611]!=1) error("Ledge did not call the car: phase %d trip %d at %d,%d ledge %d,%d",_scummVars[609],_scummVars[611],me->getRealPos().x,me->getRealPos().y,at.x,at.y);
	for(int n=0;n<400 && _scummVars[609]<kDigTramOpen+30;++n) settle(1);
	int carPixels=0; for(int i=0;i<width*height;++i) carPixels+=::Scummverse::WorldBridge::pixels()[i]!=empty[i];
	if(carPixels<500) error("Car not drawn at the station: %d pixels",carPixels);
	setCameraAt(at.x*8,60); settle(1); shot("dig-tram-80");
	// Travel is free while boarding, locked once aboard.
	for(int n=0;n<800 && _scummVars[609]<=kDigTramClose+10;++n) settle(1);
	if(!(_scummVars[610]&(1u<<3)) || !(_scummVars[610]&(1u<<5)) || !(_scummVars[610]&(1u<<6)) || (_scummVars[610]&(1u<<7)))
		error("Riders %x: expected Dave, Bernard (companion) and Wendy (on the ledge), not Razor",_scummVars[610]);
	if(me->_visible || friendly->_visible) error("Riders still visible aboard");
	if(scummverseTravel(2)) error("Travel allowed during the ride");
	{ Common::String file; _saveLoadDescription="Riding the tram";
	  if(!saveState(15,false,file)||!loadState(15,false)) error("Tram save failed");
	  settle(1);
	  if(_scummVars[609]<=kDigTramClose || !(_scummVars[610]&(1u<<3)) || me->_visible) error("Ride lost on load: phase %d riders %x visible %d",_scummVars[609],_scummVars[610],me->_visible); }
	for(int n=0;n<800 && _scummVars[609];++n) settle(1);
	int game,source; place(game,source);
	if(game!=dig || source!=37) error("Arrived in %d:%d, not the map-spire station",game,source);
	if(!me->_visible || me->_room!=_currentRoom || friendly->_room!=_currentRoom || bystander->_room!=_currentRoom) error("Riders did not step off");
	if(away->_room==_currentRoom) error("Razor rode along");
	// Off the car Wendy stays a while (600), not the short wait of someone
	// found somewhere new.
	if(_scummverseRoamers[6].wait<500) error("Wendy not resting after the ride: wait %d",_scummverseRoamers[6].wait);
	if(((_scummVars[612]>>0)&3)!=2) error("Car not parked at the spire end: %d",_scummVars[612]);
	settle(60); shot("dig-tram-37");
	// The parked car opens at once for the way back; walking off before it
	// leaves keeps it parked and the player stays.
	_scummVars[770+5]=0;
	int bx,by; ledgeOf(37,false,bx,by);
	const AdjustBoxResult back=me->adjustXYToBeInBox(bx,by), off=me->adjustXYToBeInBox(bx+8,by+4);
	me->putActor(off.x,off.y,_currentRoom); settle(4);
	me->startWalkActor(back.x,back.y,-1);
	for(int n=0;n<600 && !_scummVars[609];++n) settle(1);
	if(_scummVars[609]<kDigTramOpen || _scummVars[611]!=2) error("Parked car did not open at once: phase %d trip %d",_scummVars[609],_scummVars[611]);
	me->startWalkActor(off.x,off.y,-1);
	for(int n=0;n<800 && _scummVars[609];++n) settle(1);
	place(game,source);
	if(game!=dig || source!=37 || ((_scummVars[612]>>0)&3)!=2) error("Car left without the player: now %d:%d parked %d",game,source,_scummVars[612]);
	warning("SCUMMVERSE_DIG_TRAM_PASS enabled=1");
	quitGame();
	return;
