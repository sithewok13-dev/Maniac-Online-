	// On Mars without air, whoever breathes wears a fishbowl and an oxygen
	// tank: a Maniac kid, Zak, Melissa, and (with exported characters) Murray
	// played by Bernard; the tentacle and the Caponian do not. Indoors with
	// air (the hostel bunks) nobody does.
	if(!_scummverseRoaming) { warning("SCUMMVERSE_MARS_AIR_PASS enabled=0");quitGame();return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	if(!scummverseTravel(1) || !_scummVars[764]) error("Zak not mounted: %s",_scummverseWorldNotice.c_str());
	using namespace ::Scummverse::WorldCatalog;
	const bool murray=@MURRAY@;
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	auto park=[&]() { for(int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.room=derefActor(id,"parked")->_room; r.wait=60000; r.speech=60000; } };
	if(murray) {
		if(!scummverseSwitchActor(5)) error("Cannot switch to Bernard");
		scummverseWorldRequest(worldAppearanceRequest(worldAppearanceKey(9,49))); scummverseUpdateRoaming(0); settle(2);
		if(!scummverseAppearance(5)) error("Bernard is not Murray: %s",_scummverseWorldNotice.c_str());
		if(!scummverseSwitchActor(3)) error("Cannot switch back to Dave");
	}
	struct Person { int id; bool gear; int plain, worn; };
	Person people[]={{3,true,0,0},{24,true,0,0},{21,true,0,0},{14,false,0,0},{8,false,0,0},{5,true,0,0}};
	const int count=murray ? 6 : 5;
	auto line_up=[&](int room) {
		if(!scummverseTravel(room-50)) error("Cannot reach %d",room);
		Actor *player=derefActor(3,"air player");
		const int x0=MAX(6,player->getRealPos().x-12);
		for(int i=0;i<count;++i) {
			Actor *a=derefActor(people[i].id,"air walker");
			a->putActor(x0+i*5,player->getRealPos().y,room);
			a->showActor(); a->setDirection(90); a->startAnimActor(a->_standFrame);
		}
		park(); setCameraAt((x0+count*5/2)*8,60); settle(4);
	};
	auto heights=[&](bool worn) {
		for(int i=0;i<count;++i) {
			Actor *a=derefActor(people[i].id,"air height"); a->_needRedraw=true; settle(1);
			if(a->_top>=a->_bottom) error("Actor %d not drawn in %d (room %d visible %d costume %d look %d sprite %d key %s)",people[i].id,_currentRoom,a->_room,a->_visible,a->_costume,scummverseAppearance(people[i].id),people[i].id<25?_scummverseAvatarSprite[people[i].id]:-1,_scummverseCharactersKey.c_str());
			(worn ? people[i].worn : people[i].plain)=a->_bottom-a->_top;
			if(scummverseNeedsAir(a)!=(worn && people[i].gear)) error("Actor %d needs air %d in %d",people[i].id,scummverseNeedsAir(a),_currentRoom);
		}
	};
	// Air: the hostel bunks.
	line_up(80); heights(false);
	// No air: the Face's entrance, outdoors.
	line_up(82); heights(true);
	{ Common::DumpFile f; if(f.open(Common::Path("/workspace/Maniac-Online/build/mars-air.ppm"))) {
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); } } }
	for(int i=0;i<count;++i) {
		const Person &p=people[i];
		warning("MARS_AIR actor %d drawn %d px with air, %d without",p.id,p.plain,p.worn);
		if(p.gear ? p.worn<p.plain+2 : p.worn!=p.plain) error("Actor %d: %d px with air, %d without (gear %d)",p.id,p.plain,p.worn,p.gear);
	}
	// The landing site is the original's long shot: everyone (gear and all)
	// stands at its spacesuits' size, 27 of 62, beside its painted van.
	{
		const int plain=people[0].plain;
		line_up(79); heights(true);
		if(people[0].worn*62>plain*27*1.3 || people[0].worn*62<plain*27*0.8) error("Dave %d px at the landing site, %d px normally",people[0].worn,plain);
		warning("MARS_AIR landing site: Dave %d px (normally %d)",people[0].worn,plain);
	}
	// Leaving for air takes the gear off again.
	line_up(80); heights(false);
	warning("SCUMMVERSE_MARS_AIR_PASS enabled=1");
	quitGame();
	return;
