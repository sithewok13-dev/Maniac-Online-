	// The character screen: a new sandbox game starts without the opening
	// (the boot has already run to the sandbox here, at the end of
	// runBootscript), shows a box per game with its lead first, and plays
	// whoever is chosen.
	if(!_scummverseRoaming) { warning("SCUMMVERSE_CAST_PASS enabled=0"); quitGame(); return; }
	using namespace ::Scummverse::WorldCatalog;
	if(!_scummverseRoamingReady) error("The opening still runs: the sandbox is not ready after the boot (room %d)",_currentRoom);
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	settle(4);
	if(FakeAI::castShown!=1) error("The character screen was shown %d times at the start",FakeAI::castShown);
	if(FakeAI::castGames!=2+worldGameCount()) error("%d boxes, expected %d",FakeAI::castGames,2+worldGameCount());
	if(FakeAI::castLead[0]!=kWorldCastActorRequest+3 || FakeAI::castLead[1]!=kWorldCastActorRequest+24)
		error("Leads: Maniac %d, Zak %d",FakeAI::castLead[0]-kWorldCastActorRequest,FakeAI::castLead[1]-kWorldCastActorRequest);
	int worlds=0;
	for(int game=0;game<worldGameCount();++game) {
		if(!FakeAI::castMembers[2+game]) continue;
		++worlds;
		int lead=-1; for(const auto &l : kWorldLeads) if(l.game==game) lead=l.costume;
		if(FakeAI::castLead[2+game]!=kWorldCastRequest+worldAppearanceKey(game,lead)) error("%s: lead request %d",kWorldGames[game].title,FakeAI::castLead[2+game]);
	}
	if(FakeAI::castFaces!=2+worlds || FakeAI::castMembers[0]<11 || FakeAI::castMembers[1]<2+(int)ARRAYSIZE(kWorldZakCast))
		error("Faces %d for %d games here; Maniac %d people, Zak %d",FakeAI::castFaces,2+worlds,FakeAI::castMembers[0],FakeAI::castMembers[1]);
	warning("CAST %d boxes, %d with faces; Maniac %d people, Zak %d",FakeAI::castGames,FakeAI::castFaces,FakeAI::castMembers[0],FakeAI::castMembers[1]);
	// Another game's lead: played, where they live.
	if(FakeAI::castMembers[2]) {
		scummverseWorldRequest(FakeAI::castLead[2]); scummverseUpdateRoaming(0); settle(2);
		int source; const int game=scummverseWorldGameOf(_currentRoom,source);
		if(scummverseAppearance(VAR(VAR_EGO))!=FakeAI::castLead[2]-kWorldCastRequest || game!=0 || source!=33)
			error("Guybrush not played on Melee Island: look %d, place %d:%d",scummverseAppearance(VAR(VAR_EGO)),game,source);
	}
	// A Maniac character, as themselves.
	scummverseWorldRequest(kWorldCastActorRequest+5); scummverseUpdateRoaming(0); settle(2);
	if(VAR(VAR_EGO)!=5 || scummverseAppearance(5)) error("Not Bernard as himself: ego %d look %d",VAR(VAR_EGO),scummverseAppearance(5));
	// "Play as someone else": the screen again.
	scummverseWorldRequest(61); scummverseUpdateRoaming(0);
	if(FakeAI::castShown!=2) error("Play as someone else did not show the character screen");
	// The game's own "New Kid" button: the screen too.
	_userPut=1; runInputScript(kVerbClickArea,7,0);
	if(FakeAI::castShown!=3) error("New Kid did not show the character screen");
	// Other worlds' Maniac Mansion and Zak McKracken: their places, each
	// named once, and going to one.
	{
		auto place=[&](const char *name) { for(int i=0;i<FakeAI::places && i<200;++i) if(!strcmp(FakeAI::placeName[i],name)) return FakeAI::placeRequest[i]; return 0; };
		scummverseWorldRequest(121); scummverseUpdateRoaming(0);
		if(FakeAI::placesShown!=1 || strcmp(FakeAI::placesTitle,"Maniac Mansion") || FakeAI::places<30 || !place("Kitchen") || !place("Front lawn"))
			error("Maniac Mansion's places: shown %d, %s, %d places",FakeAI::placesShown,FakeAI::placesTitle,FakeAI::places);
		const int maniacPlaces=FakeAI::places;
		scummverseWorldRequest(place("Kitchen")); scummverseUpdateRoaming(0); settle(2);
		if(_currentRoom!=7) error("The kitchen is not room 7 but %d",_currentRoom);
		scummverseWorldRequest(122); scummverseUpdateRoaming(0);
		if(FakeAI::placesShown!=2 || strcmp(FakeAI::placesTitle,"Zak McKracken") || FakeAI::places<40 || !place("Lou's Loans") || !place("Mars landing site") || !place("Sphinx maze") || place("Sphinx maze entrance")==place("Sphinx maze"))
			error("Zak's places: shown %d, %s, %d places",FakeAI::placesShown,FakeAI::placesTitle,FakeAI::places);
		for(int i=0;i<FakeAI::places;++i) for(int j=0;j<i;++j) if(!strcmp(FakeAI::placeName[i],FakeAI::placeName[j])) error("%s listed twice",FakeAI::placeName[i]);
		scummverseWorldRequest(place("Lou's Loans")); scummverseUpdateRoaming(0); settle(2);
		if(_currentRoom!=100) error("Lou's Loans is not room 100 but %d",_currentRoom);
		warning("CAST places: Maniac %d, Zak %d",maniacPlaces,FakeAI::places);
	}
	warning("SCUMMVERSE_CAST_PASS enabled=1");
	quitGame();
	return;
