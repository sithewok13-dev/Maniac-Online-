	// SCUMMVERSE story differential (test only; tools/test_story_differential.py
	// writes this into the stock build's scumm.cpp only, where our story play
	// runs scummverseUpdateStory). Story play answers two copy-protection
	// screens for the player, a deliberate difference
	// (engines/scumm/scummverse_story.inc: scummverseStoryPassGuard and
	// scummverseStoryDressDolls); the stock build is given the same answers
	// at the same point of the same frames, so the games can be compared past
	// them. Monkey Island 2's recipe number: "1" and Return, by turns, every
	// 90 ticks in room 108. Sam & Max's dolls: the page's clothes put on and
	// the button pressed, every 90 ticks in room 71.
	if (ConfMan.hasKey("scummverse_diff_guard")) {
		static int guardWait = 0, guardTries = 0, guardStep = 0;
		const bool recipe = _game.id == GID_MONKEY2 && _currentRoom == 108 && !(_game.features & GF_ULTIMATE_TALKIE) &&
			!(_game.platform == Common::kPlatformMacintosh && _bootParam == -7873);
		const bool dolls = _game.id == GID_SAMNMAX && _currentRoom == 71 && _game.variant && !strcmp(_game.variant, "Floppy") &&
			getObjectIndex(771) != -1;
		if (_copyProtection || guardTries >= 20) {
		} else if (!recipe && !dolls) {
			guardWait = guardStep = 0;
		} else if ((guardWait += MAX(delta, 1)) >= 90) {
			guardWait = 0;
			if (dolls) {
				// (The game's own table, array 304, as its scripts read it.)
				auto arrayAt = [&](int array, int offset) {
					const byte *ah = getResourceAddress(rtString, readVar(array));
					if (!ah) return -1;
					const int dim1 = (int16)READ_LE_UINT16(ah), type = (int16)READ_LE_UINT16(ah + 2), dim2 = (int16)READ_LE_UINT16(ah + 4);
					if (offset < 0 || offset >= dim1 * dim2) return -1;
					return type != 5 ? (int)ah[6 + offset] : (int)(int16)READ_LE_UINT16(ah + 6 + offset * 2);
				};
				const int page = readVar(152), doll = readVar(153);
				const bool asked = readVar(151) == 0 && getState(771) == 1 && page >= 1 && page <= 10 && (doll == 0 || doll == 1);
				bool left = false;
				if (asked) {
					const int first = doll ? 745 : 715, last = doll ? 770 : 744;
					int items[3];
					for (int k = 0; k < 3 && !left; ++k) {
						items[k] = first + arrayAt(304, (page - 1) * 6 + doll * 3 + k) - 'A';
						if (readVar(154) != 0 || items[k] < first || items[k] > last || getObjectIndex(items[k]) == -1) {
							guardTries = 20;
							left = true;
							warning("SCUMMVERSE_DIFF_GUARD copy protection left to the player");
						}
					}
					for (int k = 0; k < 3 && !left; ++k) {
						if (!getState(items[k])) {
							putState(items[k], 1);
							markObjectRectAsDirty(items[k]);
						}
					}
				}
				if (!left) {
					const ObjectData &button = _objs[getObjectIndex(771)];
					const VirtScreen &vs = _virtscr[kMainVirtScreen];
					_mouse.x = button.x_pos + button.width / 2 - vs.xstart;
					_mouse.y = button.y_pos + button.height / 2 + vs.topline;
					_leftBtnPressed |= 2;
					++guardTries;
					warning("SCUMMVERSE_DIFF_GUARD copy protection answered (%s)", asked ? "the dolls dressed" : "a press");
				}
			} else {
				Common::Event event;
				event.type = Common::EVENT_KEYDOWN;
				event.kbd = guardStep == 0 ? Common::KeyState(Common::KEYCODE_1, '1') : Common::KeyState(Common::KEYCODE_RETURN, Common::ASCII_RETURN);
				_system->getEventManager()->pushEvent(event);
				event.type = Common::EVENT_KEYUP;
				_system->getEventManager()->pushEvent(event);
				if (guardStep == 1) ++guardTries;
				guardStep ^= 1;
				warning("SCUMMVERSE_DIFF_GUARD copy protection answered (%s)", guardStep ? "a number" : "Return");
			}
		}
	}
