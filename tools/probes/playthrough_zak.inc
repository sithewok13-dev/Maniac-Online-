	// PLAYTHROUGH (Zak McKracken, the V1 DOS edition): played to its ending
	// by the player's own taps (tools/test_playthrough_zak.py). A route of
	// sentences, each made as the player makes it: the verb tapped, then the
	// thing (a room object or actor where a tap finds it, the one played
	// walking towards it until it shows; a carried thing in the inventory),
	// twice or with its second thing; the game's own sentence script walks
	// there and does it. Every step checks what the game did (an object's
	// state, who owns what, the room, a variable the game sets) and fails
	// naming the step.
	// - Story mode (Zak's own story, scummverse-story-zak, chosen from Story
	//   mode's list): none of the mansion's additions (roaming, free doors,
	//   safety, visitors); the four played (actors 1 to 4), the flights booked
	//   with the cards (objects 18, 32) on the terminals' screen (room 45), the
	//   money, the capture and the way out of it, Mars with its air rules, and
	//   the ending (switches 424 and 425 held at once: scripts 65, 66, 149).
	//   Afterwards the app goes back to the mansion (HOME).
	// - Explore mode (the mansion as it starts: scummverse_roaming, the
	//   wanderers on, other games' visitors): Zak (actor 24) chosen on the
	//   character screen, his street, the bus, eight of the ten flights the
	//   sandbox offers (seated aboard, Arrive; not the mansion's or the home
	//   airport's), the places beyond, the maze, the pads to Mars, Mars's
	//   rooms with and without air, the tram and the pads back. What the
	//   sandbox replaces by design (docs/roaming.md: no fares, puzzles or
	//   endings) is not played; visitors must be met in as many rooms as asked.
	// The orders the game picks at random are read from its variables ($N),
	// where the player reads them on the screen; the route holds for any seed.
	// No game text: things, rooms, actors, scripts and verbs by number (the
	// verbs as the game's verb table numbers them: 1 opens, 3 gives, 11 uses,
	// 13 walks to, 45 switches the one played). Commands and conditions are
	// described where they are read, below; "step N  # ..." says what each
	// step does, by number.
	if ((_game.id == GID_ZAK || _game.id == GID_MANIAC) && ConfMan.hasKey("scummverse_playthrough_zak")) {
	const Common::String pzMode = ConfMan.get("scummverse_playthrough_zak");
	// (Story mode: after Zak's story, the app goes back to the mansion; done.)
	if (pzMode == "story" && _game.id == GID_MANIAC) { warning("SCUMMVERSE_PLAYTHROUGH_ZAK_HOME room=%d story=%d", _currentRoom, _scummverseStory); quitGame(); return; }
	static bool pzEntered = false;
	if (pzEntered) error("SCUMMVERSE_PLAYTHROUGH_ZAK_FAIL the game restarted (game over?)");
	pzEntered = true;
	Common::String pzRoute = R"PZ(
@story
step 1    # the opening; actor 1 in (1)
until egoroom 1 max=40000
settle 20000
step 2    # (1): 92 opened, 15 taken; 94 opened, 16, 17, 14 taken
do 1 92
expect state 92 8 8
do 14 15
expect owns 15
do 1 94
do 14 16
expect owns 16
do 14 17
expect owns 17
do 14 14
expect owns 14
step 3    # (2): 26, 25, 24 taken (121 opened); 22 (125 opened); 21 (119 opened)
door 84 2
do 14 26
expect owns 26
do 1 121
do 14 25
expect owns 25
do 14 24
expect owns 24
do 1 125
do 14 22
expect owns 22
do 1 119
do 14 21
expect owns 21
step 4    # (1): 94 shut, 26 with 106: 18
door 111 1
do 2 94
do 11 26 106
expect owns 18
step 5    # (3): 16 used at 142 (143); 18 with 150: the bus to (145)
door 84 2
door 112 3
near 142
do 11 16
until state 143 8 8 max=600
do 11 18 150
until egoroom 145 max=3000
settle 20000
step 6    # (145): gate 190: a flight (11); 51
near 190
until egoroom 11 max=3000
settle 20000
expect owns 51
step 7    # (11): 47 taken, used with 242 (state 4), 242 turned on (265); 245 pushed (var 248)
do 1 246
near 246
do 14 47
expect owns 47
do 11 47 242
expect state 242 4 4
do 4 242
until state 265 8 8 max=3000
do 9 245
until var 248 >= 1 max=6000
step 8    # (11): 260 opened, 22 in it, turned on (241)
do 1 260
expect state 260 8 8
do 11 22 260
do 4 260
until state 241 8 8 max=3000
step 9    # (11): 249-254 opened; 50, 48, 49 taken
do 1 249
do 1 250
do 1 251
do 1 252
do 1 253
do 1 254
do 14 50
expect owns 50
do 14 48
expect owns 48
do 14 49
expect owns 49
step 10   # the flight lands (144); 191: (12)
until egoroom 144 max=20000
settle 20000
walk 191 12
step 11   # (12): 51 given to 268 (var 147), 52 taken, 26 with 267; (13)
do 3 51 268
expect var 147 == 1
do 14 52
expect owns 52
do 11 26 267
expect state 267 8 8
walk 267 13
step 12   # (13): 52 in 273 (var 153), 26 with 285 (var 147), 54 taken, in 273, 49 with 273; out and back; 25 with 282 (281): (129)
do 11 52 273
expect var 153 == 2
near 54
do 11 26 285
expect var 147 == 2
do 14 54
expect owns 54
do 11 54 273
expect var 153 == 3
do 11 49 273
until var 153 == 4 max=6000
settle 20000
walk 272 12
walk 267 13
expect var 12 == 11
do 11 25 282
until state 281 8 8 max=600
walk 281 129
step 13   # (129): 21 used (298), 55 taken; (13), (12), (144)
do 11 21
expect state 298 8 8
do 14 55
expect owns 55
walk 297 13
walk 272 12
walk 266 144
step 14   # (144): 18 with 194: (45): 663, 657 (var 79, 82 carried); gate 190: (145)
do 11 18 194
until room 45 max=600
wait 10
tap 663
until var 121 == 1024 max=600
wait 30
tap 657
until egoroom 144 max=3000
settle 20000
expect owns 82
expect var 79 == 663
near 190
until egoroom 145 max=6000
settle 20000
step 15   # (145): 191 (3), 141 (5); 169 opened, 55 in it (script 62): actor 2 in (6); var 199; 55 and 33 carried
walk 191 3
settle 20000
walk 141 5
do 1 169
expect state 169 8 8
do 11 55 169
until running 62 max=600
until stopped 62 max=20000
settle 20000
expect var 199 == 1
expect state 169 4 4
expect owns 55
expect owns 33
expect actor 2 6
step 16   # (6) 172 (5), 160 (3): the bus (16, 18 with 150): (145); 18 given to actor 10: 45
walk 172 5
walk 160 3
near 142
do 11 16
until state 143 8 8 max=600
do 11 18 150
until egoroom 145 max=3000
settle 20000
do 3 18 10
until owns 45 max=3000
settle 20000
step 17   # (145): 18 with 194: 659: (141); 18 with 194: 666: (148); 218: (17)
do 11 18 194
until room 45 max=600
wait 10
tap 659
until var 121 == 1024 max=600
wait 30
tap 657
until egoroom 145 max=3000
settle 20000
expect var 79 == 659
near 190
until egoroom 141 max=20000
settle 20000
do 11 18 194
until room 45 max=600
wait 10
tap 666
until var 121 == 1024 max=600
wait 30
tap 657
until egoroom 141 max=3000
settle 20000
expect var 79 == 666
near 190
until egoroom 148 max=20000
settle 20000
walk 218 17
step 18   # (17): 45 given to actor 10 (351 opens); (19): near actor 10 until 55 has state 4 (var 225 at 0); 375 (17)
do 3 45 10
until state 351 8 8 max=3000
settle 20000
walk 351 19
near 10
until state 55 4 4 max=40000
settle 20000
expect var 225 == 0
walk 375 17
step 19   # (17): 49 with 359 (script 124); 59 taken
do 11 49 359
until running 124 max=6000
settle 20000
do 14 59
expect owns 59
settle 20000
step 20   # (17): 18 with 352 (script 31): (148); 18 with 220: 659; gate 217: (141)
do 11 18 352
until egoroom 148 max=3000
settle 20000
book 18 220 659
gate 217 141
step 21   # (141): 18 with 194: 661; gate 190: (143)
book 18 194 661
gate 190 143
step 22   # (143): 45 given to actor 10: 46 (object 208); 18 with 194: 668; gate 190: (131)
do 3 45 10
until owns 46 max=6000
settle 20000
book 18 194 668
gate 190 131
step 23   # (131): 77 pulled (script 50): (31); 16 used: 504; 55 with 504: actor 5 played; 505 (41): 614 pulled, 78 taken; 605 (31): 78 given to actor 1; verb 30: actor 1; scripts 75, 92: (3), 33, 55, 78 owned by actor 7, 328 state 4
do 10 77
until egoroom 31 max=6000
settle 20000
do 11 16
until state 504 2 0 max=6000
settle 20000
do 11 55 504
until ego 5 max=3000
settle 20000
walk 505 41
do 10 614
do 14 78
expect owns 78
walk 605 31
do 3 78 1
expect owner 78 1
verb 30
until running 75 max=20000
until egoroom 3 max=20000
until stopped 89 max=60000
settle 20000
expect owner 78 7
expect owner 55 7
expect owner 33 7
expect state 328 4 4
step 24   # (3): 147 pushed three times (script 39, var 152 at 3): 29 taken
do 9 147
until stopped 39 max=6000
do 9 147
until stopped 39 max=6000
do 9 147
until stopped 39 max=6000
expect var 152 == 3
do 14 29
expect owns 29
step 25   # (3) 141 (5), 161 (7): 34 bought (verb 17) and opened (35, 37, 38); 44 bought; 180 (5): 38 with 31: 31
walk 141 5
door 161 7
do 17 34
until owns 34 max=6000
do 1 34
expect owns 35
expect owns 37
expect owns 38
do 17 44
until owns 44 max=6000
door 180 5
do 11 38 31
until owns 31 max=600
step 26   # (5) 160 (3), 134 (2): 29 in 129 (130); 122 on (23 state 4), off; 35 with 126 (23 state 8): 23 taken; 14 with 129 (var 138 at 2)
walk 160 3
walk 134 2
do 11 29 129
expect state 130 8 8
do 4 122
until state 23 4 4 max=600
do 5 122
do 11 35 126
until state 23 8 8 max=600
do 14 23
expect owns 23
do 11 14 129
expect var 138 == 2
step 27   # (2) 111 (1): 107 pulled; 35 with 108; 37 with 108 (110); 110 used: (16): 328 opened: 33, 55, 78; 333 used: (1)
door 111 1
do 10 107
expect state 107 8 8
do 11 35 108
until state 108 8 8 max=600
do 11 37 108
until state 110 8 8 max=3000
do 11 110
until egoroom 16 max=3000
settle 20000
do 1 328
expect owns 33
expect owns 55
expect owns 78
do 11 333
until egoroom 1 max=3000
settle 20000
step 28   # (1): 110 taken (37); 84 (2), 112 (3); actor 2 in (6): 175 opened, 32 taken; 172 (5), 160 (3); 46 given to actor 2
do 14 110
until owns 37 max=600
door 84 2
walk 112 3
switch 2
do 1 175
do 14 32
expect owns 32
walk 172 5
walk 160 3
switch 1
do 3 46 2
expect owner 46 2
step 29   # (3): 16 used (143); actor 2: 32 with 150 (script 52); actor 1: 18 with 150: both to (145)
near 142
do 11 16
until state 143 8 8 max=600
switch 2
do 11 32 150
until running 52 max=600
switch 1
do 11 18 150
until egoroom 145 max=6000
settle 20000
expect actor 2 145
step 30   # actor 2: 32 with 194: 659; gate 190: (141); 191: (133): 46 given to actor 10 (script 76: 642 touchable); 642 turned off
switch 2
book 32 194 659
gate 190 141
walk 191 133
do 3 46 10
until running 76 max=600
until stopped 76 max=6000
settle 20000
expect state 642 2 0
do 5 642
expect state 642 8 8
step 31   # actor 1, (145): 18 with 194: 667; gate 190: (149); 218: the jungle: (42)
switch 1
book 18 194 667
gate 190 149
walk 218 175
jungle 42
step 32   # (42): 23 with 621; 55 with 630: actor 6 played: 620 (138), 636 (136): 79 taken; 631 (138), 638 (42): 79 given to actor 1; verb 30; 619: the jungle: (149)
do 11 23 621
expect state 623 10 0
until state 630 2 0 max=6000
settle 20000
do 11 55 630
until ego 6 max=3000
settle 20000
walk 620 138
walk 636 136
do 14 79
until owns 79 max=600
walk 631 138
walk 638 42
do 3 79 1
until owner 79 1 max=600
verb 30
until ego 1 max=600
settle 20000
walk 619 172
jungle 149
step 33   # (149): 18 with 220: 660; gate 217: (142); 191: the jungle: (39)
book 18 220 660
gate 217 142
walk 191 168
jungle 39
step 34   # (39): 594 (156), 747 (159), 745 (164), 747 (165), 747 (166), 741 (130); 25 with 294: the drawing screen (48; Var 119/120): 307; 56 taken; back to (39)
walk 594 156
walk 747 159
walk 745 164
walk 747 165
walk 747 166
walk 741 130
do 11 25 294
draw
expect state 307 8 8
do 14 56
until owns 56 max=600
walk 297 166
walk 745 165
walk 745 164
walk 741 159
walk 744 156
walk 745 39
step 35   # (39): 593: the jungle: (142); 18 with 194: 659; gate 190: (141); 191: (133)
walk 593 171
jungle 142
book 18 194 659
gate 190 141
walk 191 133
step 36   # (133): 38 with 643; 644 (134), actor 2 too; 59, 33, 56 with 648 (653); 79 given to actor 2; actor 2: 79 read (script 136): 81 shows; actor 1: 81 taken
do 11 38 643
until state 643 8 8 max=1200
walk 644 134
switch 2
walk 644 134
switch 1
do 11 59 648
expect owner 59 0
do 11 33 648
do 11 56 648
expect state 653 8 8
do 3 79 2
until owner 79 2 max=600
settle 20000
switch 2
do 12 79
until state 81 2 0 max=3000
settle 20000
switch 1
do 14 81
until owns 81 max=600
step 37   # actor 2: 652 (133), 639 (141); 32 with 194: 664; gate 190: (146); 218 (20), 386 (135), 392 (206), 408: (155)
switch 2
walk 652 133
walk 639 141
book 32 194 664
gate 190 146
walk 218 20
walk 386 135
walk 392 206
walk 408 155
switch 1
step 38   # actor 1: 652 (133), 639 (141); 18 with 194: 663; gate 190: (145); 191 (3), 141 (5), 161 (7): 39 bought; 180 (5), 160 (3): the bus: (145); 659: (141); 664: (146)
walk 652 133
walk 639 141
book 18 194 663
gate 190 145
walk 191 3
walk 141 5
door 161 7
do 17 39
until owns 39 max=6000
door 180 5
walk 160 3
near 142
do 11 16
until state 143 8 8 max=600
do 11 18 150
until egoroom 145 max=6000
settle 20000
book 18 194 659
gate 190 141
book 18 194 664
gate 190 146
step 39   # (146): 218 (20); 388 (140), 398 (20), 387 (139): 25 with 399: drawn (400); 400 (207); 406 (211), 404 (212), 407 (213), 406 (214), 406 (215), 403 (216), 406 (218), 408: (152)
walk 218 20
walk 388 140
walk 398 20
walk 387 139
do 11 25 399
draw
expect state 400 8 8
walk 400 207
walk 406 211
walk 404 212
walk 407 213
walk 406 214
walk 406 215
walk 403 216
walk 406 218
walk 408 152
step 40   # (152): 316-318 pushed in the order of vars 110-112: 322 (bit 1456); 310 read (script 68); 25 with 17 (var 193 at 2)
do 9 $110
do 9 $111
do 9 $112
until state 322 8 8 max=1200
until bit 1456 == 1 max=1200
settle 20000
do 12 310
until stopped 68 max=3000
settle 20000
do 11 25 17
expect var 193 == 2
step 41   # back to (146); 18 with 220: 665; gate 217: (147); 218: the jungle: (150); 578 (151): 44 given to actor 10 (script 70); 578 (151): 81 given (script 45: 81 state 4)
walk 323 218
walk 404 216
walk 404 215
walk 404 214
walk 404 213
walk 405 212
walk 403 211
walk 403 207
walk 403 139
walk 398 20
walk 390 146
book 18 220 665
gate 217 147
walk 218 170
jungle 150
walk 578 151
do 3 44 10
until running 70 max=600
until stopped 70 max=20000
settle 20000
walk 578 151
do 3 81 10
until state 81 4 4 max=20000
settle 20000
step 42   # (150): 81 used (script 60): (153): 482: (137): 80 taken
start 11 81
until room 153 max=600
wait 10
tap 482
until egoroom 137 max=6000
settle 20000
do 14 80
until owns 80 max=600
step 43   # actor 3: (26), script 81: actors 3 and 4 in (185)
switch 3
until stopped 81 max=20000
settle 20000
expect actor 3 185
expect actor 4 185
step 44   # actor 3: 452 (30): 489 opened; 74 taken (75 too); 73, 71, 72 taken; 488 (185)
door 452 30
do 1 489
expect state 489 8 8
do 14 74
until owns 75 max=600
do 14 73
until owns 73 max=600
do 14 71
until owns 71 max=600
do 14 72
until owns 72 max=600
walk 488 185
step 45   # (185): 75 given to actor 4; 74 with 448: 62; actor 4: 75 with 448: 63
do 3 75 4
until owner 75 4 max=600
do 11 74 448
until owns 62 max=1200
switch 4
do 11 75 448
until owns 63 max=1200
switch 3
step 46   # actors 4 and 3: 449 (181); 62 with 470; 64 taken; 73 with 470 (471); 466 (463 shut), 468 (464 open): 464 (180), both
switch 4
walk 449 181
switch 3
walk 449 181
do 11 62 470
until state 470 8 8 max=600
do 14 64
until state 64 8 8 max=600
do 11 73 470
until state 471 8 8 max=1200
do 9 466
until state 463 8 0 max=1200
do 9 468
until state 464 8 8 max=1200
walk 464 180
switch 4
walk 464 180
switch 3
step 47   # (180): actor 3 pulls 478 twice (478 state 8); actor 4: 68 taken; actor 3: 70, 67 taken; 476 opened, 69 taken; 67 with 72 (493 state 4); 72 with 71
do 10 478
settle 20000
do 10 478
until state 478 8 8 max=1200
settle 20000
switch 4
do 14 68
until owns 68 max=1200
switch 3
do 14 70
until owns 70 max=1200
do 14 67
until owns 67 max=600
do 1 476
do 14 69
until owns 69 max=600
do 11 67 72
until state 493 4 4 max=600
do 11 72 71
until owner 72 0 max=600
step 48   # 472 (181), both; 466 (463 open); 463 (185), both; actor 4: 68 with 451 (script 129)
walk 472 181
switch 4
walk 472 181
switch 3
do 9 466
until state 463 8 8 max=1200
walk 463 185
switch 4
walk 463 185
do 11 68 451
until state 451 8 8 max=1200
settle 20000
switch 3
step 49   # actor 3: 444 (182): 70 with 530 (536); 531-533 pushed in the order of vars 131-136: 530 opens; 538 (32)
walk 444 182
do 11 70 530
until state 536 8 8 max=1200
do 9 $131
do 9 $132
do 9 $133
do 9 $134
do 9 $135
do 9 $136
until state 530 8 8 max=1200
settle 20000
walk 538 32
step 50   # actor 3: 507 (182): 537 taken (70); 538 (32), 508 (189): 70 with 518 (535); 71 on, verb 31 (script 55); 520 pushed: 508 state 8; var 158 at 32
walk 507 182
do 14 537
until owns 70 max=1200
walk 538 32
walk 508 189
do 11 70 518
until state 535 8 8 max=1200
do 4 71
verb 31
do 9 520
until state 508 8 8 max=3000
until stopped 55 max=6000
expect var 158 == 32
step 51   # 515 (32), 509 (190): 71 on, verb 32: 509 state 8; 517 (197), 568 (192): 57 taken; 297 (197), 563 (190), 515 (32)
walk 515 32
walk 509 190
do 4 71
verb 32
until state 509 8 8 max=3000
settle 20000
walk 517 197
walk 568 192
do 14 57
until owns 57 max=600
walk 297 197
walk 563 190
walk 515 32
step 52   # 510 (191): 71 on, verb 32: 510 state 8; 517 (196), 566 (195): 57 with 549; 76 taken; 543 (196), 563 (191), 515 (32), 507 (182), 534: (185)
walk 510 191
do 4 71
verb 32
until state 510 8 8 max=3000
settle 20000
walk 517 196
walk 566 195
do 11 57 549
until state 549 8 0 max=600
do 14 76
until owns 76 max=600
walk 543 196
walk 563 191
walk 515 32
walk 507 182
walk 534 185
step 53   # (185): 62 and 63 with 445 (script 51): both in (184); 456 (183), both; actor 4: 68 with 391 (script 99: 393 touchable)
do 11 62 445
switch 4
do 11 63 445
until egoroom 184 max=6000
settle 20000
walk 456 183
switch 3
walk 456 183
switch 4
do 11 68 391
until stopped 99 max=6000
expect owner 68 0
settle 20000
expect state 393 2 0
switch 3
step 54   # actor 1, (137): 39 put on (state 4), 36 with 14 (state 4), 14 put on (var 167), 50 put on (var 164); 81 used: (153): 486: (193)
switch 1
do 6 39
expect state 39 4 4
do 11 36 14
expect state 14 4 4
do 6 14
expect var 167 == 56
do 6 50
expect var 164 == 60
start 11 81
until room 153 max=600
wait 10
tap 486
until egoroom 193 max=6000
settle 20000
step 55   # (193): 25 with 293: drawn (300 state 8; script 132); 300 (202), 566 (198), 563 (189), 515 (32), 507 (182), 534 (185); 18 with 448: 61; 61 with 445: (184); 456: (183)
do 11 25 293
draw
until state 300 8 8 max=1200
settle 20000
walk 300 202
walk 566 198
walk 563 189
walk 515 32
walk 507 182
walk 534 185
do 11 18 448
until owns 61 max=1200
do 11 61 445
until egoroom 184 max=6000
settle 20000
walk 456 183
step 56   # (183): 31 with 393 (392 state 8); actor 3 gives 76 to actor 1; actors 1 and 4: 392 (187), 408 (186); actor 4 pushes 414 (420 state 8); actor 1: 420: (188)
do 11 31 393
until state 392 8 8 max=1200
settle 20000
switch 3
do 3 76 1
until owner 76 1 max=600
switch 1
walk 392 187
walk 408 186
switch 4
walk 392 187
walk 408 186
do 9 414
until state 420 8 8 max=600
settle 20000
switch 1
walk 420 188
step 57   # actor 4 walks away (420 state 0); actor 1: 76 with 325 (state 8), near 58; actor 4 pushes 414; actor 3: 392 (187), 408 (186), 420 (188); actor 4 walks away; actor 3 pushes 326 (312 state 8 for a moment); actor 1 at once: 58 taken
switch 4
near 413
until state 420 8 0 max=600
switch 1
do 11 76 325
until state 325 8 8 max=600
near 58
switch 4
do 9 414
until state 420 8 8 max=600
switch 3
walk 392 187
walk 408 186
walk 420 188
switch 4
near 413
until state 420 8 0 max=600
switch 3
do 9 326
until state 312 8 8 max=1200
quick switch 1
quick 14 58
until owns 58 max=600
settle 20000
step 58   # actor 1, (188): 81 used: (153): 484: (25): 78 with 426, 80 with 427, 81, 58, 55 with 428 (427-431 state 0); 423 pulled (state 8)
start 11 81
until room 153 max=600
wait 10
tap 484
until egoroom 25 max=6000
settle 20000
do 11 78 426
until state 427 8 0 max=600
do 11 80 427
until state 428 8 0 max=600
near 428
do 11 81 428
until state 429 8 0 max=600
do 11 58 428
until state 430 8 0 max=600
do 11 55 428
until state 431 8 0 max=600
do 10 423
until state 423 8 8 max=600
step 59   # actor 2, (155): 421 (206), 408 (155): 420 open; 420 (25); 423 pushed back; 425 turned on (var 201); actor 1: 424 turned on (script 65): script 66, then 149 to its end
switch 2
walk 421 206
walk 408 155
walk 420 25
do 9 423
until state 423 8 0 max=600
do 4 425
expect var 201 == 2
switch 1
start 4 424
until running 66 max=6000
until running 149 max=60000
until stopped 149 max=200000
expect state 424 8 8
expect state 425 8 8
@explore
step 1    # the mansion (44) as the sandbox starts; the character screen: actor 24, in (54)
settle 20000
expect egoroom 44
cast 24
expect egoroom 54
step 2    # (54) 655 (102), 735 (55); 714 pushed: actor 15 at (55)'s window
walk 655 102
walk 735 55
do 9 714
until actor 15 55 max=600
step 3    # (55) 722 (99), 740 (100), 741 (99), 741 (101), 735 (99), 739 (55)
walk 722 99
walk 740 100
walk 741 99
walk 741 101
walk 735 99
walk 739 55
step 4    # (55): 724, the bus (nothing paid): (53)
do 13 724
until egoroom 53 max=6000
settle 20000
step 5    # (53): 688: the destinations offered; 42 chosen (var 499); 683: (56), seated; Arrive: (57)
menu
do 13 688
expect offered
request 42
expect var 499 == 7
do 13 683
until egoroom 56 max=600
settle 20000
expect seated 24
wait 300
expect egoroom 56
request 24
until egoroom 57 max=600
settle 20000
step 6    # (57) 734 (58), 737 (59), 734 (92); 732 (59), 732 (58), 732 (57)
walk 734 58
walk 737 59
walk 734 92
walk 732 59
walk 732 58
walk 732 57
step 7    # (57): 737, 47, 732: (56), seated; Arrive: (77); 734 (78), 738 (134), 733 (78), 732 (77)
menu
do 13 737
expect offered
request 47
expect var 499 == 27
do 13 732
until egoroom 56 max=600
settle 20000
expect seated 24
request 24
until egoroom 77 max=600
settle 20000
walk 734 78
walk 738 134
walk 733 78
walk 732 77
step 8    # (77): 737, 45, 732: (56), seated; Arrive: (66); 733 (67), 735 (68), 732 (67), 734 (64), 732 (67), 739 (66)
menu
do 13 737
expect offered
request 45
expect var 499 == 16
do 13 732
until egoroom 56 max=600
settle 20000
expect seated 24
request 24
until egoroom 66 max=600
settle 20000
walk 733 67
walk 735 68
walk 732 67
walk 734 64
walk 732 67
walk 739 66
step 9    # (66): 736, 43, 732: (56), seated; Arrive: (60)
menu
do 13 736
expect offered
request 43
expect var 499 == 10
do 13 732
until egoroom 56 max=600
settle 20000
expect seated 24
request 24
until egoroom 60 max=600
settle 20000
step 10   # (60): 737, 49, 732: (56), seated; Arrive: (94); 733 (95), 735 (96), 736 (69), 739 (97), 738 (69), 740 (98), 738 (69), 741 (96), 732 (95), 734 (94)
menu
do 13 737
expect offered
request 49
expect var 499 == 44
do 13 732
until egoroom 56 max=600
settle 20000
expect seated 24
request 24
until egoroom 94 max=600
settle 20000
walk 733 95
walk 735 96
walk 736 69
walk 739 97
walk 738 69
walk 740 98
walk 738 69
walk 741 96
walk 732 95
walk 734 94
step 11   # (94): 736, 48, 732: (56), seated; Arrive: (85); 734 (86), 735 (87), 733 (88), 737 (159), 739 (164), 737 (165), 737 (166), 734 (89); back to (85)
menu
do 13 736
expect offered
request 48
expect var 499 == 35
do 13 732
until egoroom 56 max=600
settle 20000
expect seated 24
request 24
until egoroom 85 max=600
settle 20000
walk 734 86
walk 735 87
walk 733 88
walk 737 159
walk 739 164
walk 737 165
walk 737 166
walk 734 89
walk 732 166
walk 739 165
walk 739 164
walk 734 159
walk 738 88
walk 739 87
walk 732 86
walk 734 85
step 12   # (85): 737, 44, 732: (56), seated; Arrive: (61); 733 (62), 735 (63), 734 (151), 735 (63), 732 (62), 734 (61)
menu
do 13 737
expect offered
request 44
expect var 499 == 11
do 13 732
until egoroom 56 max=600
settle 20000
expect seated 24
request 24
until egoroom 61 max=600
settle 20000
walk 733 62
walk 735 63
walk 734 151
walk 735 63
walk 732 62
walk 734 61
step 13   # (61): 736, 46, 732: (56), seated; Arrive: (70); 733 (72), 734 (73), 732 (72); 733 (207), 735 (211), 733 (212), 736 (213), 735 (214), 735 (215), 732 (216), 735 (218), 738 (152); back to (72)
menu
do 13 736
expect offered
request 46
expect var 499 == 20
do 13 732
until egoroom 56 max=600
settle 20000
expect seated 24
request 24
until egoroom 70 max=600
settle 20000
walk 733 72
walk 734 73
walk 732 72
walk 733 207
walk 735 211
walk 733 212
walk 736 213
walk 735 214
walk 735 215
walk 732 216
walk 735 218
walk 738 152
walk 732 218
walk 733 216
walk 733 215
walk 733 214
walk 733 213
walk 734 212
walk 732 211
walk 732 207
walk 732 73
walk 732 72
step 14   # (72) 732 (135), 735 (74), 738 (75), 739 (76): 747: the pads offered; 54: (125), no gear
walk 732 135
walk 735 74
walk 738 75
walk 739 76
menu
do 13 747
expect offered
request 54
until egoroom 125 max=600
settle 20000
expect not air 24
step 15   # (125) 736 (120), 735 (116), 732 (110), 735 (82); 735 (111), 738 (115), 737 (124) and back; 736 (112), 738 (114), 735 (113) and back; 732 (83): no gear
walk 736 120
walk 735 116
walk 732 110
walk 735 82
walk 735 111
walk 738 115
walk 737 124
walk 732 115
walk 732 111
walk 735 82
walk 736 112
walk 738 114
walk 735 113
walk 733 114
walk 732 112
walk 735 82
walk 732 83
expect not air 24
step 16   # (83) 755 (79): gear; 743 (181), 734 (80): no gear; 748 (181), 732 (79); 746 (81), 739 (79); 740, 736: the tram: (184): gear
walk 755 79
expect air 24
walk 743 181
walk 734 80
expect not air 24
walk 748 181
walk 732 79
walk 746 81
walk 739 79
do 13 740
do 13 736
until egoroom 184 max=6000
settle 20000
expect air 24
step 17   # (184) 752 (71), 735 (187), 738 (186), 739 (84): gear; 745: the pads offered; 53: (76): no gear
walk 752 71
expect air 24
walk 735 187
walk 738 186
walk 739 84
expect air 24
menu
do 13 745
expect offered
request 53
until egoroom 76 max=600
settle 20000
expect not air 24
)PZ";
	// (Development: a route read from a file instead.)
	if (ConfMan.hasKey("scummverse_playthrough_zak_route")) {
		Common::File f;
		if (!f.open(Common::FSNode(Common::Path(ConfMan.get("scummverse_playthrough_zak_route"))))) error("SCUMMVERSE_PLAYTHROUGH_ZAK_FAIL no route file");
		pzRoute = f.readString(0, f.size());
	}
	warning("SCUMMVERSE_PLAYTHROUGH_ZAK_BEGIN mode=%s game=%d story=%d roaming=%d ready=%d room=%d", pzMode.c_str(), _game.id, _scummverseStory, _scummverseRoaming, _scummverseRoamingReady, _currentRoom);
	// (Story mode is Zak's own story, by itself; Explore mode is the mansion's
	// sandbox, Zak's places reached from it.)
	if (pzMode == "story" && !(_game.id == GID_ZAK && _scummverseStory)) error("SCUMMVERSE_PLAYTHROUGH_ZAK_FAIL not Zak's story (game %d, story %d)", _game.id, _scummverseStory);
	if (pzMode == "explore" && !(_game.id == GID_MANIAC && _scummverseRoaming)) error("SCUMMVERSE_PLAYTHROUGH_ZAK_FAIL not the mansion's sandbox (game %d, roaming %d)", _game.id, _scummverseRoaming);
	if (pzMode != "story" && pzMode != "explore") error("SCUMMVERSE_PLAYTHROUGH_ZAK_FAIL mode %s", pzMode.c_str());
	int pzFrames = 0, pzStep = 0; uint32 pzTicks = 0;
	Common::String pzLine;
	auto pzEgo = [&]() { return derefActor(VAR(VAR_EGO), "playthrough"); };
	// (What a failure shows: who is played, where, carrying what.)
	auto pzState = [&]() {
		Common::String inv;
		for (int k = 1; k <= getInventoryCount(VAR(VAR_EGO)); ++k) inv += Common::String::format(" %d", findInventory(VAR(VAR_EGO), k));
		return Common::String::format("actor %d in room %d at %d,%d, carrying%s", VAR(VAR_EGO), pzEgo()->_room, pzEgo()->getRealPos().x, pzEgo()->getRealPos().y, inv.c_str());
	};
	// Where in the room (pixels) a tap finds the object (or the actor):
	// the point nearest its middle, as the input script reads it (V1's
	// eight by two pixel steps).
	auto pzPoint = [&](int obj, int &rx, int &ry) -> bool {
		const VirtScreen &vs = _virtscr[kMainVirtScreen];
		int left, top, right, bottom, best = 1 << 30;
		const bool actor = objIsActor(obj);
		if (actor) {
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
				if ((actor ? getActorFromPos(x, y) : findObject(x, y)) != obj) continue;
				const int d = (x + 4 - cx) * (x + 4 - cx) + (y - cy) * (y - cy);
				if (d < best) { best = d; rx = x + 4; ry = y; found = true; }
			}
		return found;
	};
	auto pzDump = [&]() {
		warning("PZ dump frame %d room %d (resource %d): %s; verbs shown:", pzFrames, _currentRoom, _roomResource, pzState().c_str());
		Common::String verbs;
		for (int i = 1; i < _numVerbs; ++i) if (_verbs[i].verbid && _verbs[i].curmode == 1 && !_verbs[i].saveid) verbs += Common::String::format(" %d", _verbs[i].verbid);
		warning("PZ   verbs%s", verbs.c_str());
		for (int i = 1; i < _numLocalObjects; ++i) {
			const ObjectData &o = _objs[i];
			int rx = -1, ry = -1;
			if (o.obj_nr) pzPoint(o.obj_nr, rx, ry);
			if (o.obj_nr && (rx >= 0 || ConfMan.hasKey("scummverse_playthrough_zak_trace"))) warning("PZ   object %d at %d,%d %dx%d parent %d/%d state %d owner %d tap %d,%d", o.obj_nr, o.x_pos, o.y_pos, o.width, o.height, o.parent, o.parentstate, getState(o.obj_nr), getOwner(o.obj_nr), rx, ry);
		}
		for (int n = 1; n < _numActors; ++n) { Actor *x = derefActor(n, "playthrough"); if (x->_room) warning("PZ   actor %d in room %d at %d,%d costume %d", n, x->_room, x->getRealPos().x, x->getRealPos().y, x->_costume); }
		for (int n = 1; n <= 4; ++n) { Common::String inv; for (int k = 1; k <= getInventoryCount(n); ++k) inv += Common::String::format(" %d", findInventory(n, k)); warning("PZ   actor %d carries%s", n, inv.c_str()); }
		Common::String run;
		for (int i = 0; i < NUM_SCRIPT_SLOT; ++i) if (vm.slot[i].status != ssDead) run += Common::String::format(" %d/%d", vm.slot[i].number, vm.slot[i].where);
		warning("PZ   scripts%s", run.c_str());
	};
