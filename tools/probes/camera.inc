	// The CAMERA through the real game: photos (the room, the whole screen),
	// selfies of three in the mansion and in another world (everyone posed,
	// framed on the player, enlarged), the game held still while a selfie
	// is taken, and everything put back exactly afterwards.
	if (!_scummverseRoaming) { warning("SCUMMVERSE_CAMERA_PASS enabled=0"); quitGame(); return; }
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3; _scummverseRosterPending=false;
	for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.wait=60000; r.speech=60000; }
	namespace Cam = ::Scummverse::Camera;
	using namespace ::Scummverse::WorldCatalog;
	auto settle=[&](int n) { for(int i=0;i<n;++i) { VAR(VAR_HAVE_MSG)=0; stopTalk(); scummLoop(4); } };
	auto shot=[&](const Common::String &name, const Cam::Picture &p) {
		Common::DumpFile f; if(!f.open(Common::Path("/workspace/Maniac-Online/build/"+name))) return;
		Common::String h=Common::String::format("P6\n%d %d\n255\n",p.width,p.height); f.write(h.c_str(),h.size());
		for(size_t i=0;i<p.rgba.size();i+=4) f.write(&p.rgba[i],3);
	};
	// The whole saved state of the game, as a savegame holds it.
	auto state=[&]() {
		Common::MemoryWriteStreamDynamic out(DisposeAfterUse::YES);
		Common::Serializer ser(nullptr, &out); ser.setVersion(121);
		saveLoadWithSerializer(ser);
		return Common::Array<byte>(out.getData(), out.size());
	};
	Actor *dave=derefActor(3,"camera player");
	const VirtScreen &main=_virtscr[kMainVirtScreen];
	// The enlarged picture shows these screen pixels, each kx by ky.
	auto same=[&](const Cam::Picture &p, const byte *pixels, int pitch, int x0, int y0, int kx, int ky) {
		for(int y=0;y<p.height;y+=ky) for(int x=0;x<p.width;x+=kx) {
			const byte *c=_currentPalette+3*pixels[(y0+y/ky)*pitch+x0+x/kx], *d=&p.rgba[((size_t)y*p.width+x)*4];
			if(d[0]!=c[0] || d[1]!=c[1] || d[2]!=c[2] || d[3]!=255) return false;
			const byte *e=&p.rgba[((size_t)(y+ky-1)*p.width+x+kx-1)*4];
			if(memcmp(d,e,4)) return false;
		}
		return true;
	};
	if(!scummverseTravel(2)) error("Cannot reach the mansion");
	settle(6);
	// Bernard and Michael beside Dave, Wendy far off.
	const int near[]={5,4}, nearX[]={6,-6};
	for(int i=0;i<2;++i) { Actor *a=derefActor(near[i],"near"); a->putActor(dave->getRealPos().x+nearX[i]/8*0+(i?-3:3),dave->getRealPos().y,_currentRoom); a->showActor(); a->setDirection(90); a->startAnimActor(a->_standFrame); }
	settle(4);
	// A photo of the room (CLEAN): 1600 wide, the room's rows, each 5 by 6.
	{
		// (the frame last drawn: taken before the next one is)
		FakeCamera::pictures.clear();
		Common::Array<byte> room(_screenWidth*main.h);
		for(int y=0;y<main.h;++y) memcpy(&room[y*_screenWidth],main.getPixels(0,y),_screenWidth);
		Cam::requestPhoto(false); settle(1);
		if(FakeCamera::pictures.size()!=1) error("Clean photo: %d pictures",(int)FakeCamera::pictures.size());
		const Cam::Picture &p=FakeCamera::pictures[0];
		if(FakeCamera::kinds[0]!=Cam::kClean || p.width!=_screenWidth*5 || p.height!=main.h*6) error("Clean photo %dx%d kind %d",p.width,p.height,FakeCamera::kinds[0]);
		if(!same(p,room.data(),_screenWidth,0,0,5,6)) error("The clean photo is not the room as drawn");
		shot("camera-clean.ppm",p);
		warning("CAMERA clean %dx%d",p.width,p.height);
	}
	// The whole screen (FULL): 1600 by 1200, verbs and inventory included;
	// its room is the clean photo's room (taken in the same still scene).
	// (each photo is of the frame last drawn: the room as it was just before)
	Common::Array<byte> room(_screenWidth*main.h);
	auto picture=[&](bool full) {
		for(int y=0;y<main.h;++y) memcpy(&room[y*_screenWidth],main.getPixels(0,y),_screenWidth);
		FakeCamera::pictures.clear();
		Cam::requestPhoto(full); scummLoop(4);
		if(FakeCamera::pictures.size()!=1) error("%s photo: %d pictures",full?"Full":"Clean",(int)FakeCamera::pictures.size());
		return FakeCamera::pictures[0];
	};
	{
		const Cam::Picture full=picture(true);
		if(FakeCamera::kinds[0]!=Cam::kFull || full.width!=_screenWidth*5 || full.height!=_screenHeight*6) error("Full photo %dx%d",full.width,full.height);
		const int top=main.topline*6, rows=main.h*6, row=full.width*4;
		Cam::Picture roomOnly; roomOnly.width=full.width; roomOnly.height=rows; roomOnly.rgba.assign(full.rgba.begin()+(size_t)top*row,full.rgba.begin()+(size_t)(top+rows)*row);
		if(!same(roomOnly,room.data(),_screenWidth,0,0,5,6)) {
			int first=-1; for(int y=0;y<main.h && first<0;++y) for(int x=0;x<_screenWidth;++x) if(memcmp(&roomOnly.rgba[((size_t)y*6*row/4+x*5)*4],_currentPalette+3*room[y*_screenWidth+x],3)) { first=y; break; }
			error("The full photo's room is not the room as drawn (first different line %d)",first);
		}
		const VirtScreen &verbs=_virtscr[kVerbVirtScreen];
		int lit=0; for(int y=verbs.topline*6;y<(verbs.topline+verbs.h)*6 && y<full.height;y+=6) for(int x=0;x<full.width;x+=5) lit+=memcmp(&full.rgba[((size_t)y*full.width+x)*4],&full.rgba[(size_t)verbs.topline*6*row],3)!=0;
		if(verbs.h<=0 || lit<100) error("No verbs in the full photo (%d)",lit);
		shot("camera-full.ppm",full);
		warning("CAMERA full %dx%d, room %d..%d as drawn, verbs at %d..%d",full.width,full.height,main.topline,main.topline+main.h,verbs.topline,verbs.topline+verbs.h);
		// Speech shows on the full photo, not on the clean one.
		scummverseSay(3,"Say cheese!"); scummLoop(4);
		const Cam::Picture spoken=picture(true);
		int words=0; for(int y=0;y<main.h;++y) for(int x=0;x<_screenWidth;++x) words+=memcmp(&spoken.rgba[((size_t)(top+y*6)*full.width+x*5)*4],_currentPalette+3*room[y*_screenWidth+x],3)!=0;
		if(words<30) error("No speech on the full photo (%d pixels)",words);
		shot("camera-full-speech.ppm",spoken);
		VAR(VAR_HAVE_MSG)=0; stopTalk(); settle(2);
		warning("CAMERA speech on the full photo: %d pixels",words);
	}
	// A selfie of three: the game holds still, each shot posed afresh and
	// framed on Dave, and afterwards the game is exactly as it was.
	// still: a scene where nothing moves (Dave alone), so that the screen
	// one step later can be compared with the one before.
	auto selfie=[&](const char *where, bool still) {
		FakeCamera::pictures.clear();
		settle(2);
		Common::Array<byte> screenBefore(_screenWidth*main.h);
		for(int y=0;y<main.h;++y) memcpy(&screenBefore[y*_screenWidth],main.getPixels(0,y),_screenWidth);
		const Common::Array<byte> before=state();
		Common::Array<int> vars(_scummVars, _numVariables);
		const int16 dx=dave->getRealPos().x, dy=dave->getRealPos().y;
		Cam::requestSelfie(3);
		int steps=0, shown=0;
		byte posed[3][64]={};
		for(;steps<600 && (steps==0 || Cam::busy());++steps) {
			scummLoop(4);
			if((int)FakeCamera::pictures.size()>shown) {
				// Each shot: everyone in the room posing, as drawn.
				for(int id=1;id<_numActors && id<64;++id) posed[shown][id]=_actors[id]->isInCurrentRoom() ? (byte)(_actors[id]->getFacing()/90*16+_actors[id]->_frame) : 0;
				++shown;
			}
			if(Cam::busy() && memcmp(vars.data(),_scummVars,_numVariables*sizeof(int))) error("The game ran during the selfie (%s)",where);
			_system->delayMillis(10);
		}
		if(Cam::busy() || FakeCamera::pictures.size()!=3) error("Selfie in %s: %d pictures after %d steps",where,(int)FakeCamera::pictures.size(),steps);
		for(int i=0;i<3;++i) {
			const Cam::Picture &p=FakeCamera::pictures[i];
			if(FakeCamera::kinds[i]!=Cam::kSelfie || FakeCamera::shot[i]!=i || FakeCamera::shots[i]!=3) error("Selfie %d labelled %d %d/%d",i,FakeCamera::kinds[i],FakeCamera::shot[i],FakeCamera::shots[i]);
			// Enlarged by whole pixels (rows 6/5 of columns), 4:5 to 4:3 as shown.
			int m=0;
			for(int k=1;k<40;++k) if(p.width%(5*k)==0 && p.height%(6*k)==0) { int kx,ky; Cam::factors(p.width/(5*k),p.height/(6*k),kx,ky); if(kx==5*k) m=k; }
			if(!m) error("Selfie %d (%dx%d) is not whole pixels",i,p.width,p.height);
			const double aspect=(double)p.width/p.height;
			if(aspect<0.78 || aspect>1.35 || p.width<1200) error("Selfie %d is %dx%d",i,p.width,p.height);
			shot(Common::String::format("camera-selfie-%s-%d.ppm",where,i),p);
		}
		int differ=0;
		for(int i=1;i<3;++i) differ+=memcmp(posed[i],posed[i-1],sizeof(posed[i]))!=0 || FakeCamera::pictures[i].rgba!=FakeCamera::pictures[i-1].rgba;
		if(!differ && !still) error("The selfie's shots are all alike (%s)",where);
		const Common::Array<byte> after=state();
		if(after.size()!=before.size() || memcmp(after.data(),before.data(),after.size())) {
			uint first=0; while(first<MIN(after.size(),before.size()) && after[first]==before[first]) ++first;
			for(uint i=0,n=0;i<MIN(after.size(),before.size()) && n<40;++i) if(after[i]!=before[i]) { warning("CAMERA diff at %u: %d -> %d",i,before[i],after[i]); ++n; }
			error("The selfie changed the game (%s): %u and %u bytes, first difference at %u",where,(uint)before.size(),(uint)after.size(),first);
		}
		if(dave->getRealPos().x!=dx || dave->getRealPos().y!=dy) error("Dave moved");
		// One step on, the room is drawn as it was.
		scummLoop(4);
		int changed=0;
		for(int y=0;y<main.h;++y) for(int x=0;x<_screenWidth;++x) changed+=*main.getPixels(x,y)!=screenBefore[y*_screenWidth+x];
		if(still && changed) error("The room looks different after the selfie (%s): %d pixels",where,changed);
		settle(2);
		warning("CAMERA selfie %s: %dx%d, %dx%d, %dx%d in %d steps, state unchanged",where,FakeCamera::pictures[0].width,FakeCamera::pictures[0].height,
			FakeCamera::pictures[1].width,FakeCamera::pictures[1].height,FakeCamera::pictures[2].width,FakeCamera::pictures[2].height,steps);
	};
	selfie("mansion",false);
	// Dave alone, standing still: the room looks exactly as before.
	{
		struct Away { int id, x, y; };
		Common::Array<Away> away;
		for(int id=1;id<_numActors;++id) if(id!=3 && _actors[id]->isInCurrentRoom()) {
			Away w={id,_actors[id]->getRealPos().x,_actors[id]->getRealPos().y}; away.push_back(w); _actors[id]->putActor(0,0,0);
		}
		dave->stopActorMoving(); dave->setDirection(180); dave->startAnimActor(dave->_standFrame);
		settle(4);
		// Those sent away are not marked for drawing (as after a step that
		// drew none of them): a selfie's full redraw must not leave them so.
		for (const Away &w : away) _actors[w.id]->_needRedraw=false;
		selfie("alone",true);
		for(const Away &w : away) { _actors[w.id]->putActor(w.x,w.y,_currentRoom); _actors[w.id]->showActor(); }
		settle(2);
	}
	// While iOS asks for access to Photos the game holds still.
	{
		Cam::setHold(true);
		Common::Array<int> vars(_scummVars, _numVariables);
		const Common::Array<byte> before=state();
		for(int i=0;i<20;++i) scummLoop(4);
		if(memcmp(vars.data(),_scummVars,_numVariables*sizeof(int)) || state()!=before) error("The game ran while held");
		Cam::setHold(false);
	}
	// Another world (Melee Island, if exported): guests and Bernard as
	// Guybrush pose from their own frames.
	if (worldAppearance(worldAppearanceKey(0,1))) {
		if(!scummverseSwitchActor(5)) error("Cannot switch to Bernard");
		scummverseWorldRequest(worldAppearanceRequest(worldAppearanceKey(0,1))); scummverseUpdateRoaming(0); settle(2);
		if(!scummverseSwitchActor(3)) error("Cannot switch back to Dave");
		if(!scummverseTravelPlace(0,33)) error("Cannot visit Melee Island");
		settle(8);
		Actor *bernard=derefActor(5,"world companion");
		bernard->putActor(dave->getRealPos().x+3,dave->getRealPos().y,_currentRoom); bernard->showActor();
		for (int id=1;id<25;++id) { Roamer &r=_scummverseRoamers[id]; r=Roamer(); r.room=derefActor(id,"parked")->_room; r.wait=60000; r.speech=60000; }
		settle(4);
		if(!_scummverseAvatarSprite[5]) error("Bernard is not Guybrush on Melee Island");
		selfie("melee",false);
	} else warning("CAMERA no Melee Island here (not exported)");
	// A selfie nobody can save says so and changes nothing.
	{
		Cam::setSink(nullptr,nullptr); FakeCamera::pictures.clear();
		settle(2);
		const Common::Array<byte> before=state();
		Cam::requestSelfie(1);
		int steps=0; for(;steps<300 && (steps==0 || Cam::busy());++steps) { scummLoop(4); _system->delayMillis(10); }
		std::string text;
		if(Cam::busy() || !Cam::takeNote(text) || text!="Couldn't take the selfie" || state()!=before) error("An unsaved selfie: '%s' after %d steps",text.c_str(),steps);
		Cam::setSink(FakeCamera::sink,nullptr);
		settle(2);
	}
	// No selfie without the player in the room.
	{
		dave->putActor(0,0,0); FakeCamera::pictures.clear();
		Cam::requestSelfie(1); settle(1);
		std::string text;
		if(!FakeCamera::pictures.empty() || Cam::busy() || !Cam::takeNote(text) || text!="No selfie here") error("A selfie without the player");
	}
	warning("SCUMMVERSE_CAMERA_PASS enabled=1");
	quitGame();
	return;
