	// Other worlds: visit every exported scene through the real engine.
	if (!_scummverseRoaming) { warning("SCUMMVERSE_WORLD_VISIT_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	Actor *me=derefActor(3,"world visitor");
	byte maniacColors[48]; memcpy(maniacColors,_currentPalette,48);
	auto shot=[&](const Common::String &name) {
		Common::DumpFile f; if(!f.open(Common::Path("/workspace/Maniac-Online/build/"+name))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h); f.write(h.c_str(),h.size());
		for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); f.write(_currentPalette+3*c,3); }
	};
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	int visited=0, walked=0, edges=0, guests=0, scaled=0, walkers=0;
	// Pixels of the guest's palette slots on screen inside its drawn extent.
	auto guestPixels=[&](Actor *g) {
		int n=0; if (g->_top>=g->_bottom) return 0;
		for(int y=g->_top;y<g->_bottom;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); if(c>=MAX(16,::Scummverse::WorldBridge::guestFirstSlot())) ++n; }
		return n;
	};
	// The named place at catalog position k: its game and that game's room.
	auto landmark=[&](int k, int &game, int &source) {
		int index=k; game=0;
		for (const auto &g : ::Scummverse::WorldCatalog::kWorldGames) { if (index<g.sceneCount) { source=g.scenes[index].room; return; } index-=g.sceneCount; ++game; }
	};
	auto at=[&](int k) { int game, source, held; landmark(k,game,source); return scummverseWorldGameOf(_currentRoom,held)==game && held==source; };
	for (int k=0;k<scummverseWorldSceneCount();++k) {
		scummverseWorldRequest(((_currentRoom*32+3)<<8)|(160+k)); scummverseUpdateRoaming(4);
		const int room=_currentRoom;
		if (!at(k)) {
			// Only a game that was never exported may be missing.
			int game, source; landmark(k,game,source);
			const Common::String marker=Common::String::format("%s-v%d.svx",::Scummverse::WorldCatalog::kWorldGames[game].gameid,::Scummverse::WorldCatalog::worldExportVersion(::Scummverse::WorldCatalog::kWorldGames[game].gameid));
			if (Common::FSNode(ConfMan.getPath("scummverse_worlds_path")).getChild(marker).exists()) error("Scene %d of an exported game not visited: %s",k,_scummverseWorldNotice.c_str());
			warning("WORLD scene %d not visited: %s",k,_scummverseWorldNotice.c_str()); continue;
		}
		if (room<192 || room>199) error("Place %d in room %d, not a slot room",k,room);
		++visited;
		if (_roomResource!=ScummverseContent::kForeignRoom || me->_room!=room || !me->_visible) error("Scene %d not mounted: resource %d",k,_roomResource);
		const byte *rgb=::Scummverse::WorldBridge::palette();
		if (memcmp(_currentPalette+3*16,rgb,3*::Scummverse::WorldBridge::slotCount())) error("Scene %d palette not applied",k);
		if (memcmp(_currentPalette,maniacColors,48)) error("Scene %d changed the 16 V1 colors",k);
		settle(6); shot(Common::String::format("world-visit-%d.ppm",k));
		// The scene's characters: guest actors 25.., named, drawn from their frames.
		{
			const ::Scummverse::WorldCatalog::WorldGame *game=nullptr; int scene=0;
			int index=k; for (const auto &g : ::Scummverse::WorldCatalog::kWorldGames) { if (index<g.sceneCount) { game=&g; scene=index; break; } index-=g.sceneCount; }
			int present=0;
			for (int slot=0;slot<5;++slot) {
				const ::Scummverse::WorldCatalog::WorldGuest *g=::Scummverse::WorldCatalog::worldGuestAt(::Scummverse::WorldCatalog::worldPlaceKey((int)(game-::Scummverse::WorldCatalog::kWorldGames),game->scenes[scene].room),slot);
				Actor *guest=derefActor(25+slot,"world guest");
				if (!g) { if (guest->_room) error("Scene %d slot %d has an unexpected guest",k,slot); continue; }
				if (guest->_room!=room || scummverseGuestSlot(guest)!=slot) error("Guest %s not placed (room %d)",g->name,guest->_room);
				if (strcmp((const char *)getObjOrActorName(25+slot),g->name)) error("Guest name %s",(const char *)getObjOrActorName(25+slot));
				if (!(scummverseGuestMask() & (1u<<(25+slot)))) error("Guest %s missing from the talk roster",g->name);
				guest->_needRedraw=true; settle(1);
				const int drawn=guestPixels(guest);
				// Drawn area shrinks with the square of the scene's depth scale there.
				const double depth=scummverseWorldDepth(guest);
				if (drawn<MAX(1.0,30*depth*depth)) error("Guest %s not drawn (%d pixels, extent %d..%d, depth %.2f)",g->name,drawn,guest->_top,guest->_bottom,depth);
				warning("WORLD guest %s pixels %d height %d",g->name,drawn,guest->_bottom-guest->_top);
				++guests; ++present;
			}
			if (present && memcmp(_currentPalette+3*::Scummverse::WorldBridge::guestFirstSlot(),::Scummverse::WorldBridge::guestPalette(),3*::Scummverse::WorldBridge::guestSlotCount())) error("Scene %d guest palette not applied",k);
			if (_scummVars[768]==room || derefActor(15,"resident")->_room==room) error("Scene %d borrowed the resident actor",k);
		}
		// The visitor is as tall as a person standing there in that game.
		{
			int source; const int game=scummverseWorldGameOf(room,source);
			const double depth=scummverseWorldDepth(me);
			const double expected=::Scummverse::WorldCatalog::kWorldGames[game].heroHeight*::Scummverse::WorldBridge::sceneScale()*depth;
			me->_needRedraw=true; settle(1);
			const int drawn=me->_bottom-me->_top;
			warning("WORLD scale %d: visitor %d px, expected %.1f (depth %.2f)",k,drawn,expected,depth);
			// A visitor cut by the screen top is not measured.
			if (me->_top>0 && ABS(drawn-expected)>MAX(4.0,expected*0.2)) error("Scene %d: visitor drawn %d px tall, expected about %.0f",k,drawn,expected);
			++scaled;
		}
		// Walk inside the scene's own boxes.
		if (getNumBoxes()>0) {
			const Common::Point from=me->getRealPos();
			AdjustBoxResult goal=me->adjustXYToBeInBox(from.x>20 ? from.x-12 : from.x+12, from.y);
			me->startWalkActor(goal.x,goal.y,-1); for(int n=0;n<200 && me->_moving;++n) settle(1);
			if (me->getRealPos()!=from) ++walked;
		}
	}
	if (!visited) error("No exported scenes were visited");
	// Guests the game never drew walking both ways (grafts, side walks,
	// swinging legs) walk left and right, in frames that change.
	for (const auto &c : ::Scummverse::WorldCatalog::kWorldCast) {
		const int gi=c.game, costume=c.guest.costume;
		if (!::Scummverse::WorldCatalog::worldCostumeGraft(gi,costume) && !::Scummverse::WorldCatalog::worldSideWalk(gi,costume) && !::Scummverse::WorldCatalog::worldLegSwing(gi,costume)) continue;
		if (!scummverseTravelPlace(gi,c.room)) continue; // Not exported here.
		settle(2);
		Actor *guest=derefActor(25+c.slot,"walking guest");
		if (scummverseGuestSlot(guest)!=c.slot) error("Guest %s not placed for walking",c.guest.name);
		const int sprite=_scummverseGuestSprite[c.slot];
		for (int dir=0;dir<2;++dir) {
			const int n=::Scummverse::WorldBridge::guestFrames(sprite,dir,1);
			if (n<4) error("Guest %s walks in %d frames facing %d",c.guest.name,n,dir);
			int dx0,dy0,w0,h0,dx1,dy1,w1,h1;
			const byte *a=::Scummverse::WorldBridge::guestFrame(sprite,dir,1,0,dx0,dy0,w0,h0), *b=::Scummverse::WorldBridge::guestFrame(sprite,dir,1,(n+3)/4,dx1,dy1,w1,h1);
			if (!a || !b || (w0==w1 && h0==h1 && dx0==dx1 && dy0==dy1 && !memcmp(a,b,w0*h0))) error("Guest %s walks in one picture facing %d",c.guest.name,dir);
		}
		int dx0,dy0,w0,h0,dx1,dy1,w1,h1;
		const byte *left=::Scummverse::WorldBridge::guestFrame(sprite,0,0,0,dx0,dy0,w0,h0), *right=::Scummverse::WorldBridge::guestFrame(sprite,1,0,0,dx1,dy1,w1,h1);
		if (!left || !right || (w0==w1 && h0==h1 && dx0==dx1 && !memcmp(left,right,w0*h0))) error("Guest %s does not turn",c.guest.name);
		// It walks across its room in them.
		const Common::Point from=guest->getRealPos();
		AdjustBoxResult goal=guest->adjustXYToBeInBox(from.x>40 ? from.x-30 : from.x+30, from.y);
		guest->startWalkActor(goal.x,goal.y,-1); settle(2);
		if (guest->_moving) { guest->_needRedraw=true; settle(1); if (guest->_top>=guest->_bottom) error("Walking guest %s not drawn",c.guest.name); }
		warning("WORLD walker %s frames %d/%d",c.guest.name,::Scummverse::WorldBridge::guestFrames(sprite,0,1),::Scummverse::WorldBridge::guestFrames(sprite,1,1));
		++walkers;
	}
	// Guests with a seated pose have a seated picture facing right, no
	// bigger than a cabin (and one as big over the seat's front, if any).
	int seatedPoses=0;
	for (const auto &c : ::Scummverse::WorldCatalog::kWorldCast) {
		if (!::Scummverse::WorldCatalog::worldSeatPose(c.game,c.guest.costume)) continue;
		if (!scummverseTravelPlace(c.game,c.room)) continue;
		settle(2);
		Actor *guest=derefActor(25+c.slot,"seated guest");
		if (scummverseGuestSlot(guest)!=c.slot) error("Guest %s not placed for its seat",c.guest.name);
		const int sprite=_scummverseGuestSprite[c.slot], kind=::Scummverse::WorldCatalog::kWorldSeatedKind;
		int dx,dy,w,h;
		const byte *seated=::Scummverse::WorldBridge::guestFrame(sprite,1,kind,0,dx,dy,w,h);
		const int n=::Scummverse::WorldBridge::guestFrames(sprite,1,kind);
		int ox=0,oy=0,ow=w,oh=h;
		if (n==2) ::Scummverse::WorldBridge::guestFrame(sprite,1,kind,1,ox,oy,ow,oh);
		if (n<1 || n>2 || ::Scummverse::WorldBridge::guestFrames(sprite,0,kind) || !seated || w<8 || h<8 || w>200 || h>200 || ow!=w || oh!=h)
			error("Guest %s seated in %d frames (%dx%d, over the seat %dx%d)",c.guest.name,n,w,h,ow,oh);
		warning("WORLD seated %s %dx%d",c.guest.name,w,h);
		++seatedPoses;
	}
	// Guest behaviour in the first scene that has several.
	for (int k=0;k<scummverseWorldSceneCount();++k) {
		int game, source; landmark(k,game,source);
		const int place=::Scummverse::WorldCatalog::worldPlaceKey(game,source);
		if (!::Scummverse::WorldCatalog::worldGuestAt(place,1)) continue;
		if (!scummverseTravelLandmark(k)) continue;
		const ::Scummverse::WorldCatalog::WorldGuest *g=::Scummverse::WorldCatalog::worldGuestAt(place,0);
		if (scummverseTalkRoom()!=place) error("Dialogue context %d is not place %d",scummverseTalkRoom(),place);
		Actor *guest=derefActor(25,"world guest"), *second=derefActor(26,"second guest");
		if (scummverseGuestSlot(guest)<0 || scummverseGuestSlot(second)<0) error("Guests not placed for behaviour");
		// One greeting when the player walks up; none while the player is out
		// of sight there (aboard a ride at the stop: nobody to greet).
		for (bool &greeted : _scummverseGuestGreeted) greeted=true;
		_scummverseGuestGreeted[0]=false; VAR(VAR_HAVE_MSG)=0; stopTalk();
		me->putActor(guest->getRealPos().x+3,guest->getRealPos().y,_currentRoom);
		me->hideActor();
		scummverseUpdateGuests(4,0);
		if (_scummverseGuestGreeted[0] || getTalkingActor()==25) error("Guest %s greeted a player out of sight",g->name);
		me->showActor();
		scummverseUpdateGuests(4,0);
		if (!_scummverseGuestGreeted[0] || getTalkingActor()!=25) error("Guest %s did not greet",g->name);
		// Talking frames are drawn while the line is shown.
		for(int i=0;i<12;++i) { _talkDelay=100; scummLoop(4); }
		if (guestPixels(guest)<30) error("Talking guest not drawn");
		stopTalk(); VAR(VAR_HAVE_MSG)=0;
		// Chatting holds a guest still.
		second->startWalkActor(second->getRealPos().x+4,second->getRealPos().y,-1);
		scummverseUpdateGuests(4,1u<<26);
		if (second->_moving) error("Chatting guest kept walking");
		// A stroll: walking frames follow the actor.
		const Common::Point from=guest->getPos();
		AdjustBoxResult goal=guest->adjustXYToBeInBox(guest->getRealPos().x>20 ? guest->getRealPos().x-10 : guest->getRealPos().x+10,guest->getRealPos().y);
		guest->startWalkActor(goal.x,goal.y,-1);
		int walkingFrames=0;
		for(int n=0;n<200 && guest->_moving;++n) { scummLoop(4); if (guest->_moving && guestPixels(guest)>=30) ++walkingFrames; }
		if (getNumBoxes()>0 && guest->getPos()!=from && !walkingFrames) error("Guest %s not drawn while walking",g->name);
		shot("world-guest.ppm");
		// Saves keep only Maniac's 25 actors; loading places the guests again.
		Common::String file; _saveLoadDescription="Guests";
		if (!saveState(15,false,file) || !loadState(15,false)) error("Guest save/load failed");
		settle(2); guest->_needRedraw=true; settle(1);
		if (scummverseGuestSlot(guest)<0 || guestPixels(guest)<30) error("Guests lost on load");
		// Leaving sends them away.
		scummverseTravel(2); settle(2);
		for (int slot=0;slot<5;++slot) if (derefActor(25+slot,"guest")->_room) error("Guest actor %d stayed after leaving",25+slot);
		if (scummverseGuestMask()) error("Guests left in the talk roster");
		warning("WORLD guest behaviour %s walked frames %d",g->name,walkingFrames);
		break;
	}
	// A save from patch 0058 lent actor 15 to a world character: it is returned.
	{
		Actor *resident=derefActor(15,"resident");
		const int costume=resident->_costume;
		scummverseTravelLandmark(0);
		_scummVars[768]=200; _scummVars[769]=costume; resident->putActor(10,50,200);
		scummverseUpdateResident();
		if (_scummVars[768] || resident->_room) error("0058 world resident not returned: 768=%d room %d",_scummVars[768],resident->_room);
	}
	// Doors: in every game with a door map, tap each door from its room and
	// stand at it; the player goes through to the room the door leads to.
	int doors=0, doorFailures=0, doorSkipped=0, doorHidden=0, doorCovered=0;
	for (int g=0;g<::Scummverse::WorldCatalog::worldGameCount();++g) {
		const ::Scummverse::WorldCatalog::WorldMap *map=::Scummverse::WorldCatalog::worldMap(g);
		if (!map || ::Scummverse::WorldCatalog::worldHome(g)) continue; // (The mansion is played here itself.)
		for (int i=0;i<map->linkCount;++i) {
			const ::Scummverse::WorldCatalog::WorldLink &link=map->links[i];
			// Rooms the export found no place (one color) are not visited.
			if (!scummverseWorldSceneInstalled(g,link.target)) { ++doorSkipped; continue; }
			const int room=scummverseWorldRoomFor(g,link.room);
			if (!room || !scummverseTravelWorld(room)) { ++doorSkipped; continue; }
			int found=-1, x=0, y=0, w=0, h=0, wx=0, wy=0;
			for (int k=0;k<::Scummverse::WorldBridge::objectCount();++k) {
				int id; ::Scummverse::WorldBridge::object(k,id,x,y,w,h,wx,wy);
				if (id==link.object) { found=k; break; }
			}
			if (found<0) { ++doorSkipped; continue; }
			// A door this instance of a script-built room does not show.
			if (link.switched && !::Scummverse::WorldBridge::objectState(found)) { ++doorHidden; continue; }
			// Start beside the door, tap it, and walk there like a player: on
			// the part of it no other door covers, nearest its middle (a door
			// wholly under others is tapped in its middle; one that then leads
			// elsewhere, one doorway the game shows in two states, is counted
			// apart). A Dig tram car is reached from its platform (where riders
			// step off); it comes to the ledge and leaves after its boarding
			// wait.
			int tapX=(x+w/2)/8, tapY=(y+h/2)/2;
			// (Where those over a door's middle lead, when it is wholly under
			// them; at most eight.)
			bool covered=false; int coverTargets[8], coverCount=0;
			{
				auto coveringAt=[&](int px, int py, int *targets, int &count) {
					count=0;
					for (int k=0;k<::Scummverse::WorldBridge::objectCount();++k) {
						int id, ox, oy, ow, oh, owx, owy; ::Scummverse::WorldBridge::object(k,id,ox,oy,ow,oh,owx,owy);
						const ::Scummverse::WorldCatalog::WorldLink *other=::Scummverse::WorldCatalog::worldLinkFrom(g,link.room,id);
						if (k!=found && other && !(other->switched && !::Scummverse::WorldBridge::objectState(k)) && px>=ox && px<ox+ow && py>=oy && py<oy+oh) {
							if (targets && count<8) targets[count]=other->target;
							++count;
						}
					}
					return count>0;
				};
				long best=-1; int bx=tapX, by=tapY, inside=0;
				for (int ty=y/2;ty<(y+h+1)/2;++ty) for (int tx=x/8;tx<=(x+w-1)/8;++tx) {
					const int px=tx*8+4, py=ty*2;
					if (px<x || px>=x+w || py<y || py>=y+h) continue;
					++inside;
					int n;
					const long d=(long)(px-(x+w/2))*(px-(x+w/2))+(long)(py-(y+h/2))*(py-(y+h/2));
					if (!coveringAt(px,py,nullptr,n) && (best<0 || d<best)) { best=d; bx=tx; by=ty; }
				}
				// (A door too narrow for any tap inside it is tapped beside it, by
				// its middle, as before: a tap near a door finds it.)
				covered=inside && best<0;
				if (covered) coveringAt(tapX*8+4,tapY*2,coverTargets,coverCount);
				else { tapX=bx; tapY=by; }
			}
			for (const auto &line : ::Scummverse::WorldCatalog::kWorldTramLines)
				for (const auto &stop : line.ends)
					if (line.game==g && stop.room==link.room && stop.car==link.object) {
						scummverseWorldUnits(g,link.room,stop.exitX,stop.exitY,wx,wy);
						scummverseWorldUnits(g,link.room,stop.ledgeX,stop.ledgeY,tapX,tapY);
						covered=false; // (Its ledge is tapped, not the car.)
					}
			AdjustBoxResult near=me->adjustXYToBeInBox(wx,wy);
			me->putActor(near.x,near.y,_currentRoom);
			const int startRoom=_currentRoom;
			me->startWalkActor(tapX,tapY,-1);
			for (int n=0;n<900 && _currentRoom==startRoom;++n) { stopTalk(); VAR(VAR_HAVE_MSG)=0; scummLoop(4); }
			int source; const int game=scummverseWorldGameOf(_currentRoom,source);
			if (game==g && source==link.target) ++doors;
			// (Wholly under others: through one of them instead, if not this one.)
			else if (covered && game==g && Common::find(coverTargets,coverTargets+MIN(coverCount,8),source)!=coverTargets+MIN(coverCount,8)) {
				++doorCovered; warning("WORLD door %d:%d obj %d -> %d covered by another door (to %d:%d)",g,link.room,link.object,link.target,game,source);
			}
			else { ++doorFailures; warning("WORLD door %d:%d obj %d -> %d failed (now %d:%d)",g,link.room,link.object,link.target,game,source); }
		}
	}
	warning("WORLD doors %d failed %d skipped %d hidden %d covered %d",doors,doorFailures,doorSkipped,doorHidden,doorCovered);
	// Every door led where its map says with 0193 (the walker's routes
	// mended); more than one in a hundred failing is a regression.
	if (doors<500 || doorFailures*100>doors+doorFailures) error("%d of %d doors did not lead where their map says",doorFailures,doors+doorFailures);
	// Story areas: each menu entrance mounts its room.
	int areas=0;
	for (int g=0;g<::Scummverse::WorldCatalog::worldGameCount();++g) {
		const ::Scummverse::WorldCatalog::WorldMap *map=::Scummverse::WorldCatalog::worldHome(g) ? nullptr : ::Scummverse::WorldCatalog::worldMap(g);
		for (int i=0;map && i<map->areaCount;++i) {
			const int room=map->areas[i].room;
			if (!scummverseWorldSceneInstalled(g,room)) continue; // Not offered (see the menu).
			if (!scummverseTravelPlace(g,room)) error("story area %d:%d (%s) not reached: %s",g,room,map->areas[i].name,_scummverseWorldNotice.c_str());
			int source; if (scummverseWorldGameOf(_currentRoom,source)!=g || source!=room) error("story area %d:%d mounted %d",g,room,source);
			++areas;
		}
	}
	warning("WORLD story areas %d",areas);
	// Map rooms (Melee Island, the Venice catacomb tunnels) and floor plans
	// (Castle Brunwald's floors): visitors are small figures. Floor plans
	// show every section (they used to export black).
	int maps=0, plans=0;
	for (int g=0;g<::Scummverse::WorldCatalog::worldGameCount();++g) {
		const ::Scummverse::WorldCatalog::WorldMap *map=::Scummverse::WorldCatalog::worldHome(g) ? nullptr : ::Scummverse::WorldCatalog::worldMap(g);
		for (int i=0;map && i<map->roomCount;++i) {
			const int kind=map->rooms[i].kind;
			if ((kind!=::Scummverse::WorldCatalog::kWorldMapRoom && kind!=::Scummverse::WorldCatalog::kWorldFloorPlan) || !scummverseTravelPlace(g,map->rooms[i].room)) continue;
			if (kind==::Scummverse::WorldCatalog::kWorldFloorPlan) {
				settle(6);
				bool used[256]={}; int colors=0;
				for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) { byte c=*_virtscr[0].getPixels(x,y); if(!used[c]) { used[c]=true; ++colors; } }
				if (colors<16) error("Floor plan %d:%d shows %d colors (sections hidden)",g,map->rooms[i].room,colors);
				++plans;
			}
			settle(6); me->_needRedraw=true; settle(1);
			const double expected=::Scummverse::WorldCatalog::kWorldGames[g].heroHeight*::Scummverse::WorldBridge::sceneScale()*scummverseWorldDepth(me);
			const int drawn=me->_bottom-me->_top;
			if (me->_top>0 && ABS(drawn-expected)>MAX(4.0,expected*0.25)) error("Map %d:%d: visitor drawn %d px tall, expected about %.0f",g,map->rooms[i].room,drawn,expected);
			if (expected>0.4*::Scummverse::WorldCatalog::kWorldGames[g].heroHeight*::Scummverse::WorldBridge::sceneScale()) error("Map %d:%d: visitor not drawn as a map figure",g,map->rooms[i].room);
			++maps;
		}
	}
	warning("WORLD map rooms %d (floor plans %d)",maps,plans);
	if (plans<3) error("Only %d floor plans visited",plans);
	// Every character, in its own room: placed, named, in the talk roster, drawn.
	int everyone=0, small=0;
	for (const auto &cast : ::Scummverse::WorldCatalog::kWorldCast) {
		if (::Scummverse::WorldCatalog::worldHome(cast.game)) continue;
		if (!scummverseTravelPlace(cast.game,cast.room)) error("Character %s: place %d:%d not reached: %s",cast.guest.name,cast.game,cast.room,_scummverseWorldNotice.c_str());
		settle(6);
		Actor *guest=derefActor(25+cast.slot,"world guest");
		if (guest->_room!=_currentRoom || scummverseGuestSlot(guest)!=cast.slot) error("Character %s not placed (room %d)",cast.guest.name,guest->_room);
		if (strcmp((const char *)getObjOrActorName(25+cast.slot),cast.guest.name)) error("Character name %s",(const char *)getObjOrActorName(25+cast.slot));
		if (!(scummverseGuestMask() & (1u<<(25+cast.slot)))) error("Character %s missing from the talk roster",cast.guest.name);
		guest->_needRedraw=true; settle(1);
		const int drawn=guestPixels(guest);
		if (drawn<=0) error("Character %s not drawn (extent %d..%d)",cast.guest.name,guest->_top,guest->_bottom);
		if (drawn<30) { ++small; warning("WORLD small character %s (%d pixels)",cast.guest.name,drawn); }
		++everyone;
	}
	warning("WORLD characters %d (small %d)",everyone,small);
	// Side exits: from a scene whose boxes reach the right side, walk on.
	for (int k=0;k<scummverseWorldSceneCount()-1;++k) {
		int scene=0, count=0; scummverseWorldPlace(k,scene,count);
		if (scene+1>=count || !scummverseTravelLandmark(k) || ::Scummverse::WorldBridge::rightX()<0) continue;
		me->putActor(::Scummverse::WorldBridge::rightX(),::Scummverse::WorldBridge::rightY(),_currentRoom); _scummverseTransitArmed=true;
		scummverseWorldEdges();
		if (!at(k+1)) error("Side exit from scene %d reached room %d",k,_currentRoom);
		++edges; if (edges>=3) break;
	}
	// Save and load inside a scene keep the scene and its picture.
	scummverseTravelLandmark(0); settle(4);
	const int savedRoom=_currentRoom;
	Common::Array<byte> before; before.resize(_screenWidth*_virtscr[0].h);
	for(int y=0;y<_virtscr[0].h;++y) memcpy(&before[y*_screenWidth],_virtscr[0].getPixels(0,y),_screenWidth);
	Common::String file; _saveLoadDescription="Other world";
	if (!saveState(14,false,file) || !loadState(14,false)) error("World save/load failed");
	settle(4);
	if (_currentRoom!=savedRoom || !at(0) || _roomResource!=ScummverseContent::kForeignRoom) error("World lost on load: room %d",_currentRoom);
	for(int y=0;y<_virtscr[0].h;++y) if (memcmp(&before[y*_screenWidth],_virtscr[0].getPixels(0,y),_screenWidth)) error("World picture changed on load (row %d)",y);
	// A missing cache: travel refuses with a reason; a save inside it loads at the airport.
	const Common::Path cache=scummverseWorldCache();
	ConfMan.setPath("scummverse_worlds_path",Common::Path("/nonexistent-worlds"));
	_scummverseWorldRoom=0;
	if (scummverseTravelLandmark(1) || _scummverseWorldNotice.find("isn't installed")==Common::String::npos) error("Missing scene not refused: %s",_scummverseWorldNotice.c_str());
	if (!loadState(14,false)) error("Load without cache failed");
	if (_currentRoom!=53) error("Stranded visitor not moved to the airport: %d",_currentRoom);
	ConfMan.setPath("scummverse_worlds_path",cache);
	// A save from patches 0057..0060 held places as rooms 200 + position: the
	// viewer and anyone there move to the slot room for the same place.
	{
		scummverseTravelLandmark(3); settle(2);
		Actor *companion=derefActor(5,"legacy companion");
		me->putActor(me->getRealPos().x,me->getRealPos().y,205); companion->putActor(20,60,205);
		for (int i=0;i<8;++i) _scummVars[600+i]=0;
		_scummVars[608]=0; _currentRoom=205;
		scummverseRestoreWorld(); settle(2);
		if (!at(5) || me->_room!=_currentRoom || companion->_room!=_currentRoom || _scummVars[608]!=1) error("Legacy place not migrated: room %d",_currentRoom);
		companion->putActor(0,0,0);
	}
	// Eight slot rooms are reused: visiting many places never runs out.
	for (int k=0;k<scummverseWorldSceneCount();k+=3) if (!scummverseTravelLandmark(k) || !at(k)) error("Slot reuse failed at place %d",k);
	// Home again: the Maniac colors are intact.
	scummverseTravelLandmark(2); scummverseTravel(2); settle(4);
	if (_currentRoom>=53 || memcmp(_currentPalette,maniacColors,48)) error("Return home failed: room %d",_currentRoom);
	warning("WORLD visited %d walked %d edges %d guests %d doors %d scaled %d walkers %d seated poses %d",visited,walked,edges,guests,doors,scaled,walkers,seatedPoses);
	warning("SCUMMVERSE_WORLD_VISIT_PASS enabled=1"); quitGame();
