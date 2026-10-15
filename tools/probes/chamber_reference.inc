 // Run original entry handlers, rather than inferring rooms from backgrounds.
 if(_game.id!=GID_ZAK || _game.version!=1 || _scummverseRoaming)
  error("Chamber reference requires isolated original Zak DOS V1");
 for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
 _currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=1;
 Actor *a=derefActor(1,"original chamber reference");a->setActorCostume(1);a->setPalette(1,13);

 for(int room : {129,130,192,193}) _resourceMapper[room&127]=14;
 byte initialStates[775];for(int id=0;id<775;++id) initialStates[id]=getState(id);
 Common::String report="{\"edition\":\"zak-dos-v1-en\",\"scenes\":[";
 for(int room : {129,130,192,193}) {
  for(int id=0;id<775;++id) putState(id,initialStates[id]);
  for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
  _currentScript=0xFF;
  // Transition pairs are scratch variables; avoid inheriting absent exits.
  for(int key=44;key<=55;++key) _scummVars[key]=0;
  a->putActor(20,55,room);startScene(room,a,0);
  for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
  _currentScript=0xFF;
  if(_currentRoom!=room || _roomResource!=14)
   error("Logical temple scene did not resolve to original resource 14");
  if(room!=129) report+=",";
  report+=Common::String::format("{\"logical_room\":%d,\"resource\":%d,\"camera\":[%d,%d],\"objects\":[",room,_roomResource,VAR(VAR_CAMERA_MIN_X),VAR(VAR_CAMERA_MAX_X));
  bool first=true;
  for(int n=1;n<_numLocalObjects;++n) if(_objs[n].obj_nr) {
   if(!first) report+=",";first=false;
   report+=Common::String::format("{\"id\":%d,\"x\":%d,\"y\":%d,\"state\":%d}",_objs[n].obj_nr,_objs[n].x_pos,_objs[n].y_pos,getState(_objs[n].obj_nr));
  }
  report+="],\"transition_pairs\":[";
  for(int key=44;key<=54;key+=2) {
   if(key!=44) report+=",";
   report+=Common::String::format("[%d,%d]",_scummVars[key],_scummVars[key+1]);
  }
  report+="],\"box_flags\":[";
  for(int box=0;box<getNumBoxes();++box) {if(box)report+=",";report+=Common::String::format("%d",getBoxFlags(box));}
  report+="]}";
  // Illuminate the reference for visual audit; lighting puzzles are out of scope.
  VAR(VAR_CURRENT_LIGHTS)=11;stopTalk();VAR(VAR_HAVE_MSG)=0;
  setCameraFollows(a);setCameraAtEx(160);a->hideActor();cameraMoved();updateObjectStates();_fullRedraw=true;scummLoop_handleDrawing();
  Common::DumpFile shot;
  if(shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/chamber-reference-%d.ppm",room)))) {
   Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
   for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte c=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*c,3);}
  }
 }
 report+="]}\n";Common::DumpFile out;
 if(!out.open(Common::Path("/workspace/Maniac-Online/build/chamber-reference.json"))) error("Cannot write private temple audit");
 out.write(report.c_str(),report.size());out.close();
 warning("SCUMMVERSE_CHAMBER_REFERENCE_PASS enabled=%d",ConfMan.getBool("scummverse_roaming"));quitGame();
