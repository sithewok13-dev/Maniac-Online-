	if (!_scummverseRoaming) { warning("SCUMMVERSE_ZAK_CAST_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;

	if (!scummverseTravel(1) || !_scummVars[763]) error("Zak cast failed to initialize");
	for(int id=20;id<=22;++id) {
		Actor *a=derefActor(id,"cast probe");
		if(a->_costume!=id+15 || a->_room!=(id==20 ? 101 : 54)) error("Wrong cast resource/spawn %d",id);
		_currentScript=1; if(!scummverseOwnsActor(id)) error("Original scripts can alter guest"); _currentScript=0xFF;
	}
	// Isolate authentic costumes and all four facing directions for rendering.
	for(int id=1;id<25;++id) if(id!=3 && (id<20 || id>22)) derefActor(id,"isolate")->putActor(0,0,0);
	for(int direction : {0,90,180,270}) {
		for(int id=20;id<=22;++id) {
			Actor *a=derefActor(id,"guest draw"); a->putActor(23+(id-20)*7,56,54); a->setDirection(direction); a->startAnimActor(a->_standFrame);
		}
		stopTalk(); VAR(VAR_HAVE_MSG)=0; _fullRedraw=true; scummLoop(0);
		Common::DumpFile shot; if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/zak-cast-%d.ppm",direction)))) {
			Common::String header=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(header.c_str(),header.size());
			for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
		}
	}
	for(int id=20;id<=22;++id) {
		Actor *a=derefActor(id,"walk guest"); const int before=a->getRealPos().x;
		a->startWalkActor(before-3,56,-1);
		for(int n=0;n<80;++n) {walkActors(); processActors();}
		if(a->getRealPos().x==before) error("Guest cannot walk %d",id);
		scummverseCompanionCommand(64+id); if(_scummVars[770+id]!=3) error("Cannot recruit guest");
	}
	if(!scummverseTravel(3)) error("Airport failed");
	_scummVars[733]=7; scummverseBoard();
	for(int id=20;id<=22;++id) if(derefActor(id,"passenger")->_room!=56 || !(_scummVars[725]&(1u<<id))) error("Missing guest passenger");
	Common::String filename;_saveLoadDescription="Zak cast flight";
	if(!saveState(8,false,filename) || !loadState(8,false)) error("Cast save/load failed");
	scummverseArrive();
	for(int id=20;id<=22;++id) {
		Actor *a=derefActor(id,"arrival"); if(a->_room!=57 || a->_costume!=id+15 || _scummVars[770+id]!=3) error("Saved guest lost identity");
		scummverseCompanionCommand(96+id); if(_scummVars[770+id]) error("Cannot release guest");
		_scummverseRoamers[id].room=57; _scummverseNpcDestination[id]=4; _scummverseNpcBoarding[id]=0;
	}
	stopTalk(); VAR(VAR_HAVE_MSG)=0; scummverseUpdateRoaming(4);
	// Released guests board one flight together, then land on its clock.
	for(int id=20;id<=22;++id) if(derefActor(id,"independent boarding")->_room!=56 || !(_scummVars[725]&(1u<<id))) error("Guest did not board independently");
	if(_scummVars[724]!=4 || _scummVars[726]!=57 || !_scummVars[796]) error("Guests did not share an NPC flight");
	_scummVars[795]=30000; scummverseUpdateTransit(4); // past any flight time
	for(int id=20;id<=22;++id) if(derefActor(id,"independent travel")->_room!=1) error("Guest cannot travel independently");
	// The King as on the Caponians' ship: costume 27 (imported 39) in his
	// white suit, the Elvis quiff over his standing and closed-mouth frames.
	{
		Actor *king=derefActor(17,"The King");
		if(king->_costume!=39 || king->_talkColor!=1 || strcmp((const char *)king->getActorName(),"The King")) error("The King's look: costume %d color %d",king->_costume,king->_talkColor);
		if(scummverseOverlayFrame(king,king->_standFrame)!=6 || scummverseOverlayFrame(king,king->_talkStopFrame)!=6 || scummverseOverlayFrame(king,king->_walkFrame)>=0) error("The King's quiff frames");
		if(scummverseOverlayFrame(derefActor(8,"Caponian"),1)>=0) error("Another Caponian wears the quiff");
		// An older save's grey King gets the look back.
		king->_talkColor=11; scummverseInitVisitors();
		if(king->_talkColor!=1) error("An older King keeps his grey suit");
	}
	// Zak's people who stay in one place, each where the original scripts put
	// them (through the borrowed resident actor), in their own costume.
	{
		static const struct { int room, costume; const char *name; } residents[]={
			{100,44,"Lou"},{60,46,"Bum"},{53,47,"Devotee"},{64,42,"Policeman"},{78,48,"Sentry"},{113,49,"Skolarian"},{57,50,"Pilot"},{67,42,"Nepal guard"},{68,43,"Guru"},{56,45,"Stewardess"}};
		_scummVars[724]=0; VAR(VAR_EGO)=3; _scummverseLastEgo=3; _userPut=1;
		for(const auto &r : residents) {
			if(!scummverseTravel(r.room-50)) error("Cannot reach %s's room %d",r.name,r.room);
			Actor *resident=derefActor(15,"Zak resident");
			if(_currentRoom!=r.room || resident->_room!=r.room || resident->_costume!=r.costume || strcmp((const char *)resident->getActorName(),r.name))
				error("%s not in room %d: actor in %d, costume %d, name %s",r.name,r.room,resident->_room,resident->_costume,(const char *)resident->getActorName());
			setCameraAt(resident->getPos().x,resident->getPos().y);
			stopTalk(); VAR(VAR_HAVE_MSG)=0; _fullRedraw=true; scummLoop(0);
			if(!resident->_visible || resident->_bottom<=resident->_top) error("%s not drawn",r.name);
		}
		// The baker: away from his window until the bakery's doorbell rings,
		// then at it (in front of its glass), speaking; a second ring keeps
		// him there; after a while he goes again.
		{
			Actor *resident=derefActor(15,"baker");
			if(!scummverseTravel(5)) error("Cannot reach Zak's street");
			if(resident->_room==55 || _scummVars[768]==55) error("The baker waits at his window unasked");
			if(strcmp((const char *)getObjOrActorName(ProbeCatalog::kZakBakeryBell),"doorbell")) error("Object %d is %s, not the doorbell",ProbeCatalog::kZakBakeryBell,(const char *)getObjOrActorName(ProbeCatalog::kZakBakeryBell));
			if(!getVerbEntrypoint(ProbeCatalog::kZakBakeryBell,9)) error("The doorbell cannot be pushed");
			runObjectScript(ProbeCatalog::kZakBakeryBell,9,false,false,nullptr);
			if(resident->_room!=55 || resident->_costume!=51 || resident->getRealPos().y!=22 || !getClass(15,kObjectClassNeverClip) || getTalkingActor()!=15)
				error("The baker did not come to his window: room %d costume %d at %d,%d talking %d",resident->_room,resident->_costume,resident->getRealPos().x,resident->getRealPos().y,getTalkingActor());
			setCameraAt(resident->getPos().x,resident->getPos().y); stopTalk(); VAR(VAR_HAVE_MSG)=0; _fullRedraw=true; scummLoop(0);
			if(!resident->_visible || resident->_bottom<=resident->_top) error("The baker is not drawn at his window");
			runObjectScript(ProbeCatalog::kZakBakeryBell,11,false,false,nullptr);
			if(resident->_room!=55 || getTalkingActor()!=15) error("A second ring sent the baker away");
			for(int i=0;i<400 && resident->_room==55;++i) { stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(4); }
			if(resident->_room==55 || _scummVars[768] || getClass(15,kObjectClassNeverClip)) error("The baker stays at his window");
		}
		_scummVars[724]=0;
	}
	// Playing as one of them: their costume in their own colour; save and
	// load keep it; back as herself, Annie has her costume and colour again.
	{
		using namespace ::Scummverse::WorldCatalog;
		Actor *annie=derefActor(20,"Zak look");
		const int ownCostume=annie->_costume, ownColor=annie->scummversePalette(1);
		for(const auto &look : kWorldZakCast) {
			if(!scummverseSetAppearance(20,worldAppearanceKey(kWorldZakLooks,look.costume))) error("Cannot play as %s",look.name);
			if(annie->_costume!=look.costume || annie->scummversePalette(1)!=worldLookTint(kWorldZakLooks,look.costume) || strcmp((const char *)annie->getActorName(),look.name))
				error("Annie as %s: costume %d colour %d name %s",look.name,annie->_costume,annie->scummversePalette(1),(const char *)annie->getActorName());
		}
		scummverseSetAppearance(20,worldAppearanceKey(kWorldZakLooks,44));
		Common::String file; _saveLoadDescription="Annie as Lou";
		if(!saveState(8,false,file) || !loadState(8,false)) error("Look save/load failed");
		stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(0);
		if(annie->_costume!=44 || annie->scummversePalette(1)!=1) error("Loaded look lost: costume %d colour %d",annie->_costume,annie->scummversePalette(1));
		scummverseSetAppearance(20,0);
		if(annie->_costume!=ownCostume || annie->scummversePalette(1)!=ownColor || strcmp((const char *)annie->getActorName(),"Annie Larris"))
			error("Annie not herself again: costume %d colour %d",annie->_costume,annie->scummversePalette(1));
		if(getClass(15,kObjectClassNeverClip)) error("The borrowed actor keeps the window's drawing");
		warning("ZAK CAST %d residents placed, the baker came when rung, %d looks played",10,(int)ARRAYSIZE(kWorldZakCast));
	}
	// Without Zak's files (a save from when they were there), whoever plays
	// one of Zak's people is themselves again, not a costume that cannot
	// load; and nobody can choose one. (Last: Zak's costumes are gone.)
	{
		using namespace ::Scummverse::WorldCatalog;
		Actor *dave=derefActor(3,"Zak look without Zak");
		if(!scummverseSetAppearance(3,worldAppearanceKey(kWorldZakLooks,44)) || dave->_costume!=44) error("Dave cannot play Lou");
		ConfMan.setPath("scummverse_zak_path", Common::Path("/nonexistent/zak"));
		for(auto &costume : _scummverseZakCastCostumes) costume.clear();
		if(scummverseSetAppearance(3,worldAppearanceKey(kWorldZakLooks,45))) error("One of Zak's chosen without Zak's files");
		stopTalk(); VAR(VAR_HAVE_MSG)=0; scummverseUpdateRoaming(4);
		if(scummverseAppearance(3) || dave->_costume!=3) error("Still Lou without Zak's files: look %d costume %d",scummverseAppearance(3),dave->_costume);
	}
	warning("SCUMMVERSE_ZAK_CAST_PASS enabled=1");quitGame();
