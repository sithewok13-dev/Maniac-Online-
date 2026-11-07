 // Render original logical scenes through Zak's own entry handlers. Private
 // captures only; no scripts or artwork leave build/. @CANDIDATES@ expands to
 // {logical room, physical resource, region} triples. Region is the original
 // per-actor destination variable (222+ego) that jungle entry uses for colors.
 if(_game.id!=GID_ZAK || _game.version!=1 || _scummverseRoaming)
  error("Scene audit reference requires isolated original Zak DOS V1");
 for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
 _currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=1;
 Actor *a=derefActor(1,"scene audit reference");a->setActorCostume(1);
 const int candidates[][3]={@CANDIDATES@};
 for(const auto &c:candidates) if(c[0]>=128) _resourceMapper[c[0]&127]=c[1];
 byte initialStates[775];for(int id=0;id<775;++id) initialStates[id]=getState(id);
 Common::String report="{\"scenes\":[";
 bool firstScene=true;
 for(const auto &c:candidates) {
  const int room=c[0];
  for(int id=0;id<775;++id) putState(id,initialStates[id]);
  for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
  _currentScript=0xFF;
  for(int key=44;key<=60;++key) _scummVars[key]=0;
  _scummVars[223]=c[2];
  _rnd.setSeed(1); // Entry handlers randomize scenery (e.g. airport planes).
  a->putActor(60,55,room);startScene(room,a,0);_sound->processSound();
  for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
  _currentScript=0xFF;
  if(_currentRoom!=room || _roomResource!=c[1]) error("Logical %d resolved to resource %d, expected %d",room,_roomResource,c[1]);
  report+=Common::String::format("%s{\"logical_room\":%d,\"resource\":%d,\"region\":%d,\"camera\":[%d,%d],\"palette\":[%d,%d,%d],\"objects\":[",
   firstScene?"":",",room,_roomResource,c[2],VAR(VAR_CAMERA_MIN_X),VAR(VAR_CAMERA_MAX_X),_roomPalette[0],_roomPalette[1],_roomPalette[2]);
  // Room-file order, matching the sandbox importer's scratch numbering.
  for(int n=1,first=1;n<_numLocalObjects;++n) if(_objs[n].obj_nr) {
   report+=Common::String::format("%s{\"id\":%d,\"x\":%d,\"y\":%d,\"state\":%d}",first?"":",",_objs[n].obj_nr,_objs[n].x_pos,_objs[n].y_pos,getState(_objs[n].obj_nr));first=0;
  }
  report+="],\"box_flags\":[";
  for(int box=0;box<getNumBoxes();++box) report+=Common::String::format("%s%d",box?",":"",getBoxFlags(box));
  report+="]}";
  firstScene=false;
  // Illuminate for visual audit; lighting puzzles are out of scope.
  VAR(VAR_CURRENT_LIGHTS)=11;stopTalk();VAR(VAR_HAVE_MSG)=0;
  setCameraFollows(a);setCameraAtEx(VAR(VAR_CAMERA_MIN_X));a->hideActor();cameraMoved();updateObjectStates();_fullRedraw=true;scummLoop_handleDrawing();
  Common::DumpFile shot;
  if(!shot.open(Common::Path(Common::String::format("/workspace/Maniac-Online/build/scene-audit/ref-%d-%d.ppm",room,c[2])))) error("Cannot write scene audit");
  Common::String h=Common::String::format("P6\n%d %d\n255\n",_screenWidth,_virtscr[0].h);shot.write(h.c_str(),h.size());
  for(int y=0;y<_virtscr[0].h;++y) for(int x=0;x<_screenWidth;++x) {byte p=*_virtscr[0].getPixels(x,y);shot.write(_currentPalette+3*p,3);}
 }
 report+="]}\n";Common::DumpFile out;
 if(!out.open(Common::Path("/workspace/Maniac-Online/build/scene-audit/reference.json"))) error("Cannot write scene audit report");
 out.write(report.c_str(),report.size());out.close();
 warning("SCUMMVERSE_SCENE_REFERENCE_PASS enabled=%d",ConfMan.getBool("scummverse_roaming"));quitGame();