#define PZ_FAIL(...) pzDump(), error("SCUMMVERSE_PLAYTHROUGH_ZAK_FAIL step %d [%s] frame %d room %d: %s (%s)", pzStep, pzLine.c_str(), pzFrames, _currentRoom, Common::String::format(__VA_ARGS__).c_str(), pzState().c_str())
	const bool pzTrace = ConfMan.hasKey("scummverse_playthrough_zak_trace");
	bool pzSeen[256]; memset(pzSeen, 0, sizeof(pzSeen));
	int pzLastRoom = -1;
	// Each frame: no death or game over (Zak's scripts 78 and 154: someone
	// dies; 135: the one played caught); with the trace, the scripts that
	// start and the rooms shown.
	bool pzVisitorRooms[256]; memset(pzVisitorRooms, 0, sizeof(pzVisitorRooms));
	int pzVisitorFrames = 0, pzVisitorRoomCount = 0, pzVisitorMost = 0;
	auto pzWatch = [&]() {
		bool now[256]; memset(now, 0, sizeof(now));
		for (int i = 0; i < NUM_SCRIPT_SLOT; ++i)
			if (vm.slot[i].status != ssDead && vm.slot[i].where == WIO_GLOBAL && vm.slot[i].number < 256) now[vm.slot[i].number] = true;
		Common::String started;
		for (int s = 0; s < 256; ++s) { if (now[s] && !pzSeen[s]) started += Common::String::format(" %d", s); pzSeen[s] = now[s]; }
		if (pzTrace && !started.empty()) warning("PZ frame %d room %d ego %d: scripts%s", pzFrames, _currentRoom, VAR(VAR_EGO), started.c_str());
		if (pzTrace && pzLastRoom != _currentRoom) warning("PZ frame %d room %d (from %d)", pzFrames, _currentRoom, pzLastRoom);
		pzLastRoom = _currentRoom;
		if (_game.id == GID_ZAK && (now[78] || now[154] || now[135])) PZ_FAIL("death or game over (script %d, cause %d)", now[135] ? 135 : now[78] ? 78 : 154, _scummVars[166]);
		// (Other games' visitors in the room shown, counted.)
		int here = 0;
		for (int v = 0; v < kScummverseVisitorSlots; ++v) {
			const ScummverseVisitor &w = _scummverseVisitors[v];
			if (w.who && w.actor && w.placed && w.actor->_room == _currentRoom) ++here;
		}
		if (here) {
			++pzVisitorFrames;
			pzVisitorMost = MAX(pzVisitorMost, here);
			if (!pzVisitorRooms[_currentRoom]) { pzVisitorRooms[_currentRoom] = true; ++pzVisitorRoomCount; }
		}
	};
	// One turn of the main loop, as go() takes it (its delta), without
	// waiting for the clock; the events read as go() reads them, as often
	// as keeps the sound (mixed a slice each time, on the null backend) in
	// step with the game's time: the game waits for its sounds and music.
	double pzSoundDue = 0;
	auto pzFrame = [&]() {
		int delta = VAR_TIMER_NEXT != 0xFF ? VAR(VAR_TIMER_NEXT) : 4;
		if (delta < 1) delta = 1;
		// (Maniac V1's rounding to three, as go() takes it: the mansion.)
		if (_game.id == GID_MANIAC && _game.version == 1) delta = (delta + 2) / 3 * 3;
		_lastWaitTime = _system->getMillis();
		for (pzSoundDue += delta * 1000.0 / 60; pzSoundDue > 0; pzSoundDue -= 2048 * 1000.0 / 22050) parseEvents();
		scummLoop(delta);
		++pzFrames; pzTicks += delta;
		pzWatch();
	};
	// Why the game is not yet waiting for the player (0: it is).
	auto pzBusy = [&]() -> int {
		if (_userPut <= 0) return 1;
		if (vm.cutSceneStackPointer) return 2;
		if (_sentenceNum) return 3;
		if (isScriptRunning(2)) return 4;
		for (int i = 0; i < NUM_SCRIPT_SLOT; ++i)
			// (Its verb's script; not a background one of the thing's,
			// started for the game's own verbs 250 and 253: the V1/V2
			// sentence code marks those slots "recursive".)
			if (vm.slot[i].status != ssDead && !vm.slot[i].recursive && (vm.slot[i].where == WIO_ROOM || vm.slot[i].where == WIO_INVENTORY || vm.slot[i].where == WIO_FLOBJECT) && vm.slot[i].number == (uint)VAR(VAR_ACTIVE_OBJECT1)) return 5;
		if (pzEgo()->_moving) return 6;
		return 0;
	};
	auto pzSettle = [&](int limit) {
		int calm = 0, n = 0;
		for (; n < limit && calm < 8; ++n) { pzFrame(); calm = pzBusy() ? 0 : calm + 1; }
		if (calm < 8) PZ_FAIL("the game never waited for the player (busy %d after %d frames)", pzBusy(), n);
	};
	// A tap on the screen (screen pixels), taken as the mouse's.
	auto pzClick = [&](int sx, int sy) {
		_mouse.x = sx; _mouse.y = sy; _leftBtnPressed = 3;
		pzFrame();
		_leftBtnPressed = 0;
	};
	auto pzVerb = [&](int verb) {
		for (int i = 1; i < _numVerbs; ++i) {
			const VerbSlot &vs = _verbs[i];
			if (vs.verbid != verb || vs.curmode != 1 || vs.saveid) continue;
			const int x = (vs.curRect.left + vs.curRect.right) / 2, y = (vs.curRect.top + vs.curRect.bottom) / 2;
			if (findVerbAtPos(x, y) != i) continue;
			pzClick(x, y);
			return;
		}
		PZ_FAIL("verb %d not shown", verb);
	};
	auto pzOnScreen = [&](int rx) { const VirtScreen &vs = _virtscr[kMainVirtScreen]; return rx >= vs.xstart && rx < vs.xstart + _screenWidth; };
	auto pzWellOnScreen = [&](int rx) {
		const VirtScreen &vs = _virtscr[kMainVirtScreen];
		if (!pzOnScreen(rx)) return false;
		// (Or where the camera goes no further: the room's ends, or its
		// scrolling limits, as the plane's cabin sets them.)
		const bool leftEnd = vs.xstart <= 0 || camera._cur.x <= VAR(VAR_CAMERA_MIN_X), rightEnd = vs.xstart + _screenWidth >= _roomWidth || camera._cur.x >= VAR(VAR_CAMERA_MAX_X);
		return (leftEnd || rx >= vs.xstart + 40) && (rightEnd || rx < vs.xstart + _screenWidth - 40);
	};
	auto pzCarried = [&](int obj) { return !objIsActor(obj) && whereIsObject(obj) == WIO_INVENTORY; };
	int pzRoomAt = -1;
	auto pzInterrupted = [&]() { return _userPut <= 0 || vm.cutSceneStackPointer || _currentRoom != pzRoomAt; };
	// Off screen: the one played walks towards it, as a player would (Walk
	// to the floor at the screen's edge on its side), until it shows.
	auto pzShow = [&](int obj) -> bool {
		if (pzCarried(obj)) return true;
		int rx = 0, ry = 0;
		auto where = [&]() -> bool {
			if (objIsActor(obj)) { Actor *a = derefActor(obj, "playthrough"); rx = a->getRealPos().x * V12_X_MULTIPLIER; return a->_room == _currentRoom; }
			return pzPoint(obj, rx, ry);
		};
		if (!where()) PZ_FAIL("%d cannot be tapped in room %d", obj, _currentRoom);
		for (int tries = 0; !pzWellOnScreen(rx) && tries < 40; ++tries) {
			const VirtScreen &vs = _virtscr[kMainVirtScreen];
			const int idx = objIsActor(obj) ? -1 : getObjectIndex(obj);
			const int floors[2] = {pzEgo()->getRealPos().y * V12_Y_MULTIPLIER, idx >= 0 ? _objs[idx].walk_y : pzEgo()->getRealPos().y * V12_Y_MULTIPLIER};
			// (Towards it, no further than where it is: past it may be
			// something else's, as the sandbox's bus stop on Zak's street.)
			const int sx = CLIP(rx - vs.xstart, 4, _screenWidth - 4);
			int sy = -1;
			for (int f = tries & 1; f < 2 && sy < 0; ++f)
				for (int d = 0; d < 40 && sy < 0; d += 2)
					for (int sgn = -1; sgn <= 1 && sy < 0; sgn += 2) {
						const int y = CLIP(floors[f] + sgn * d, 0, vs.h - 2) / 2 * 2;
						if (!findObject((vs.xstart + sx) / 8 * 8, y)) sy = y;
					}
			// (Things at the edge from floor to ceiling, as a bus: Walk to
			// there all the same; it walks towards them.)
			if (sy < 0) sy = CLIP(floors[1], 0, vs.h - 2) / 2 * 2;
			pzVerb(13);
			pzClick(sx, sy + vs.topline);
			pzSettle(3000);
			for (int n = 0, still = 0; n < 200 && still < 3; ++n) { const int x0 = camera._cur.x; pzFrame(); still = camera._cur.x == x0 ? still + 1 : 0; }
			if (pzInterrupted()) return false;
			if (!where()) PZ_FAIL("%d gone while walking to it", obj);
		}
		if (!pzOnScreen(rx)) PZ_FAIL("%d (x %d) never came on screen", obj, rx);
		return true;
	};
	// One tap on a thing; carried things where the inventory shows them.
	auto pzTap = [&](int obj) -> bool {
		if (pzInterrupted()) return false;
		if (pzCarried(obj)) {
			if (getOwner(obj) != VAR(VAR_EGO)) PZ_FAIL("%d is carried by %d, not %d", obj, getOwner(obj), VAR(VAR_EGO));
			runInputScript(kInventoryClickArea, obj, 0);
			return true;
		}
		int rx = 0, ry = 0;
		if (!pzPoint(obj, rx, ry)) PZ_FAIL("%d cannot be tapped in room %d", obj, _currentRoom);
		if (!pzOnScreen(rx)) PZ_FAIL("%d (x %d) off screen", obj, rx);
		const VirtScreen &vs = _virtscr[kMainVirtScreen];
		pzClick(rx - vs.xstart, ry + vs.topline);
		if (pzTrace) warning("PZ frame %d tap %d at %d,%d: sentence %d %d %d", pzFrames, obj, rx, ry, _scummVars[26], _scummVars[27], _scummVars[28]);
		return !pzInterrupted();
	};
	auto pzAttempt = [&](int verb, int o1, int o2) -> bool {
		pzSettle(20000);
		pzRoomAt = _currentRoom;
		if (!pzShow(o1) || (o2 && !pzShow(o2))) return false;
		if (!pzCarried(o1)) {
			int rx = -1, ry = 0;
			if (objIsActor(o1)) rx = derefActor(o1, "playthrough")->getRealPos().x * V12_X_MULTIPLIER;
			else pzPoint(o1, rx, ry);
			if (!pzWellOnScreen(rx)) return false;
		}
		pzVerb(verb);
		// (Zak's input script keeps the sentence's thing when another verb
		// is tapped, Give (3) and Switch aside: verb 13 on a thing, then 11,
		// is verb 11 on it. The player taps Give first, which clears it.)
		if (verb != 13 && verb != 3 && _scummVars[27]) { pzVerb(3); pzVerb(verb); }
		if (_scummVars[26] != verb) PZ_FAIL("verb %d tapped, the sentence's verb is %d", verb, _scummVars[26]);
		if (verb == 13) { pzTap(o1); return true; }
		if (!pzTap(o1)) return false;
		if (_scummVars[27] != o1) PZ_FAIL("tapped %d, the sentence has %d", o1, _scummVars[27]);
		if (o2) {
			if (!_scummVars[29]) PZ_FAIL("verb %d with %d takes no second thing", verb, o1);
			if (!pzTap(o2)) return false;
			if (_scummVars[28] != o2) PZ_FAIL("tapped %d second, the sentence has %d", o2, _scummVars[28]);
			pzTap(o2);
		} else {
			if (_scummVars[29]) PZ_FAIL("verb %d with %d wants a second thing", verb, o1);
			pzTap(o1);
		}
		return true;
	};
	// (goal: a room the sentence leads to; reached on the way, as the
	// one played walks towards a way out at the screen's edge, it is done.)
	// (leave: a room the sentence leads out of, to anywhere: the jungle.)
	auto pzSentence = [&](int verb, int o1, int o2, int goal, int leave) {
		for (int tries = 0; !pzAttempt(verb, o1, o2); ++tries) {
			if (goal >= 0 && _currentRoom == goal && pzEgo()->_room == goal) break;
			if (leave >= 0 && _currentRoom != leave && pzEgo()->_room == _currentRoom) break;
			if (tries >= 5) PZ_FAIL("interrupted %d times", tries + 1);
			if (pzTrace) warning("PZ frame %d sentence %d %d %d interrupted; again", pzFrames, verb, o1, o2);
		}
		pzFrame();
		pzSettle(20000);
	};
	// Conditions: room R | egoroom R | state O MASK VALUE | owns O |
	// owner O A | var N OP V | bit N OP V | running S | stopped S |
	// actor A R | ego A, each may follow "not".
	int pzOffers = 0;
	auto pzCond1 = [&](const Common::StringArray &t, uint at) -> bool {
		if (at >= t.size()) PZ_FAIL("condition missing");
		const Common::String &k = t[at];
		auto num = [&](uint i) { if (at + i >= t.size()) PZ_FAIL("condition %s: too short", k.c_str()); return atoi(t[at + i].c_str()); };
		if (k == "room") return _currentRoom == num(1);
		if (k == "egoroom") return _currentRoom == num(1) && pzEgo()->_room == num(1);
		if (k == "state") return (getState(num(1)) & num(2)) == num(3);
		if (k == "owns") return getOwner(num(1)) == VAR(VAR_EGO);
		if (k == "owner") return getOwner(num(1)) == num(2);
		if (k == "running") return isScriptRunning(num(1));
		if (k == "stopped") return !isScriptRunning(num(1));
		if (k == "actor") return derefActor(num(1), "playthrough")->_room == num(2);
		if (k == "ego") return VAR(VAR_EGO) == num(1);
		// (The sandbox's: a menu offered to the phone (the airport's or the
		// pads'), a seat on the plane, the air gear drawn on someone.)
		if (k == "offered") return FakeAI::airportOffers > pzOffers;
		if (k == "seated") return scummverseSeated(num(1));
		if (k == "air") return scummverseNeedsAir(derefActor(num(1), "playthrough"));
		if (k == "visitors") return pzVisitorRooms[num(1) & 255];
		if (k == "var" || k == "bit") {
			const int v = k == "var" ? _scummVars[num(1)] : ((_scummVars[num(1) >> 4] >> (num(1) & 15)) & 1);
			if (at + 3 >= t.size()) PZ_FAIL("condition %s: too short", k.c_str());
			const Common::String &op = t[at + 2]; const int w = num(3);
			if (op == "==") return v == w;
			if (op == "!=") return v != w;
			if (op == ">=") return v >= w;
			if (op == "<=") return v <= w;
			PZ_FAIL("condition %s: operator %s", k.c_str(), op.c_str());
		}
		PZ_FAIL("unknown condition %s", k.c_str());
		return false;
	};
	auto pzCond = [&](const Common::StringArray &t, uint at) -> bool {
		const bool neg = at < t.size() && t[at] == "not";
		return neg != pzCond1(t, at + (neg ? 1 : 0));
	};
	const uint32 pzStart = _system->getMillis();
	const Common::StringArray pzLines = Common::StringTokenizer(pzRoute, "\n").split();
	Common::String pzSection = "both";
	// (Development: checkpoints saved at each step, and a run begun from one.)
	const bool pzCheckpoints = ConfMan.hasKey("scummverse_playthrough_zak_checkpoints");
	const int pzFrom = ConfMan.hasKey("scummverse_playthrough_zak_from") ? ConfMan.getInt("scummverse_playthrough_zak_from") : 0;
	bool pzSkipping = pzFrom > 0;
	for (uint li = 0; li < pzLines.size(); ++li) {
		Common::String line = pzLines[li];
		const int hash = line.findFirstOf('#');
		if (hash >= 0) line = Common::String(line.c_str(), hash);
		line.trim();
		if (line.empty()) continue;
		const Common::StringArray t = Common::StringTokenizer(line, " \t").split();
		if (t[0] == "@story" || t[0] == "@explore") { pzSection = t[0].c_str() + 1; continue; }
		if (pzSection != pzMode) continue;
		pzLine = line;
		const Common::String &c = t[0];
		// (An argument $N: what the game holds in its variable N, as an
		// order or an answer the player has read in the game.)
		auto arg = [&](uint i) { if (i >= t.size()) PZ_FAIL("missing argument"); return t[i].hasPrefix("$") ? (int)_scummVars[atoi(t[i].c_str() + 1)] : atoi(t[i].c_str()); };
		if (c == "step") {
			pzStep = arg(1);
			if (pzSkipping && pzStep == pzFrom) {
				pzSkipping = false;
				requestLoad(10 + pzStep % 80);
				pzFrame();
				warning("PZ step %d: begun from its checkpoint (room %d)", pzStep, _currentRoom);
				pzSettle(20000);
			} else if (!pzSkipping && pzCheckpoints) {
				pzSettle(20000);
				requestSave(10 + pzStep % 80, Common::String::format("step %d", pzStep));
				pzFrame();
			}
			if (pzTrace) warning("PZ step %d frame %d room %d", pzStep, pzFrames, _currentRoom);
			continue;
		}
		if (pzSkipping) continue;
		if (c == "do") pzSentence(arg(1), arg(2), t.size() > 3 ? arg(3) : 0, -1, -1);
		// start V O [O2]: the sentence made, not waited for (it opens a
		// screen of its own, as object 81 used does: room 153).
		else if (c == "start") { if (!pzAttempt(arg(1), arg(2), t.size() > 3 ? arg(3) : 0)) PZ_FAIL("interrupted"); pzFrame(); }
		// door O R: opened if shut (1), walked through (13) into room R;
		// walk O R: walked through (stairs, ways out).
		else if (c == "door" || c == "walk") {
			const int o = arg(1), r = arg(2);
			pzSettle(20000);
			if (c == "door" && !(getState(o) & kObjectStateIntrinsic)) {
				pzSentence(1, o, 0, -1, -1);
				if (!(getState(o) & kObjectStateIntrinsic)) PZ_FAIL("door %d did not open (state %d)", o, getState(o));
			}
			auto there = [&]() { return _currentRoom == r && pzEgo()->_room == r; };
			for (int tries = 0; tries < 4 && !there(); ++tries) {
				pzSentence(13, o, 0, r, -1);
				for (int n = 0; n < 600 && !there(); ++n) pzFrame();
			}
			if (!there()) PZ_FAIL("through %d: in room %d, not %d", o, _currentRoom, r);
		}
		// near O: Walk to O (to where the game walks to it), in this room.
		else if (c == "near") { pzSentence(13, arg(1), 0, -1, -1); pzSettle(20000); }
		// to X Y: Walk to that floor spot (room pixels).
		else if (c == "to") {
			pzSettle(20000);
			const VirtScreen &vs = _virtscr[kMainVirtScreen];
			const int x = arg(1), y = arg(2);
			for (int tries = 0; tries < 20 && !(x >= vs.xstart && x < vs.xstart + _screenWidth); ++tries) {
				pzVerb(13); pzClick(x < vs.xstart ? 4 : _screenWidth - 4, y + vs.topline); pzSettle(3000);
			}
			pzVerb(13);
			pzClick(x - vs.xstart, y + vs.topline);
			pzSettle(20000);
		}
		else if (c == "expect") { if (!pzCond(t, 1)) PZ_FAIL("not %s", line.c_str() + 7); }
		else if (c == "until") {
			const int limit = t.back().hasPrefix("max=") ? atoi(t.back().c_str() + 4) : 20000;
			for (int n = 0; !pzCond(t, 1); ++n) { if (n >= limit) PZ_FAIL("waited %d frames for %s", limit, line.c_str() + 6); pzFrame(); }
		}
		else if (c == "wait") { for (int n = arg(1); n > 0; --n) pzFrame(); }
		else if (c == "settle") pzSettle(t.size() > 1 ? arg(1) : 6000);
		// tap THING: one tap (where a tap does it).
		else if (c == "tap") { pzRoomAt = _currentRoom; pzTap(arg(1)); pzFrame(); }
		// verb V: one verb tapped.
		else if (c == "verb") { pzVerb(arg(1)); pzFrame(); }
		// switch A: Switch (verb 45), then the name (verb 45 + A).
		else if (c == "switch") {
			const int a = arg(1);
			pzSettle(20000);
			pzVerb(45);
			pzFrame();
			pzVerb(45 + a);
			for (int n = 0; n < 600 && VAR(VAR_EGO) != a; ++n) pzFrame();
			if (VAR(VAR_EGO) != a) PZ_FAIL("playing %d, not %d", VAR(VAR_EGO), a);
			pzSettle(20000);
		}
		// jungle R: a jungle's paths walked (not back the way in, the
		// game's Var[58]) until the one played is in room R.
		else if (c == "jungle") {
			const int r = arg(1);
			for (int walks = 0; !(_currentRoom == r && pzEgo()->_room == r); ++walks) {
				if (walks >= 30) PZ_FAIL("lost in the jungle (room %d)", _currentRoom);
				pzSettle(20000);
				int path = 0;
				for (int o = 572; o <= 575 && !path; ++o) { int rx, ry; if (o != _scummVars[58] && !(getState(o) & kObjectStateUntouchable) && pzPoint(o, rx, ry)) path = o; }
				if (!path) PZ_FAIL("no way on in the jungle (room %d, way in %d)", _currentRoom, _scummVars[58]);
				const int from = _currentRoom;
				pzSentence(13, path, 0, -1, from);
				for (int n = 0; n < 3000 && _currentRoom == from; ++n) pzFrame();
				if (pzTrace) warning("PZ jungle: path %d from %d to %d", path, from, _currentRoom);
			}
			pzSettle(20000);
		}
		// draw: on the drawing screen (room 48), the squares tapped as the
		// markings read (Var[119], Var[120]), then the verb that ends it.
		else if (c == "draw") {
			for (int n = 0; n < 600 && _currentRoom != 48; ++n) pzFrame();
			if (_currentRoom != 48) PZ_FAIL("no drawing screen (room %d)", _currentRoom);
			pzSettle(20000);
			pzRoomAt = _currentRoom;
			for (int i = 0; i < 24; ++i) {
				const bool want = (_scummVars[119 + i / 16] >> (i % 16)) & 1, have = (getState(672 + i) & kObjectStateIntrinsic) != 0;
				if (want == have) continue;
				pzTap(672 + i);
				pzSettle(20000);
				if (((getState(672 + i) & kObjectStateIntrinsic) != 0) != want) PZ_FAIL("square %d did not change", 672 + i);
			}
			pzVerb(30);
			// (The drawing script judges it once back in the room.)
			for (int n = 0; n < 3000 && (_currentRoom == 48 || isScriptRunning(28)); ++n) pzFrame();
			pzSettle(20000);
		}
		// book CARD TERMINAL DEST: a flight booked as the player books it
		// (the card used with the terminal; on its screen, room 45, the
		// destination tapped, then the button that buys it).
		else if (c == "book") {
			pzSettle(20000);
			const int home = _currentRoom, dest = arg(3);
			pzSentence(11, arg(1), arg(2), -1, -1);
			for (int n = 0; n < 600 && _currentRoom != 45; ++n) pzFrame();
			if (_currentRoom != 45) PZ_FAIL("no reservations screen (room %d)", _currentRoom);
			for (int n = 0; n < 10; ++n) pzFrame();
			pzRoomAt = 45; pzTap(dest); pzFrame();
			for (int n = 0; n < 600 && _scummVars[121] != 1024; ++n) pzFrame();
			for (int n = 0; n < 30; ++n) pzFrame();
			pzRoomAt = 45; pzTap(657); pzFrame();
			for (int n = 0; n < 3000 && !(_currentRoom == home && pzEgo()->_room == home); ++n) pzFrame();
			if (_currentRoom != home) PZ_FAIL("not back from the reservations screen (room %d)", _currentRoom);
			pzSettle(20000);
			if (_scummVars[78 + VAR(VAR_EGO)] != dest) PZ_FAIL("no ticket to %d (ticket var %d)", dest, _scummVars[78 + VAR(VAR_EGO)]);
		}
		// gate G R: through the gate to the plane, flown to room R.
		else if (c == "gate") {
			const int r = arg(2);
			pzSentence(13, arg(1), 0, -1, -1);
			for (int n = 0; n < 40000 && !(_currentRoom == r && pzEgo()->_room == r); ++n) pzFrame();
			if (_currentRoom != r) PZ_FAIL("the flight did not reach %d (room %d)", r, _currentRoom);
			pzSettle(20000);
		}
		// owners O...: who holds each thing, and its state.
		else if (c == "owners") { Common::String s; for (uint i = 1; i < t.size(); ++i) s += Common::String::format(" %d=%d/%d", atoi(t[i].c_str()), getOwner(atoi(t[i].c_str())), getState(atoi(t[i].c_str()))); warning("PZ owners%s", s.c_str()); }
		else if (c == "boxes") {
			warning("PZ boxes: ego in box %d at %d,%d", pzEgo()->_walkbox, pzEgo()->getRealPos().x, pzEgo()->getRealPos().y);
			for (int b = 0; b < getNumBoxes(); ++b) { BoxCoords bc = getBoxCoordinates(b); warning("PZ   box %d flags %d: %d,%d %d,%d %d,%d %d,%d", b, getBoxFlags(b), bc.ul.x, bc.ul.y, bc.ur.x, bc.ur.y, bc.lr.x, bc.lr.y, bc.ll.x, bc.ll.y); }
		}
		// quick switch A | quick V O: as fast as a player taps, not
		// waiting for the game to settle first (object 312 stays open
		// two seconds: one presses, the other takes).
		else if (c == "quick" && t.size() > 1 && t[1] == "switch") {
			const int a = arg(2);
			pzVerb(45); pzFrame(); pzVerb(45 + a);
			for (int n = 0; n < 60 && VAR(VAR_EGO) != a; ++n) pzFrame();
			if (VAR(VAR_EGO) != a) PZ_FAIL("playing %d, not %d", VAR(VAR_EGO), a);
		}
		else if (c == "quick") {
			const int v = arg(1), o = arg(2);
			pzRoomAt = _currentRoom;
			pzVerb(v);
			if (_scummVars[27]) { pzVerb(3); pzVerb(v); }
			pzTap(o);
			if (_scummVars[27] != o) PZ_FAIL("tapped %d, the sentence has %d", o, _scummVars[27]);
			pzTap(o);
		}
		// cast A: the character screen (verb 7 in the mansion; here the
		// test's stand-in for the phone's), A chosen on it.
		else if (c == "cast") {
			const int a = arg(1), shown = FakeAI::castShown;
			pzSettle(20000);
			pzVerb(7);
			pzFrame();
			if (FakeAI::castShown == shown) PZ_FAIL("verb 7 showed no character screen");
			FakeAI::worldRequest = ::Scummverse::WorldCatalog::kWorldCastActorRequest + a;
			for (int n = 0; n < 600 && VAR(VAR_EGO) != a; ++n) pzFrame();
			if (VAR(VAR_EGO) != a) PZ_FAIL("playing %d, not %d", VAR(VAR_EGO), a);
			pzSettle(20000);
		}
		// request C: what a menu of the phone's sends for the one played
		// here (its scene's token and the command C).
		else if (c == "request") {
			pzSettle(20000);
			FakeAI::worldRequest = ((_currentRoom * 32 + VAR(VAR_EGO)) << 8) | arg(1);
			for (int n = 0; n < 600 && FakeAI::worldRequest; ++n) pzFrame();
			if (FakeAI::worldRequest) PZ_FAIL("request %d not taken", arg(1));
			pzFrame();
			pzSettle(20000);
		}
		// place R: one of Zak's places chosen from the Worlds menu.
		else if (c == "place") {
			pzSettle(20000);
			FakeAI::worldRequest = ::Scummverse::WorldCatalog::kWorldPlaceRequest + ::Scummverse::WorldCatalog::kWorldZakPlaces * 1024 + arg(1);
			for (int n = 0; n < 600 && FakeAI::worldRequest; ++n) pzFrame();
			pzSettle(20000);
		}
		// expect offered: since the last tap of this kind (offers counted
		// from here).
		else if (c == "menu") pzOffers = FakeAI::airportOffers;
		else if (c == "dump") pzDump();
		else if (c == "vars") { Common::String s; for (uint i = 1; i < t.size(); ++i) s += Common::String::format(" %s=%d", t[i].c_str(), _scummVars[atoi(t[i].c_str())]); warning("PZ vars%s", s.c_str()); }
		else if (c == "end") break;
		else PZ_FAIL("unknown command %s", c.c_str());
	}
	if (pzCheckpoints) { requestSave(10 + (pzStep + 1) % 80, "end"); pzFrame(); }
	// Story mode: none of the mansion's additions at all; Explore mode: the
	// sandbox, with other games' visitors in as many rooms as asked.
	if (pzMode == "story" && (_scummverseRoaming || _scummverseRoamingReady || _scummverseExplorationDoors || _scummverseExplorationSafety || pzVisitorFrames))
		PZ_FAIL("the mansion's additions in the story: roaming %d/%d, doors %d, safety %d, visitors seen %d frames", _scummverseRoaming, _scummverseRoamingReady, _scummverseExplorationDoors, _scummverseExplorationSafety, pzVisitorFrames);
	const int pzVisitorsAsked = ConfMan.hasKey("scummverse_playthrough_zak_visitor_rooms") ? ConfMan.getInt("scummverse_playthrough_zak_visitor_rooms") : 0;
	if (pzMode == "explore" && (!_scummverseRoamingReady || pzVisitorRoomCount < pzVisitorsAsked))
		PZ_FAIL("the sandbox: roaming %d, visitors in %d rooms (%d asked)", _scummverseRoamingReady, pzVisitorRoomCount, pzVisitorsAsked);
	warning("SCUMMVERSE_PLAYTHROUGH_ZAK_PASS mode=%s steps=%d frames=%d gameticks=%u seconds=%u visitors: %d frames, %d rooms, at most %d at once", pzMode.c_str(), pzStep, pzFrames, pzTicks, (_system->getMillis() - pzStart) / 1000, pzVisitorFrames, pzVisitorRoomCount, pzVisitorMost);
#undef PZ_FAIL
	quitGame();
	return;
	}
