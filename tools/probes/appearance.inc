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
	// Murray (Curse of Monkey Island's talking skull) rests on the ground,
	// bounces like a ball to move (landing when he stops), and talking, his
	// head lifts off his jaw every other step.
	{
		const int murray=worldAppearanceKey(9,49);
		if (!worldAppearance(murray) || strcmp(worldAppearance(murray)->name,"Murray")) error("Murray's key changed");
		if (!scummverseTravel(2)) error("Cannot return to the mansion");
		settle(4);
		request(murray);
		if (!_scummverseAvatarSprite[3]) error("Murray's frames not mounted");
		const int feet=dave->getPos().y-dave->getElevation();
		for (int n=0;n<20;++n) { dave->_needRedraw=true; settle(1); if (ABS(dave->_bottom-feet)>1) error("Murray off the ground at rest: drawn to %d, feet at %d",dave->_bottom,feet); }
		const int restTop=dave->_top;
		// Bouncing along: up and down again more than once.
		const Common::Point start=dave->getRealPos();
		dave->startWalkActor(start.x+10,start.y,-1);
		int highest=0, landings=0, moving=0; bool up=false;
		for (int n=0;n<120 && (dave->_moving || !moving);++n) {
			settle(1); if (!dave->_moving) continue;
			++moving; const int lift=feet-dave->_bottom;
			highest=MAX(highest,lift);
			if (lift>=6) up=true; else if (lift<=1 && up) { up=false; ++landings; }
		}
		if (!moving || highest<8 || landings<2) error("Murray does not bounce: %d steps moving, %d px high, %d landings",moving,highest,landings);
		for (int n=0;n<30;++n) settle(1);
		dave->_needRedraw=true; settle(1);
		if (ABS(dave->_bottom-feet)>1) error("Murray did not land: drawn to %d, feet at %d",dave->_bottom,feet);
		// Talking: the mouth opens and closes.
		scummverseSay(3,"Behold, the mighty Murray speaks, at great and terrible length, to all of you!");
		int opened=0, closed=0;
		for (int n=0;n<40;++n) {
			scummLoop(4); if (getTalkingActor()!=3) continue;
			if (dave->_top<=restTop-2) ++opened; else if (dave->_top==restTop) ++closed;
		}
		stopTalk(); VAR(VAR_HAVE_MSG)=0;
		if (opened<3 || closed<3) error("Murray's mouth does not move (%d open, %d closed)",opened,closed);
		warning("APPEARANCE Murray bounces %d px high, %d landings; mouth %d open, %d closed",highest,landings,opened,closed);
		dave->putActor(start.x,start.y,_currentRoom);
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
	// Curse's Murray a second time, in the green of the ship's hold where he
	// washed up (his costume in that room's colors), bouncing too.
	{
		const int green=worldAppearanceKey(9,949);
		if (!worldAppearance(green) || strcmp(worldAppearance(green)->name,"Murray (green)") || !worldBouncer(9,949) || worldHovers(9,949)) error("Green Murray's key changed");
		if (scummverseCharacterFrames(9,949).empty()) warning("APPEARANCE no export of Curse: green Murray skipped");
		else {
			if (!scummverseTravel(2)) error("Cannot return to the mansion");
			settle(4); request(green);
			if (_scummVars[kScummverseAppearanceVar+3]!=green || !_scummverseAvatarSprite[3] || strcmp((const char *)dave->getActorName(),"Murray (green)")) error("Not playing green Murray");
			dave->_needRedraw=true; settle(1);
			if (ABS(dave->_bottom-(dave->getPos().y-dave->getElevation()))>1) error("Green Murray is not on the ground at rest");
			shot("appearance-murray-green.ppm");
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
		if (_scummVars[kScummverseAppearanceVar+3]!=meteor || FakeAI::appearance[3]!=meteor || dave->_costume!=16 || (_scummVars[kScummverseHomeCostumeVar+3]&0xFF)!=3 || _scummverseAvatarSprite[3])
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
	// The Meteor Police officer and the man-eating plant (Maniac's own): the
	// officer in his own colors under a glass dome; the plant at its everyday
	// size whichever way it faces, on a newly drawn pot whose wheels turn as
	// it rolls, needing no air; both through save/load.
	{
		const int police=worldAppearanceKey(kWorldManiacLooks,15), plant=worldAppearanceKey(kWorldManiacLooks,19);
		if (!worldAppearance(police) || strcmp(worldAppearance(police)->name,"Meteor Police") || !worldAppearance(plant) || strcmp(worldAppearance(plant)->name,"Man-Eating Plant"))
			error("The officer's or the plant's key changed");
		if (!scummverseTravel(2)) error("Cannot return to the mansion");
		settle(4);
		// What the character drew over the background near its feet (-1:
		// nothing): rows from `above` over its feet to `below` under them.
		auto picture=[&](int above, int below) {
			dave->_needRedraw=true; settle(1);
			const int cx=dave->getPos().x-_virtscr[0].xstart, fy=dave->getPos().y;
			Common::Array<int> p;
			for(int y=fy-above;y<fy+below;++y) for(int x=cx-32;x<cx+32;++x) {
				const bool in=x>=0 && x<_screenWidth && y>=0 && y<_virtscr[0].h;
				const byte f=in ? *_virtscr[0].getPixels(x,y) : 0, b=in ? *_virtscr[0].getBackPixels(x,y) : 0;
				p.push_back(f!=b ? f : -1);
			}
			return p;
		};
		auto worldGuestDir=[](int facing) { facing=(facing%360+360)%360; return facing>45 && facing<135 ? 1 : facing>=135 && facing<=225 ? 2 : facing>225 && facing<315 ? 0 : 3; };
		auto rolls=[&](Actor *a) { int gear, x; return scummverseRollingGear(a,gear,x) ? gear : -1; };
		request(police);
		if (dave->_costume!=15 || scummverseColorActor(3)!=15 || !scummverseDomed(dave) || worldBreathes(kWorldManiacLooks,15) || strcmp((const char *)dave->getActorName(),"Meteor Police"))
			error("Not the officer: costume %d colors %d",dave->_costume,scummverseColorActor(3));
		{
			// The dome's white glint, which his own colors do not have.
			const Common::Array<int> p=picture(80,0);
			int glint=0; for(int c : p) glint+=c==15;
			if (!glint) error("No dome on the officer");
			shot("appearance-police.ppm");
		}
		request(plant);
		if (dave->_costume!=19 || scummverseColorActor(3)!=19 || scummverseDomed(dave) || !worldBreathes(kWorldManiacLooks,19) || rolls(dave)!=0 ||
			(_scummVars[kScummverseHomeCostumeVar+3]&0xFF)!=3 || strcmp((const char *)dave->getActorName(),"Man-Eating Plant"))
			error("Not the plant: costume %d colors %d home %d",dave->_costume,scummverseColorActor(3),_scummVars[kScummverseHomeCostumeVar+3]);
		// Its costume's directions are growth stages: always the grown plant
		// (the one facing away), standing in the pot.
		const int dirs[]={180,90,270,0};
		for (int dir : dirs) {
			dave->setDirection(dir); dave->startAnimActor(dave->_standFrame);
			dave->_needRedraw=true; settle(1);
			for (int i=0;i<16;++i) if (dave->_cost.curpos[i]!=0xFFFF && (dave->_cost.frame[i]&3)!=3) error("Facing %d the plant shows stage %d",dir,dave->_cost.frame[i]&3);
			if (dave->_bottom-dave->_top<80 || dave->_bottom-dave->_top>96) error("Facing %d the plant drawn %d..%d",dir,dave->_top,dave->_bottom);
		}
		// One step on: the same plant and pot, the wheels turned.
		dave->setDirection(90); dave->startAnimActor(dave->_standFrame);
		const Common::Array<int> before=picture(17,0);
		dave->putActor(dave->getRealPos().x+1,dave->getRealPos().y,_currentRoom);
		const Common::Array<int> after=picture(17,0);
		int pot=0, potSame=0, wheels=0, wheelsSame=0;
		for (uint i=0;i<before.size();++i) {
			if (before[i]<0 || after[i]<0) continue;
			if (i<12*64u) { ++pot; potSame+=before[i]==after[i]; } else if (i>=14*64u && i<16*64u) { ++wheels; wheelsSame+=before[i]==after[i]; }
		}
		if (pot<40 || potSame!=pot) error("The pot changed as it rolled (%d of %d)",potSame,pot);
		if (wheels<8 || wheelsSame==wheels) error("The wheels did not turn (%d of %d alike)",wheelsSame,wheels);
		warning("APPEARANCE plant: pot %d pixels, wheels %d of %d turned",pot,wheels-wheelsSame,wheels);
		shot("appearance-plant.ppm");
		Common::String file; _saveLoadDescription="Playing the plant";
		if (!saveState(15,false,file) || !loadState(15,false)) error("Save failed");
		settle(4);
		if (_scummVars[kScummverseAppearanceVar+3]!=plant || dave->_costume!=19 || rolls(dave)!=0) error("The plant lost on load");
		// Dead Cousin Ted (Maniac's): his own costume up on newly drawn roller
		// skates, whose wheels turn as he rolls; no air needed.
		const int ted=worldAppearanceKey(kWorldManiacLooks,12);
		request(ted);
		if (dave->_costume!=12 || rolls(dave)!=1 || !worldBreathes(kWorldManiacLooks,12) || strcmp((const char *)dave->getActorName(),"Dead Cousin Ted"))
			error("Not Ted on skates: costume %d gear %d",dave->_costume,rolls(dave));
		settle(2);
		if (dave->getElevation()!=2) error("Ted is not up on his skates (%d)",dave->getElevation());
		dave->setDirection(90); dave->startAnimActor(dave->_standFrame);
		{
			// The skates: the four rows from his lifted feet to the floor
			// (plate, wheels).
			const Common::Array<int> on=picture(3,1);
			dave->putActor(dave->getRealPos().x+1,dave->getRealPos().y,_currentRoom);
			const Common::Array<int> on2=picture(3,1);
			int plate=0, plateSame=0, wheel=0, wheelSame=0;
			for (uint i=0;i<on.size();++i) {
				if (on[i]<0 || on2[i]<0) continue;
				if (i<64u) { ++plate; plateSame+=on[i]==on2[i]; } else { ++wheel; wheelSame+=on[i]==on2[i]; }
			}
			if (plate<10 || plateSame!=plate || wheel<8 || wheelSame==wheel) { shot("appearance-ted.ppm"); error("Ted's skates: plate %d/%d, wheels %d/%d alike (Ted at %d,%d room %d drawn %d..%d elevation %d)",plateSame,plate,wheelSame,wheel,dave->getPos().x-_virtscr[0].xstart,dave->getPos().y,_currentRoom,dave->_top,dave->_bottom,dave->getElevation()); }
			warning("APPEARANCE Ted's skates: plate %d pixels, wheels %d of %d turned",plate,wheel-wheelSame,wheel);
			shot("appearance-ted.ppm");
		}
		{
			// Seen from the side (newly drawn; his costume shows only his
			// front): his glasses and nose out ahead of his hips the way he
			// faces, left and right mirrored; facing away, his own costume.
			auto body=[&](int facing) {
				const int cx=dave->getPos().x-_virtscr[0].xstart, fy=dave->getPos().y;
				for (int y=MAX(0,fy-90);y<MIN<int>(_virtscr[0].h,fy);++y) for (int x=MAX(0,cx-32);x<MIN<int>(_screenWidth,cx+32);++x)
					*(byte *)_virtscr[0].getBackPixels(x,y)=*(byte *)_virtscr[0].getPixels(x,y)=9;
				dave->setDirection(facing); dave->startAnimActor(dave->_standFrame);
				return picture(90,0);
			};
			// Columns drawn (window of 64) in a band of rows from the top of the figure.
			auto extent=[&](const Common::Array<int> &p, int from, int to, int &left, int &right) {
				int top=-1;
				for (uint i=0;i<p.size() && top<0;++i) if (p[i]>=0) top=i/64;
				left=64; right=-1;
				for (int y=top+from;top>=0 && y<=top+to && y<(int)p.size()/64;++y)
					for (int x=0;x<64;++x) if (p[y*64+x]>=0) { left=MIN(left,x); right=MAX(right,x); }
			};
			const Common::Array<int> front=body(180), away=body(0), left=body(270), right=body(90);
			bool ahead[2]={false,false};
			int lead[2]={0,0};
			for (int k=0;k<2;++k) {
				const Common::Array<int> &p=k ? right : left;
				int fl,fr,hl,hr; extent(p,8,13,fl,fr); extent(p,44,55,hl,hr);
				lead[k]=k ? fr-hr : hl-fl; ahead[k]=lead[k]>=4;
			}
			if (!ahead[0] || !ahead[1] || lead[0]!=lead[1] || left==front || right==front || left==right || away!=front)
				error("Ted from the side: glasses ahead of his hips by %d px facing left, %d right; differs from the front %d %d; away as front %d",lead[0],lead[1],left!=front,right!=front,away==front);
			warning("APPEARANCE Ted from the side: glasses and nose %d px ahead of his hips both ways",lead[0]);
			_fullRedraw=true; settle(1);
		}
		request(0);
		if (dave->_costume!=3 || dave->getElevation() || _scummVars[kScummverseHomeCostumeVar+3] || rolls(dave)>=0 || strcmp((const char *)dave->getActorName(),"Dave"))
			error("Not Dave again after Ted: costume %d elevation %d",dave->_costume,dave->getElevation());
		// Day of the Tentacle's Ted (when exported): on his own skates he
		// glides in his standing pose, dressed up for the contest (spaghetti
		// hair, big lips, newly drawn); Chaos (Loom) floats. Neither needs air.
		const int dott=worldAppearanceKey(5,235), chaos=worldAppearanceKey(2,130);
		if (!scummverseCharacterFrames(5,235).empty()) {
			request(dott);
			if (!_scummverseAvatarSprite[3] || !worldBreathes(5,235) || !worldGlider(5,235)) error("Not Day of the Tentacle's Ted");
			// Off the moon (white teeth would not show on it).
			dave->putActor(dave->getRealPos().x-10,dave->getRealPos().y,_currentRoom);
			// The dress-up on his head; his lips (light red) at the front of
			// his face, which looks the way he faces (mirrored to the left).
			const int cx=dave->getPos().x-_virtscr[0].xstart;
			int yellow=0, red=0, white=0, lipsX=0;
			auto dress=[&](int facing) {
				dave->setDirection(facing); dave->_needRedraw=true; settle(1);
				yellow=red=white=lipsX=0;
				for (int y=MAX(0,dave->_top);y<MIN(dave->_top+24,(int)_virtscr[0].h);++y) for (int x=MAX(0,cx-40);x<MIN(cx+40,_screenWidth);++x) {
					const byte f=*_virtscr[0].getPixels(x,y);
					if (f==*_virtscr[0].getBackPixels(x,y)) continue;
					yellow+=f==14; red+=f==12; white+=f==15; if (f==12) lipsX+=x;
				}
				if (yellow<15 || red<4 || white<1) error("No contest dress-up on Ted facing %d: %d yellow, %d red, %d white",facing,yellow,red,white);
				return (double)lipsX/red-cx;
			};
			const double leftLips=dress(270);
			shot("appearance-dott-ted-left.ppm");
			const double rightLips=dress(90);
			if (rightLips<1 || leftLips>-1) error("Ted's lips at %.1f facing right, %.1f facing left",rightLips,leftLips);
			shot("appearance-dott-ted.ppm");
			dave->startWalkActor(dave->getRealPos().x+12,dave->getRealPos().y,-1);
			int moving=0;
			for (int n=0;n<12;++n) { settle(1); if (dave->_moving) { ++moving; if ((_scummverseAvatarShown[3]/64)%3!=0) error("Ted walks instead of gliding"); } }
			if (!moving) error("Ted did not move");
			warning("APPEARANCE Day of the Tentacle's Ted: dress-up %d yellow, %d red, %d white, lips %.1f / %.1f px from his feet; glides",yellow,red,white,rightLips,leftLips);
		} else warning("APPEARANCE no Day of the Tentacle characters here");
		if (!scummverseCharacterFrames(2,130).empty()) {
			request(chaos);
			if (!_scummverseAvatarSprite[3] || worldBreathes(2,130) || !worldHovers(2,130)) error("Not Chaos");
			// How far his feet line rides above the floor (his frames hang
			// a ragged robe below it): the least and most over a bob.
			dave->setDirection(180);
			int fdx, fdy, fw, fh;
			if (!::Scummverse::WorldBridge::guestFrame(_scummverseAvatarSprite[3]-1,worldGuestDir(180),0,0,fdx,fdy,fw,fh) || fh<=0) error("No standing Chaos");
			int highest=1000, lowest=-1000;
			for (int n=0;n<80;++n) {
				dave->_needRedraw=true; settle(1);
				if (dave->_top<=0) error("Chaos is cut off at the top (%d)",dave->_top);
				const double scale=(double)(dave->_bottom-dave->_top)/fh;
				const int lift=dave->getPos().y+(int)floor((fdy+fh)*scale+0.5)-dave->_bottom;
				highest=MIN(highest,lift); lowest=MAX(lowest,lift);
			}
			if (highest<6 || lowest-highest<2) error("Chaos does not float (%d..%d above the floor)",highest,lowest);
			warning("APPEARANCE Chaos floats %d..%d px above the floor, top %d",highest,lowest,dave->_top);
			shot("appearance-chaos.ppm");
		} else warning("APPEARANCE no Loom characters here");
		request(0);
		request(indy);
	}
	// In a plane seat everyone sits: Maniac's own looks down in the chair
	// (no wheels, skates or floating), the others behind the seat's front
	// (nothing of them below it) in the chair's middle, the small ones up on
	// its cushion, giants no taller than a seat allows.
	if (scummverseTravel(6)) {
		for (int id=1;id<25;++id) if (id!=3 && derefActor(id,"cabin")->_room==56) derefActor(id,"cabin")->putActor(0,0,0);
		for (int n=1;n<25;++n) _scummVars[501+n]=0;
		_scummVars[724]=7; _scummVars[725]=1u<<3; _scummVars[727]=3; _scummVars[504]=1; _scummVars[526]=1;
		dave->putActor(63,52,56); scummverseRestoreSeats(); setCameraAtEx(504);
		static const int looks[][2]={{kWorldManiacLooks,19},{kWorldManiacLooks,12},{kWorldManiacLooks,16},{0,42},{0,1},{8,321},{2,130}};
		int sprites=0;
		for (const auto &l : looks) {
			const int key=worldAppearanceKey(l[0],l[1]);
			if (!worldNativeLook(key) && !scummverseCharacterInstalled(l[0],l[1])) continue;
			request(key); _fullRedraw=true; settle(2);
			if (!scummverseSeated(3) || dave->getElevation()!=-4 || dave->getRealPos().y!=52 || dave->getFacing()!=90)
				error("%s not seated: elevation %d at %d,%d facing %d",worldAppearance(key)->name,dave->getElevation(),dave->getRealPos().x,dave->getRealPos().y,dave->getFacing());
			if (worldNativeLook(key)) continue;
			int left=_screenWidth, right=-1, top=1000, bottom=-1;
			for (int y=0;y<_virtscr[0].h;++y) for (int x=0;x<_screenWidth;++x) if (*_virtscr[0].getPixels(x,y)>=192) {
				left=MIN(left,x); right=MAX(right,x); top=MIN(top,y); bottom=MAX(bottom,y); }
			const int middle=(left+right)/2+_virtscr[0].xstart;
			if (right<0 || bottom>=80 || bottom-top<8 || bottom-top>84 || middle<63*8 || middle>63*8+40)
				error("%s in a seat: rows %d..%d, middle %d (chair %d..%d)",worldAppearance(key)->name,top,bottom,middle,63*8,63*8+40);
			++sprites;
		}
		warning("APPEARANCE seated: %d characters from other games",sprites);
		request(indy);
		scummverseArrive();
	}
	// Unknown keys are refused; key 0 makes Dave himself again.
	request(worldAppearanceKey(3,999));
	if (_scummVars[kScummverseAppearanceVar+3]!=indy) error("Unknown character accepted");
	request(0);
	if (_scummVars[kScummverseAppearanceVar+3] || FakeAI::appearance[3] || _scummverseAvatarSprite[3] || strcmp((const char *)dave->getActorName(),"Dave")) error("Not Dave again: %s",(const char *)dave->getActorName());
	warning("SCUMMVERSE_APPEARANCE_PASS enabled=1");
	quitGame();
	return;
