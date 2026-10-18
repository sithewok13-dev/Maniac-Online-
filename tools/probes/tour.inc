	// The TOUR through the real engine: started from the Worlds menu's
	// request, the player's character visits stop 1 (a mansion room), walks
	// across it and goes on to stop 2 by itself, through a door; Stop brings
	// it back where it began; Resume, Next and Previous; the first stops of
	// each game walked in turn without standing still, through their doors;
	// every stop gone to by number must be entered (the label naming it),
	// its room the one it names; and every door of the route taken from the
	// stop before. Stops of games not exported are passed over.
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
	// stops on); Play walks on.
	{
		settle(6);
		T::request(T::kPause); settle(1);
		if (!_scummverseTourPaused || !T::paused()) error("Pause not taken");
		status(label);
		const Common::String pausedLabel=label;
		const int pausedRoom=_currentRoom;
		const Common::Point at=dave->getRealPos();
		settle(60); status(label);
		if (dave->_moving || dave->getRealPos()!=at || _currentRoom!=pausedRoom || label!=pausedLabel)
			error("Paused, yet the guide went on: '%s' at %d,%d in %d, now '%s' at %d,%d in %d",pausedLabel.c_str(),at.x,at.y,pausedRoom,label.c_str(),dave->getRealPos().x,dave->getRealPos().y,_currentRoom);
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
		warning("TOUR pause: stood 60 steps in stop %d; Previous to %d, Next twice to %d, paused; Play walked on",was,was-1,was+1);
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
	warning("SCUMMVERSE_TOUR_PASS enabled=1");
	quitGame();
	return;
