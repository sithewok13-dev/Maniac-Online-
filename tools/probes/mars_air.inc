	// On Mars without air (outdoors and inside the Great Pyramid), whoever
	// breathes wears a fishbowl and an oxygen tank: a Maniac kid, Zak,
	// Melissa, and (with exported characters) Murray played by Bernard; the
	// tentacle and the Caponian do not. Indoors with air (the hostel, the
	// Face from its Great Chamber in) nobody does.
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
	// Air: the hostel's airlock; the Face's Great Chamber, its three massive
	// doors and its machine chamber; the hostel bunks.
	line_up(181); heights(false); line_up(83); heights(false); line_up(82); heights(false); line_up(93); heights(false);
	line_up(80); heights(false);
	// No air: outside the Great Pyramid.
	line_up(71); heights(true);
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
	// Inside the Great Pyramid: no air either.
	line_up(187); heights(true);
	// Leaving for air takes the gear off again.
	line_up(80); heights(false);
	// Looks outside on Mars: the Meteor Police officer's dome is his helmet
	// (no air needed); the grown plant and both Teds breathe (fishbowl and
	// tank; Ted is dead: the user's dark joke); Chaos (when exported) needs
	// none.
	{
		struct Look { int game, costume; bool gear; const char *shot; };
		const Look looks[]={{kWorldManiacLooks,15,false,"mars-police.ppm"},{kWorldManiacLooks,19,true,"mars-plant.ppm"},
			{kWorldManiacLooks,12,true,"mars-ted.ppm"},{5,235,true,"mars-dott-ted.ppm"},{2,130,false,nullptr}};
		Actor *dave=derefActor(3,"looks on Mars");
		for(const Look &l : looks) {
			if(l.game!=kWorldManiacLooks && scummverseCharacterFrames(l.game,l.costume).empty()) continue;
			const int key=worldAppearanceKey(l.game,l.costume);
			scummverseWorldRequest(worldAppearanceRequest(key)); scummverseUpdateRoaming(0); settle(4);
			if(scummverseAppearance(3)!=key) error("Dave did not become %d:%d: %s",l.game,l.costume,_scummverseWorldNotice.c_str());
			line_up(71); dave->_needRedraw=true; settle(1);
			if(scummverseNeedsAir(dave)!=l.gear) error("Look %d:%d needs air %d on Mars",l.game,l.costume,scummverseNeedsAir(dave));
			if(l.costume==15 && !scummverseDomed(dave)) error("The officer lost his dome on Mars");
			if(l.shot) { Common::DumpFile f; if(f.open(Common::Path(Common::String("/workspace/Maniac-Online/build/")+l.shot))) {
				Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
				for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); } } }
			warning("MARS_AIR look %d:%d needs air %d",l.game,l.costume,scummverseNeedsAir(dave));
		}
		// The landing site's long shot (the tram station) draws people at
		// 27/62 of their size: someone from another game too.
		const int far[][2]={{4,74},{3,2},{0,1}};
		for(const auto &c : far) {
			if(scummverseCharacterFrames(c[0],c[1]).empty()) continue;
			const int key=worldAppearanceKey(c[0],c[1]);
			scummverseWorldRequest(worldAppearanceRequest(key)); scummverseUpdateRoaming(0); settle(4);
			if(scummverseAppearance(3)!=key) error("Dave did not become %d:%d: %s",c[0],c[1],_scummverseWorldNotice.c_str());
			line_up(71); dave->_needRedraw=true; settle(1);
			const int near=dave->_bottom-dave->_top;
			if(!scummverseTravel(134) || _currentRoom!=184) error("Cannot reach the tram station");
			park(); setCameraAt(dave->getPos().x,60); dave->_needRedraw=true; settle(2);
			const int small=dave->_bottom-dave->_top;
			warning("MARS_AIR look %d:%d long shot %d px (near %d)",c[0],c[1],small,near);
			if(near<20 || ABS(small*62-near*27)>MAX(3,near*15/100)*62) error("Look %d:%d drawn %d px in the long shot, %d near",c[0],c[1],small,near);
			break;
		}
		scummverseWorldRequest(worldAppearanceRequest(0)); scummverseUpdateRoaming(0); settle(4);
		if(scummverseAppearance(3) || dave->_costume!=3) error("Not Dave again after the looks on Mars");
	}
	warning("SCUMMVERSE_MARS_AIR_PASS enabled=1");
	quitGame();
	return;
