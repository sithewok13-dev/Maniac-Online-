	// The TOUR through the real engine: started from the Worlds menu's
	// request, the player's character visits stop 1 (a mansion room), walks
	// across it and goes on to stop 2 by itself, through a door; Stop brings
	// it back where it began; Resume, Next and Previous; the first stops of
	// each game walked in turn without standing still, through their doors;
	// every stop gone to by number must be entered (the label naming it),
	// its room the one it names; and every door of the route taken from the
	// stop before. Stops of games not exported are passed over. Then what
	// interrupts it: a load, playing someone else, somewhere else chosen from
	// the menus (paused or not), a ride boarded while paused, the van's
	// flight chosen as it plays on; a door tapped while paused (no tap kept
	// after Stop or a load); the autosave kept where it began, and a save
	// waiting for its frame never taken over by one. Without Monkey
	// Island's export, what needs its places is passed over.
	if (!_scummverseRoaming) { warning("SCUMMVERSE_TOUR_PASS enabled=0"); quitGame(); return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3; _scummverseRosterPending=false;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	namespace T = ::Scummverse::Tour;
	using namespace ::Scummverse::WorldCatalog;
	Actor *dave=derefActor(3,"tour guide");
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	auto shot=[&](const Common::String &name) {
		Common::DumpFile f; if(!f.open(Common::Path("/workspace/Maniac-Online/build/"+name))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); }
	};
	auto status=[&](Common::String &label) {
		bool running=false; char text[200]; int next=0, total=0;
		T::status(running,text,sizeof(text),next,total); label=text; return running;
	};
	// The stop number a label names ("Stop 12 of 846 · ..."), or 0.
	auto number=[&](const Common::String &label) { int n=0; return sscanf(label.c_str(),"Stop %d of",&n)==1 ? n : 0; };
	auto request=[&](int command, int stop, int loops) { T::request(command,stop); settle(loops); };
	if(!scummverseTravel(2)) error("Cannot reach the mansion");
	settle(4);
	const int total=scummverseTourCount();
	if (total<100) error("Only %d stops",total);
	const int homeRoom=_currentRoom, homeX=dave->getRealPos().x, homeY=dave->getRealPos().y;
	// The way back to the mansion as the tour began (kept: the tour's own
	// departures from the mansion are not the player's).
	const int wayKey=700+3*3; // (Dave's: travellerReturnKey, declared after this)
	const int wayBack[3]={_scummVars[wayKey],_scummVars[wayKey+1],_scummVars[wayKey+2]};
	ConfMan.removeKey("scummverse_tour_stop",ConfMan.getActiveDomainName());
	ConfMan.removeKey("scummverse_tour_speed",ConfMan.getActiveDomainName());
	Common::String label;
	settle(1);
	if (status(label) || !label.empty()) error("Touring before being asked: %s",label.c_str());

	// Stop 1: a mansion room, named; walking across it, then stop 2.
	request(T::kResume,0,2);
	if (!status(label) || number(label)!=1 || !label.contains("Maniac ")) error("Stop 1 not begun: '%s'",label.c_str());
	const ScummverseTourStop first=_scummverseTourStops[0];
	if (_currentRoom!=first.room || dave->_room!=first.room) error("Stop 1 is room %d, the guide in %d (view %d)",first.room,dave->_room,_currentRoom);
	// No saving while touring (it would go on from a stop, the tour gone).
	{ Common::U32String why; if (canSaveGameStateCurrently(&why) || why.empty()) error("Saving not refused during the tour"); }
	shot("tour-1.ppm");
	int left=10000, right=-1, steps=0;
	while (number(label)==1 && steps<3000) {
		settle(1); ++steps; status(label);
		if (number(label)==1) { left=MIN(left,(int)dave->getRealPos().x); right=MAX(right,(int)dave->getRealPos().x); }
	}
	if (number(label)!=2) error("Stop 1 never ended (%d steps): '%s'",steps,label.c_str());
	if (right-left<4) error("The guide did not walk across stop 1 (x %d..%d)",left,right);
	if (!_scummverseTourStops[1].legs || !_scummverseTourViaDoor || label.contains("warped") || !scummverseTourThere(1))
		error("Stop 2 not walked into through its door: '%s' (%d doors)",label.c_str(),_scummverseTourStops[1].legs);
	warning("TOUR stop 1 (room %d): walked x %d..%d in %d steps; then '%s'",first.room,left,right,steps,label.c_str());

	// Stop: back where the tour began; nothing touring or labelled.
	request(T::kStop,0,3);
	if (status(label) || !label.empty()) error("Still touring after Stop: '%s'",label.c_str());
	if (_currentRoom!=homeRoom || dave->_room!=homeRoom || ABS(dave->getRealPos().x-homeX)>2 || ABS(dave->getRealPos().y-homeY)>4)
		error("Not back home: room %d at %d,%d (began in %d at %d,%d)",_currentRoom,dave->getRealPos().x,dave->getRealPos().y,homeRoom,homeX,homeY);
	// Resume: at the stop it was at (remembered); Next and Previous.
	if (ConfMan.getInt("scummverse_tour_stop")!=2) error("Remembered stop %d",ConfMan.getInt("scummverse_tour_stop"));
	request(T::kResume,0,2);
	if (!status(label) || number(label)!=2) error("Resume: '%s'",label.c_str());
	request(T::kNext,0,2);
	if (!status(label) || number(label)!=3) error("Next: '%s'",label.c_str());
	request(T::kPrevious,0,2);
	if (!status(label) || number(label)!=2) error("Previous: '%s'",label.c_str());
	// Speed: 4x, 8x and 16x taken up and remembered; the wait between game
	// steps a quarter, an eighth, a sixteenth while touring (not otherwise,
	// nor paused); back to 1x.
	{
		auto waited=[&]() { _lastWaitTime=_system->getMillis(); const uint32 began=_system->getMillis(); waitForTimer(120); return (int)(_system->getMillis()-began); };
		auto speed=[&](int n) {
			T::setSpeed(n); settle(1);
			if (_scummverseTourSpeed!=n || ConfMan.getInt("scummverse_tour_speed")!=n) error("Speed %d not taken (%d, saved %d)",n,_scummverseTourSpeed,ConfMan.getInt("scummverse_tour_speed"));
		};
		const int normal=waited();
		speed(4); const int fast=waited();
		speed(8); const int faster=waited();
		speed(16); const int fastest=waited();
		_scummverseTouring=false; const int untoured=waited(); _scummverseTouring=true;
		_scummverseTourPaused=true; const int paused=waited(); _scummverseTourPaused=false;
		if (normal<400 || fast>300 || faster>200 || faster>=fast || fastest>120 || fastest>=faster || untoured<400 || paused<400)
			error("Waits at 1x %d ms, 4x %d ms, 8x %d ms, 16x %d ms, 16x not touring %d ms, paused %d ms (500, 125, 62, 31, 500, 500 asked)",normal,fast,faster,fastest,untoured,paused);
		speed(1);
		warning("TOUR speed: a 500 ms wait takes %d ms at 1x, %d ms at 4x, %d ms at 8x, %d ms at 16x (%d ms not touring, %d ms paused)",normal,fast,faster,fastest,untoured,paused);
	}
	// Pause: the guide stands, the stop stays; Previous and Next go from
	// stop to stop and stay paused (taps waiting in turn: two on Next, two
	// stops on); Play walks on. The player's taps, verbs and keys wait
	// while touring (the one played is on autopilot), and are taken paused:
	// a verb tapped (Walk to where there is one) sets the click area (V1's
	// variable 32) before the game's input script runs, or leaves it.
	{
		settle(6);
		int verb=0;
		for (int i=1;i<_numVerbs;++i)
			if (_verbs[i].verbid && _verbs[i].curmode==1 && (!verb || _verbs[i].verbid==13) && _verbs[i].verbid!=7 && (_verbs[i].verbid<20 || _verbs[i].verbid>22)) verb=_verbs[i].verbid;
		if (!verb) error("No verb to tap");
		auto tapped=[&]() {
			const int before=_scummVars[32];
			_scummVars[32]=99; runInputScript(kVerbClickArea,verb,1);
			if (_scummVars[32]!=99) return true;
			_scummVars[32]=before; return false;
		};
		if (!_scummverseTouring || _scummverseTourPaused || tapped()) error("A verb tapped while touring was taken (touring %d, paused %d)",_scummverseTouring,_scummverseTourPaused);
		T::request(T::kPause); settle(1);
		if (!_scummverseTourPaused || !T::paused()) error("Pause not taken");
		status(label);
		const Common::String pausedLabel=label;
		const int pausedRoom=_currentRoom;
		const Common::Point at=dave->getRealPos();
		settle(60); status(label);
		if (dave->_moving || dave->getRealPos()!=at || _currentRoom!=pausedRoom || label!=pausedLabel)
			error("Paused, yet the guide went on: '%s' at %d,%d in %d, now '%s' at %d,%d in %d",pausedLabel.c_str(),at.x,at.y,pausedRoom,label.c_str(),dave->getRealPos().x,dave->getRealPos().y,_currentRoom);
		if (!tapped()) error("A verb tapped while paused was not taken");
		settle(2);
		const int was=number(label);
		T::request(T::kPrevious); settle(3); status(label);
		if (number(label)!=was-1 || !_scummverseTourPaused || !scummverseTourThere(was-2)) error("Previous while paused: '%s'",label.c_str());
		settle(30); status(label);
		if (dave->_moving || number(label)!=was-1) error("Paused at stop %d, yet the guide went on: '%s'",was-1,label.c_str());
		T::request(T::kNext); T::request(T::kNext); settle(4); status(label);
		if (number(label)!=was+1 || !_scummverseTourPaused || !scummverseTourThere(was)) error("Next twice while paused: '%s'",label.c_str());
		T::request(T::kPlay); settle(1);
		if (_scummverseTourPaused || T::paused()) error("Play not taken");
		int moved=0;
		for (int i=0;i<10;++i) { settle(1); moved+=dave->_moving!=0; }
		if (!moved) error("Played, yet the guide stands");
		warning("TOUR pause: stood 60 steps in stop %d; Previous to %d, Next twice to %d, paused; Play walked on; verb %d tapped waited while touring, taken paused",was,was-1,was+1,verb);
	}

	// Stops walked in turn, from one gone to by number: the guide never stands
	// still (only the step between two walks, or at the door out until a
	// stop has been shown a second); one pass through each stop
	// (it turns back at most once, at the far end of a room whose door out
	// is near where it came in; in other games' rooms the converted walk
	// boxes can turn a walk round, so those stops are listed); each stop is
	// shown, none skipped, the guide
	// in its room until the next (a walk across is no tap on a door);
	// entered through its doors where the route has some (a warp only where
	// it has none).
	auto walk=[&](int first, int last, const char *what) {
		request(T::kGoTo,first,2);
		int walkedIn=0, warped=0, passed=0, at=first, still=0, longest=0, frames=0, shortest=100000;
		int dir=0, pivot=dave->getRealPos().x, turns=0, turned=0, waits=0;
		Common::String winding;
		for (int n=0;n<60000 && at<last;++n) {
			settle(1); status(label);
			const bool waiting=!dave->_moving && number(label)==at && frames<16; // (shown a second at least)
			still=dave->_moving || waiting ? 0 : still+1; longest=MAX(longest,still);
			if (waiting) ++waits;
			if (label.contains("on the way through")) { ++passed; continue; }
			const int now=number(label);
			if (now==at) {
				++frames;
				if (!scummverseTourThere(at-1)) error("%s: the guide left stop %d for room %d before it ended: '%s'",what,at,_currentRoom,label.c_str());
				// Turning back: four units (32 pixels) the other way from the
				// furthest point (less is a path bending round the walk boxes).
				const int x=dave->getRealPos().x;
				if (dir*(x-pivot)>0 || (!dir && ABS(x-pivot)>=4)) { if (!dir) dir=x>pivot ? 1 : -1; pivot=x; }
				else if (dir && dir*(pivot-x)>=4) { ++turns; dir=-dir; pivot=x; }
				continue;
			}
			if (now!=at+1) error("%s: stop %d followed by '%s'",what,at,label.c_str());
			if (turns>1 && _scummverseTourStops[at-1].kind!=2) error("%s: the guide turned back %d times in stop %d",what,turns,at);
			if (turns>1) winding+=Common::String::format(" %d (%d)",at,turns);
			if (at>first) shortest=MIN(shortest,frames);
			turned+=turns>0;
			at=now; frames=0; dir=0; turns=0; pivot=dave->getRealPos().x;
			const ScummverseTourStop &stop=_scummverseTourStops[at-1];
			if (stop.legs && (!_scummverseTourViaDoor || label.contains("warped"))) error("%s: stop %d has doors but was warped to: '%s'",what,at,label.c_str());
			if (!stop.legs && !label.contains("warped")) error("%s: stop %d has no doors, yet: '%s'",what,at,label.c_str());
			if (!scummverseTourThere(at-1)) error("%s: stop %d: in room %d",what,at,_currentRoom);
			(stop.legs ? walkedIn : warped)++;
		}
		if (at<last) error("%s: the tour did not reach stop %d on its own (at %d)",what,last,at);
		if (longest>1) error("%s: the guide stood still for %d steps in a row",what,longest);
		if (shortest<14) error("%s: a stop shown only %d steps",what,shortest);
		warning("TOUR %s, stops %d..%d on their own: %d walked in through doors, %d warped (%d steps passing through), still at most %d step (%d steps waiting at doors), each shown at least %d steps, %d turning back%s%s",
			what,first+1,last,walkedIn,warped,passed,longest,waits,shortest,turned,winding.empty()?"":"; more than once (walk boxes):",winding.c_str());
	};
	walk(1,12,"the mansion");
	// Then the first stretch of Zak's world and of each other game whose
	// rooms are here (walks across them could reach a door).
	for (int i=0, last=-2;i+8<total;++i) {
		const ScummverseTourStop &stop=_scummverseTourStops[i];
		const int key=stop.kind==2 ? stop.game : -1;
		if (stop.kind==0 || key==last) continue;
		bool whole=true;
		for (int k=i;k<i+8;++k) whole=whole && _scummverseTourStops[k].kind==stop.kind && _scummverseTourStops[k].game==stop.game && scummverseTourAvailable(k);
		if (!whole) continue;
		walk(i+1,i+8,stop.kind==1 ? "Zak" : kWorldGames[stop.game].gameid);
		last=key;
	}
	// Every stop, by number: entered and named, in the room it names.
	int entered[3]={0,0,0}, passed[3]={0,0,0}, failed=0;
	Common::String failures;
	for (int i=0;i<total;++i) {
		const ScummverseTourStop &stop=_scummverseTourStops[i];
		request(T::kGoTo,i+1,2);
		status(label);
		const int at=number(label);
		if (at>i+1) { ++passed[stop.kind]; continue; } // not here (a game not exported): passed over
		if (at!=i+1) error("Stop %d: the label says '%s'",i+1,label.c_str());
		if (label.contains("couldn't go there")) { ++failed; failures+=Common::String::format(" [%s]",label.c_str()); continue; }
		bool there=false;
		if (stop.kind==2) { int source=0; there=scummverseWorldGameOf(_currentRoom,source)==stop.game && source==stop.room; }
		else there=_currentRoom==stop.room;
		if (!there || dave->_room!=_currentRoom) error("Stop %d (%s): in room %d, the guide in %d",i+1,label.c_str(),_currentRoom,dave->_room);
		++entered[stop.kind];
		if (i==total/2 || i==total-1 || (stop.kind==1 && entered[1]==1)) shot(Common::String::format("tour-%d.ppm",i+1));
	}
	warning("TOUR %d stops: Maniac %d entered, Zak %d entered (%d passed over), other worlds %d entered (%d passed over); %d refused%s",
		total,entered[0],entered[1],passed[1],entered[2],passed[2],failed,failures.c_str());
	if (failed) error("%d stops refused:%s",failed,failures.c_str());
	if (!entered[0] || !entered[1]) error("No mansion or Zak stops entered");
	// Every door of the route: from the stop before, through it, into the
	// stop. (The tour itself warps where a door will not take the guide.)
	int doors=0, doorFailures=0, warps=0, longest=0;
	Common::String doorList;
	for (int i=1;i<total;++i) {
		const ScummverseTourStop &stop=_scummverseTourStops[i];
		if (!stop.legs) { ++warps; continue; }
		longest=MAX(longest,(int)stop.legs);
		if (!scummverseTourAvailable(i) || !scummverseTourAvailable(i-1)) continue;
		if (!scummverseTourEnter(i-1)) error("Stop %d (before a door) not entered",i);
		for (int leg=0;leg<stop.legs;++leg) {
			stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(0);
			int x=0, y=0;
			const bool point=scummverseTourDoorPoint(i,leg,x,y);
			if (point && scummverseTourThrough(i,leg)) { ++doors; continue; }
			++doorFailures;
			const ScummverseTourLeg &way=_scummverseTourLegs[stop.firstLeg+leg];
			if (doorFailures<=40) doorList+=Common::String::format(" [to stop %d, door %d into %s%s]",i+1,way.door,
				scummverseTourRoomName(stop.kind,stop.game,way.room).c_str(),point?"":", no door here");
			break; // (the tour warps to the stop from here)
		}
	}
	warning("TOUR route: %d doors taken, %d failed, %d warps, at most %d doors to a stop%s",doors,doorFailures,warps,longest,doorList.c_str());
	request(T::kStop,0,3);
	if (status(label)) error("Still touring at the end");
	for (int i=0;i<3;++i) if (_scummVars[wayKey+i]!=wayBack[i]) error("The way back to the mansion changed by the tour: %d,%d,%d (was %d,%d,%d)",_scummVars[wayKey],_scummVars[wayKey+1],_scummVars[wayKey+2],wayBack[0],wayBack[1],wayBack[2]);
	// After the last stop: home (where it began, from here), the next tour
	// from the first.
	{
		const int fromRoom=_currentRoom, fromX=dave->getRealPos().x, fromY=dave->getRealPos().y;
		request(T::kGoTo,total,2);
		int ended=0;
		while (status(label) && ++ended<3000) settle(1);
		bool running=false; char text[200]; int resume=0, stops=0;
		T::status(running,text,sizeof(text),resume,stops);
		if (running) error("The tour did not end after its last stop: '%s'",text);
		if (_currentRoom!=fromRoom || dave->_room!=fromRoom || ABS(dave->getRealPos().x-fromX)>2 || ABS(dave->getRealPos().y-fromY)>4)
			error("Not home after the last stop: room %d at %d,%d (began in %d at %d,%d)",_currentRoom,dave->getRealPos().x,dave->getRealPos().y,fromRoom,fromX,fromY);
		if (resume!=1 || ConfMan.getInt("scummverse_tour_stop")!=1) error("After the last stop the tour resumes at %d (saved %d), not 1",resume,ConfMan.getInt("scummverse_tour_stop"));
		for (int i=0;i<3;++i) if (_scummVars[wayKey+i]!=wayBack[i]) error("The way back to the mansion changed by the tour's end");
		warning("TOUR after the last stop (%d steps): home in room %d, the next tour from stop 1",ended,_currentRoom);
	}
	// A load ends the tour (it would go on from the place loaded); so does
	// playing someone else (as in the new engine), the way back as it began.
	{
		Common::String file;
		if (!saveState(14,false,file)) error("Save before the tour failed");
		request(T::kResume,0,2);
		if (!status(label)) error("Not touring again: '%s'",label.c_str());
		if (!loadState(14,false) || _scummverseTouring || status(label)) error("Still touring after a load: '%s'",label.c_str());
		settle(2);
		if (status(label) || _scummverseTouring) error("Touring again after a load: '%s'",label.c_str());
		int other=0;
		for (int id : {1,2,4,5,6,7}) if (!other && _actors[id]->_room>=1 && _actors[id]->_room<53 && _actors[id]->_room!=45 && _actors[id]->_costume) other=id;
		if (other) {
			request(T::kResume,0,2);
			if (!status(label)) error("Not touring before playing someone else: '%s'",label.c_str());
			if (!scummverseSwitchActor(other) || VAR(VAR_EGO)!=other || _scummverseTouring || status(label)) error("Still touring after playing actor %d: '%s'",other,label.c_str());
			for (int i=0;i<3;++i) if (_scummVars[wayKey+i]!=wayBack[i]) error("The way back to the mansion changed by playing someone else mid-tour");
			if (!scummverseSwitchActor(3) || VAR(VAR_EGO)!=3) error("Cannot play Dave again");
		}
		warning("TOUR ended by a load%s",other ? Common::String::format(" and by playing actor %d",other).c_str() : "");
	}
	// Choices from the menus mid-tour, paused or not, and what a paused tour lets the player do.
	{
		const int mi=(int)(worldGame("monkey")-kWorldGames);
		const WorldGame &monkey=kWorldGames[mi];
		int landmark=-1; // (the menu's numbering of named places, home games left out)
		for (int g=0, base=0; g<worldGameCount(); ++g) { if (worldHome(g)) continue; if (g==mi) landmark=base; base+=kWorldGames[g].sceneCount; }
		auto chose=[&](int choice) { FakeAI::worldRequest=choice; settle(3); };
		auto in=[&](int g, int room) { int source=0; return scummverseWorldGameOf(_currentRoom,source)==g && source==room && dave->_room==_currentRoom; };
		auto ended=[&](const char *what) { const bool shown=status(label); if (_scummverseTouring || shown) error("%s mid-tour: still touring ('%s', room %d)",what,label.c_str(),_currentRoom); };
		auto stale=[&]() { return ((_currentRoom==44 ? 1 : 44)*32+VAR(VAR_EGO))<<8; }; // (a room the tour was in before)
		int zakStop=-1, monkeyStop=-1, airportStop=-1, cockpitStop=-1;
		for (int i=0;i<total;++i) {
			const ScummverseTourStop &s=_scummverseTourStops[i];
			if (s.kind==1 && s.room==54 && zakStop<0) zakStop=i;
			if (s.kind==1 && s.room==53 && airportStop<0) airportStop=i;
			if (s.kind==1 && s.room==kVanCockpit && cockpitStop<0) cockpitStop=i;
			if (s.kind==2 && s.game==mi && monkeyStop<0 && scummverseTourAvailable(i)) monkeyStop=i;
		}
		if (zakStop<0 || !scummverseTourAvailable(zakStop)) error("No Zak stops (%d)",zakStop);
		// (Monkey Island's places need its export, build/worlds: without it
		// what needs one of them is passed over, as its stops are.)
		const bool monkeyHere=monkeyStop>=0 && landmark>=0 && scummverseWorldSceneInstalled(mi,monkey.scenes[1].room);
		if (!monkeyHere) warning("TOUR no %s export (stop %d): a place of another game chosen mid-tour, and a door of one tapped while paused, not tried",monkey.gameid,monkeyStop);
		// Somewhere else chosen mid-tour, paused or not (a place from the Worlds
		// menu, Return to Maniac Mansion, the mansion's own places, a teleport
		// pad, someone from another game on the character screen): the tour ends
		// where it is and the one played goes where chosen, to stay; their way
		// back to the mansion is theirs (as the tour began, or the mansion stop
		// they chose to leave from), never the tour's own departures. A menu's
		// scene token may name a room the tour has left meanwhile: still the
		// player's choice.
		{
			if (monkeyHere) {
				// A named place of another game, from a mansion stop (unpaused).
				request(T::kGoTo,3,2);
				if (!_scummverseTouring || _scummverseTourPaused || _currentRoom>=53) error("Not touring stop 3 in the mansion (room %d)",_currentRoom);
				const int leftRoom=_currentRoom, leftX=dave->getRealPos().x, leftY=dave->getRealPos().y;
				chose(stale()|(160+landmark+1));
				ended("A place chosen from the Worlds menu");
				if (!in(mi,monkey.scenes[1].room)) error("A place chosen mid-tour (%s %d) not reached: room %d",monkey.gameid,monkey.scenes[1].room,_currentRoom);
				if (_scummVars[wayKey]!=leftRoom || ABS(_scummVars[wayKey+1]-leftX)>6 || ABS(_scummVars[wayKey+2]-leftY)>6)
					error("The way back after leaving the tour's stop: %d,%d,%d (left room %d at %d,%d)",_scummVars[wayKey],_scummVars[wayKey+1],_scummVars[wayKey+2],leftRoom,leftX,leftY);
				settle(300);
				if (!in(mi,monkey.scenes[1].room) || _scummverseTouring) error("Taken back from the place chosen mid-tour: room %d",_currentRoom);
				warning("TOUR a place chosen mid-tour (the menu's token from a stop before): the tour ended, still in %s %d 300 steps on; the way back the mansion stop left (room %d)",monkey.gameid,monkey.scenes[1].room,leftRoom);
				chose(2); // (Return to Maniac Mansion: the stop left.)
				if (_currentRoom!=leftRoom) error("Return to Maniac Mansion: room %d, not %d",_currentRoom,leftRoom);
			}
			// Return to Maniac Mansion from a paused tour in Zak's apartment (the
			// tour left the mansion for it: its departure is not the way back).
			const int way[3]={_scummVars[wayKey],_scummVars[wayKey+1],_scummVars[wayKey+2]};
			const int wayRoom=way[0]>=1 && way[0]<=52 ? way[0] : 1; // (where Return to Maniac Mansion takes them by it)
			request(T::kGoTo,5,2); request(T::kGoTo,zakStop+1,2); request(T::kPause,0,1);
			if (!_scummverseTourPaused || !scummverseTourThere(zakStop)) error("Not paused in Zak's apartment: room %d",_currentRoom);
			const int tourWay=_scummVars[wayKey];
			chose(2);
			ended("Return to Maniac Mansion");
			if (_currentRoom!=wayRoom || dave->_room!=wayRoom) error("Return to Maniac Mansion mid-tour: room %d, not the way back %d (the tour left from %d)",_currentRoom,wayRoom,tourWay);
			for (int i=0;i<3;++i) if (_scummVars[wayKey+i]!=way[i]) error("The way back changed by Return to Maniac Mansion mid-tour");
			warning("TOUR Return to Maniac Mansion, paused in Zak's apartment: the tour ended, in room %d (the player's way back; the tour had left from %d)",_currentRoom,tourWay);
			// The mansion's own places offered mid-tour (the tour going on), the
			// kitchen chosen from Monkey Island (without it, Zak's apartment).
			const int awayStop=monkeyHere ? monkeyStop : zakStop;
			request(T::kGoTo,awayStop+1,2);
			if (!scummverseTourThere(awayStop)) error("Not in stop %d (%s): room %d",awayStop+1,monkeyHere ? monkey.gameid : "zak",_currentRoom);
			const int offered=FakeAI::placesShown;
			chose(((_currentRoom*32+VAR(VAR_EGO))<<8)|121);
			if (FakeAI::placesShown!=offered+1 || !_scummverseTouring) error("The mansion's places not offered mid-tour (shown %d, touring %d)",FakeAI::placesShown-offered,_scummverseTouring);
			chose(worldPlaceRequest(kWorldManiacPlaces,7));
			ended("The mansion's kitchen chosen");
			if (_currentRoom!=7 || dave->_room!=7) error("The mansion's kitchen chosen mid-tour: room %d",_currentRoom);
			for (int i=0;i<3;++i) if (_scummVars[wayKey+i]!=way[i]) error("The way back changed by a mansion place chosen mid-tour");
			warning("TOUR the mansion's places offered mid-tour, the kitchen chosen from %s: the tour ended, in room 7",monkeyHere ? monkey.gameid : "zak");
			// A teleport pad, its token from a stop before: where it leads when
			// not touring.
			chose(((_currentRoom*32+VAR(VAR_EGO))<<8)|50);
			const int padRoom=_currentRoom;
			chose(2);
			if (padRoom<56 || _currentRoom!=7) error("The first pad: room %d, back in %d",padRoom,_currentRoom);
			request(T::kGoTo,3,2);
			chose(stale()|50);
			ended("A teleport pad chosen");
			if (_currentRoom!=padRoom || dave->_room!=padRoom) error("A teleport pad chosen mid-tour: room %d, not %d",_currentRoom,padRoom);
			warning("TOUR a teleport pad chosen mid-tour (its token from a stop before): the tour ended, in room %d",padRoom);
			// Someone from another game on the character screen: met where they
			// live, as them.
			const WorldCastGuest *met=nullptr;
			for (const auto &c : kWorldCast)
				if (!met && scummverseWorldSceneInstalled(c.game,c.room) && scummverseCharacterInstalled(c.game,c.guest.costume) && worldAppearance(worldAppearanceKey(c.game,c.guest.costume))) met=&c;
			if (met) {
				request(T::kGoTo,zakStop+1,2);
				const int key=worldAppearanceKey(met->game,met->guest.costume);
				chose(kWorldCastRequest+key);
				ended("Someone met where they live");
				if (!in(met->game,met->room) || scummverseAppearance(3)!=key) error("Someone chosen mid-tour: room %d, look %d (not %s %d, %d)",_currentRoom,scummverseAppearance(3),kWorldGames[met->game].gameid,met->room,key);
				scummverseSetAppearance(3,0);
				warning("TOUR someone from another game chosen on the character screen mid-tour: the tour ended, in %s %d as them",kWorldGames[met->game].gameid,met->room);
			}
			chose(2);
		}
		// Paused, the player has the controls back: a door tapped in another
		// game's place is walked through (the tour stays paused); played on, the
		// tap is not kept, and touring a walk is no tap. A tap waiting as the
		// tour stops, or as a save is loaded, is no door to take after (where
		// the player goes may be another game's map, where a tap is taken at
		// once).
		if (monkeyHere) {
			int tried=0; bool through=false;
			Common::String door;
			for (int i=0;i<total && !through && tried<8;++i) {
				const ScummverseTourStop &s=_scummverseTourStops[i];
				if (s.kind!=2 || s.game!=mi || !scummverseTourAvailable(i)) continue;
				request(T::kGoTo,i+1,2); request(T::kPause,0,1);
				if (!_scummverseTourPaused || !scummverseTourThere(i)) error("Not paused in stop %d: room %d",i+1,_currentRoom);
				int source=0; const int g=scummverseWorldGameOf(_currentRoom,source);
				for (int k=0;k<::Scummverse::WorldBridge::objectCount() && !through && tried<8;++k) {
					int id,x,y,w,h,wx,wy;
					if (!::Scummverse::WorldBridge::object(k,id,x,y,w,h,wx,wy)) continue;
					const WorldLink *link=worldLinkFrom(g,source,id);
					if (!link || (link->switched && !::Scummverse::WorldBridge::objectState(k)) || link->target==source || !scummverseWorldSceneInstalled(g,link->target)) continue;
					const int tx=(x+w/2)/8, ty=(y+h/2)/2, px=tx*8+4, py=ty*2;
					bool covered=px<x || px>=x+w || py<y || py>=y+h; // (its middle under it, and under no other door)
					for (int o=0;o<::Scummverse::WorldBridge::objectCount() && !covered;++o) {
						int oid,ox,oy,ow,oh,owx,owy;
						if (o==k || !::Scummverse::WorldBridge::object(o,oid,ox,oy,ow,oh,owx,owy) || !worldLinkFrom(g,source,oid)) continue;
						covered=px>=ox && px<ox+ow && py>=oy && py<oy+oh;
					}
					if (covered) continue;
					++tried;
					const int from=_currentRoom;
					dave->startWalkActor(tx,ty,-1);
					for (int n=0;n<900 && _currentRoom==from;++n) settle(1);
					int now=0;
					through=scummverseWorldGameOf(_currentRoom,now)==g && now==link->target;
					door=Common::String::format("%s %d's door %d to %d",kWorldGames[g].gameid,source,id,link->target);
					if (!_scummverseTouring || !_scummverseTourPaused) error("Through a door paused (%s), the tour ended or played on",door.c_str());
					if (_currentRoom!=from) break;
				}
			}
			if (!through) error("No door tapped while paused was walked through (%d tried; the last %s)",tried,door.c_str());
			T::request(T::kPlay); settle(1);
			if (_scummverseTourPaused || _scummverseTapPending) error("Played on: paused %d, a tap kept %d",_scummverseTourPaused,_scummverseTapPending);
			scummverseWorldTap(VAR(VAR_EGO),dave->getRealPos().x,dave->getRealPos().y);
			if (_scummverseTapPending) error("Touring, a walk was taken as a tap");
			T::request(T::kPause); settle(1);
			scummverseWorldTap(VAR(VAR_EGO),dave->getRealPos().x,dave->getRealPos().y);
			if (!_scummverseTourPaused || !_scummverseTapPending) error("Paused, a tap not taken (paused %d)",_scummverseTourPaused);
			scummverseTourCommand(T::kStop,0); // (the tour's Stop, as its controls send it)
			if (_scummverseTouring || _scummverseTapPending) error("Stopped: touring %d, the tap made paused kept %d",_scummverseTouring,_scummverseTapPending);
			settle(3);
			if (!scummverseTravelPlace(mi,monkey.scenes[1].room)) error("Cannot go to %s %d",monkey.gameid,monkey.scenes[1].room);
			scummverseWorldTap(VAR(VAR_EGO),dave->getRealPos().x,dave->getRealPos().y);
			if (!_scummverseTapPending) error("A tap in %s %d not taken",monkey.gameid,monkey.scenes[1].room);
			if (!loadState(14,false) || _scummverseTapPending) error("Loaded: the tap made before kept %d",_scummverseTapPending);
			settle(2);
			warning("TOUR paused in another game's place: %s tapped and walked through (%d tried), still paused; played on, no tap kept; none kept after Stop or a load",door.c_str(),tried);
		}
		// Paused, the player boarded a ride: the tour ends there (played on it
		// would leave the ride holding them). A flight from Zak's airport; the
		// van's flight chosen in its cockpit.
		if (airportStop>=0) {
			request(T::kGoTo,airportStop+1,2); request(T::kPause,0,1);
			if (!_scummverseTourPaused || _currentRoom!=53) error("Not paused at the airport: room %d",_currentRoom);
			_scummVars[733]=7; // (Dave's destination: travellerDestinationKey; Seattle)
			scummverseBoard();
			if (_currentRoom!=56 || !_scummVars[724]) error("Not boarded at the airport: room %d",_currentRoom);
			settle(1);
			ended("A flight boarded while paused");
			if (_currentRoom!=56) error("Not aboard after the tour ended: room %d",_currentRoom);
			scummverseArrive();
			if (_currentRoom==56 || _scummVars[724]) error("The flight did not land: room %d",_currentRoom);
			warning("TOUR paused at the airport, a flight boarded: the tour ended aboard; landed in room %d",_currentRoom);
		}
		if (cockpitStop>=0 && !_scummVars[kVanPhaseVar] && scummverseVanSite()==0) {
			request(T::kGoTo,cockpitStop+1,2); request(T::kPause,0,1);
			if (!_scummverseTourPaused || _currentRoom!=kVanCockpit) error("Not paused in the van's cockpit: room %d",_currentRoom);
			FakeAI::worldRequest=kWorldVanRequest+3; settle(3); // (the mansion's site)
			if (_scummverseTouring || !scummverseInVan()) error("The van's flight chosen while paused: touring %d, aboard %d",_scummverseTouring,scummverseInVan());
			for (int n=0;n<600 && _currentRoom!=kVanFlightRoom;++n) settle(1);
			if (_currentRoom!=kVanFlightRoom) error("The van did not lift off: room %d",_currentRoom);
			FakeAI::worldRequest=((kVanFlightRoom*32+VAR(VAR_EGO))<<8)|24; settle(3); // (Arrive)
			if (_currentRoom!=44 || scummverseInVan()) error("The van did not land at the mansion: room %d",_currentRoom);
			warning("TOUR paused in the van's cockpit, its flight chosen: the tour ended aboard; landed in room %d",_currentRoom);
			// Its list shown paused, a destination chosen once the tour played
			// on (the phone's list stays up): the tour ends there too, the one
			// played aboard (played on, the tour would walk off and the liftoff
			// take them from wherever it went).
			request(T::kGoTo,cockpitStop+1,2);
			if (!_scummverseTouring || _scummverseTourPaused || _currentRoom!=kVanCockpit) error("Not touring the van's cockpit: room %d",_currentRoom);
			FakeAI::worldRequest=kWorldVanRequest; settle(3); // (Mars, where it began)
			if (_scummverseTouring || !scummverseInVan()) error("The van's flight chosen as the tour played on: touring %d, aboard %d",_scummverseTouring,scummverseInVan());
			for (int n=0;n<600 && _currentRoom!=kVanFlightRoom;++n) settle(1);
			if (_currentRoom!=kVanFlightRoom) error("The van did not lift off again: room %d",_currentRoom);
			FakeAI::worldRequest=((kVanFlightRoom*32+VAR(VAR_EGO))<<8)|24; settle(3); // (Arrive)
			if (_currentRoom!=kVanLandingSite || scummverseInVan() || scummverseVanSite()!=0) error("The van did not land on Mars: room %d, site %d",_currentRoom,scummverseVanSite());
			warning("TOUR the van's flight chosen in its cockpit as the tour played on: the tour ended aboard; landed in room %d",_currentRoom);
		} else warning("TOUR the van's flight not tried (cockpit stop %d, van phase %d, site %d)",cockpitStop,_scummVars[kVanPhaseVar],scummverseVanSite());
		// The autosave is written as the tour begins (where it began: the
		// phone's restore point if it stops the app mid-tour); asked for
		// meanwhile (as the phone puts the app away, and by ScummVM) it is kept
		// as it is, not written from a stop. Loaded, it is where the tour began.
		{
			if (_currentRoom>=53 && !scummverseTravel(2)) error("Not back in the mansion");
			settle(2);
			const int home=_currentRoom; const Common::Point at=dave->getRealPos();
			const int slot=getAutosaveSlot();
			auto bytes=[&]() {
				Common::Array<byte> b;
				Common::ScopedPtr<Common::InSaveFile> f(_saveFileMan->openForLoading(makeSavegameName(slot,false)));
				if (f) { b.resize(f->size()); f->read(b.data(),b.size()); }
				return b;
			};
			request(T::kGoTo,zakStop+1,2);
			if (!_scummverseTouring || !scummverseTourThere(zakStop)) error("Not touring in Zak's apartment: room %d",_currentRoom);
			const Common::Array<byte> began=bytes();
			if (began.empty() || !getMetaEngine()->querySaveMetaInfos(_targetName.c_str(),slot).isAutosave()) error("No autosave written as the tour began");
			if (!canSaveAutosaveCurrently()) error("No autosave can be made mid-tour: the phone would keep no place to go on from");
			if (saveGameState(slot,"Autosave",true).getCode()!=Common::kNoError) error("The phone's autosave failed mid-tour");
			saveAutosaveIfEnabled();
			settle(2);
			if (bytes()!=began) error("The autosave was written from the tour's stop");
			{ Common::U32String why; if (canSaveGameStateCurrently(&why) || why.empty()) error("Saving not refused mid-tour"); }
			if (!loadState(slot,false) || _scummverseTouring || status(label)) error("The autosave not loaded, or still touring");
			settle(2);
			if (_currentRoom!=home || dave->_room!=home || ABS(dave->getRealPos().x-at.x)>2 || ABS(dave->getRealPos().y-at.y)>4)
				error("The autosave is not where the tour began: room %d at %d,%d (began in %d at %d,%d)",_currentRoom,dave->getRealPos().x,dave->getRealPos().y,home,at.x,at.y);
			warning("TOUR autosave: written as the tour began (room %d), kept mid-tour (the phone's and ScummVM's autosaves made without writing it from the stop); loaded, there again",home);
		}
	}
	// Not touring, a save waiting for the main loop's next frame (Day of the
	// Tentacle's computer's temporary save, slot 100, as startManiac asks for
	// it; a load) is never taken over by an autosave asked for meanwhile,
	// ScummVM's or the phone's: refused, and the save written as asked.
	{
		const int slot=getAutosaveSlot();
		auto bytes=[&](int s, bool temporary) {
			Common::Array<byte> b;
			Common::ScopedPtr<Common::InSaveFile> f(_saveFileMan->openForLoading(makeSavegameName(s,temporary)));
			if (f) { b.resize(f->size()); f->read(b.data(),b.size()); }
			return b;
		};
		auto phone=[&]() { PauseToken pt=pauseEngine(); return saveGameState(slot,"Autosave",true).getCode(); }; // (held still)
		const Common::Array<byte> autosaved=bytes(slot,false);
		_saveFileMan->removeSavefile(makeSavegameName(100,true));
		_saveLoadFlag=1; _saveLoadSlot=100; _saveTemporaryState=true;
		const bool offered=canSaveAutosaveCurrently();
		saveAutosaveIfEnabled();
		const Common::ErrorCode held=phone();
		if (offered || held==Common::kNoError || _saveLoadFlag!=1 || _saveLoadSlot!=100 || !_saveTemporaryState)
			error("A save waiting taken over by an autosave: offered %d, the phone's %d; flag %d, slot %d, temporary %d",offered,held,_saveLoadFlag,_saveLoadSlot,_saveTemporaryState);
		scummLoop_handleSaveLoad();
		if (_saveLoadFlag || bytes(100,true).empty() || bytes(slot,false)!=autosaved) error("Slot 100 not written, or the autosave written meanwhile");
		_saveLoadFlag=2; _saveLoadSlot=100; _saveTemporaryState=true;
		saveAutosaveIfEnabled();
		if (phone()==Common::kNoError || _saveLoadFlag!=2 || _saveLoadSlot!=100 || bytes(slot,false)!=autosaved)
			error("A load waiting taken over by an autosave: flag %d, slot %d",_saveLoadFlag,_saveLoadSlot);
		_saveLoadFlag=0; _saveTemporaryState=false;
		if (!canSaveAutosaveCurrently() || phone()!=Common::kNoError || _saveLoadFlag || bytes(slot,false)==autosaved) error("With nothing waiting, the phone's autosave not written at once");
		warning("TOUR not touring, a save waiting for its frame (slot 100, as Tentacle's computer asks for it) or a load kept: ScummVM's and the phone's autosaves refused meanwhile; with nothing waiting, written");
	}
	warning("SCUMMVERSE_TOUR_PASS enabled=1");
	quitGame();
	return;
