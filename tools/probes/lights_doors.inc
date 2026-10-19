	// Lights and doors through the real engine. Maniac Mansion's six rooms
	// the original starts dark are lit in a new sandbox; the basement's
	// switch still turns its light off and on, and off stays off; a save
	// from before is lit once. The tour opens each door the guide sets off
	// to before it goes through (Maniac's; Zak's clean ones, and the door
	// back on arrival), never Zak's others; the player's walk through a Zak
	// door opens it and the one back.
	if (!_scummverseRoaming) { warning("SCUMMVERSE_LIGHTS_DOORS_PASS enabled=0"); quitGame(); return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3; _scummverseRosterPending=false;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	namespace T = ::Scummverse::Tour;
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	auto lightOff=[&](int room) { const int bit=2816+room; return (_scummVars[bit>>4]>>(bit&15))&1; };
	auto lit=[&]() { return VAR(VAR_CURRENT_LIGHTS)==11; };
	int none[NUM_SCRIPT_LOCAL]; memset(none,0,sizeof(none));

	// Lights: the six rooms lit from the start.
	if (_scummVars[kScummverseLightsVar]!=1) error("Lights not switched on at the start (var %d)",_scummVars[kScummverseLightsVar]);
	const int dark[][3]={{5,23,57},{8,44,64},{9,18,65},{15,18,56},{22,9,61},{23,26,61}};
	for (const auto &d : dark) {
		if (!scummverseTourPlace(d[0],d[1],d[2])) error("Cannot enter room %d",d[0]);
		settle(4);
		if (lightOff(d[0]) || !lit()) error("Room %d dark (lights %d)",d[0],VAR(VAR_CURRENT_LIGHTS));
	}
	// The basement's switch: off, and off stays off; then on again.
	scummverseTourPlace(8,44,64); settle(2);
	runObjectScript(335,5,false,false,none); settle(6);
	if (lit() || !lightOff(8)) error("Switched off, the basement is lit (lights %d)",VAR(VAR_CURRENT_LIGHTS));
	scummverseTourPlace(10,36,60); settle(2);
	scummverseLightsOn();
	scummverseTourPlace(8,44,64); settle(4);
	if (lit()) error("The basement lit again by itself");
	runObjectScript(335,4,false,false,none); settle(6);
	if (!lit()) error("Switched on again, the basement is dark (lights %d)",VAR(VAR_CURRENT_LIGHTS));
	// A save from before: lit once.
	{ _scummVars[kScummverseLightsVar]=0; const int bit=2816+22; _scummVars[bit>>4]|=1<<(bit&15); }
	scummverseLightsOn();
	if (lightOff(22) || _scummVars[kScummverseLightsVar]!=1) error("An old save's medical office not lit");
	warning("LIGHTS six rooms lit; the basement's switch off stays off, on again; an old save lit once");

	// Doors: the tables, from the source (tools/test_lights_doors.py).
	struct Passage { int room, object; bool door; };
	static const Passage passages[] = {@PASSAGES@};
	struct Link { int room, object, destination; };
	static const Link links[] = {@ZAKLINKS@};
	static const short clean[][2] = {@ZAKOPEN@};
	auto isClean=[&](int room, int object) { for (const auto &c : clean) if (c[0]==room && c[1]==object) return true; return false; };
	auto open=[&](int object) { return (getState(object) & kObjectStateIntrinsic)!=0; };
	// The tour, walked: Maniac's stops, then Zak's.
	const int total=scummverseTourCount();
	int maniac=0, zak=0, zakShut=0, zakBack=0;
	auto walk=[&](int first, int last) {
		T::request(T::kGoTo,first); settle(2);
		int phase=-1, legAt=-1, stop=-1, steps=0;
		while (_scummverseTourShown+1<last && ++steps<60000) {
			const int fromRoom=_currentRoom;
			settle(1);
			// A door walk just begun (phase 4: to the door; leg legAt of stop).
			if (_scummverseTourPhase==4 && (phase!=4 || legAt!=_scummverseTourLegAt || stop!=_scummverseTourStop)) {
				const ScummverseTourStop &s=_scummverseTourStops[_scummverseTourStop];
				const int door=_scummverseTourLegs[s.firstLeg+_scummverseTourLegAt].door;
				if (s.kind==0 && passages[door-1].door) {
					if (passages[door-1].room!=_currentRoom) error("Stop %d: the door walk in room %d, not %d",_scummverseTourStop+1,_currentRoom,passages[door-1].room);
					if (!open(passages[door-1].object)) error("Stop %d: Maniac's door %d (room %d) not open as the guide sets off",_scummverseTourStop+1,passages[door-1].object,_currentRoom);
					++maniac;
				} else if (s.kind==1) {
					const Link &l=links[door-1];
					if (l.room==_currentRoom && getObjectIndex(l.object)>=0) {
						if (isClean(l.room,l.object)) { if (!open(l.object)) error("Stop %d: Zak's door %d in room %d not open as the guide sets off",_scummverseTourStop+1,l.object,l.room); ++zak; }
						else if (getState(l.object)==0 && open(l.object)) error("Stop %d: Zak's door %d in room %d opened, its picture unchecked",_scummverseTourStop+1,l.object,l.room);
						else ++zakShut;
					}
				}
			}
			// Arrived in a Zak room by a door: the clean door back is open.
			if (_currentRoom!=fromRoom && _scummverseTourStop<total && _scummverseTourStops[_scummverseTourStop].kind==1)
				for (const auto &l : links) if (l.room==_currentRoom && l.destination==fromRoom && isClean(l.room,l.object)) {
					if (!open(l.object)) error("Arrived in room %d from %d: the door back (%d) shut",_currentRoom,fromRoom,l.object);
					++zakBack;
				}
			phase=_scummverseTourPhase; legAt=_scummverseTourLegAt; stop=_scummverseTourStop;
		}
		if (_scummverseTourShown+1<last) error("The tour did not reach stop %d (at %d)",last,_scummverseTourShown+1);
	};
	walk(2,37);
	walk(38,139);
	if (maniac<10 || !zak) error("Too few doors seen: Maniac %d, Zak %d",maniac,zak);
	T::request(T::kStop); settle(3);
	warning("DOORS the tour: %d of Maniac's doors open as the guide set off, %d of Zak's clean doors, %d doors back on arrival; %d other Zak doors left as drawn",maniac,zak,zakBack,zakShut);

	// The player through a clean Zak door (the jail's, room 64, to 67): it
	// opens, and so does the door back on the other side.
	if (!scummverseTourZakRoom(64)) error("Cannot enter Zak's room 64");
	settle(3);
	if (open(732)) { putState(732,getState(732)&~kObjectStateIntrinsic); }
	runObjectScript(732,13,false,false,none); settle(3);
	if (_currentRoom!=67) error("The player's walk through door 732 went to room %d",_currentRoom);
	if (!open(734)) error("The door back in room 67 (734) shut");
	warning("DOORS the player through Zak's door: the door back open");
	// Nurse Edna's ladder (object 235) is drawn: the way up to room 20.
	if (!scummverseTourPlace(21,12,63)) error("Cannot enter Edna's room");
	settle(2);
	if (!(getState(235) & kObjectStateIntrinsic)) error("Edna's ladder not drawn: state %d",getState(235));
	warning("DOORS Edna's ladder drawn");
	warning("SCUMMVERSE_LIGHTS_DOORS_PASS enabled=1");
	quitGame();
	return;
