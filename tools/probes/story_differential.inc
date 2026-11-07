		// SCUMMVERSE story differential (test only; tools/test_story_differential.py
		// writes this at the top of the main loop of a temporary copy of
		// engines/scumm/scumm.cpp, the same in a stock build and in ours).
		// Each frame: what the screen shows (pixels, palette, cursor, shake),
		// the sound mixed during it and what the game holds (variables, bit
		// variables, objects, actors, script slots), as hashes in frames.txt;
		// at every scummverse_diff_every frames and from scummverse_diff_from
		// to scummverse_diff_to, all of it written out (state-N.txt, shot-N.raw).
		// The player's part, the same inputs at the same frames: Escape now
		// and then (openings and cutscenes), the talk-skip key, a click every
		// 8 frames on one of the verbs shown, a thing in the room or anywhere
		// on the screen, picked by the probe's own numbers, a right click now and
		// then, the game's own menu key (F5; The Curse's F1) now and then,
		// and ScummVM's save (slot 7) and, a moment later, its load of it,
		// every 1000 frames; in the oldest games, a room tour (below). Stops after scummverse_diff_frames frames. Any
		// other target (ours, in Story mode, when the list did not open the
		// game) stops at once.
		if (ConfMan.hasKey("scummverse_diff_out") && _targetName != ConfMan.get("scummverse_diff_target")) {
			warning("SCUMMVERSE_DIFF_OTHER %s", _targetName.c_str());
			_system->quit();
		} else if (ConfMan.hasKey("scummverse_diff_out")) {
			static int diffFrame = -1;
			static Common::DumpFile *diffLog = nullptr;
			static uint32 diffPick = 0;
			static Common::Point diffDown, diffRight;
			static bool diffSaved = false;
			static int diffTourRoom = 0;
			static bool diffTourDue = false;
			++diffFrame;
			scummverseDiffFrame();
			const Common::String diffOut = ConfMan.get("scummverse_diff_out");
			const int diffFrames = ConfMan.getInt("scummverse_diff_frames"), diffEvery = ConfMan.getInt("scummverse_diff_every");
			const int diffFrom = ConfMan.getInt("scummverse_diff_from"), diffTo = ConfMan.getInt("scummverse_diff_to");
			if (!diffLog) {
				diffPick = (uint32)ConfMan.getInt("scummverse_diff_seed");
				diffLog = new Common::DumpFile();
				if (!diffLog->open(Common::Path(diffOut + "/frames.txt"), true))
					error("story differential: cannot write in %s", diffOut.c_str());
				diffLog->writeString(Common::String::format("game %s version %d screen %dx%d actors %d vars %d bits %d objects %d\n", _game.gameid,
					_game.version, _screenWidth, _screenHeight, _numActors, _numVariables, _numBitVariables, _numGlobalObjects));
			}
			auto fnv = [](uint32 hash, const void *data, uint size) {
				const byte *p = (const byte *)data;
				while (size--) { hash ^= *p++; hash *= 16777619u; }
				return hash;
			};
			const byte *pixels = nullptr, *palette = nullptr;
			int sw = 0, sh = 0, pitch = 0, bpp = 1, shake = 0;
			uint32 cursor = 0;
			bool shown = false;
			scummverseDiffScreen(pixels, sw, sh, pitch, bpp, palette, cursor, shake, shown);
			uint32 hScreen = 2166136261u;
			for (int y = 0; pixels && y < sh; ++y)
				hScreen = fnv(hScreen, pixels + y * pitch, sw * bpp);
			const uint32 hPalette = palette ? fnv(2166136261u, palette, 768) : 0;
			const uint32 hVars = fnv(2166136261u, _scummVars, _numVariables * sizeof(int32));
			const uint32 hBits = _bitVars ? fnv(2166136261u, _bitVars, _numBitVariables >> 3) : 0;
			uint32 hObjects = fnv(2166136261u, _objectStateTable, _numGlobalObjects);
			hObjects = fnv(hObjects, _objectOwnerTable, _numGlobalObjects);
			hObjects = fnv(hObjects, _classData, _numGlobalObjects * sizeof(uint32));
			// (Maniac Mansion V1's own 25 actors: ours keeps 5 more slots for
			// other worlds' guests, never used in a story; frames.txt's head
			// says how many each has.)
			const int diffActors = _game.id == GID_MANIAC && _game.version <= 1 ? MIN<int>(_numActors, 25) : _numActors;
			uint32 hActors = 2166136261u;
			for (int i = 0; i < diffActors; ++i) {
				const Actor *a = _actors[i];
				const int v[] = {a->_room, a->getPos().x, a->getPos().y, a->_costume, a->getFacing(), a->getElevation(), a->_visible, a->_moving, a->_scalex, a->_scaley};
				hActors = fnv(hActors, v, sizeof(v));
			}
			uint32 hSlots = 2166136261u;
			for (int i = 0; i < NUM_SCRIPT_SLOT; ++i) {
				if (vm.slot[i].status == ssDead)
					continue;
				const int v[] = {i, vm.slot[i].number, vm.slot[i].status, vm.slot[i].where, (int)vm.slot[i].offs};
				hSlots = fnv(hSlots, v, sizeof(v));
			}
			const int diffEgo = VAR_EGO != 0xFF ? VAR(VAR_EGO) : -1;
			// (pending: a save or load asked for, for the next frame: 1 save, 2 load; its slot, temporary or not.)
			diffLog->writeString(Common::String::format("%d t=%u spun=%u room=%d ego=%d cam=%d screen=%08x palette=%08x cursor=%08x/%d shake=%d audio=%08x vars=%08x bits=%08x objects=%08x actors=%08x slots=%08x pending=%d/%d/%d\n",
				diffFrame, scummverseDiffNow(), scummverseDiffSpun(), _currentRoom, diffEgo, camera._cur.x, hScreen, hPalette, cursor, shown ? 1 : 0, shake,
				scummverseDiffAudio(), hVars, hBits, hObjects, hActors, hSlots, _saveLoadFlag, _saveLoadFlag ? _saveLoadSlot : 0, _saveLoadFlag && _saveTemporaryState ? 1 : 0));
			diffLog->flush(); // (Kept should the game stop.)
			if ((diffEvery > 0 && diffFrame % diffEvery == 0) || (diffFrame >= diffFrom && diffFrame <= diffTo)) {
				Common::DumpFile state;
				if (state.open(Common::Path(Common::String::format("%s/state-%05d.txt", diffOut.c_str(), diffFrame)))) {
					state.writeString(Common::String::format("frame %d room %d ego %d cam %d userput %d cursorstate %d\n", diffFrame, _currentRoom, diffEgo, camera._cur.x, _userPut, _cursor.state));
					for (int i = 0; i < _numVariables; ++i)
						if (_scummVars[i]) state.writeString(Common::String::format("var %d %d\n", i, _scummVars[i]));
					for (int i = 0; _bitVars && i < _numBitVariables; ++i)
						if (_bitVars[i >> 3] & (1 << (i & 7))) state.writeString(Common::String::format("bit %d\n", i));
					for (int i = 0; i < _numGlobalObjects; ++i)
						if (_objectStateTable[i] || _objectOwnerTable[i] || _classData[i])
							state.writeString(Common::String::format("object %d %d %d %u\n", i, _objectStateTable[i], _objectOwnerTable[i], _classData[i]));
					for (int i = 0; i < diffActors; ++i) {
						const Actor *a = _actors[i];
						state.writeString(Common::String::format("actor %d %d %d %d %d %d %d %d %d %d %d\n", i, a->_room, a->getPos().x, a->getPos().y, a->_costume,
							a->getFacing(), a->getElevation(), a->_visible, a->_moving, a->_scalex, a->_scaley));
					}
					for (int i = 0; i < NUM_SCRIPT_SLOT; ++i)
						if (vm.slot[i].status != ssDead)
							state.writeString(Common::String::format("slot %d %d %d %d %u\n", i, vm.slot[i].number, vm.slot[i].status, vm.slot[i].where, vm.slot[i].offs));
					state.flush();
				}
				Common::DumpFile shot;
				if (pixels && shot.open(Common::Path(Common::String::format("%s/shot-%05d.raw", diffOut.c_str(), diffFrame)))) {
					shot.writeString(Common::String::format("SVD1 %d %d %d\n", sw, sh, bpp));
					shot.write(palette, 768);
					for (int y = 0; y < sh; ++y)
						shot.write(pixels + y * pitch, sw * bpp);
					shot.flush();
				}
			}
			if (diffFrame >= diffFrames) {
				diffLog->flush();
				diffLog->close();
				warning("SCUMMVERSE_DIFF_DONE %d frames", diffFrame);
				_system->quit();
			}
			// The player's part.
			auto pick = [&](uint n) {
				diffPick = diffPick * 1103515245u + 12345u;
				return n ? (int)((diffPick >> 16) % n) : 0;
			};
			// (A point of the game's screen as the backend reports a pointer
			// there: input.cpp's mapping, undone.)
			auto pointer = [&](Common::Point p) {
				if (_useMacScreenCorrectHeight && _macScreen)
					p.y += _macScreenDrawOffset;
				if (_textSurfaceMultiplier == 2 || _macScreen || _renderMode == Common::kRenderCGA_BW || _enableEGADithering) {
					p.x *= 2;
					p.y *= 2;
				}
				return p;
			};
			auto send = [&](Common::EventType type, Common::Point at) {
				Common::Event event;
				event.type = type;
				event.mouse = at;
				_system->getEventManager()->pushEvent(event);
			};
			auto press = [&](Common::KeyCode code, uint16 ascii) {
				Common::Event event;
				event.type = Common::EVENT_KEYDOWN;
				event.kbd = Common::KeyState(code, ascii);
				_system->getEventManager()->pushEvent(event);
				event.type = Common::EVENT_KEYUP;
				_system->getEventManager()->pushEvent(event);
			};
			// (The oldest games, one room file each: every scummverse_diff_tour
			// frames the player's character is taken to the next room there is,
			// as ScummVM's debugger's room command does, so play goes on in
			// every room; once the player has the controls, no cutscene and no
			// save or load waiting. Test only; the same in both builds.)
			const int diffTour = ConfMan.getInt("scummverse_diff_tour");
			if (diffTour > 0 && diffFrame > 0 && diffFrame % diffTour == 0 && _game.version <= 3)
				diffTourDue = true;
			if (diffTourDue && VAR_EGO != 0xFF && _currentScript == 0xFF && _userPut > 0 && !vm.cutSceneStackPointer && !_saveLoadFlag) {
				diffTourDue = false;
				for (int tries = 0; tries < 99; ++tries) {
					diffTourRoom = diffTourRoom % 99 + 1;
					if (diffTourRoom != _currentRoom && Common::File::exists(Common::Path(Common::String::format("%02d.lfl", diffTourRoom))))
						break;
				}
				Actor *diffEgo = derefActor(VAR(VAR_EGO), "story differential");
				diffEgo->_room = diffTourRoom;
				_sound->stopAllSounds();
				startScene(diffTourRoom, nullptr, 0);
				_fullRedraw = true;
				// (Within the new room: a place beyond its edge would take the
				// camera, and the strips drawn, past it.)
				const int wide = _game.version <= 2 ? _roomWidth / V12_X_MULTIPLIER : _roomWidth;
				const int high = _game.version <= 2 ? _roomHeight / V12_Y_MULTIPLIER : _roomHeight;
				const Common::Point was = diffEgo->getRealPos();
				diffEgo->putActor(CLIP<int>(was.x, 0, MAX(wide - 1, 0)), CLIP<int>(was.y, 0, MAX(high - 1, 0)), diffTourRoom);
				diffLog->writeString(Common::String::format("%d tour %d\n", diffFrame, diffTourRoom));
			}
			if (diffFrame % 1000 == 300 && canSaveGameStateCurrently()) {
				diffSaved = saveGameState(7, "Differential", false).getCode() == Common::kNoError;
				diffLog->writeString(Common::String::format("%d save %d\n", diffFrame, diffSaved ? 1 : 0));
			} else if (diffFrame % 1000 == 340 && diffSaved && canLoadGameStateCurrently()) {
				diffSaved = false;
				const bool loading = loadGameState(7).getCode() == Common::kNoError;
				diffLog->writeString(Common::String::format("%d load %d\n", diffFrame, loading ? 1 : 0));
			}
			if (diffFrame % 700 == 355) {
				if (_game.version <= 3)
					press(Common::KEYCODE_F5, Common::ASCII_F5);
				else if (_game.version == 8)
					press(Common::KEYCODE_F1, Common::ASCII_F1);
			}
			if (diffFrame % 64 == 36) {
				const VirtScreen &vs = _virtscr[kMainVirtScreen];
				diffRight = pointer(Common::Point(pick(_screenWidth), vs.topline + pick(MAX<int>(vs.h, 1))));
				send(Common::EVENT_MOUSEMOVE, diffRight);
				send(Common::EVENT_RBUTTONDOWN, diffRight);
			} else if (diffFrame % 64 == 37) {
				send(Common::EVENT_RBUTTONUP, diffRight);
			}
			if (diffFrame % 50 == 25)
				press(Common::KEYCODE_ESCAPE, Common::ASCII_ESCAPE);
			if (VAR_TALKSTOP_KEY != 0xFF && diffFrame % 20 == 10)
				press(Common::KEYCODE_PERIOD, '.');
			if (diffFrame % 8 == 0) {
				Common::Array<Common::Point> verbs, things;
				for (int i = 1; i < _numVerbs; ++i)
					if (_verbs[i].verbid && _verbs[i].curmode == 1 && !_verbs[i].curRect.isEmpty())
						verbs.push_back(Common::Point((_verbs[i].curRect.left + _verbs[i].curRect.right) / 2, (_verbs[i].curRect.top + _verbs[i].curRect.bottom) / 2));
				const VirtScreen &vs = _virtscr[kMainVirtScreen];
				for (int i = 1; i < _numLocalObjects; ++i) {
					if (!_objs[i].obj_nr || _objs[i].width <= 0 || _objs[i].height <= 0)
						continue;
					const Common::Point at(_objs[i].x_pos + _objs[i].width / 2 - vs.xstart, _objs[i].y_pos + _objs[i].height / 2 + vs.topline);
					if (at.x >= 0 && at.x < _screenWidth && at.y >= vs.topline && at.y < vs.topline + vs.h)
						things.push_back(at);
				}
				const int kind = (diffFrame / 8) % 4;
				Common::Point at;
				if (kind == 0 && !verbs.empty())
					at = verbs[pick(verbs.size())];
				else if (kind != 3 && !things.empty())
					at = things[pick(things.size())];
				else
					at = Common::Point(pick(_screenWidth), pick(_screenHeight)); // (the room, its verbs, its inventory)
				diffDown = pointer(at);
				send(Common::EVENT_MOUSEMOVE, diffDown);
				send(Common::EVENT_LBUTTONDOWN, diffDown);
			} else if (diffFrame % 8 == 1) {
				send(Common::EVENT_LBUTTONUP, diffDown);
			}
		}
