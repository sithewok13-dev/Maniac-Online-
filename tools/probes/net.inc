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
	// Invalid rooms and the local player's own character are ignored.
	const Common::Point mine=me->getRealPos();
	device.setLocal(avatar(24,200,10,60)); pump(20);
	if (zak->_room!=53) error("Invalid room accepted");
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
	// Leaving gives the character back to this world.
	device.close(); for(int n=0;n<200 && scummverseRemoteActor(24);++n) pump(1);
	if (scummverseRemoteActor(24) || N::players()!=0) error("Departed player not released");
	if (!scummverseSwitchActor(24) || VAR(VAR_EGO)!=24 || !scummverseSwitchActor(3)) error("Released character not playable");
	request.kind=N::Request::Leave; N::postRequest(request); pump(1);
	if (_scummverseNetOn || ::Scummverse::NetBridge::active() || N::online()) error("Leave did not stop hosting");
	warning("SCUMMVERSE_NET_PASS enabled=1"); quitGame();
