 // Run original entry handlers, rather than inferring rooms from backgrounds.
 if(_game.id!=GID_ZAK || _game.version!=1 || _scummverseRoaming)
  error("Mars reference requires isolated original Zak DOS V1");
 for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
 _currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=5;
 Actor *a=derefActor(5,"original Mars reference");a->setActorCostume(1);a->setPalette(1,13);
 const int rooms[][2]={{32,32},{34,34},{180,28},{181,28},{182,33},{184,27},{185,27},{188,15},{189,33},{190,33},{191,33},{192,14},{193,14},{194,35},{195,35},{196,36},{197,36},{198,36},{199,36},{200,36},{201,36},{202,36},{203,36},{204,36},{205,36}};
 for(const auto &r:rooms) if(r[0]>=128) _resourceMapper[r[0]&127]=r[1];
 byte initialStates[775];for(int id=0;id<775;++id) initialStates[id]=getState(id);
 Common::String report="{\"edition\":\"zak-dos-v1-en\",\"scenes\":[";
 for(const auto &definition:rooms) {
  int room=definition[0];
  for(int id=0;id<775;++id) putState(id,initialStates[id]);
  for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
  _currentScript=0xFF;
  // Transition pairs are scratch variables; avoid inheriting absent exits.
  for(int key=44;key<=55;++key) _scummVars[key]=0;
  // Explicit exploration fixture: original massive doors and rock tunnels open.
  // These are source puzzle states, not permission to run foreign scripts in-game.
  for(int id:{508,509,510,530,300,302,304}) putState(id,getState(id)|8);
  for(int id:{299,301,303}) putState(id,getState(id)|4);
  _scummVars[161]=57;_scummVars[162]=57;
  a->putActor(60,55,room);startScene(room,a,0);
  for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
  _currentScript=0xFF;
  if(_currentRoom!=room || _roomResource!=definition[1]) error("Mars logical resource mismatch");
  if(room!=32) report+=",";
  report+=Common::String::format("{\"logical_room\":%d,\"resource\":%d,\"camera\":[%d,%d],\"objects\":[",room,_roomResource,VAR(VAR_CAMERA_MIN_X),VAR(VAR_CAMERA_MAX_X));
  bool first=true;
  for(int n=1;n<_numLocalObjects;++n) if(_objs[n].obj_nr) {
   if(!first) report+=",";first=false;
   report+=Common::String::format("{\"id\":%d,\"x\":%d,\"y\":%d,\"state\":%d,\"walk_x\":%d,\"walk_y\":%d}",_objs[n].obj_nr,_objs[n].x_pos,_objs[n].y_pos,getState(_objs[n].obj_nr),_objs[n].walk_x,_objs[n].walk_y);
  }
  report+="],\"transition_pairs\":[";
  for(int key=44;key<=54;key+=2) {
   if(key!=44) report+=",";
   report+=Common::String::format("[%d,%d]",_scummVars[key],_scummVars[key+1]);
  }
  report+="],\"palette\":[";
  for(int c=0;c<3;++c) {if(c)report+=",";report+=Common::String::format("%d",_roomPalette[c]);}
  report+="],\"box_flags\":[";
  for(int box=0;box<getNumBoxes();++box) {if(box)report+=",";report+=Common::String::format("%d",getBoxFlags(box));}
  report+="]}";
  // Illuminate the reference for visual audit; lighting puzzles are out of scope.
  VAR(VAR_CURRENT_LIGHTS)=11;stopTalk();VAR(VAR_HAVE_MSG)=0;
  setCameraFollows(a);setCameraAtEx(VAR(VAR_CAMERA_MIN_X));a->hideActor();cameraMoved();updateObjectStates();_fullRedraw=true;scummLoop_handleDrawing();
  Common::DumpFile shot;
  if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/mars-reference-%d.ppm",room)))) {
   Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
   for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
  }
 }
 report+="]}\n";Common::DumpFile out;
 if(!out.open(Common::Path("/workspace/Maniac-Online/build/mars-reference.json"))) error("Cannot write private Mars audit");
 out.write(report.c_str(),report.size());out.close();
 warning("SCUMMVERSE_MARS_REFERENCE_PASS enabled=%d",ConfMan.getBool("scummverse_roaming"));quitGame();
