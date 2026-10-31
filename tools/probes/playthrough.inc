	// PLAYTHROUGH: Maniac Mansion played to one of its endings, the player's
	// own taps (tools/test_playthrough_engine.py). A route of sentences, each
	// made as the player makes it: the verb tapped, then the thing (a room
	// object or actor where a tap finds it, walking the kid towards it until
	// it shows; an inventory item), twice or with its second thing, then the
	// game's own sentence script walks the kid there and does it. Every step
	// checks what the game did (an object's state, who owns what, the room, a
	// variable the game sets), and fails naming the step.
	// - Story mode (Maniac's own story, scummverse-story-maniac, none of the
	//   mansion's additions): the kid screen, the opening, three kids, and
	//   the ending where actor 15 takes actor 16 away (script 43, variable
	//   162 at 3) and the game is won (script 63).
	// - Explore mode (the mansion, scummverse_roaming, other games' visitors):
	//   one kid takes the same things in the same rooms; what the sandbox
	//   replaces by design (docs/roaming.md: no opening, doors without keys or
	//   codes, lights on, no captures, timed events or endings) is checked as
	//   it promises, and the ending is not reached.
	// The two codes the game picks at random (variables 59..62, set by script
	// 102 when actor 9 plays object 206; 77..80, set at the start) are read
	// from its variables, where the player reads them on the screen.
	// No game text; things by number (V1 verbs: 1 open, 3 give, 4 turn on,
	// 5 turn off, 6 fix, 8 unlock, 9 push, 10 pull, 11 use, 12 read, 13 walk
	// to, 14 pick up).
	if (_game.id == GID_MANIAC && ConfMan.hasKey("scummverse_playthrough")) {
	const Common::String ptMode = ConfMan.get("scummverse_playthrough");
	// (Story mode: after the story, the app goes back to the mansion; done.)
	if (ptMode == "story" && !_scummverseStory) { warning("SCUMMVERSE_PLAYTHROUGH_HOME room=%d", _currentRoom); quitGame(); return; }
	// (The game's own restart, its game over or the end of the win, would
	// come back here.)
	static bool ptEntered = false;
	if (ptEntered) error("SCUMMVERSE_PLAYTHROUGH_FAIL the game restarted (game over?)");
	ptEntered = true;
	static const char *const ptRoute = R"PT(
# Kids (actors): 3, 2 (chosen first: New Kid's verb 21), 5 (verb 22). (room) in brackets.
@story
step 1    # (45) 261 and 263 tapped (kids 2, 5), 403; the opening; (44)
until room 45 max=3000
tap 261
wait 20
tap 263
wait 20
tap 403
until room 44 max=20000
settle 20000
expect var 47 == 3
expect var 48 == 2
expect var 49 == 5
step 2    # 3: (1) 54 pulled, 55 taken, 61 unlocked with 55; (10)
walk 258 1
do 10 54
expect state 54 8 8
do 14 55
expect owns 55
do 8 61 55
expect state 61 8 8
walk 61 10
step 3    # 2, 5: (1), (10)
kid 2
walk 258 1
walk 61 10
kid 5
walk 258 1
walk 61 10
step 4    # 2: 351 pushed and held (69 open); 5: (8) dark, 335 on, 158 taken; (10)
kid 2
do 9 351
expect state 69 8 8
kid 5
walk 69 8
expect var 12 == 0
do 4 335
expect var 12 != 0
do 14 158
expect owns 158
walk 154 10
step 5    # actor 10 leaves (7); 5: 84 taken (7), 125 unlocked with 158 (36); (6)
until not actor 10 7 max=30000
door 68 7
do 14 84
expect owns 84
door 82 37
door 98 36
do 8 125 158
expect state 125 8 8
door 125 6
step 6    # 3: 130 (36); 198, 200 (14); 198, 130 given to actor 14 (12); (38)
kid 3
door 68 7
door 82 37
door 98 36
do 14 130
expect owns 130
door 124 37
door 95 7
door 81 10
walk 230 11
door 180 14
do 14 198
expect owns 198
do 14 200
expect owns 200
door 197 11
door 182 13
walk 194 12
do 3 198 14
expect var 98 >= 7
do 3 130 14
expect var 99 == 1
walk 457 38
expect var 103 == 1
step 7    # 3: 215 (20); 111 used (25: bit 2947); 144 opened, 151 unlocked with 215, 152 taken (16)
door 460 21
walk 235 20
do 14 215
expect owns 215
door 213 21
door 465 38
door 463 25
do 11 111
expect bit 2947 == 1
door 109 38
walk 229 12
walk 456 13
door 193 11
walk 179 10
door 68 7
door 82 37
door 98 36
door 125 6
door 138 16
do 1 144
until state 144 8 0 max=200
do 8 151 215
expect state 151 8 8
do 14 152
expect owns 152
step 8    # 2: (11), (13), (12), (38), (21)
kid 2
walk 230 11
door 182 13
walk 194 12
walk 457 38
door 460 21
step 9    # actor 11 leaves (26) (script 87); 2: 34, 104 taken (26); (21); actor 11 back
until running 87 max=8000
until actor 11 12 max=4000
door 465 38
door 462 26
do 14 34
do 14 104
expect owns 104
door 39 38
door 460 21
until stopped 98 max=8000
until actor 11 26 max=4000
step 10   # 3: 52 pulled, 53 opened (1); 66 on (29: 139 set, script 12); 5: (2) 141, 142, 167; 3: 66 off; 5: 167 with 84
kid 3
door 143 6
door 137 36
door 124 37
door 95 7
door 81 10
door 67 1
do 10 52
expect state 52 8 8
do 1 53
expect state 53 8 8
walk 53 29
expect state 139 8 0
do 4 66
until state 139 8 8 max=300
expect running 12
kid 5
walk 172 2
do 14 141
expect owns 141
do 14 142
expect owns 142
do 1 142
expect owns 167
walk 171 6
kid 3
do 5 66
until state 139 8 0 max=300
until stopped 12 max=300
kid 5
do 11 167 84
expect var 50 == 2
step 11   # 5 gives 84 to 3 (10); 3 holds 351, 5 to (8); 3: 200 with 101 (27), (15), 84 on
door 137 36
door 124 37
door 95 7
door 81 10
kid 3
walk 234 1
door 61 10
kid 5
do 3 84 3
expect owner 84 3
kid 3
do 9 351
expect state 69 8 8
kid 5
walk 69 8
kid 3
walk 230 11
door 182 13
walk 194 12
walk 457 38
door 464 27
do 11 200 101
expect state 101 8 8
door 102 15
do 4 84
expect var 156 == 1
step 12   # 5: 156 opened, 157 off (8); 3: 225 fixed with 152 (15: script 101); 5: 157 on
kid 5
do 1 156
expect state 156 8 8
do 5 157
expect state 157 8 8
kid 3
do 6 225 152
expect state 225 8 8
expect running 101
kid 5
do 4 157
expect state 157 8 0
walk 154 10
step 13   # 5: 72 opened, 73 taken (3); 73 with 398 (21); 141 given to 2
door 70 3
do 1 72
expect state 72 8 8
do 14 73
expect owns 73
door 71 10
walk 230 11
door 182 13
walk 194 12
walk 457 38
door 460 21
do 11 73 398
expect state 212 8 0
do 3 141 2
expect owner 141 2
step 14   # 2: (19); actor 10 takes 2 to (4)
kid 2
door 465 38
expect actor 10 19
door 461 19
until egoroom 4 max=3000
settle
step 15   # script 102 sets variables 59..62; 2: 161, 162 unlocked with 141, 160, 163 opened, keypad (43) 59..62
until var 59 != 100 max=6000
do 8 161 141
do 8 162 141
expect state 160 4 0
do 1 160
expect state 160 8 8
do 1 163
dial 59
until state 163 8 8 max=600
step 16   # 5: 399 on, 397 read, 399 used, keypad (43) 77..80; scripts 42, 136
kid 5
do 4 399
expect var 172 == 1
do 12 397
do 11 399
dial 77
until running 42 max=600
until stopped 42 max=6000
settle
expect running 136
expect var 75 == 1
step 17   # script 43 (actor 15): variable 162 3; 2: 214 taken (4), (31), 214 given to actor 13, (30)
kid 2
until running 43 max=4000
settle 20000
until stopped 43 max=8000
expect var 162 == 3
do 14 214
expect owns 214
walk 163 31
do 3 214 13
expect var 151 == 1
door 168 30
step 18   # 2: 104 with 415 (255 opens), (51), 176 off; scripts 126, 63; (0)
do 11 104 415
expect state 255 8 8
walk 255 51
do 5 176
until running 63 max=6000
until room 0 max=6000
wait 300
expect running 63
expect var 162 == 3
expect var 101 != 4
@explore
step 1    # kids 3, 2, 5 as the sandbox picks them, 3 played, no opening; New Kid: 2, then 3
settle 20000
expect var 47 == 3
expect var 48 == 2
expect var 49 == 5
expect ego 3
expect stopped 131
kid 2
kid 3
expect egoroom 44
step 2    # 3: (1) 54 pulled, 55 taken, 61 (a passage: opens); (10)
walk 258 1
do 10 54
expect state 54 8 8
do 14 55
expect owns 55
do 8 61 55
expect state 61 8 8
walk 61 10
step 3    # 3: 198, 200 (14); 215 (20); 111 (25); 34, 104 (26); 200 with 101 (27); (15)
walk 230 11
door 180 14
do 14 198
expect owns 198
do 14 200
expect owns 200
door 197 11
door 182 13
walk 194 12
walk 457 38
door 460 21
walk 235 20
do 14 215
expect owns 215
door 213 21
door 465 38
door 463 25
do 11 111
expect bit 2947 == 1
door 109 38
door 462 26
do 14 34
do 14 104
expect owns 104
door 39 38
door 464 27
do 11 200 101
expect state 101 8 8
door 102 15
door 223 27
door 99 38
walk 229 12
walk 456 13
door 193 11
walk 179 10
step 4    # 3: 351 pushed (69 opens); (8) lit already; 158
do 9 351
expect state 69 8 8
walk 69 8
expect var 12 != 0
do 14 158
expect owns 158
walk 154 10
step 5    # 3: 84 (7); 130, 125 with 158 (36); (6) 139 set already; 141, 142, 167 (2); 167 with 84
door 68 7
do 14 84
expect owns 84
door 82 37
door 98 36
do 14 130
expect owns 130
do 8 125 158
expect state 125 8 8
door 125 6
expect state 139 8 8
walk 172 2
do 14 141
expect owns 141
do 14 142
expect owns 142
do 1 142
expect owns 167
walk 171 6
do 11 167 84
expect var 50 == 2
step 6    # 3: 144 opened, 151 unlocked with 215, 152 (16)
door 138 16
do 1 144
until state 144 8 0 max=200
do 8 151 215
expect state 151 8 8
do 14 152
expect owns 152
step 7    # 3: 52, 53 (1); 66 on and off (29): no script 12
door 143 6
door 137 36
door 124 37
door 95 7
door 81 10
door 67 1
do 10 52
expect state 52 8 8
do 1 53
expect state 53 8 8
walk 53 29
do 4 66
until state 66 8 8 max=300
wait 60
expect stopped 12
do 5 66
until state 66 8 0 max=300
walk 234 1
door 61 10
step 8    # 3: 156, 157 off (8): no script 12; 84 on, 225 fixed with 152 (15): no script 101; 157 on (8)
walk 69 8
do 1 156
expect state 156 8 8
do 5 157
expect state 157 8 8
wait 60
expect stopped 12
walk 154 10
walk 230 11
door 182 13
walk 194 12
walk 457 38
door 464 27
door 102 15
do 4 84
expect var 156 == 1
do 6 225 152
expect state 225 8 8
expect stopped 101
door 223 27
door 99 38
walk 229 12
walk 456 13
door 193 11
walk 179 10
walk 69 8
do 4 157
expect state 157 8 0
step 9    # 3: (4) by 155 (a passage: no key); 161, 162 unlocked with 141; 160; 163 (a passage: no code)
door 155 4
do 8 161 141
do 8 162 141
expect state 160 4 0
do 1 160
expect state 160 8 8
do 1 163
expect state 163 8 8
expect var 59 == 100
step 10   # 3: (31), (30), (51) (255 a passage: no 104); 176 off: no scripts 126, 63
walk 163 31
door 168 30
walk 255 51
do 5 176
expect state 176 8 8
wait 600
expect stopped 126
expect stopped 63
expect var 162 == 0
)PT";
	warning("SCUMMVERSE_PLAYTHROUGH_BEGIN mode=%s story=%d roaming=%d ready=%d safety=%d doors=%d room=%d", ptMode.c_str(), _scummverseStory, _scummverseRoaming, _scummverseRoamingReady, _scummverseExplorationSafety, _scummverseExplorationDoors, _currentRoom);
	int ptFrames = 0, ptStep = 0; uint32 ptTicks = 0;
	Common::String ptLine;
	auto ptEgo = [&]() { return derefActor(VAR(VAR_EGO), "playthrough"); };
	// (What a failure shows: who is played, where, carrying what.)
	auto ptState = [&]() {
		Common::String inv;
		for (int k = 1; k <= getInventoryCount(VAR(VAR_EGO)); ++k) inv += Common::String::format(" %d", findInventory(VAR(VAR_EGO), k));
		return Common::String::format("kid %d in room %d at %d,%d, carrying%s", VAR(VAR_EGO), ptEgo()->_room, ptEgo()->getRealPos().x, ptEgo()->getRealPos().y, inv.c_str());
	};
