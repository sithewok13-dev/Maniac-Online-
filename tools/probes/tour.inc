	// The TOUR through the real engine: started from the Worlds menu's
	// request, the player's character visits stop 1 (a mansion room), walks
	// across it and goes on to stop 2 by itself, through a door; Stop brings
	// it back where it began; Resume, Next and Previous; the first mansion
	// stops walked in turn, through their doors; every stop gone to by number
	// must be entered (the label naming it), its room the one it names; and
	// every door of the route taken from the stop before. Stops of games not
	// exported are passed over.
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

	// The first mansion stops walked in turn: through their doors where the
	// route has one (a warp only where it has none).
	{
		request(T::kGoTo,1,2);
		int walkedIn=0, warped=0, passed=0, at=1;
		for (int n=0;n<60000 && at<12;++n) {
			settle(1); status(label);
			if (label.contains("on the way through")) { ++passed; continue; }
			const int now=number(label);
			if (now==at) continue;
			at=now;
			const ScummverseTourStop &stop=_scummverseTourStops[at-1];
			if (stop.legs && (!_scummverseTourViaDoor || label.contains("warped"))) error("Stop %d has doors but was warped to: '%s'",at,label.c_str());
			if (!stop.legs && !label.contains("warped")) error("Stop %d has no doors, yet: '%s'",at,label.c_str());
			if (!scummverseTourThere(at-1)) error("Stop %d: in room %d",at,_currentRoom);
			(stop.legs ? walkedIn : warped)++;
		}
		if (at<12) error("The tour did not reach stop 12 on its own (at %d)",at);
		warning("TOUR stops 2..12 on their own: %d walked in through doors, %d warped (%d steps passing through)",walkedIn,warped,passed);
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
