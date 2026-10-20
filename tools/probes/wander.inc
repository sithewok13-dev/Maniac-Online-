	// Wanderers: other games' characters out of their homes, shown where they are.
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
	if (!scummverseTravel(2)) error("Cannot return to the mansion");
	settle(4);
	// Built and started: forty out, each once, at known places.
	int32 *who=_scummVars+kScummverseWanderVar, *where=who+W::kMostWanderers;
	if (WB::places()<60 || WB::cast()<W::kMostWanderers) error("Wanderers' world too small: %d places, %d characters",WB::places(),WB::cast());
	for (int i=0;i<W::kMostWanderers;++i) {
		if (!who[i] || !where[i] || !worldAppearance(who[i])) error("Wanderer %d: %d at %d",i,who[i],where[i]);
		for (int j=0;j<i;++j) if (who[j]==who[i]) error("%s out twice",worldAppearance(who[i])->name);
	}
	warning("WANDER %d places, %d characters",WB::places(),WB::cast());
	// Where they set out: every game an equal share (spread evenly over the
	// places, the mansion's 37 of 743 had about two of forty).
	{
		int maniac=0, zak=0; bool game[16]={};
		for (int i=0;i<W::kMostWanderers;++i) {
			maniac+=W::placeKind(where[i])==W::kManiac; zak+=W::placeKind(where[i])==W::kZak;
			game[W::placeKind(where[i])==W::kWorld ? 2+W::placeGame(where[i]) : W::placeKind(where[i])]=true;
		}
		int games=0; for (bool g : game) games+=g;
		warning("WANDER set out: %d in the mansion, %d in Zak's places, %d elsewhere, in %d games",maniac,zak,W::kMostWanderers-maniac-zak,games);
		if (games<6) error("Wanderers set out in only %d games",games);
	}
	// Standing in the kitchen for ten minutes, they come by (to it or next door).
	{
		int32 kept[2*W::kMostWanderers]; memcpy(kept,who,sizeof(kept));
		const int kitchen=W::placeCode(W::kManiac,0,7);
		int near=0, inside=0;
		for (int n=0;n<60;++n) {
			WB::advance(60*10,kitchen);
			for (int i=0;i<W::kMostWanderers;++i) inside+=where[i]==kitchen;
		}
		for (int i=0;i<W::kMostWanderers;++i) near+=W::placeKind(where[i])==W::kManiac;
		warning("WANDER after ten minutes by the kitchen: %d in the mansion, kitchen visits %d",near,inside);
		if (!inside) error("Nobody came to the kitchen in ten minutes");
		memcpy(who,kept,sizeof(kept));
	}
	// Guybrush (Monkey Island's lead, at home in room 33) and two more in the
	// living room.
	const int guybrush=worldAppearanceKey(0,1), living=W::placeCode(W::kManiac,0,3);
	for (int i=1;i<W::kMostWanderers;++i) if (who[i]==guybrush) who[i]=who[0];
	who[0]=guybrush; where[0]=where[1]=where[2]=living;
	for (int i=3;i<W::kMostWanderers;++i) if (where[i]==living) where[i]=W::placeCode(W::kManiac,0,1);
	// At home he is not there while he wanders.
	if (!scummverseTravelPlace(0,33)) error("Cannot visit Monkey Island: %s",_scummverseWorldNotice.c_str());
	settle(8);
	bool home=false;
	for (int k=0;k<kScummverseGuestSlots;++k) {
		const WorldGuest *g=worldGuestAt(worldPlaceKey(0,33),k);
		if (g && worldAppearanceKey(0,g->costume)==guybrush) { home=true; if (derefActor(kScummverseGuestActor+k,"wander home")->_room==_currentRoom) error("Guybrush at home while out wandering"); }
	}
	if (!home) error("Guybrush does not live in Monkey Island 33");
	shot("wander-home.ppm");
	// In the living room: the three are there, drawn from their frames.
	if (!scummverseTourPlace(3,57,59)) error("Cannot enter the living room");
	settle(8);
	if (scummverseWanderPlace(_currentRoom)!=living) error("Living room is place %d",scummverseWanderPlace(_currentRoom));
	if (_scummverseVisitorCapacity<3) error("Living room has room for %d visitors",_scummverseVisitorCapacity);
	// (The room is wider than the screen: into view beside Dave.)
	for (int i=0;i<3;++i) {
		const int s=visitor(who[i]);
		if (s<0) error("%s not in the living room",worldAppearance(who[i])->name);
		Actor *a=_scummverseVisitors[s].actor, *dave=derefActor(3,"wander view");
		const AdjustBoxResult p=a->adjustXYToBeInBox(dave->getRealPos().x+(i-1)*7+(i>0?3:-3),dave->getRealPos().y);
		a->stopActorMoving(); a->putActor(p.x,p.y,_currentRoom);
	}
	settle(2);
	for (int i=0;i<3;++i) {
		const int s=visitor(who[i]);
		if (s<0) error("%s not in the living room",worldAppearance(who[i])->name);
		const ScummverseVisitor &v=_scummverseVisitors[s];
		if (!v.sprite || v.drawn.isEmpty()) error("%s not drawn: sprite %d rect %d,%d-%d,%d visible %d room %d/%d costume %d top %d bottom %d",worldAppearance(who[i])->name,v.sprite,v.drawn.left,v.drawn.top,v.drawn.right,v.drawn.bottom,v.actor->_visible,v.actor->_room,_currentRoom,v.actor->_costume,v.actor->_top,v.actor->_bottom);
		int mine=0;
		for (int y=v.drawn.top;y<v.drawn.bottom;++y) for (int x=v.drawn.left;x<v.drawn.right;++x) {
			const int sx=x-_virtscr[0].xstart;
			if (sx>=0 && sx<_screenWidth && *_virtscr[0].getPixels(sx,y)>=MAX(16,::Scummverse::WorldBridge::guestFirstSlot())) ++mine;
		}
		if (mine<100) error("%s drawn with %d pixels",worldAppearance(who[i])->name,mine);
	}
	if (shownHere()!=3) error("%d visitors shown, expected 3",shownHere());
	shot("wander-living.ppm");
	warning("WANDER living room: capacity %d",_scummverseVisitorCapacity);
	// Someone else arrives while the player watches: it walks in from a side.
	where[3]=living;
	settle(1);
	{
		const int s=visitor(who[3]);
		if (s<0) error("%s did not arrive",worldAppearance(who[3])->name);
		const ScummverseVisitor &v=_scummverseVisitors[s];
		const bool walks=::Scummverse::WorldBridge::guestFrames(v.sprite-1,1,1)>=2 || ::Scummverse::WorldBridge::guestFrames(v.sprite-1,0,1)>=2 || worldBouncer(worldAppearanceGame(who[3]),worldAppearanceCostume(who[3]));
		if (walks && !v.actor->_moving) error("%s does not walk in",worldAppearance(who[3])->name);
		for (int n=0;n<200 && v.actor->_moving;++n) settle(1);
		if (v.actor->_moving) error("%s never arrives",worldAppearance(who[3])->name);
		warning("WANDER %s arrived (%s)",worldAppearance(who[3])->name,walks?"walked in":"stands");
	}
	// Time passes: the others move on, the living room's stay.
	{
		int before[W::kMostWanderers]; for (int i=0;i<W::kMostWanderers;++i) before[i]=where[i];
		for (int n=0;n<60;++n) scummverseUpdateWanderers(60*30);
		int moved=0;
		for (int i=0;i<W::kMostWanderers;++i) {
			if (before[i]==living && (where[i]!=living || who[i]!=_scummVars[kScummverseWanderVar+i])) error("A living room wanderer left while watched");
			moved+=before[i]!=where[i];
		}
		if (moved<10) error("Only %d wanderers moved",moved);
		if (shownHere()<4) error("Visitors went away while watched");
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
		const int s=visitor(guybrush);
		ScummverseVisitor &v=_scummverseVisitors[s];
		v.actor->stopActorMoving(); settle(3);
		const Common::Rect at=v.drawn;
		if (at.isEmpty()) error("Guybrush not on screen before the redraw");
		for (int x=at.left;x<at.right;x+=8) setGfxUsageBit(x/8,USAGE_BIT_DIRTY);
		_bgNeedsRedraw=true; scummLoop(4);
		int mine=0;
		for (int y=at.top;y<at.bottom;++y) for (int x=at.left;x<at.right;++x) {
			const int sx=x-_virtscr[0].xstart;
			if (sx>=0 && sx<_screenWidth && *_virtscr[0].getPixels(sx,y)>=MAX(16,::Scummverse::WorldBridge::guestFirstSlot())) ++mine;
		}
		if (mine<100) error("Guybrush gone after the background was drawn again (%d pixels)",mine);
	}
	// No ghost: someone moved away leaves only the floor behind.
	{
		const int s=visitor(who[1]);
		ScummverseVisitor &v=_scummverseVisitors[s];
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
		if (ghost) error("%d pixels left behind where %s stood",ghost,worldAppearance(who[1])->name);
		shot("wander-moved.ppm");
	}
	// Saved and loaded: the same wanderers, shown again.
	{
		int32 kept[2*W::kMostWanderers]; memcpy(kept,who,sizeof(kept));
		Common::String file; _saveLoadDescription="Wanderers";
		if (!saveState(15,false,file)) error("Save failed");
		where[5]=W::placeCode(W::kManiac,0,7);
		if (!loadState(15,false)) error("Load failed");
		settle(4);
		if (memcmp(kept,_scummVars+kScummverseWanderVar,sizeof(kept))) error("Wanderers changed by save and load");
		if (shownHere()<4) error("%d visitors after loading",shownHere());
	}
	// No visitors in the plane, the van's cockpit, or a game's map.
	if (scummverseWanderPlace(56) || scummverseWanderPlace(81)) error("Visitors on the plane or in the cockpit");
	// Taking turns: in time, others set out from home.
	{
		int start[W::kMostWanderers]; memcpy(start,who,sizeof(start));
		for (int n=0;n<40;++n) scummverseUpdateWanderers(60*150);
		int fresh=0;
		for (int i=0;i<W::kMostWanderers;++i) { bool was=false; for (int j=0;j<W::kMostWanderers;++j) was=was||start[j]==who[i]; fresh+=!was; }
		if (fresh<10) error("Only %d new wanderers set out",fresh);
		for (int i=0;i<W::kMostWanderers;++i) for (int j=0;j<i;++j) if (who[i]==who[j]) error("Out twice after turns");
		warning("WANDER %d set out in turn",fresh);
	}
	warning("SCUMMVERSE_WANDER_PASS enabled=1");
	quitGame();
	return;