#define PT_FAIL(...) error("SCUMMVERSE_PLAYTHROUGH_FAIL step %d [%s] frame %d room %d: %s (%s)", ptStep, ptLine.c_str(), ptFrames, _currentRoom, Common::String::format(__VA_ARGS__).c_str(), ptState().c_str())
	const bool ptTrace = ConfMan.hasKey("scummverse_playthrough_trace");
	bool ptSeen[256]; memset(ptSeen, 0, sizeof(ptSeen));
	bool ptVisitorRooms[256]; memset(ptVisitorRooms, 0, sizeof(ptVisitorRooms));
	int ptVisitorFrames = 0, ptVisitorRoomCount = 0, ptVisitorMost = 0, ptLastRoom = -1;
	// Each frame: no death or game over (scripts 61, 62); other games'
	// visitors in the room shown, counted; with the trace, the scripts that
	// start and the rooms shown.
	auto ptWatch = [&]() {
		bool now[256]; memset(now, 0, sizeof(now));
		for (int i = 0; i < NUM_SCRIPT_SLOT; ++i)
			if (vm.slot[i].status != ssDead && vm.slot[i].where == WIO_GLOBAL && vm.slot[i].number < 256) now[vm.slot[i].number] = true;
		Common::String started;
		for (int s = 0; s < 256; ++s) { if (now[s] && !ptSeen[s]) started += Common::String::format(" %d", s); ptSeen[s] = now[s]; }
		if (ptTrace && !started.empty()) warning("PT frame %d room %d kid %d: scripts%s", ptFrames, _currentRoom, VAR(VAR_EGO), started.c_str());
		if (ptTrace && ptLastRoom != _currentRoom) warning("PT frame %d room %d (from %d)", ptFrames, _currentRoom, ptLastRoom);
		ptLastRoom = _currentRoom;
		if (now[61] || now[62]) PT_FAIL("death or game over (script %d)", now[62] ? 62 : 61);
		int here = 0;
		for (int v = 0; v < kScummverseVisitorSlots; ++v) {
			const ScummverseVisitor &w = _scummverseVisitors[v];
			if (w.who && w.actor && w.placed && w.actor->_room == _currentRoom) ++here;
		}
		if (here) {
			++ptVisitorFrames;
			ptVisitorMost = MAX(ptVisitorMost, here);
			if (!ptVisitorRooms[_currentRoom]) { ptVisitorRooms[_currentRoom] = true; ++ptVisitorRoomCount; }
		}
	};
	// One turn of the main loop, as go() takes it (its delta, Maniac V1's
	// rounding to three), without waiting for the clock.
	auto ptFrame = [&]() {
		int delta = VAR_TIMER_NEXT != 0xFF ? VAR(VAR_TIMER_NEXT) : 4;
		if (delta < 1) delta = 1;
		if (_game.version == 1) delta = (delta + 2) / 3 * 3;
		_lastWaitTime = _system->getMillis();
		scummLoop(delta);
		++ptFrames; ptTicks += delta;
		ptWatch();
	};
	// Why the game is not yet waiting for the player (0: it is): no input,
	// a cutscene, a sentence queued or being done, the kid walking.
	auto ptBusy = [&]() -> int {
		if (_userPut <= 0) return 1;
		if (vm.cutSceneStackPointer) return 2;
		if (_sentenceNum) return 3;
		if (isScriptRunning(2)) return 4;
		for (int i = 0; i < NUM_SCRIPT_SLOT; ++i)
			if (vm.slot[i].status != ssDead && (vm.slot[i].where == WIO_ROOM || vm.slot[i].where == WIO_INVENTORY || vm.slot[i].where == WIO_FLOBJECT) && vm.slot[i].number == (uint)VAR(VAR_ACTIVE_OBJECT1)) return 5;
		if (ptEgo()->_moving) return 6;
		return 0;
	};
	auto ptSettle = [&](int limit) {
		int calm = 0, n = 0;
		for (; n < limit && calm < 8; ++n) { ptFrame(); calm = ptBusy() ? 0 : calm + 1; }
		if (calm < 8) PT_FAIL("the game never waited for the player (busy %d after %d frames)", ptBusy(), n);
	};
	// A tap on the screen (screen pixels), taken as the mouse's: clicked and
	// down for one frame (input.cpp's msClicked | msDown).
	auto ptClick = [&](int sx, int sy) {
		_mouse.x = sx; _mouse.y = sy; _leftBtnPressed = 3;
		ptFrame();
		_leftBtnPressed = 0;
	};
	// V1's sentence variables (vars.cpp): verb 26, things 27 and 28, preposition 29.
	auto ptVerb = [&](int verb) {
		for (int i = 1; i < _numVerbs; ++i) {
			const VerbSlot &vs = _verbs[i];
			if (vs.verbid != verb || vs.curmode != 1 || vs.saveid) continue;
			const int x = (vs.curRect.left + vs.curRect.right) / 2, y = (vs.curRect.top + vs.curRect.bottom) / 2;
			if (findVerbAtPos(x, y) != i) continue;
			ptClick(x, y);
			if (_scummVars[26] != verb && verb != 7 && verb < 20) PT_FAIL("verb %d tapped, the sentence's verb is %d", verb, _scummVars[26]);
			return;
		}
		PT_FAIL("verb %d not shown", verb);
	};
	// Where in the room (pixels) a tap finds the object (or the actor, 25 or
	// below): the point nearest its middle, as the input script reads it
	// (V1's eight by two pixel steps).
	auto ptPoint = [&](int obj, int &rx, int &ry) -> bool {
		const VirtScreen &vs = _virtscr[kMainVirtScreen];
		int left, top, right, bottom, best = 1 << 30;
		if (obj <= 25) {
			Actor *a = derefActor(obj, "playthrough");
			if (a->_room != _currentRoom) return false;
			left = a->getRealPos().x * V12_X_MULTIPLIER - 24; right = a->getRealPos().x * V12_X_MULTIPLIER + 24; top = a->_top; bottom = a->_bottom;
		} else {
			const int idx = getObjectIndex(obj);
			if (idx < 0) return false;
			left = _objs[idx].x_pos; top = _objs[idx].y_pos; right = left + _objs[idx].width; bottom = top + _objs[idx].height;
		}
		const int cx = (left + right) / 2, cy = (top + bottom) / 2;
		bool found = false;
		for (int x = MAX(0, left) / 8 * 8; x < MIN(right, (int)_roomWidth); x += 8)
			for (int y = MAX(0, top) / 2 * 2; y < MIN(bottom, (int)vs.h); y += 2) {
				if ((obj <= 25 ? getActorFromPos(x, y) : findObject(x, y)) != obj) continue;
				const int d = (x + 4 - cx) * (x + 4 - cx) + (y - cy) * (y - cy);
				if (d < best) { best = d; rx = x + 4; ry = y; found = true; }
			}
		return found;
	};
	auto ptOnScreen = [&](int rx) { const VirtScreen &vs = _virtscr[kMainVirtScreen]; return rx >= vs.xstart && rx < vs.xstart + _screenWidth; };
	// On screen, and not at an edge the camera could still scroll past.
	auto ptWellOnScreen = [&](int rx) {
		const VirtScreen &vs = _virtscr[kMainVirtScreen];
		if (!ptOnScreen(rx)) return false;
		const bool leftEnd = vs.xstart <= 0, rightEnd = vs.xstart + _screenWidth >= _roomWidth;
		return (leftEnd || rx >= vs.xstart + 40) && (rightEnd || rx < vs.xstart + _screenWidth - 40);
	};
	auto ptCarried = [&](int obj) { return obj > 25 && whereIsObject(obj) == WIO_INVENTORY; };
	// Something of the game's own took over while the player was tapping (a
	// cutscene, no input, another room shown): wait, then tap again.
	int ptRoomAt = -1;
	auto ptInterrupted = [&]() { return _userPut <= 0 || vm.cutSceneStackPointer || _currentRoom != ptRoomAt; };
	// Off screen: the kid walks towards it, as a player would (Walk to the
	// floor at the screen's edge on its side, along the floor the kid stands
	// on or in front of it, where no object is), until it shows.
	auto ptShow = [&](int obj) -> bool {
		if (ptCarried(obj)) return true;
		int rx = 0, ry = 0;
		// (An actor not yet drawn has no tap point: where it stands.)
		auto where = [&]() -> bool {
			if (obj <= 25) { Actor *a = derefActor(obj, "playthrough"); rx = a->getRealPos().x * V12_X_MULTIPLIER; return a->_room == _currentRoom; }
			return ptPoint(obj, rx, ry);
		};
		if (!where()) PT_FAIL("%d cannot be tapped in room %d", obj, _currentRoom);
		for (int tries = 0; !ptWellOnScreen(rx) && tries < 40; ++tries) {
			const VirtScreen &vs = _virtscr[kMainVirtScreen];
			const int idx = obj > 25 ? getObjectIndex(obj) : -1;
			const int floors[2] = {ptEgo()->getRealPos().y * V12_Y_MULTIPLIER, idx >= 0 ? _objs[idx].walk_y : ptEgo()->getRealPos().y * V12_Y_MULTIPLIER};
			const int sx = rx < vs.xstart + _screenWidth / 2 ? 4 : _screenWidth - 4;
			int sy = -1;
			for (int f = tries & 1; f < 2 && sy < 0; ++f)
				for (int d = 0; d < 40 && sy < 0; d += 2)
					for (int sgn = -1; sgn <= 1 && sy < 0; sgn += 2) {
						const int y = CLIP(floors[f] + sgn * d, 0, vs.h - 2) / 2 * 2;
						if (!findObject((vs.xstart + sx) / 8 * 8, y)) sy = y;
					}
			if (sy < 0) PT_FAIL("no floor to walk on towards %d", obj);
			ptVerb(13);
			ptClick(sx, sy + vs.topline);
			ptSettle(3000);
			// (And the camera has stopped.)
			for (int n = 0, still = 0; n < 200 && still < 3; ++n) { const int x0 = camera._cur.x; ptFrame(); still = camera._cur.x == x0 ? still + 1 : 0; }
			if (ptInterrupted()) return false;
			if (!where()) PT_FAIL("%d gone while walking to it", obj);
		}
		if (!ptOnScreen(rx)) PT_FAIL("%d (x %d) never came on screen", obj, rx);
		return true;
	};
	// One tap on a thing. Carried things are tapped where the inventory
	// shows them, as checkExecVerbs passes such a tap on (kInventoryClickArea).
	auto ptTap = [&](int obj) -> bool {
		if (ptInterrupted()) return false;
		if (ptCarried(obj)) {
			if (getOwner(obj) != VAR(VAR_EGO)) PT_FAIL("%d is carried by %d, not %d", obj, getOwner(obj), VAR(VAR_EGO));
			runInputScript(kInventoryClickArea, obj, 0);
			return true;
		}
		int rx = 0, ry = 0;
		if (!ptPoint(obj, rx, ry)) PT_FAIL("%d cannot be tapped in room %d", obj, _currentRoom);
		if (!ptOnScreen(rx)) PT_FAIL("%d (x %d) off screen", obj, rx);
		const VirtScreen &vs = _virtscr[kMainVirtScreen];
		ptClick(rx - vs.xstart, ry + vs.topline);
		if (ptTrace) warning("PT frame %d tap %d at %d,%d: sentence %d %d %d", ptFrames, obj, rx, ry, _scummVars[26], _scummVars[27], _scummVars[28]);
		return !ptInterrupted();
	};
	// A sentence: the verb, the thing (and its second); false when
	// interrupted before its last tap, which does it.
	auto ptAttempt = [&](int verb, int o1, int o2) -> bool {
		ptSettle(20000);
		ptRoomAt = _currentRoom;
		if (!ptShow(o1) || (o2 && !ptShow(o2))) return false;
		// (The first still well on screen once the second shows.)
		if (!ptCarried(o1)) {
			int rx = -1, ry = 0;
			if (o1 <= 25) rx = derefActor(o1, "playthrough")->getRealPos().x * V12_X_MULTIPLIER;
			else ptPoint(o1, rx, ry);
			if (!ptWellOnScreen(rx)) return false;
		}
		ptVerb(verb);
		if (verb == 13) { ptTap(o1); return true; }
		if (!ptTap(o1)) return false;
		if (_scummVars[27] != o1) PT_FAIL("tapped %d, the sentence has %d", o1, _scummVars[27]);
		if (o2) {
			if (!_scummVars[29]) PT_FAIL("verb %d with %d takes no second thing", verb, o1);
			if (!ptTap(o2)) return false;
			if (_scummVars[28] != o2) PT_FAIL("tapped %d second, the sentence has %d", o2, _scummVars[28]);
			ptTap(o2);
		} else {
			if (_scummVars[29]) PT_FAIL("verb %d with %d wants a second thing", verb, o1);
			ptTap(o1);
		}
		return true;
	};
	auto ptSentence = [&](int verb, int o1, int o2) {
		for (int tries = 0; !ptAttempt(verb, o1, o2); ++tries) {
			if (tries >= 5) PT_FAIL("interrupted %d times", tries + 1);
			if (ptTrace) warning("PT frame %d sentence %d %d %d interrupted; again", ptFrames, verb, o1, o2);
		}
		ptFrame();
		ptSettle(20000);
	};
	// Conditions: room R | egoroom R | state O MASK VALUE | owns O |
	// owner O A | var N OP V | bit N OP V | running S | stopped S |
	// actor A R | ego A, each may follow "not".
	auto ptCond1 = [&](const Common::StringArray &t, uint at) -> bool {
		if (at >= t.size()) PT_FAIL("condition missing");
		const Common::String &k = t[at];
		auto num = [&](uint i) { if (at + i >= t.size()) PT_FAIL("condition %s: too short", k.c_str()); return atoi(t[at + i].c_str()); };
		if (k == "room") return _currentRoom == num(1);
		if (k == "egoroom") return _currentRoom == num(1) && ptEgo()->_room == num(1);
		if (k == "state") return (getState(num(1)) & num(2)) == num(3);
		if (k == "owns") return getOwner(num(1)) == VAR(VAR_EGO);
		if (k == "owner") return getOwner(num(1)) == num(2);
		if (k == "running") return isScriptRunning(num(1));
		if (k == "stopped") return !isScriptRunning(num(1));
		if (k == "actor") return derefActor(num(1), "playthrough")->_room == num(2);
		if (k == "ego") return VAR(VAR_EGO) == num(1);
		if (k == "var" || k == "bit") {
			const int v = k == "var" ? _scummVars[num(1)] : ((_scummVars[num(1) >> 4] >> (num(1) & 15)) & 1);
			if (at + 3 >= t.size()) PT_FAIL("condition %s: too short", k.c_str());
			const Common::String &op = t[at + 2]; const int w = num(3);
			if (op == "==") return v == w;
			if (op == "!=") return v != w;
			if (op == ">=") return v >= w;
			if (op == "<=") return v <= w;
			PT_FAIL("condition %s: operator %s", k.c_str(), op.c_str());
		}
		PT_FAIL("unknown condition %s", k.c_str());
		return false;
	};
	auto ptCond = [&](const Common::StringArray &t, uint at) -> bool {
		const bool neg = at < t.size() && t[at] == "not";
		return neg != ptCond1(t, at + (neg ? 1 : 0));
	};
	const uint32 ptStart = _system->getMillis();
	const Common::StringArray ptLines = Common::StringTokenizer(ptRoute, "\n").split();
	Common::String ptSection = "both";
	for (uint li = 0; li < ptLines.size(); ++li) {
		Common::String line = ptLines[li];
		const int hash = line.findFirstOf('#');
		if (hash >= 0) line = Common::String(line.c_str(), hash);
		line.trim();
		if (line.empty()) continue;
		const Common::StringArray t = Common::StringTokenizer(line, " \t").split();
		// (A mode's section: "@story", "@explore".)
		if (t[0] == "@story" || t[0] == "@explore") { ptSection = t[0].c_str() + 1; continue; }
		if (ptSection != ptMode) continue;
		ptLine = line;
		const Common::String &c = t[0];
		auto arg = [&](uint i) { if (i >= t.size()) PT_FAIL("missing argument"); return atoi(t[i].c_str()); };
		if (c == "step") { ptStep = arg(1); if (ptTrace) warning("PT step %d frame %d room %d", ptStep, ptFrames, _currentRoom); }
		// do VERB THING [THING]: a sentence.
		else if (c == "do") ptSentence(arg(1), arg(2), t.size() > 3 ? arg(3) : 0);
		// door O R: opened if shut (1), walked through (13) into room R;
		// walk O R: walked through (stairs, ladders, ways out). A walk cut
		// short by a cutscene is walked again.
		else if (c == "door" || c == "walk") {
			const int o = arg(1), r = arg(2);
			ptSettle(20000);
			if (c == "door" && !(getState(o) & kObjectStateIntrinsic)) {
				ptSentence(1, o, 0);
				if (!(getState(o) & kObjectStateIntrinsic)) PT_FAIL("door %d did not open (state %d)", o, getState(o));
			}
			auto there = [&]() { return _currentRoom == r && ptEgo()->_room == r; };
			for (int tries = 0; tries < 4 && !there(); ++tries) {
				ptSentence(13, o, 0);
				for (int n = 0; n < 600 && !there(); ++n) ptFrame();
			}
			if (!there()) PT_FAIL("through %d: in room %d, not %d", o, _currentRoom, r);
		}
		else if (c == "expect") { if (!ptCond(t, 1)) PT_FAIL("not %s", line.c_str() + 7); }
		// until CONDITION [max=FRAMES]: the game plays on until it holds.
		else if (c == "until") {
			const int limit = t.back().hasPrefix("max=") ? atoi(t.back().c_str() + 4) : 20000;
			for (int n = 0; !ptCond(t, 1); ++n) { if (n >= limit) PT_FAIL("waited %d frames for %s", limit, line.c_str() + 6); ptFrame(); }
		}
		else if (c == "wait") { for (int n = arg(1); n > 0; --n) ptFrame(); }
		else if (c == "settle") ptSettle(t.size() > 1 ? arg(1) : 6000);
		// tap THING: one tap (the kid screen, where a tap does it).
		else if (c == "tap") { ptRoomAt = _currentRoom; ptTap(arg(1)); ptFrame(); }
		// dial V: on the keypad (room 43), the four digits the game keeps in
		// variables V..V+3 (0: object 300, 1..9: objects 429..437), as it waits
		// for each (variable 68 back at 255).
		else if (c == "dial") {
			for (int n = 0; n < 600 && !(_currentRoom == 43 && _userPut > 0); ++n) ptFrame();
			if (_currentRoom != 43) PT_FAIL("no keypad (room %d)", _currentRoom);
			for (int i = 0; i < 4; ++i) {
				const int digit = _scummVars[arg(1) + i];
				if (digit < 0 || digit > 9) PT_FAIL("digit %d is %d", i + 1, digit);
				for (int n = 0; n < 600 && _scummVars[68] != 255; ++n) ptFrame();
				ptRoomAt = _currentRoom;
				ptTap(digit ? 428 + digit : 300);
				for (int n = 0; n < 20; ++n) ptFrame();
			}
		}
		// kid A: New Kid (7), then the kid's name (20..22: variables 47..49);
		// in Explore mode New Kid is the character screen (the phone's;
		// here the test's stand-in, test_ai_encounters.py's PRELUDE), the
		// kid chosen on it as the phone sends the choice.
		else if (c == "kid") {
			const int a = arg(1);
			ptSettle(20000);
			const int shown = FakeAI::castShown;
			ptVerb(7);
			ptFrame();
			if (ptMode == "explore") {
				if (FakeAI::castShown == shown) PT_FAIL("New Kid showed no character screen");
				FakeAI::worldRequest = ::Scummverse::WorldCatalog::kWorldCastActorRequest + a;
				for (int n = 0; n < 600 && VAR(VAR_EGO) != a; ++n) ptFrame();
			} else {
				ptVerb(a == _scummVars[47] ? 20 : a == _scummVars[48] ? 21 : 22);
				ptFrame();
			}
			if (VAR(VAR_EGO) != a) PT_FAIL("playing %d, not %d", VAR(VAR_EGO), a);
			ptSettle(20000);
		}
		// dump: the room's objects (state, owner, where a tap finds them),
		// its actors and the scripts running (for writing a route).
		else if (c == "dump") {
			warning("PT dump frame %d room %d: %s", ptFrames, _currentRoom, ptState().c_str());
			for (int i = 1; i < _numLocalObjects; ++i) {
				const ObjectData &o = _objs[i];
				int rx = -1, ry = -1;
				if (o.obj_nr) ptPoint(o.obj_nr, rx, ry);
				if (o.obj_nr) warning("PT   object %d at %d,%d %dx%d parent %d/%d state %d owner %d tap %d,%d", o.obj_nr, o.x_pos, o.y_pos, o.width, o.height, o.parent, o.parentstate, getState(o.obj_nr), getOwner(o.obj_nr), rx, ry);
			}
			for (int n = 1; n <= 25; ++n) { Actor *x = derefActor(n, "playthrough"); if (x->_room == _currentRoom) warning("PT   actor %d at %d,%d", n, x->getRealPos().x, x->getRealPos().y); }
			Common::String run;
			for (int i = 0; i < NUM_SCRIPT_SLOT; ++i) if (vm.slot[i].status != ssDead) run += Common::String::format(" %d/%d", vm.slot[i].number, vm.slot[i].where);
			warning("PT   scripts%s", run.c_str());
		}
		else PT_FAIL("unknown command %s", c.c_str());
	}
	// Story mode: none of the mansion's additions at all; Explore mode: the
	// sandbox, with other games' visitors in as many rooms as asked.
	if (ptMode == "story" && (_scummverseRoaming || _scummverseRoamingReady || _scummverseExplorationDoors || _scummverseExplorationSafety || ptVisitorFrames))
		PT_FAIL("the mansion's additions in the story: roaming %d/%d, doors %d, safety %d, visitors seen %d frames", _scummverseRoaming, _scummverseRoamingReady, _scummverseExplorationDoors, _scummverseExplorationSafety, ptVisitorFrames);
	const int ptVisitorsAsked = ConfMan.hasKey("scummverse_playthrough_visitor_rooms") ? ConfMan.getInt("scummverse_playthrough_visitor_rooms") : 0;
	if (ptMode == "explore" && (!_scummverseRoamingReady || ptVisitorRoomCount < ptVisitorsAsked))
		PT_FAIL("the sandbox: roaming %d, visitors in %d rooms (%d asked)", _scummverseRoamingReady, ptVisitorRoomCount, ptVisitorsAsked);
	warning("SCUMMVERSE_PLAYTHROUGH_PASS mode=%s steps=%d frames=%d gameticks=%u seconds=%u visitors: %d frames, %d rooms, at most %d at once", ptMode.c_str(), ptStep, ptFrames, ptTicks, (_system->getMillis() - ptStart) / 1000, ptVisitorFrames, ptVisitorRoomCount, ptVisitorMost);
#undef PT_FAIL
	quitGame();
	return;
	}
