	// Local WiFi play through the real engine: the engine hosts; a second
	// session in this process joins over loopback TCP as another device
	// playing Zak. Not two devices and not iPhone networking.
	if (!_scummverseRoaming) { warning("SCUMMVERSE_NET_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	if (!scummverseTravel(1) || !_scummVars[760] || !scummverseTravel(3) || _currentRoom!=53) error("Sandbox not ready");
	namespace N = ::Scummverse::Net;
	std::vector<N::Event> seen;
	N::Session device;
	auto pump=[&](int ticks) {
		for(int n=0;n<ticks;++n) {
			device.poll(seen); VAR(VAR_HAVE_MSG)=0; stopTalk(); scummverseUpdateRoaming(4); walkActors(); g_system->delayMillis(2);
		}
	};
	auto heard=[&](N::Event::Kind kind,int actor,const char *text) {
		for(const auto &e:seen) if(e.kind==kind && e.avatar.actor==actor && (!text || e.text==text)) return true;
		return false;
	};
	auto avatar=[](int actor,int room,int x,int y) { N::Avatar a; a.actor=actor; a.room=room; a.x=x; a.y=y; return a; };
	N::Request request; request.kind=N::Request::Host; N::postRequest(request); pump(1);
	if (!_scummverseNetOn || !::Scummverse::NetBridge::active() || N::online()==false) error("Engine did not host: %s",N::status().c_str());
	std::string problem;
	if (!device.join("127.0.0.1",scummverseNetContent(),24,problem)) error("Join failed: %s",problem.c_str());
	device.setLocal(avatar(24,53,20,60));
	Actor *zak=derefActor(24,"remote zak"), *me=derefActor(3,"local player");
	for(int n=0;n<200 && !(scummverseRemoteActor(24) && zak->_room==53 && heard(N::Event::Moved,3,nullptr));++n) pump(1);
	if (!scummverseRemoteActor(24) || zak->_room!=53 || !heard(N::Event::Moved,3,nullptr) || N::players()!=1)
		error("Remote player not shown: remote %d room %d heard %d players %d",scummverseRemoteActor(24),zak->_room,heard(N::Event::Moved,3,nullptr),N::players());
	// The remote character walks where its player walks; locals cannot take it.
	const Common::Point before=zak->getRealPos(); device.setLocal(avatar(24,53,before.x>=12 ? before.x-8 : before.x+8,60));
	bool walked=false; for(int n=0;n<200 && !walked;++n) { pump(1); walked=zak->getRealPos().x!=before.x; }
	if (!walked) error("Remote walk not applied");
	if (scummverseSwitchActor(24)) error("Switched to a character another player controls");
	_scummVars[794]=0; scummverseCompanionCommand(64+24); pump(4);
	if (_scummVars[794]) error("Remote player became a companion");
	// (From 0196) A room this device can't show: the character away from
	// every place here, still its player's. The local player's own
	// character is ignored.
	const Common::Point mine=me->getRealPos();
	device.setLocal(avatar(24,200,10,60)); pump(20);
	if (zak->_room!=0 || !scummverseRemoteActor(24) || scummverseSwitchActor(24)) error("A room not shown here: room %d remote %d",zak->_room,scummverseRemoteActor(24));
	device.setLocal(avatar(24,::Scummverse::NetBridge::worldPlace(0,1000),10,60)); pump(20);
	if (zak->_room!=0 || !scummverseRemoteActor(24)) error("A place not installed here: room %d remote %d",zak->_room,scummverseRemoteActor(24));
	device.setLocal(avatar(24,53,10,60)); for(int n=0;n<100 && zak->_room!=53;++n) pump(1);
	if (zak->_room!=53) error("Back from a place not shown here failed: %d",zak->_room);
	device.setLocal(avatar(3,1,10,60)); pump(20);
	if (me->_room!=53 || me->getRealPos()!=mine) error("Remote took the local player's character");
	// Speech both ways.
	device.setLocal(avatar(24,53,24,60)); pump(20);
	device.say("Hello from my phone");
	bool spoke=false; for(int n=0;n<200 && !spoke;++n) { device.poll(seen); scummverseUpdateRoaming(4); spoke=getTalkingActor()==24 && VAR(VAR_HAVE_MSG); g_system->delayMillis(2); }
	if (!spoke) error("Remote speech not shown");
	stopTalk(); VAR(VAR_HAVE_MSG)=0;
	request.kind=N::Request::Say; request.text="Hi Zak, welcome!"; N::postRequest(request); pump(1); stopTalk(); VAR(VAR_HAVE_MSG)=0;
	for(int n=0;n<200 && !heard(N::Event::Said,3,"Hi Zak, welcome!");++n) pump(1);
	if (!heard(N::Event::Said,3,"Hi Zak, welcome!")) error("Local speech not sent");
	// Another room: the remote character moves there without loading it here.
	device.setLocal(avatar(24,57,30,60)); for(int n=0;n<100 && zak->_room!=57;++n) pump(1);
	if (zak->_room!=57 || _currentRoom!=53) error("Remote room change failed: %d",zak->_room);
	// (From 0196) A place in another world: the remote character in this
	// device's own slot for it; the local player there sent as the place,
	// not as this device's slot room; a place not installed here: away.
	if (scummverseWorldSceneInstalled(0,33)) {
		namespace B = ::Scummverse::NetBridge;
		device.setLocal(avatar(24,B::worldPlace(0,33),20,60));
		int src=0; auto inPlace=[&]() { return scummverseWorldGameOf(zak->_room,src)==0 && src==33; };
		for(int n=0;n<100 && !inPlace();++n) pump(1);
		if (!inPlace() || _currentRoom!=53) error("Remote not in the other world's place here: room %d",zak->_room);
		const int slot=zak->_room;
		seen.clear();
		if (!scummverseTravelPlace(0,33) || _currentRoom!=slot) error("Local player not taken to the remote's place: %d",_currentRoom);
		bool sent=false;
		for(int n=0;n<200 && !sent;++n) { pump(1); for(const auto &e:seen) sent=sent || (e.kind==N::Event::Moved && e.avatar.actor==3 && e.avatar.room==B::worldPlace(0,33)); }
		if (!sent) error("The local player in another world not sent as the place");
		if (!zak->isInCurrentRoom()) error("The remote not here with the local player");
		device.setLocal(avatar(24,B::worldPlace(0,1000),20,60)); pump(20);
		if (zak->_room!=0 || !scummverseRemoteActor(24)) error("A place not installed here: room %d",zak->_room);
		device.setLocal(avatar(24,57,30,60)); for(int n=0;n<100 && zak->_room!=57;++n) pump(1);
		if (zak->_room!=57 || !scummverseTravel(3) || _currentRoom!=53) error("Back from the other world failed");
		warning("SCUMMVERSE net: Monkey Island 33 shared (slot %d)",slot);
	} else warning("SCUMMVERSE net: no other world installed; places not checked");
	// Leaving gives the character back to this world; from another world's
	// place, home (no slot kept by a character nobody plays).
	int fromSlot=0;
	if (scummverseWorldSceneInstalled(0,33)) {
		device.setLocal(avatar(24,::Scummverse::NetBridge::worldPlace(0,33),20,60));
		int src=0; for(int n=0;n<100 && !(scummverseWorldGameOf(zak->_room,src)==0 && src==33);++n) pump(1);
		if (scummverseWorldGameOf(zak->_room,src)!=0 || src!=33) error("Remote not back in the other world's place: %d",zak->_room);
		fromSlot=zak->_room;
	}
	device.close(); for(int n=0;n<200 && scummverseRemoteActor(24);++n) pump(1);
	if (scummverseRemoteActor(24) || N::players()!=0) error("Departed player not released");
	if (fromSlot && zak->_room!=53) error("Released character left in another world's slot: room %d",zak->_room);
	// A character nobody plays, left in another world's place out of sight,
	// goes home after a while.
	if (fromSlot) {
		zak->putActor(20,60,fromSlot); _scummverseRoamers[24]=Roamer();
		for(int n=0;n<200 && zak->_room!=53;++n) scummverseUpdateRoaming(4);
		if (zak->_room!=53) error("A character left in another world's slot not home: room %d",zak->_room);
		warning("SCUMMVERSE net: released from Monkey Island 33 and home; a stranded one home too");
	}
	if (!scummverseSwitchActor(24) || VAR(VAR_EGO)!=24 || !scummverseSwitchActor(3)) error("Released character not playable");
	request.kind=N::Request::Leave; N::postRequest(request); pump(1);
	if (_scummverseNetOn || ::Scummverse::NetBridge::active() || N::online()) error("Leave did not stop hosting");
	warning("SCUMMVERSE_NET_PASS enabled=1"); quitGame();
