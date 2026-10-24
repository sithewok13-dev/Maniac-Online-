	if (!_scummverseRoaming) { warning("SCUMMVERSE_SEATING_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;


 scummverseTravel(3);
 for(int id : {1,2,3,4,5,6,7,9,10,11,13,14,23,24,20,21,22,8,17,18}) if(id!=3) derefActor(id,"isolate roster")->putActor(0,0,0);
 Actor *zak=derefActor(24,"seated Zak");zak->putActor(20,60,53);_scummVars[794]=3;
 _scummVars[733]=7;scummverseBoard();
 int zakSeat=_scummVars[525], daveSeat=_scummVars[504];
 if(!scummverseSeated(24) || !scummverseSeated(3) || zakSeat==daveSeat) error("First party not seated");
 // Painted passengers: a chair a rider holds shows the empty chair (74)
 // in the background; chairs nobody holds keep their painted passenger.
 auto chair=[&](int seat) {
  setCameraAtEx(seat*8+16); _fullRedraw=true; stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(0);
  Common::Array<byte> cells; VirtScreen &vs=_virtscr[kMainVirtScreen];
  for(int y=48;y<96;++y) for(int x=0;x<40;++x) cells.push_back(*((byte *)vs.getBackPixels(seat*8-vs.xstart+x,y)));
  return cells;
 };
 static const int chairs[6]={63,52,41,30,19,74};
 // The seat and back as chair 74's; under the seat (the last tile row) the
 // painted chairs' black (chair 52's), not the wall 74 shows there.
 auto top=[&](const Common::Array<byte> &c) { return Common::Array<byte>(c.data(),40*40); };
 auto under=[&](const Common::Array<byte> &c) { return Common::Array<byte>(c.data()+40*40,40*8); };
 const Common::Array<byte> empty=top(chair(74)), black=under(chair(52));
 int painted=0;
 for(int slot=1;slot<=6;++slot) {
  if(chairs[slot-1]==63 || chairs[slot-1]==74) continue;
  const bool held=slot==zakSeat || slot==daveSeat;
  const Common::Array<byte> shown=chair(chairs[slot-1]);
  const bool shownEmpty=top(shown)==empty;
  if(held!=shownEmpty) error("Chair %d (slot %d) held=%d shown empty=%d",chairs[slot-1],slot,held,shownEmpty);
  if(held && under(shown)!=black) error("Chair %d (slot %d) shows the wall under its seat",chairs[slot-1],slot);
  if(!held) ++painted;
 }
 if(!painted) error("No painted passenger left to compare");
 warning("SEATING chairs held %d,%d painted kept %d",chairs[zakSeat-1],chairs[daveSeat-1],painted);
 // Four more local passengers join without changing existing reservations.
 for(int id : {20,21,22,23}) {
  derefActor(id,"joining rider")->putActor(20,60,53);
  if(!scummverseSwitchActor(id)) error("Cannot select joiner");
  _scummVars[ProbeCatalog::travellerDestinationKey(id)]=7;scummverseBoard();
  if(_currentRoom!=56 || !scummverseSeated(id)) error("Joiner not seated");
 }
 if(_scummVars[525]!=zakSeat || _scummVars[504]!=daveSeat) error("Joining reassigned seats");
 // Every held chair besides chair 52 itself (whose row is the black) shows
 // the black under its seat.
 int blackened=0;
 for(int id : {3,20,21,22,23,24}) {
  const int slot=_scummVars[501+id];
  if(slot<1 || slot>6 || chairs[slot-1]==63 || chairs[slot-1]==74 || chairs[slot-1]==52) continue;
  if(under(chair(chairs[slot-1]))!=black) error("Held chair %d shows the wall under its seat",chairs[slot-1]);
  ++blackened;
 }
 if(!blackened) error("No held chair to compare with the painted black");
 warning("SEATING black under %d more held chairs",blackened);
 unsigned used=0;
 for(int id : {3,20,21,22,23,24}) {
  int slot=_scummVars[501+id];
  Actor *a=derefActor(id,"seat pose");
  if(slot<1 || slot>6 || (used&(1u<<slot)) || a->getRealPos().y!=52 || a->getElevation()!=-4 || a->getFacing()!=90)
   error("Invalid or duplicate seat for %d slot=%d pose=%d,%d elev=%d facing=%d",id,slot,a->getRealPos().x,a->getRealPos().y,a->getElevation(),a->getFacing());
  used|=1u<<slot;
 }
 Actor *extra=derefActor(11,"seventh passenger");extra->putActor(20,60,53);
 scummverseSwitchActor(11);_scummVars[ProbeCatalog::travellerDestinationKey(11)]=7;
 unsigned manifest=_scummVars[725];scummverseBoard();
 if(_currentRoom!=53 || _scummVars[725]!=manifest || _scummVars[ProbeCatalog::travellerDestinationKey(11)]!=7)
  error("Full plane changed rejected booking");
 scummverseSwitchActor(24);
 _scummverseNpcDestination[11]=7;_scummverseNpcBoarding[11]=0;_scummverseRoamers[11].room=53;
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummverseUpdateRoaming(0);
 if(extra->_room!=53 || _scummVars[725]!=manifest) error("NPC overbooked flight");
 // Switching, saving and load preserve occupied chairs.
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 Common::String save;_saveLoadDescription="Six seated passengers";
 if(!saveState(10,false,save) || !loadState(10,false)) error("Seat persistence failed");
 if(_scummVars[525]!=zakSeat || _scummVars[504]!=daveSeat || !scummverseSeated(24)) error("Load moved reservations");
 for(int x : {200,504,664}) {
  setCameraAtEx(x);_fullRedraw=true;stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
  Common::DumpFile shot;
  if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/seated-%d.ppm",x)))) {
   Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
   for(int y=0;y<_virtscr[0].h;++y) for(int px=0;px<_screenWidth;++px) {byte c=*_virtscr[0].getPixels(px,y);shot.write(_currentPalette+3*c,3);}
  }
 }
 zak->startWalkActor(65,55,-1);
 if(scummverseSeated(24) || _scummVars[525]!=-zakSeat || zak->getElevation()) error("Cannot leave seat");
 // Standing up keeps the chair empty (no painted passenger appears in it).
 for(int i=0;i<40 && zak->_moving;++i) { stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(4); }
 if(top(chair(chairs[zakSeat-1]))!=empty) error("Painted passenger reappeared in chair %d after standing",chairs[zakSeat-1]);
 scummverseRestoreSeats();if(scummverseSeated(24)) error("Standing passenger reseated automatically");
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 if(!saveState(10,false,save) || !loadState(10,false) || _scummVars[525]!=-zakSeat || scummverseSeated(24))
  error("Standing reservation did not survive save/load");
 runObjectScript(753,11,false,false,nullptr);
 if(!scummverseSeated(24) || _scummVars[525]!=zakSeat) error("Use seat did not return to reservation");
 scummverseArrive();
 for(int id : {3,20,21,22,23,24}) if(derefActor(id,"landed rider")->_room!=57 || derefActor(id,"landed rider")->getElevation() || _scummVars[501+id]) error("Arrival left seating state");

 // Saves predating seat allocation acquire reservations without losing riders.
 scummverseTravel(6);_scummVars[724]=7;_scummVars[725]=1u<<24;_scummVars[727]=3;
 derefActor(3,"legacy owner")->putActor(40,55,56);
 zak->putActor(45,55,56);_scummVars[526]=0;
 scummverseRestoreSeats();
 if(!scummverseSeated(3) || !scummverseSeated(24)) error("Legacy seats not migrated");
 scummverseArrive();
 // Seven-person legacy flights remain intact; capacity never deletes a rider.
 scummverseTravel(6);_scummVars[724]=7;_scummVars[725]=0;_scummVars[727]=24;_scummVars[526]=0;
 for(int id : {3,5,20,21,22,23,24}) {
  derefActor(id,"legacy overflow")->putActor(30+id%6,55,56);_scummVars[725]|=1u<<id;
 }
 scummverseRestoreSeats();
 for(int id : {3,5,20,21,22,23,24}) if(derefActor(id,"legacy rider")->_room!=56 || _scummVars[501+id]) error("Legacy overflow lost rider");
 scummverseArrive();
 for(int id : {3,5,20,21,22,23,24}) if(derefActor(id,"legacy landing")->_room!=57) error("Legacy overflow arrival failed");
 // Everyone else rides seated: someone in the cabin without a chair walks
 // to a free one and sits; a walk does not stand a seated rider; a rider
 // the player stood up and left sits again; a look keeps them in the chair.
 {
  const int everyone[]={1,2,3,4,5,6,7,9,10,11,13,14,23,24,20,21,22,8,17,18};
  scummverseTravel(6);
  for(int id : everyone) derefActor(id,"clear cabin")->putActor(0,0,0);
  for(int n=1;n<25;++n) _scummVars[501+n]=0;
  _scummVars[724]=7;_scummVars[725]=1u<<9;_scummVars[727]=9;_scummVars[526]=1;_scummVars[510]=1;
  Actor *fred=derefActor(9,"seated player");fred->putActor(63,52,56);
  VAR(VAR_EGO)=9;_scummverseLastEgo=9;scummverseRestoreSeats();
  Actor *annie=derefActor(20,"late rider");annie->putActor(20,60,56);_scummVars[770+20]=9;
  auto ride=[&](int steps) { for(int i=0;i<steps && !scummverseSeated(20);++i) { stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(4); } };
  ride(400);
  if(!scummverseSeated(20) || annie->getElevation()!=-4 || annie->getRealPos().y!=52 || _scummVars[521]==1)
   error("Late rider not seated: seat %d at %d,%d elevation %d",_scummVars[521],annie->getRealPos().x,annie->getRealPos().y,annie->getElevation());
  const int annieSeat=_scummVars[521];
  annie->startWalkActor(30,60,-1);
  if(!scummverseSeated(20) || annie->_moving) error("A walk stood up a seated rider");
  if(!scummverseSwitchActor(20)) error("Cannot play the rider");
  annie->startWalkActor(30,60,-1);
  if(scummverseSeated(20)) error("The player could not stand up");
  for(int i=0;i<40 && annie->_moving;++i) { stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(4); }
  if(!scummverseSwitchActor(9)) error("Cannot play Dr Fred again");
  ride(400);
  if(!scummverseSeated(20) || _scummVars[521]!=annieSeat || annie->getRealPos().y!=52) error("Rider left standing did not sit again");
  if(!scummverseSetAppearance(20,::Scummverse::WorldCatalog::worldAppearanceKey(::Scummverse::WorldCatalog::kWorldManiacLooks,19))) error("No plant look");
  for(int i=0;i<4;++i) { stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(4); }
  if(!scummverseSeated(20) || annie->getElevation()!=-4) error("The plant rolls out of the seat: elevation %d",annie->getElevation());
  scummverseSetAppearance(20,0);
  warning("SEATING late rider walked to seat %d and sat",annieSeat);
  scummverseArrive();
 }
 // Every available source costume can be seated and rendered in isolation.
 const int cast[]={1,2,3,4,5,6,7,9,10,11,13,14,23,24,20,21,22,8,17,18};
 scummverseTravel(6);
 for(int id : cast) derefActor(id,"clear cabin")->putActor(0,0,0);
 for(int id : cast) {
  for(int n=1;n<25;++n) _scummVars[501+n]=0;
  _scummVars[724]=7;_scummVars[725]=1u<<id;_scummVars[727]=id;
  Actor *a=derefActor(id,"cast seating");a->putActor(63,52,56);
  VAR(VAR_EGO)=id;_scummverseLastEgo=id;_scummVars[501+id]=1;_scummVars[526]=1;
  scummverseRestoreSeats();setCameraFollows(a);setCameraAtEx(504);
  stopTalk();VAR(VAR_HAVE_MSG)=0;_fullRedraw=true;scummLoop(0);
  if(!a->_visible || a->_bottom<=a->_top || a->getElevation()!=-4) error("Cast seating failed %d",id);
  Common::DumpFile shot;
  if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/seated-cast-%d.ppm",id)))) {
   Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
   for(int y=0;y<_virtscr[0].h;++y) for(int px=0;px<_screenWidth;++px) {byte c=*_virtscr[0].getPixels(px,y);shot.write(_currentPalette+3*c,3);}
  }
  a->putActor(0,0,0);
 }
 warning("SCUMMVERSE_SEATING_PASS enabled=1");quitGame();
