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
	// (From 0197) Zak plays the Meteor Police before his player comes: kept
	// for him while they play him, his again when they leave.
	namespace C = ::Scummverse::WorldCatalog;
	const int zakHome=derefActor(24,"zak's own")->_costume, police=C::worldAppearanceKey(C::kWorldManiacLooks,15);
	if (!scummverseSetAppearance(24,police)) error("Zak's own look refused");
	if (!device.join("127.0.0.1",scummverseNetContent(),24,problem)) error("Join failed: %s",problem.c_str());
	device.setLocal(avatar(24,53,20,60));
	Actor *zak=derefActor(24,"remote zak"), *me=derefActor(3,"local player");
	for(int n=0;n<200 && !(scummverseRemoteActor(24) && zak->_room==53 && heard(N::Event::Moved,3,nullptr) && !scummverseAppearance(24));++n) pump(1);
	if (scummverseAppearance(24) || zak->_costume!=zakHome || _scummverseRemoteLookBefore[24]!=police+1) error("Zak's player's own look (none) not shown, his kept: %d %d",scummverseAppearance(24),_scummverseRemoteLookBefore[24]);
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
	// (From 0209) A player taking a character this device refuses (not one
	// of the cast here) gives back the one they played at once.
	device.setLocal(avatar(12,53,10,60)); pump(20);
	if (scummverseRemoteActor(24) || scummverseRemoteActor(12)) error("A refused character kept another claimed: Zak %d, 12 %d",scummverseRemoteActor(24),scummverseRemoteActor(12));
	device.setLocal(avatar(24,53,10,60)); for(int n=0;n<100 && !(scummverseRemoteActor(24) && zak->_room==53);++n) pump(1);
	if (!scummverseRemoteActor(24)) error("Zak not taken again");
	// (From 0209) Taking the local player's own character: refused and
	// closed by this host; Zak is everyone's again, until they join again.
	device.setLocal(avatar(3,1,10,60)); pump(20);
	if (me->_room!=53 || me->getRealPos()!=mine) error("Remote took the local player's character");
	if (device.active() || scummverseRemoteActor(24)) error("Taking the local player's character not refused: active %d remote %d",device.active(),scummverseRemoteActor(24));
	if (!device.join("127.0.0.1",scummverseNetContent(),24,problem)) error("Join again failed: %s",problem.c_str());
	device.setLocal(avatar(24,53,24,60)); for(int n=0;n<200 && !(scummverseRemoteActor(24) && zak->_room==53);++n) pump(1);
	if (!scummverseRemoteActor(24) || zak->_room!=53 || scummverseAppearance(24) || _scummverseRemoteLookBefore[24]!=police+1) error("Joined again: remote %d room %d look %d",scummverseRemoteActor(24),zak->_room,scummverseAppearance(24));
	// (patch 0221) The engine away longer than the silence limit (as in
	// ScummVM's menu: paused, no updates; real time, as a menu is) while
	// Zak's player walks on: nobody dropped, the session's own thread
	// answering for it; back, Zak goes where his player is now.
	{
		seen.clear();
		const int to=zak->getRealPos().x>=40 ? zak->getRealPos().x-16 : zak->getRealPos().x+16;
		{
			PauseToken paused=pauseEngine();
			const uint32 start=g_system->getMillis();
			bool walked=false;
			while (g_system->getMillis()-start<(uint32)(N::kSilentMs+3000)) {
				device.poll(seen);
				if (!walked && g_system->getMillis()-start>(uint32)N::kSilentMs/2) { device.setLocal(avatar(24,53,to,60)); walked=true; }
				g_system->delayMillis(10);
			}
		}
		for(const auto &e:seen) if (e.kind==N::Event::Failed || e.kind==N::Event::Left) error("The engine away: the device lost the game (%s)",e.kind==N::Event::Failed ? e.text.c_str() : "a player left");
		if (!device.connected() || !_scummverseNetOn) error("The engine away: dropped (device %d, net %d)",device.connected(),_scummverseNetOn);
		const int reach=zak->adjustXYToBeInBox(to,60).x;
		for(int n=0;n<300 && (zak->_moving || zak->getRealPos().x!=reach);++n) pump(1);
		if (!scummverseRemoteActor(24) || zak->getRealPos().x!=reach || N::players()!=1 || !N::online())
			error("The engine away: Zak at %d, not %d (remote %d, players %d)",zak->getRealPos().x,reach,scummverseRemoteActor(24),N::players());
		// The device away as long (its own menu; session time moved on, its
		// keeper's polls only): the engine keeps Zak.
		seen.clear();
		for(int t=0;t<2*N::kSilentMs;t+=N::kPingMs/2) {
			N::advanceClockForTests(N::kPingMs/2);
			const int polls=device.keeperPollsForTests();
			for(int n=0;n<1000 && device.keeperPollsForTests()<=polls;++n) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummverseUpdateRoaming(4); walkActors(); g_system->delayMillis(2); }
			if (device.keeperPollsForTests()<=polls) error("The device's keeper never polled");
		}
		pump(4);
		for(const auto &e:seen) if (e.kind==N::Event::Failed || e.kind==N::Event::Left) error("The device away: it lost the game (%s)",e.kind==N::Event::Failed ? e.text.c_str() : "a player left");
		if (!scummverseRemoteActor(24) || !device.connected() || N::players()!=1)
			error("The device away: Zak dropped (remote %d, device %d, players %d)",scummverseRemoteActor(24),device.connected(),N::players());
		warning("SCUMMVERSE net: the engine away %d ms (paused) and the device away %d ms: nobody dropped; Zak walked on",N::kSilentMs+3000,2*N::kSilentMs);
	}
	// Speech both ways.
	device.setLocal(avatar(24,53,24,60)); pump(20);
	device.say("Hello from my phone");
	bool spoke=false; for(int n=0;n<200 && !spoke;++n) { device.poll(seen); scummverseUpdateRoaming(4); spoke=getTalkingActor()==24 && VAR(VAR_HAVE_MSG); g_system->delayMillis(2); }
	if (!spoke) error("Remote speech not shown");
	stopTalk(); VAR(VAR_HAVE_MSG)=0;
	request.kind=N::Request::Say; request.text="Hi Zak, welcome!"; N::postRequest(request); pump(1); stopTalk(); VAR(VAR_HAVE_MSG)=0;
	for(int n=0;n<200 && !heard(N::Event::Said,3,"Hi Zak, welcome!");++n) pump(1);
	if (!heard(N::Event::Said,3,"Hi Zak, welcome!")) error("Local speech not sent");
	// (From 0209) Lines wait their turn: a friend's while another shows and
	// while the local player has no control (a cutscene); the local
	// player's while another shows. Then each is shown (and sent).
	{
		auto ticks=[&](int n,bool quiet) { for(int i=0;i<n;++i) { if(quiet && getTalkingActor()!=24 && getTalkingActor()!=3) { stopTalk(); VAR(VAR_HAVE_MSG)=0; } device.poll(seen); scummverseUpdateRoaming(4); g_system->delayMillis(2); } };
		stopTalk(); VAR(VAR_HAVE_MSG)=0;
		scummverseSay(3,"One moment, please."); device.say("Wait for me"); ticks(20,false);
		if (getTalkingActor()!=3) error("A friend's line cut into another: %d",getTalkingActor());
		_userPut=0; stopTalk(); VAR(VAR_HAVE_MSG)=0; ticks(20,true);
		if (getTalkingActor()==24) error("A friend's line shown without control");
		_userPut=1; ticks(1,true);
		if (getTalkingActor()!=24 || !VAR(VAR_HAVE_MSG)) error("A friend's waiting line not shown: %d",getTalkingActor());
		seen.clear(); request.kind=N::Request::Say; request.text="After you"; N::postRequest(request); ticks(20,false);
		if (getTalkingActor()!=24 || heard(N::Event::Said,3,"After you")) error("The local player's line cut into another: %d",getTalkingActor());
		stopTalk(); VAR(VAR_HAVE_MSG)=0; ticks(1,true);
		if (getTalkingActor()!=3) error("The local player's waiting line not said: %d",getTalkingActor());
		for(int n=0;n<100 && !heard(N::Event::Said,3,"After you");++n) ticks(1,true);
		if (!heard(N::Event::Said,3,"After you")) error("The local player's waiting line not sent");
		stopTalk(); VAR(VAR_HAVE_MSG)=0;
		// (Five seconds, then dropped.)
		scummverseSay(3,"A long story."); device.say("Too late"); ticks(90,false);
		stopTalk(); VAR(VAR_HAVE_MSG)=0; ticks(2,true);
		if (getTalkingActor()==24) error("A friend's line shown after waiting too long");
		warning("SCUMMVERSE net: lines wait their turn (a friend's over another and a cutscene, the local player's), and no longer than five seconds");
	}
	// (From 0197) The look a player plays: theirs shown here, where this
	// device has it, without the local player's notice; one it hasn't (a
	// custom character, the new engine's own): the character itself. Saves
	// keep the character's own look; the local player's look is sent.
	{
		const int ted=C::worldAppearanceKey(C::kWorldManiacLooks,12), crispy=C::worldAppearanceKey(C::kWorldCustomLooks,1);
		auto looked=[&](int look) { N::Avatar a=avatar(24,53,24,60); a.look=look; return a; };
		_scummverseWorldNotice.clear();
		device.setLocal(looked(ted)); for(int n=0;n<100 && scummverseAppearance(24)!=ted;++n) pump(1);
		if (scummverseAppearance(24)!=ted || zak->_costume!=12 || !_scummverseWorldNotice.empty()) error("Remote look not shown quietly: %d '%s'",scummverseAppearance(24),_scummverseWorldNotice.c_str());
		scummverseRemoteLooksSaved(true);
		if (scummverseAppearance(24)!=police || _scummVars[kScummverseAppearanceVar+24]!=police || zak->_costume!=15) error("A save would keep the remote player's look");
		scummverseRemoteLooksSaved(false);
		if (scummverseAppearance(24)!=ted || zak->_costume!=12) error("Remote look not back after saving");
		// A real save and load (this probe's own save folder): the save holds
		// Zak's own look; loaded, the player's look goes back on.
		// (The cursor as the game's start sets it: this probe stops the
		// game's scripts before they do, and a load restores it.)
		// Saved while Zak walks (his player's last frame on its way): he
		// goes on there, though his costume changed twice for the save.
		Common::String file; setBuiltinCursor(0);
		const int start=zak->getRealPos().x, goal=start>40 ? start-24 : start+24;
		N::Avatar walking=looked(ted); walking.x=goal; device.setLocal(walking);
		for(int n=0;n<100 && !zak->_moving;++n) { device.poll(seen); scummverseUpdateRoaming(4); g_system->delayMillis(2); }
		if (!zak->_moving) error("Remote walk for the save not begun");
		// (From 0209: the save also has him as the local player's companion.)
		_scummVars[794]=VAR(VAR_EGO);
		const bool saved=saveState(98,false,file);
		_scummVars[794]=0;
		if (!saved || scummverseAppearance(24)!=ted) error("Saving lost the remote look: %d",scummverseAppearance(24));
		const int reach=zak->adjustXYToBeInBox(goal,60).x; // (where the walk can end)
		for(int n=0;n<300 && (zak->_moving || zak->getRealPos().x!=reach);++n) pump(1);
		if (zak->getRealPos().x!=reach || reach==start) error("A save stopped the remote walk: at %d, sent to %d",zak->getRealPos().x,reach);
		// (From 0209) His player walks on to another room before the load:
		// loaded, he is there, not where the save had him, and no one's
		// companion.
		N::Avatar on=looked(ted); on.room=57; on.x=30; device.setLocal(on);
		for(int n=0;n<100 && zak->_room!=57;++n) pump(1);
		if (zak->_room!=57) error("Remote room change before the load failed: %d",zak->_room);
		if (!loadState(98,false) || scummverseAppearance(24)!=ted || zak->_costume!=12 || _scummverseRemoteLookBefore[24]!=police+1 || !scummverseRemoteActor(24))
			error("After loading: look %d, kept %d",scummverseAppearance(24),_scummverseRemoteLookBefore[24]);
		if (_currentRoom!=53 || zak->_room!=57 || zak->getRealPos().x!=30 || _scummVars[794]) error("After loading: room %d at %d, companion of %d",zak->_room,zak->getRealPos().x,_scummVars[794]);
		// One of Monkey Island's people, where that game's characters are
		// exported here (drawn from their own frames).
		bool islander=false;
		for (int costume=1; costume<200 && !islander; ++costume) {
			const int key=C::worldAppearanceKey(0,costume);
			if (!C::worldAppearance(key) || C::worldNativeLook(key) || !scummverseCharacterInstalled(0,costume)) continue;
			device.setLocal(looked(key)); for(int n=0;n<100 && scummverseAppearance(24)!=key;++n) pump(1);
			if (scummverseAppearance(24)!=key || !_scummverseWorldNotice.empty()) error("Remote Monkey Island look not shown: %d",scummverseAppearance(24));
			islander=true;
		}
		if (!islander) warning("SCUMMVERSE net: no Monkey Island characters exported; that look not checked");
		device.setLocal(looked(crispy)); pump(20);
		if (scummverseAppearance(24) || _scummverseRemoteLook[24]!=crispy) error("A look not here not shown as the character itself: %d",scummverseAppearance(24));
		device.setLocal(looked(0)); pump(20);
		if (scummverseAppearance(24) || zak->_costume!=zakHome) error("Zak himself again not shown: %d",scummverseAppearance(24));
		seen.clear();
		if (!scummverseSetAppearance(3,police)) error("Local look refused");
		bool sentLook=false; for(int n=0;n<200 && !sentLook;++n) { pump(1); for(const auto &e:seen) sentLook=sentLook || (e.kind==N::Event::Moved && e.avatar.actor==3 && e.avatar.look==police); }
		if (!sentLook || !scummverseSetAppearance(3,0)) error("The local player's look not sent");
		_scummverseWorldNotice.clear();
		warning("SCUMMVERSE net: looks relayed (Ted%s shown, Crispy as Zak, the local player's sent; saved and loaded)",islander?" and a Monkey Island look":"");
	}
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
	if (scummverseAppearance(24)!=police || zak->_costume!=15 || !scummverseSetAppearance(24,0) || zak->_costume!=zakHome) error("Released character's own look not back: %d",scummverseAppearance(24));
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
