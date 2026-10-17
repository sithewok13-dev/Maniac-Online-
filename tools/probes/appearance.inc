	// Playing someone from another game, through the menu's request.
	if (!_scummverseRoaming) { warning("SCUMMVERSE_APPEARANCE_PASS enabled=0"); quitGame(); return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3; _scummverseRosterPending=false;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	using namespace ::Scummverse::WorldCatalog;
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	auto request=[&](int key) { scummverseWorldRequest(worldAppearanceRequest(key)); scummverseUpdateRoaming(0); settle(4); };
	auto shot=[&](const Common::String &name) {
		Common::DumpFile f; if(!f.open(Common::Path("/workspace/Maniac-Online/build/"+name))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); }
	};
	// Drawn height of a character from its exported frames (slots 192+).
	auto drawn=[&](Actor *a) {
		a->_needRedraw=true; settle(1);
		if (a->_top>=a->_bottom) return 0;
		int top=a->_bottom, bottom=a->_top;
		for(int y=a->_top;y<a->_bottom;++y) for(int x=0;x<_screenWidth;++x) if(*_virtscr[0].getPixels(x,y)>=192) { top=MIN(top,y); bottom=MAX(bottom,y+1); }
		return bottom>top ? bottom-top : 0;
	};
	Actor *dave=derefActor(3,"appearance player");
	const int indy=worldAppearanceKey(3,2), guybrush=worldAppearanceKey(0,1);
	if (!worldAppearance(indy) || strcmp(worldAppearance(indy)->name,"Indiana Jones") || !worldAppearance(guybrush)) error("Catalog keys changed");
	// In the mansion: Dave plays Indiana Jones, as tall as a teenager there.
	if (!scummverseTravel(2)) error("Cannot return to the mansion");
	settle(4);
	scummverseRosterOffer();
	static unsigned char daveFace[64*64*4]; memcpy(daveFace,FakeFaces::pixels[3],sizeof(daveFace));
	request(indy);
	// The character menu shows Indy's face for Dave.
	scummverseRosterOffer();
	{ int opaque=0; for(int i=0;i<64*64;++i) if(FakeFaces::pixels[3][i*4+3]) ++opaque;
	  if (opaque<300 || !memcmp(daveFace,FakeFaces::pixels[3],sizeof(daveFace))) error("Roster portrait not Indy's (%d pixels)",opaque); }
	if (_scummVars[kScummverseAppearanceVar+3]!=indy || FakeAI::appearance[3]!=indy) error("Appearance not set: var %d chat %d",_scummVars[kScummverseAppearanceVar+3],FakeAI::appearance[3]);
	if (strcmp((const char *)dave->getActorName(),"Indiana Jones")) error("Name is %s",(const char *)dave->getActorName());
	if (!_scummverseAvatarSprite[3]) error("Indy's frames not mounted in the mansion");
	{
		const int h=drawn(dave);
		if (ABS(h-72)>12) error("Indy drawn %d px tall in the mansion, expected about 72",h);
		shot("appearance-mansion.ppm");
		warning("APPEARANCE mansion height %d",h);
	}
	// Bernard plays Guybrush beside him: two characters share the slots.
	Actor *bernard=derefActor(5,"second player");
	bernard->putActor(dave->getRealPos().x+6,dave->getRealPos().y,_currentRoom); bernard->showActor();
	if (!scummverseSwitchActor(5)) error("Cannot switch to Bernard");
	request(guybrush);
	if (_scummVars[kScummverseAppearanceVar+5]!=guybrush || !_scummverseAvatarSprite[5] || !_scummverseAvatarSprite[3] || _scummverseAvatarSprite[3]==_scummverseAvatarSprite[5])
		error("Two characters not mounted together: %d %d",_scummverseAvatarSprite[3],_scummverseAvatarSprite[5]);
	if (drawn(bernard)<40) error("Guybrush not drawn");
	if (!scummverseSwitchActor(3)) error("Cannot switch back to Dave");
	// In other worlds: as tall as a person standing there, in his own game
	// (Last Crusade) and in another (Monkey Island).
	const int places[][2]={{3,6},{0,33}};
	for (const auto &place : places) {
		if (!scummverseTravelPlace(place[0],place[1])) error("Cannot visit %d:%d: %s",place[0],place[1],_scummverseWorldNotice.c_str());
		settle(8);
		if (!_scummverseAvatarSprite[3]) error("Indy's frames not mounted in %d:%d",place[0],place[1]);
		const double expected=kWorldGames[place[0]].heroHeight*::Scummverse::WorldBridge::sceneScale()*scummverseWorldDepth(dave);
		const int h=drawn(dave);
		if (ABS(h-expected)>MAX(4.0,expected*0.2)) error("Indy drawn %d px tall in %d:%d, expected about %.0f",h,place[0],place[1],expected);
		warning("APPEARANCE world %d:%d height %d expected %.0f",place[0],place[1],h,expected);
		shot(Common::String::format("appearance-%d-%d.ppm",place[0],place[1]));
		// The place's own characters are still there, except Indy himself, who
		// steps aside while Dave plays him (and is back once Dave is himself).
		for (int k=0;k<kScummverseGuestSlots;++k) {
			const WorldGuest *g=worldGuestAt(worldPlaceKey(place[0],place[1]),k);
			if (!g) continue;
			const bool same=worldAppearanceKey(place[0],g->costume)==indy;
			Actor *guest=derefActor(kScummverseGuestActor+k,"guest probe");
			if (same != (guest->_room!=_currentRoom)) error("Guest %s at %d:%d: in room %d while Dave plays Indy",g->name,place[0],place[1],guest->_room);
			if (same) {
				request(0); settle(2);
				if (guest->_room!=_currentRoom || _scummverseGuestSprite[k]<0) error("%s did not come back",g->name);
				request(indy); settle(2);
				if (guest->_room==_currentRoom) error("%s did not step aside again",g->name);
			}
		}
	}
	// Saved and loaded: still Indy, mounted again.
	{
		Common::String file; _saveLoadDescription="Playing Indy";
		if (!saveState(15,false,file) || !loadState(15,false)) error("Save failed");
		settle(4);
		if (_scummVars[kScummverseAppearanceVar+3]!=indy || strcmp((const char *)dave->getActorName(),"Indiana Jones") || !_scummverseAvatarSprite[3]) error("Appearance lost on load");
	}
	// Murray (Curse of Monkey Island's talking skull) floats above his feet,
	// bobbing, and keeps his standing pose while he moves.
	{
		const int murray=worldAppearanceKey(9,49);
		if (!worldAppearance(murray) || strcmp(worldAppearance(murray)->name,"Murray")) error("Murray's key changed");
		if (!scummverseTravel(2)) error("Cannot return to the mansion");
		settle(4);
		request(murray);
		if (!_scummverseAvatarSprite[3]) error("Murray's frames not mounted");
		dave->_needRedraw=true; settle(1);
		const int feet=dave->getPos().y-dave->getElevation();
		if (dave->_bottom>=feet-1) error("Murray does not float: drawn to %d, feet at %d",dave->_bottom,feet);
		int lowest=1000, highest=-1000;
		for (int n=0;n<80;++n) { dave->_needRedraw=true; settle(1); lowest=MIN(lowest,dave->_bottom); highest=MAX(highest,dave->_bottom); }
		if (highest-lowest<2) error("Murray does not bob (%d..%d)",lowest,highest);
		warning("APPEARANCE Murray floats %d..%d px above his feet",feet-highest,feet-lowest);
		request(indy);
	}
	// The Creator (The Dig) has one pose; in the mansion he stands as much
	// taller than a teenager as he does beside a person in his own game.
	{
		const int creator=worldAppearanceKey(8,321);
		if (!worldAppearance(creator) || strcmp(worldAppearance(creator)->name,"The Creator")) error("The Creator's key changed");
		if (scummverseCharacterFrames(8,321).empty()) warning("APPEARANCE no export of The Dig: The Creator skipped");
		else {
			if (!scummverseTravel(2)) error("Cannot return to the mansion");
			settle(4);
			request(creator);
			if (_scummVars[kScummverseAppearanceVar+3]!=creator || !_scummverseAvatarSprite[3] || strcmp((const char *)dave->getActorName(),"The Creator"))
				error("Not playing The Creator: %s",(const char *)dave->getActorName());
			const int h=drawn(dave), expected=90*72/kWorldGames[8].heroHeight;
			if (ABS(h-expected)>expected/5) error("The Creator drawn %d px tall, expected about %d",h,expected);
			warning("APPEARANCE The Creator height %d (expected %d)",h,expected);
			shot("appearance-creator.ppm");
		}
	}
	// The Purple Meteor (Maniac's own): Dave wears its costume, named and
	// chatting as it, floating with a bob, with no fishbowl on Mars, through
	// save/load and into another world; his own costume comes back after.
	{
		const int meteor=worldAppearanceKey(kWorldManiacLooks,16);
		if (!worldAppearance(meteor) || strcmp(worldAppearance(meteor)->name,"Purple Meteor")) error("The Meteor's key changed");
		if (!scummverseTravel(2)) error("Cannot return to the mansion");
		settle(4);
		request(meteor);
		if (_scummVars[kScummverseAppearanceVar+3]!=meteor || FakeAI::appearance[3]!=meteor || dave->_costume!=16 || _scummVars[kScummverseHomeCostumeVar+3]!=3 || _scummverseAvatarSprite[3])
			error("Not the Meteor: key %d chat %d costume %d home %d sprite %d",_scummVars[kScummverseAppearanceVar+3],FakeAI::appearance[3],dave->_costume,_scummVars[kScummverseHomeCostumeVar+3],_scummverseAvatarSprite[3]);
		if (strcmp((const char *)dave->getActorName(),"Purple Meteor")) error("Name is %s",(const char *)dave->getActorName());
		// In the Meteor's own colors (Maniac colors costumes by actor).
		if (scummverseColorActor(3)!=16) error("Dave as the Meteor wears actor %d's colors",scummverseColorActor(3));
		if (worldBreathes(kWorldManiacLooks,16)) error("The Meteor needs air");
		int lowest=1000, highest=-1000;
		for (int n=0;n<80;++n) { settle(1); lowest=MIN(lowest,dave->getElevation()); highest=MAX(highest,dave->getElevation()); }
		if (lowest<1 || highest-lowest<2) error("The Meteor does not hover and bob (%d..%d)",lowest,highest);
		if (dave->_top>=dave->_bottom) error("The Meteor is not drawn");
		warning("APPEARANCE Purple Meteor floats %d..%d px, drawn %d..%d",lowest,highest,dave->_top,dave->_bottom);
		shot("appearance-meteor.ppm");
		Common::String file; _saveLoadDescription="Playing the Meteor";
		if (!saveState(15,false,file) || !loadState(15,false)) error("Save failed");
		settle(4);
		if (_scummVars[kScummverseAppearanceVar+3]!=meteor || dave->_costume!=16 || strcmp((const char *)dave->getActorName(),"Purple Meteor")) error("The Meteor lost on load");
		if (!scummverseTravelPlace(0,33)) error("Cannot visit Melee Island");
		settle(8);
		dave->_needRedraw=true; settle(1);
		if (dave->_top>=dave->_bottom || dave->_bottom-dave->_top>40) error("The Meteor drawn %d..%d on Melee Island",dave->_top,dave->_bottom);
		shot("appearance-meteor-melee.ppm");
		request(0);
		if (dave->_costume!=3 || _scummVars[kScummverseHomeCostumeVar+3] || dave->getElevation() || scummverseColorActor(3)!=3 || strcmp((const char *)dave->getActorName(),"Dave"))
			error("Not Dave again: costume %d elevation %d",dave->_costume,dave->getElevation());
		request(indy);
	}
	// Unknown keys are refused; key 0 makes Dave himself again.
	request(worldAppearanceKey(3,999));
	if (_scummVars[kScummverseAppearanceVar+3]!=indy) error("Unknown character accepted");
	request(0);
	if (_scummVars[kScummverseAppearanceVar+3] || FakeAI::appearance[3] || _scummverseAvatarSprite[3] || strcmp((const char *)dave->getActorName(),"Dave")) error("Not Dave again: %s",(const char *)dave->getActorName());
	warning("SCUMMVERSE_APPEARANCE_PASS enabled=1");
	quitGame();
	return;
