	// DAMAGED: the mansion given what a settings file cut short as the app
	// was stopped writing it, an export stopped partway or a damaged save
	// leaves, read without ending or holding up the app. The settings are
	// tools/test_damaged_engine.py's: one not true or false is read as its
	// default, one not a number (or out of range) as not kept. A scene whose
	// size says gigabytes is not read; the van's scale and the Dig tram's
	// trip and phase from a damaged save are kept within reason.
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	if(!_scummverseRoaming || !_scummverseRoamingReady) error("The mansion not as itself (roaming=tr, its default, on): roaming %d, ready %d",_scummverseRoaming,_scummverseRoamingReady);
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	using namespace ::Scummverse::WorldCatalog;
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	Actor *me=derefActor(3,"damaged");
	const Common::String transient=Common::ConfigManager::kTransientDomain;
	settle(4);
	// The settings as read: those it cannot read as their defaults, the one
	// it can (doors, false or true) as it is.
	scummverseWanderBuild();
	const bool doors=ConfMan.getBool("scummverse_exploration_doors");
	if(!_scummverseExplorationSafety || _scummverseExplorationDoors!=doors || !_scummverseWanderersOn || _scummverseStory)
		error("Settings: safety %d (ye: on), doors %d (%d), wanderers %d (fal: out), story %d",_scummverseExplorationSafety,_scummverseExplorationDoors,doors,_scummverseWanderersOn,_scummverseStory);
	_scummverseWanderersOn=false; // (the rooms as the other probes have them)
	if(!_scummverseTourPublished || _scummverseTourStop!=0 || ::Scummverse::Tour::speed()!=1)
		error("Tour: stop %d (abc: the first), speed %d (out of range: 1), published %d",_scummverseTourStop,::Scummverse::Tour::speed(),_scummverseTourPublished);
	// (How the two read what they find, unset and registered defaults too.)
	{
		struct Number { const char *text; int read; } numbers[]={{"12",12},{"0x10",16},{"-3",-3},{"abc",7},{"",7},{"9x",9}};
		for(const Number &c : numbers) {
			ConfMan.set("scummverse_probe_number",c.text,transient);
			if(scummverseSetting("scummverse_probe_number",7)!=c.read) error("'%s' read as %d, not %d",c.text,scummverseSetting("scummverse_probe_number",7),c.read);
		}
		ConfMan.removeKey("scummverse_probe_number",transient);
		ConfMan.registerDefault("scummverse_probe_number",5);
		if(scummverseSetting("scummverse_probe_number",7)!=7) error("A number not set read as its registered default");
		ConfMan.registerDefault("scummverse_probe_switch",true);
		if(!scummverseSwitch("scummverse_probe_switch",false)) error("A switch not set not read as its registered default");
		struct Switch { const char *text; bool otherwise, read; } switches[]={{"yes",false,true},{"0",true,false},{"",true,false},{"maybe",true,true},{"maybe",false,false},{"tr",false,false}};
		for(const Switch &c : switches) {
			ConfMan.set("scummverse_probe_switch",c.text,transient);
			if(scummverseSwitch("scummverse_probe_switch",c.otherwise)!=c.read) error("Switch '%s' (else %d) not read as %d",c.text,c.otherwise,c.read);
		}
		ConfMan.removeKey("scummverse_probe_switch",transient);
	}
	warning("DAMAGED settings: roaming, safety and wanderers not true or false as their defaults, doors as set (%d); the tour's stop not a number and speed out of range as none kept",doors);
	// A scene an export stopped partway through left (the last four bytes, a
	// compressed one's size, saying gigabytes), in a scratch worlds folder:
	// not read, said so at once, and the mansion as it was.
	{
		const Common::FSNode scratch(ConfMan.getPath("savepath").appendComponent("damaged-worlds"));
		if(!scratch.exists() && !scratch.createDirectory()) error("No scratch worlds folder");
		static const byte cut[]={0x1f,0x8b,8,0,0,0,0,0,0,3, 0x63,0x60,0x60,0x64, 0xde,0xad,0xbe,0xef, 0xf0,0xff,0xff,0xff};
		{
			Common::DumpFile f;
			if(!f.open(scratch.getPath().appendComponent("monkey-33.svw"))) error("Cannot write the damaged scene");
			f.write(cut,sizeof(cut)); f.finalize();
		}
		Common::Array<int> slots(_scummVars+600,9); // (the world room slots, 600..607, and their layout, 608)
		ConfMan.setPath("scummverse_worlds_path",scratch.getPath(),transient);
		const int room=_currentRoom; const Common::Point at=me->getRealPos();
		const int slot=scummverseWorldRoomFor(0,33);
		const uint32 began=_system->getMillis();
		const bool mounted=slot && scummverseMountWorld(slot);
		const uint32 took=_system->getMillis()-began;
		if(!slot || mounted || _scummverseWorldNotice!="The scene file could not be read." || took>2000)
			error("A damaged scene: slot %d, mounted %d, '%s' in %u ms",slot,mounted,_scummverseWorldNotice.c_str(),took);
		if(scummverseTravelPlace(0,33) || _currentRoom!=room || me->_room!=room || me->getRealPos().x!=at.x) error("Travelled to a damaged scene: room %d",_currentRoom);
		ConfMan.removeKey("scummverse_worlds_path",transient);
		for(uint i=0;i<slots.size();++i) _scummVars[600+i]=slots[i];
		settle(2);
		warning("DAMAGED scene: its size saying %u bytes, not read (%u ms), the player still in room %d",0xfffffff0u,took,room);
	}
	// The van parked at the mansion, its scale as a damaged save holds it:
	// within ten times its own there, a step as quick as ever.
	{
		int site=-1;
		for(int i=0;i<kWorldVanSiteCount;++i) if(kWorldVanSites[i].game<0 && kWorldVanSites[i].room==44) site=i;
		if(site<0) error("No van site at the mansion");
		if(_currentRoom!=44) { me->putActor(100,60,44); startScene(44,me,0); settle(2); }
		const int was[]={_scummVars[kVanSiteVar],_scummVars[kVanXVar],_scummVars[kVanYVar],_scummVars[kVanPhaseVar],_scummVars[kVanScaleVar]};
		_scummVars[kVanSiteVar]=site; _scummVars[kVanPhaseVar]=0; _scummVars[kVanXVar]=40; _scummVars[kVanYVar]=120; _scummVars[kVanScaleVar]=100;
		int x,y,w,h,ownW,ownH;
		if(!scummverseVanRect(x,y,ownW,ownH)) error("No van parked at the mansion");
		for(int scale : {20000000,1000000,0x7FFFFFFF,-5,1,0}) {
			_scummVars[kVanScaleVar]=scale;
			if(!scummverseVanRect(x,y,w,h)) error("No van parked at the mansion");
			if(w<1 || h<1 || w>10*ownW+1 || h>10*ownH+1) error("The van at scale %d: %dx%d (%dx%d at its own)",scale,w,h,ownW,ownH);
			const uint32 began=_system->getMillis();
			_fullRedraw=true; settle(1);
			if(_system->getMillis()-began>2000) error("A step with the van at scale %d took %u ms",scale,_system->getMillis()-began);
		}
		_scummVars[kVanSiteVar]=was[0]; _scummVars[kVanXVar]=was[1]; _scummVars[kVanYVar]=was[2]; _scummVars[kVanPhaseVar]=was[3]; _scummVars[kVanScaleVar]=was[4];
		settle(1);
		warning("DAMAGED van: its scale within ten times its own %dx%d at the mansion",ownW,ownH);
	}
	// The Dig's tram from a damaged save (a time no trip takes, a trip no
	// line has): none, at once, wherever the player is; one under way as
	// saved goes on.
	{
		struct Tram { int phase, trip; } trams[]={{-5,1},{kDigTramDone+1,1},{0x7FFFFFFF,1},{-0x7FFFFFFF,2},{100,0},{100,-3},{100,2*kWorldTramLineCount+1}};
		for(const Tram &t : trams) {
			_scummVars[609]=t.phase; _scummVars[610]=0xFFFF; _scummVars[611]=t.trip;
			scummverseServiceDigTram(4);
			if(_scummVars[609] || _scummVars[610] || _scummVars[611]) error("A damaged tram (phase %d, trip %d): phase %d, riders %x, trip %d",t.phase,t.trip,_scummVars[609],_scummVars[610],_scummVars[611]);
		}
		_scummVars[609]=100; _scummVars[610]=0; _scummVars[611]=1;
		scummverseServiceDigTram(4);
		if(_scummVars[609]!=104 || _scummVars[611]!=1) error("A tram under way stopped: phase %d, trip %d",_scummVars[609],_scummVars[611]);
		_scummVars[609]=_scummVars[610]=_scummVars[611]=0;
		warning("DAMAGED tram: %d damaged trips dropped, one under way kept",(int)ARRAYSIZE(trams));
	}
	warning("SCUMMVERSE_DAMAGED_PASS enabled=%d",_scummverseExplorationDoors ? 1 : 0);
	quitGame();
	return;
