	// Wanderers: every other game's character out, anywhere, shown where it
	// is; the mansion's and Zak's people out of their own game's places;
	// never two of one person (by name: another game's of the same name).
	if (!_scummverseRoaming) { warning("SCUMMVERSE_WANDER_PASS enabled=0"); quitGame(); return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3; _scummverseRosterPending=false;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	using namespace ::Scummverse::WorldCatalog;
	namespace W = ::Scummverse::Wander;
	namespace WB = ::Scummverse::WanderBridge;
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); _scummverseVisitorQuiet=60000; scummLoop(4); } };
	auto shot=[&](const Common::String &name) {
		Common::DumpFile f; if(!f.open(Common::Path("/workspace/Maniac-Online/build/"+name))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); }
	};
	auto visitor=[&](int key) { for (int s=0;s<kScummverseVisitorSlots;++s) if (_scummverseVisitors[s].who==key) return s; return -1; };
	auto shownHere=[&]() { int n=0; for (const ScummverseVisitor &v : _scummverseVisitors) n+=v.who && v.sprite && v.actor && v.actor->_room==_currentRoom && v.actor->_visible; return n; };
	auto name=[&](int key) { return worldAppearance(key) ? worldAppearance(key)->name : "?"; };
	auto pixelsOf=[&](const ScummverseVisitor &v) {
		int mine=0;
		for (int y=v.drawn.top;y<v.drawn.bottom;++y) for (int x=v.drawn.left;x<v.drawn.right;++x) {
			const int sx=x-_virtscr[0].xstart;
			if (sx>=0 && sx<_screenWidth && *_virtscr[0].getPixels(sx,y)>=MAX(16,::Scummverse::WorldBridge::guestFirstSlot())) ++mine;
		}
		return mine;
	};
	if (!scummverseTravel(2)) error("Cannot return to the mansion");
	settle(4);
	// Everyone out: every installed character somewhere, anywhere at all
	// (every game an equal share), all over the place; the mansion's and
	// Zak's people too, but never in their own game's places (their own
	// actors are there); the mansion's kids (the party) never.
	int mm=-1, zk=-1;
	for (int g=0;g<worldGameCount();++g) { if (sameId(kWorldGames[g].gameid,"maniac")) mm=g; if (sameId(kWorldGames[g].gameid,"zak")) zk=g; }
	Common::Array<int> keys;
	int homeFolk=0;
	for (const auto &c : kWorldCast) {
		const int key=worldAppearanceKey(c.game,c.guest.costume);
		if (worldManiacKid(c.game,c.guest.costume)) { if (WB::where(key)) error("%s, a kid, is out",name(key)); continue; }
		if (scummverseCharacterInstalled(c.game,c.guest.costume) && Common::find(keys.begin(),keys.end(),key)==keys.end()) { keys.push_back(key); homeFolk+=worldHome(c.game); }
	}
	if (WB::places()<60 || WB::cast()!=(int)keys.size() || keys.size()<100) error("Wanderers' world: %d places, %d characters of %d",WB::places(),WB::cast(),(int)keys.size());
	if (homeFolk<20) error("Only %d of the mansion's and Zak's people out",homeFolk);
	auto ownPlace=[&](int key, int at) {
		const int g=worldAppearanceGame(key);
		return g==mm ? W::placeKind(at)==W::kManiac : g==zk ? W::placeKind(at)==W::kZak : W::placeKind(at)==W::kWorld && W::placeGame(at)==g;
	};
	auto noneHome=[&](const char *when) {
		for (int key : keys) if (worldHome(worldAppearanceGame(key)) && ownPlace(key,WB::where(key))) error("%s in their own game's places (%s)",name(key),when);
	};
	{
		int own=0, maniac=0, zak=0, visiting=0; bool game[16]={};
		for (int key : keys) {
			const int at=WB::where(key);
			if (!at || !scummverseWandering(key)) error("%s is not out",name(key));
			own+=ownPlace(key,at);
			maniac+=W::placeKind(at)==W::kManiac; zak+=W::placeKind(at)==W::kZak;
			visiting+=worldHome(worldAppearanceGame(key)) && W::placeKind(at)==W::kWorld;
			game[W::placeKind(at)==W::kWorld ? 2+W::placeGame(at) : W::placeKind(at)]=true;
		}
		int games=0; for (bool g : game) games+=g;
		warning("WANDER %d places, %d out (%d the mansion's and Zak's, %d of them in the other games): %d in their own game, %d in the mansion, %d in Zak's places, in %d games",
			WB::places(),(int)keys.size(),homeFolk,visiting,own,maniac,zak,games);
		if (own*3>(int)keys.size() || games<11 || !visiting) error("Not all over the place: %d of %d in their own game, %d games",own,(int)keys.size(),games);
		noneHome("setting out");
	}
	// Saved in the game's variables: the cast's signature and everyone's place.
	if ((uint32)_scummVars[kScummverseWanderVar]!=WB::signature() || !_scummVars[257]) error("Wanderers not saved in the variables");
	const int guybrush=worldAppearanceKey(0,1), living=W::placeCode(W::kManiac,0,3);
	if (Common::find(keys.begin(),keys.end(),guybrush)==keys.end()) error("Guybrush not exported");
	// Guybrush's home (Monkey Island 33) shows none of its own characters at
	// home: they are out (some may be visiting).
	if (!scummverseTravelPlace(0,33)) error("Cannot visit Monkey Island: %s",_scummverseWorldNotice.c_str());
	settle(8);
	for (int k=0;k<kScummverseGuestSlots;++k)
		if (derefActor(kScummverseGuestActor+k,"wander home")->_room==_currentRoom) error("A resident at home in Monkey Island 33 while everyone is out");
	shot("wander-home.ppm");
	// Nurse Edna and Lou visit Monkey Island, drawn from their own frames; one
	// steps aside while someone here plays them (the Purple Meteor's look),
	// or while their own actor is here (Edna's).
	{
		const int place=W::placeCode(W::kWorld,0,33), edna=worldAppearanceKey(mm,10), lou=worldAppearanceKey(zk,16), meteor=worldAppearanceKey(mm,16);
		for (int key : {edna,lou,meteor}) if (Common::find(keys.begin(),keys.end(),key)==keys.end()) error("%s not among the wanderers",name(key));
		int there[64]; const int n=MIN(64,WB::at(place,there,64));
		for (int i=0;i<n;++i) WB::send(there[i],W::placeCode(worldAppearanceGame(there[i])==mm ? W::kZak : W::kManiac,0,worldAppearanceGame(there[i])==mm ? 55 : 1));
		WB::send(edna,place); WB::send(lou,place);
		settle(8);
		Actor *dave=derefActor(3,"wander visit");
		for (int key : {edna,lou}) {
			const int s=visitor(key);
			if (s<0) error("%s not visiting Monkey Island",name(key));
			Actor *a=_scummverseVisitors[s].actor;
			const AdjustBoxResult p=a->adjustXYToBeInBox(dave->getRealPos().x+(key==edna?-5:5),dave->getRealPos().y);
			a->stopActorMoving(); a->putActor(p.x,p.y,_currentRoom);
		}
		settle(3);
		for (int key : {edna,lou}) {
			const ScummverseVisitor &v=_scummverseVisitors[visitor(key)];
			if (!v.sprite || v.drawn.isEmpty() || pixelsOf(v)<60) error("%s not drawn in Monkey Island (%d pixels)",name(key),pixelsOf(v));
		}
		shot("wander-home-folk.ppm");
		if (!scummverseSetAppearance(3,worldAppearanceKey(kWorldManiacLooks,16))) error("Cannot play the Purple Meteor: %s",_scummverseWorldNotice.c_str());
		WB::send(meteor,place); settle(4);
		if (visitor(meteor)<0 || _scummverseVisitors[visitor(meteor)].sprite) error("The visiting Purple Meteor does not step aside for the one played");
		scummverseSetAppearance(3,0); settle(4);
		if (visitor(meteor)<0 || !_scummverseVisitors[visitor(meteor)].sprite) error("The visiting Purple Meteor not back once nobody plays it");
		int ednaActor=0;
		for (int id=1;id<kScummverseManiacActors && !ednaActor;++id) if (id!=3 && _actors[id]->_costume==10) ednaActor=id;
		if (ednaActor) {
			Actor *e=_actors[ednaActor]; const int room=e->_room; const Common::Point at=e->getRealPos();
			e->putActor(dave->getRealPos().x+12,dave->getRealPos().y,_currentRoom); settle(4);
			if (_scummverseVisitors[visitor(edna)].sprite) error("The visiting Edna does not step aside for her own actor");
			e->putActor(at.x,at.y,room); settle(4);
			if (!_scummverseVisitors[visitor(edna)].sprite) error("The visiting Edna not back once her actor left");
		}
		warning("WANDER Monkey Island: Nurse Edna and Lou visiting; the Purple Meteor stepped aside%s",ednaActor?", Edna for her actor":"");
		// Zak's people known by their costumes (Zak's own numbers), not their
		// names: Lou steps aside while Dave plays Lou; the Zaire shaman while
		// he plays the Zaire villager (one costume of Zak's, two names); Zak
		// while Zak's own actor is here.
		for (int key : {edna,meteor}) WB::send(key,W::placeCode(W::kZak,0,55));
		if (!scummverseSetAppearance(3,worldAppearanceKey(kWorldZakLooks,44))) error("Cannot play Lou: %s",_scummverseWorldNotice.c_str());
		settle(4);
		if (visitor(lou)<0 || _scummverseVisitors[visitor(lou)].sprite) error("The visiting Lou does not step aside for the one played");
		scummverseSetAppearance(3,0); settle(4);
		if (visitor(lou)<0 || !_scummverseVisitors[visitor(lou)].sprite) error("The visiting Lou not back once nobody plays him");
		Common::String zakFolk;
		const int shaman=worldAppearanceKey(zk,21), zakKey=worldAppearanceKey(zk,1);
		if (Common::find(keys.begin(),keys.end(),shaman)!=keys.end()) {
			if (!scummverseSetAppearance(3,worldAppearanceKey(kWorldZakLooks,41))) error("Cannot play the Zaire villager: %s",_scummverseWorldNotice.c_str());
			WB::send(shaman,place); settle(4);
			if (visitor(shaman)<0 || _scummverseVisitors[visitor(shaman)].sprite) error("The visiting Zaire shaman does not step aside for the Zaire villager played");
			scummverseSetAppearance(3,0); settle(4);
			if (visitor(shaman)<0 || !_scummverseVisitors[visitor(shaman)].sprite) error("The visiting Zaire shaman not back once nobody plays the villager");
			WB::send(shaman,W::placeCode(W::kManiac,0,1)); zakFolk+=", the Zaire shaman for the villager";
		}
		Actor *zak=_actors[24];
		if (Common::find(keys.begin(),keys.end(),zakKey)!=keys.end() && _scummVars[760] && zak->_costume==34) {
			const int room=zak->_room; const Common::Point at=zak->getRealPos();
			WB::send(zakKey,place); settle(4);
			if (visitor(zakKey)<0 || !_scummverseVisitors[visitor(zakKey)].sprite) error("The visiting Zak not drawn before his actor came");
			zak->putActor(dave->getRealPos().x+12,dave->getRealPos().y,_currentRoom); settle(4);
			if (visitor(zakKey)<0 || _scummverseVisitors[visitor(zakKey)].sprite) error("The visiting Zak does not step aside for his own actor");
			zak->putActor(at.x,at.y,room); settle(4);
			if (visitor(zakKey)<0 || !_scummverseVisitors[visitor(zakKey)].sprite) error("The visiting Zak not back once his actor left");
			WB::send(zakKey,W::placeCode(W::kManiac,0,1)); zakFolk+=", Zak for his actor";
		}
		warning("WANDER Monkey Island: Lou stepped aside for the one played%s",zakFolk.c_str());
	}
	// Guybrush and two more in the living room (nobody else there; none the
	// same person as another: Monkey Island 2's Guybrush is not taken).
	int four[4]={guybrush,0,0,0};
	for (int i=1, k=0; i<4 && k<(int)keys.size(); ++k) {
		bool twin=false;
		for (int j=0;j<i;++j) twin=twin || WB::twins(keys[k],four[j]);
		if (keys[k]!=guybrush && !twin && !WB::small(keys[k]) && worldAppearanceGame(keys[k])!=worldAppearanceGame(four[i-1]) && worldAppearanceGame(keys[k])!=mm) four[i++]=keys[k];
	}
	{
		int there[64]; const int n=MIN(64,WB::at(living,there,64));
		for (int i=0;i<n;++i) WB::send(there[i],W::placeCode(W::kManiac,0,1));
		for (int i=0;i<3;++i) WB::send(four[i],living);
	}
	if (!scummverseTourPlace(3,57,59)) error("Cannot enter the living room");
	settle(8);
	if (scummverseWanderPlace(_currentRoom)!=living) error("Living room is place %d",scummverseWanderPlace(_currentRoom));
	if (_scummverseVisitorCapacity<3) error("Living room has room for %d visitors",_scummverseVisitorCapacity);
	// (The room is wider than the screen: into view beside Dave.)
	for (int i=0;i<3;++i) {
		const int s=visitor(four[i]);
		if (s<0) error("%s not in the living room",name(four[i]));
		Actor *a=_scummverseVisitors[s].actor, *dave=derefActor(3,"wander view");
		const AdjustBoxResult p=a->adjustXYToBeInBox(dave->getRealPos().x+(i-1)*7+(i>0?3:-3),dave->getRealPos().y);
		a->stopActorMoving(); a->putActor(p.x,p.y,_currentRoom);
	}
	settle(2);
	for (int i=0;i<3;++i) {
		const ScummverseVisitor &v=_scummverseVisitors[visitor(four[i])];
		if (!v.sprite || v.drawn.isEmpty() || pixelsOf(v)<100) error("%s not drawn (%d pixels)",name(four[i]),pixelsOf(v));
	}
	if (shownHere()!=3) error("%d visitors shown, expected 3",shownHere());
	shot("wander-living.ppm");
	warning("WANDER living room: %s, %s, %s; capacity %d",name(four[0]),name(four[1]),name(four[2]),_scummverseVisitorCapacity);
	// Someone else arrives while the player watches: it walks in from a side.
	WB::send(four[3],living);
	settle(1);
	{
		const int s=visitor(four[3]);
		if (s<0) error("%s did not arrive",name(four[3]));
		const ScummverseVisitor &v=_scummverseVisitors[s];
		const bool walks=::Scummverse::WorldBridge::guestFrames(v.sprite-1,1,1)>=2 || ::Scummverse::WorldBridge::guestFrames(v.sprite-1,0,1)>=2 || worldBouncer(worldAppearanceGame(four[3]),worldAppearanceCostume(four[3]));
		if (walks && !v.actor->_moving) error("%s does not walk in",name(four[3]));
		for (int n=0;n<200 && v.actor->_moving;++n) settle(1);
		if (v.actor->_moving) error("%s never arrives",name(four[3]));
		warning("WANDER %s arrived (%s)",name(four[3]),walks?"walked in":"stands");
	}
	// Time passes: the others move on, the living room's stay; nobody more
	// than a crowd (small ones aside) comes in.
	{
		Common::Array<int> before; for (int key : keys) before.push_back(WB::where(key));
		int most=0;
		for (int n=0;n<60;++n) {
			scummverseUpdateWanderers(60*30);
			int there[64]; const int k=MIN(64,WB::at(living,there,64)); int big=0;
			for (int i=0;i<k;++i) big+=!WB::small(there[i]);
			most=MAX(most,big);
		}
		int moved=0;
		for (uint i=0;i<keys.size();++i) {
			if (before[i]==living && WB::where(keys[i])!=living) error("%s left the living room while watched",name(keys[i]));
			moved+=before[i]!=WB::where(keys[i]);
		}
		if (moved<(int)keys.size()/2 || most>4) error("%d of %d moved; %d in the living room at most",moved,(int)keys.size(),most);
		noneHome("half an hour");
		if (shownHere()<4) error("Visitors went away while watched");
		warning("WANDER half an hour: %d moved, the living room at most %d",moved,most);
	}
	// Walking up to Guybrush: he says one of his lines once, in his colour.
	{
		const int s=visitor(guybrush);
		ScummverseVisitor &v=_scummverseVisitors[s];
		Actor *dave=derefActor(3,"wander greeter");
		for (ScummverseVisitor &o : _scummverseVisitors) o.greeted=true; // (only Guybrush greets)
		v.actor->stopActorMoving(); v.greeted=false;
		dave->putActor(v.actor->getRealPos().x+3,v.actor->getRealPos().y,_currentRoom);
		VAR(VAR_HAVE_MSG)=0; stopTalk(); _scummverseVisitorQuiet=0; _scummverseAIActor=0;
		for (int n=0;n<4 && _scummverseVisitorTalking<0;++n) scummLoop(4);
		if (_scummverseVisitorTalking!=s || getTalkingActor()!=0xFF || !VAR(VAR_HAVE_MSG)) error("Guybrush did not greet (%d, %d)",_scummverseVisitorTalking,getTalkingActor());
		if (_charsetColor!=worldAppearance(guybrush)->talkColor) error("Greeting in colour %d, not %d",_charsetColor,worldAppearance(guybrush)->talkColor);
		shot("wander-greeting.ppm");
		settle(2);
		dave->putActor(10,60,_currentRoom);
	}
	// Chat: Guybrush is on the list of people nearby (past 32 bits) as
	// himself, answers in his colour and stands still meanwhile; a tap on
	// him picks him.
	{
		const int s=visitor(guybrush), id=kScummverseTalkVisitor+s;
		ScummverseVisitor &v=_scummverseVisitors[s];
		VAR(VAR_HAVE_MSG)=0; stopTalk(); _scummverseVisitorQuiet=60000;
		scummverseUpdateRoaming(4);
		if (!(FakeAI::roster & (1ull<<id)) || FakeAI::wanderers[s]!=guybrush) error("Guybrush not on the chat list (%llx, %d)",FakeAI::roster,FakeAI::wanderers[s]);
		const AdjustBoxResult away=v.actor->adjustXYToBeInBox(v.actor->getRealPos().x+10,v.actor->getRealPos().y);
		v.actor->startWalkActor(away.x,away.y,-1);
		FakeAI::talk=id; FakeAI::reply=true;
		scummverseUpdateRoaming(4);
		if (_scummverseVisitorTalking!=s || getTalkingActor()!=0xFF || _charsetColor!=worldAppearance(guybrush)->talkColor) error("Guybrush's chat reply not shown (%d)",_scummverseVisitorTalking);
		if (v.actor->_moving) error("Guybrush walks on while chatting");
		settle(2);
		const int x=(v.drawn.left+v.drawn.right)/2, y=(v.drawn.top+v.drawn.bottom)/2;
		if (v.drawn.isEmpty() || scummverseTalkTarget(x,y)!=id) error("A tap on Guybrush picks %d",scummverseTalkTarget(x,y));
		FakeAI::talk=0; FakeAI::reply=false; stopTalk(); VAR(VAR_HAVE_MSG)=0;
	}
	// The background drawn again under a standing visitor (an object's
	// state changing there): the visitor is drawn again over it.
	{
		ScummverseVisitor &v=_scummverseVisitors[visitor(guybrush)];
		v.actor->stopActorMoving(); settle(3);
		const Common::Rect at=v.drawn;
		if (at.isEmpty()) error("Guybrush not on screen before the redraw");
		for (int x=at.left;x<at.right;x+=8) setGfxUsageBit(x/8,USAGE_BIT_DIRTY);
		_bgNeedsRedraw=true; scummLoop(4);
		if (pixelsOf(v)<100) error("Guybrush gone after the background was drawn again (%d pixels)",pixelsOf(v));
	}
	// No ghost: someone moved away leaves only the floor behind.
	{
		ScummverseVisitor &v=_scummverseVisitors[visitor(four[1])];
		settle(2);
		const Common::Rect was=v.drawn;
		const int far=v.actor->getRealPos().x<_roomWidth/16 ? _roomWidth/8-6 : 6;
		v.actor->stopActorMoving(); v.actor->putActor(far,v.actor->getRealPos().y,_currentRoom);
		settle(3);
		int ghost=0;
		for (int y=was.top;y<was.bottom;++y) for (int x=was.left;x<was.right;++x) {
			const int sx=x-_virtscr[0].xstart;
			if (sx<0 || sx>=_screenWidth || testGfxAnyUsageBits(_screenStartStrip+sx/8)) continue;
			bool covered=false;
			for (const ScummverseVisitor &o : _scummverseVisitors) covered=covered || (o.who && o.drawn.contains(x,y));
			if (!covered && *_virtscr[0].getPixels(sx,y)!=*_virtscr[0].getBackPixels(sx,y)) ++ghost;
		}
		if (ghost) error("%d pixels left behind where %s stood",ghost,name(four[1]));
		shot("wander-moved.ppm");
	}
	// Saved and loaded: everyone where they were, those here shown again.
	{
		Common::Array<int> kept; for (int key : keys) kept.push_back(WB::where(key));
		Common::String file; _saveLoadDescription="Wanderers";
		if (!saveState(15,false,file)) error("Save failed");
		WB::send(keys[5],W::placeCode(W::kManiac,0,7));
		if (!loadState(15,false)) error("Load failed");
		settle(4);
		for (uint i=0;i<keys.size();++i) if (WB::where(keys[i])!=kept[i]) error("%s moved by save and load",name(keys[i]));
		if (shownHere()<4) error("%d visitors after loading",shownHere());
	}
	// Never two of one person in view, by name: Monkey Island 2's Guybrush
	// sent into the living room, where Monkey Island's is shown, stays aside;
	// Dave playing Monkey Island 2's Guybrush, neither visiting one is drawn,
	// one again once he is himself; Day of the Tentacle's Edna steps aside
	// while the mansion's own Edna stands here.
	{
		const int guy2=worldAppearanceKey(1,1), edna2=worldAppearanceKey(5,330);
		Common::String done;
		if (Common::find(keys.begin(),keys.end(),guy2)!=keys.end()) {
			if (!WB::twins(guybrush,guy2) || WB::twins(guybrush,four[1])) error("Guybrush told by name wrongly");
			WB::send(guy2,living); settle(4);
			const int s1=visitor(guybrush), s2=visitor(guy2);
			if (s1<0 || s2<0) error("Both Guybrushes not in the living room");
			if (!_scummverseVisitors[s1].sprite || _scummverseVisitors[s2].sprite) error("Two Guybrushes drawn in the living room (%d, %d)",_scummverseVisitors[s1].sprite,_scummverseVisitors[s2].sprite);
			if (!scummverseSetAppearance(3,guy2)) error("Cannot play Monkey Island 2's Guybrush: %s",_scummverseWorldNotice.c_str());
			settle(4);
			if (_scummverseVisitors[s1].sprite || _scummverseVisitors[s2].sprite) error("A visiting Guybrush drawn beside Dave playing him");
			scummverseSetAppearance(3,0); settle(4);
			if (!_scummverseVisitors[s1].sprite == !_scummverseVisitors[s2].sprite) error("Not one Guybrush drawn once Dave is himself again");
			WB::send(guy2,W::placeCode(W::kManiac,0,1)); settle(4);
			if (visitor(guy2)>=0 || visitor(guybrush)<0 || !_scummverseVisitors[visitor(guybrush)].sprite) error("Guybrush not drawn once the other one left");
			done+="the two Guybrushes drawn once, both aside for Dave playing him";
		}
		int ednaActor=0;
		for (int id=1;id<kScummverseManiacActors && !ednaActor;++id) if (id!=3 && _actors[id]->_costume==10) ednaActor=id;
		if (ednaActor && Common::find(keys.begin(),keys.end(),edna2)!=keys.end()) {
			WB::send(edna2,living); settle(4);
			if (visitor(edna2)<0 || !_scummverseVisitors[visitor(edna2)].sprite) error("Day of the Tentacle's Edna not drawn in the living room");
			Actor *e=_actors[ednaActor], *dave=derefActor(3,"wander twins"); const int room=e->_room; const Common::Point at=e->getRealPos();
			e->putActor(dave->getRealPos().x+12,dave->getRealPos().y,_currentRoom); settle(4);
			if (_scummverseVisitors[visitor(edna2)].sprite) error("Day of the Tentacle's Edna does not step aside for the mansion's");
			e->putActor(at.x,at.y,room); settle(4);
			if (!_scummverseVisitors[visitor(edna2)].sprite) error("Day of the Tentacle's Edna not back once the mansion's left");
			WB::send(edna2,W::placeCode(W::kManiac,0,1)); settle(4);
			done+=Common::String(done.empty()?"":"; ")+"Day of the Tentacle's Edna aside for the mansion's";
		}
		if (done.empty()) error("No one of the same name to try");
		warning("WANDER nobody twice in view: %s",done.c_str());
	}
	// No visitors on the plane, in the van's cockpit or in the van in flight.
	if (scummverseWanderPlace(56) || scummverseWanderPlace(81) || scummverseWanderPlace(221)) error("Visitors on the plane, in the cockpit or in the van in flight");
	// Small ones (an animal, a critter) are known and never part of a crowd.
	{
		const int parrot=worldAppearanceKey(4,72);
		if (Common::find(keys.begin(),keys.end(),parrot)!=keys.end() && !WB::small(parrot)) error("The parrot is not small");
		if (WB::small(guybrush)) error("Guybrush is small");
	}
	// Standing in the kitchen for ten minutes, they come by (to it or next
	// door), never more than a crowd.
	{
		const int kitchen=W::placeCode(W::kManiac,0,7);
		int inside=0, most=0;
		for (int n=0;n<60;++n) {
			WB::advance(60*10,kitchen);
			int there[64]; const int k=MIN(64,WB::at(kitchen,there,64)); int big=0;
			for (int i=0;i<k;++i) big+=!WB::small(there[i]);
			inside+=k; most=MAX(most,big);
		}
		warning("WANDER ten minutes by the kitchen: %d visits, at most %d at once",inside,most);
		noneHome("by the kitchen");
		if (!inside || most>4+1) error("Kitchen: %d visits, %d at once",inside,most);
	}
	// Nobody twice: everyone out afresh, then an hour passing by the
	// kitchen: in no place two of one person (by name: another game's of the
	// same name), nor anyone where the same person of the engine's own
	// stands (the mansion's people by their costume, anyone played by the
	// look: Day of the Tentacle's Edna never in the mansion's Edna's room).
	{
		const int kitchen=W::placeCode(W::kManiac,0,7);
		scummverseUpdateWanderers(0); // (who stands where told)
		auto standingAs=[&](int id) {
			const int look=scummverseAppearance(id), worn=_actors[id]->_costume;
			const int as=look && !worldNativeLook(look) ? look : worn<kScummverseFirstZakCostume && worn!=34 ? worldAppearanceKey(mm,worn) : 0;
			return worldSmall(worldAppearanceGame(as),worldAppearanceCostume(as)) ? 0 : as;
		};
		// (Told: each of the cast of a standing one's name is kept from there.)
		int told=0, standers=0;
		for (int id=1;id<kScummverseManiacActors;++id) {
			const int at=_actors[id]->_room ? scummverseWanderPlace(_actors[id]->_room) : 0;
			const WorldGuest *who=worldAppearance(standingAs(id));
			standers+=at!=0;
			if (!at || !who) continue;
			for (int key : keys)
				if (!WB::small(key) && ::Scummverse::Wander::samePerson(who->name,name(key))) {
					if (!WB::taken(key,at)) error("%s not kept from place %d where %s stands",name(key),at,who->name);
					++told;
				}
		}
		if (!told) error("Nobody of a standing one's name kept from where they stand");
		WB::start();
		int checked=0, stood=0;
		for (int n=0;n<=60;++n) {
			if (n) WB::advance(60*60,kitchen);
			Common::Array<int> places;
			for (int key : keys) { const int at=WB::where(key); if (at && Common::find(places.begin(),places.end(),at)==places.end()) places.push_back(at); }
			for (int at : places) {
				int there[64]; const int k=MIN(64,WB::at(at,there,64));
				for (int i=0;i<k;++i) for (int j=i+1;j<k;++j) if (WB::twins(there[i],there[j])) error("%s and %s both in place %d",name(there[i]),name(there[j]),at);
				bool here=false;
				for (int id=1;id<kScummverseManiacActors;++id) {
					if (!_actors[id]->_room || scummverseWanderPlace(_actors[id]->_room)!=at) continue;
					const WorldGuest *who=worldAppearance(standingAs(id));
					if (!who) continue;
					here=true;
					for (int i=0;i<k;++i)
						if (!WB::small(there[i]) && ::Scummverse::Wander::samePerson(who->name,name(there[i]))) error("%s in place %d where %s stands",name(there[i]),at,who->name);
				}
				++checked; stood+=here;
			}
		}
		warning("WANDER nobody twice: %d places checked with nobody twice over an hour, everyone out afresh (%d where one of the %d people of the engine's own stands; %d of the cast of their names kept from there)",checked,stood,standers,told);
		if (checked<1000 || !stood) error("Nobody twice: only %d places checked, %d where the engine's own stand",checked,stood);
		noneHome("out afresh");
	}
	// In the dark (the basement's light switched off) a visitor is drawn as
	// the room's own people are, a grey shape with black lines, not in its
	// colours; lit again, in its colours.
	{
		const int basement=W::placeCode(W::kManiac,0,8);
		{ int there[64]; const int n=MIN(64,WB::at(basement,there,64)); for (int i=0;i<n;++i) WB::send(there[i],W::placeCode(W::kManiac,0,1)); }
		WB::send(guybrush,basement);
		if (!scummverseTourPlace(8,44,64)) error("Cannot enter the basement");
		settle(6);
		const int s=visitor(guybrush);
		if (s<0) error("Guybrush not in the basement");
		ScummverseVisitor &v=_scummverseVisitors[s];
		Actor *dave=derefActor(3,"wander dark");
		const AdjustBoxResult p=v.actor->adjustXYToBeInBox(dave->getRealPos().x+6,dave->getRealPos().y);
		v.actor->stopActorMoving(); v.actor->putActor(p.x,p.y,_currentRoom); v.idle=60000;
		const byte shade=_gdi->remapColorToRenderMode(11);
		auto grey=[&]() {
			int n=0;
			for (int y=v.drawn.top;y<v.drawn.bottom;++y) for (int x=v.drawn.left;x<v.drawn.right;++x) {
				const int sx=x-_virtscr[0].xstart;
				n+=sx>=0 && sx<_screenWidth && *_virtscr[0].getPixels(sx,y)==shade;
			}
			return n;
		};
		int none[NUM_SCRIPT_LOCAL]; memset(none,0,sizeof(none));
		settle(3);
		if (pixelsOf(v)<100) error("Guybrush not drawn in the lit basement (%d pixels)",pixelsOf(v));
		runObjectScript(335,5,false,false,none); settle(6);
		if (VAR(VAR_CURRENT_LIGHTS) & LIGHTMODE_actor_use_colors) error("The basement's light not off (lights %d)",VAR(VAR_CURRENT_LIGHTS));
		if (pixelsOf(v) || grey()<60) error("Guybrush in his colours in the dark (%d coloured pixels, %d grey)",pixelsOf(v),grey());
		shot("wander-dark.ppm");
		runObjectScript(335,4,false,false,none); settle(6);
		if (pixelsOf(v)<100) error("Guybrush not in his colours once the basement is lit (%d pixels)",pixelsOf(v));
		warning("WANDER the dark basement: Guybrush grey there, in his colours lit");
	}
	// Riding Zak's bus the player is out of sight at the stop: a visitor
	// beside it greets nobody.
	{
		const int street=W::placeCode(W::kZak,0,55);
		{ int there[64]; const int n=MIN(64,WB::at(street,there,64)); for (int i=0;i<n;++i) WB::send(there[i],W::placeCode(W::kManiac,0,1)); }
		WB::send(guybrush,street);
		if (!scummverseTravel(5) || _currentRoom!=55) error("Cannot reach the street (%d)",_currentRoom);
		settle(4);
		const int s=visitor(guybrush);
		if (s<0) error("Guybrush not on the street");
		Actor *dave=derefActor(3,"wander bus");
		scummverseWaitBus();
		for (int n=0;n<400 && !(_scummVars[765]>kBusBoarding && !dave->_visible);++n) settle(1);
		if (dave->_visible || _scummVars[765]<=kBusBoarding) error("Dave not aboard the bus (phase %d)",_scummVars[765]);
		ScummverseVisitor &v=_scummverseVisitors[s];
		const AdjustBoxResult p=v.actor->adjustXYToBeInBox(dave->getRealPos().x+2,dave->getRealPos().y+4);
		v.actor->stopActorMoving(); v.actor->putActor(p.x,p.y,_currentRoom); v.idle=60000;
		for (ScummverseVisitor &o : _scummverseVisitors) o.greeted=&o!=&v;
		VAR(VAR_HAVE_MSG)=0; stopTalk(); _scummverseVisitorQuiet=0; _scummverseAIActor=0;
		bool greeted=false;
		for (int n=0;n<6 && _scummVars[765]>kBusBoarding;++n) { scummLoop(4); greeted=greeted || _scummverseVisitorTalking==s; }
		if (greeted) error("A visitor greeted the player out of sight on the bus");
		warning("WANDER on Zak's bus: nobody greets the stop");
	}
	warning("SCUMMVERSE_WANDER_PASS enabled=1");
	quitGame();
	return;
