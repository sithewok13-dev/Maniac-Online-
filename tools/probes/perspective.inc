	if(!_scummverseRoaming) { warning("SCUMMVERSE_PERSPECTIVE_PASS enabled=0");quitGame();return; }
	// Fresh boot must advance without clicking the original kid picker.
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0;_talkDelay=0;runAllScripts();scummverseUpdateRoaming(4);walkActors();_sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=3;_scummverseLastEgo=3;_scummverseRosterPending=false;
	if(!_scummverseRoamingReady || !scummverseTravel(1) || !_scummVars[764]) error("Expanded cast failed ready=%d v763=%d v764=%d room=%d reason=%s",_scummverseRoamingReady,_scummVars[763],_scummVars[764],_currentRoom,_scummverseWorldNotice.c_str());

 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 const int savedRoom=_currentRoom;
 for(int id : {1,2,3,4,5,6,7,8,9,10,11,13,14,17,18,20,21,22,23,24}) {
  Actor *a=derefActor(id,"perspective actor");
  for(int facing : {0,90,180,270}) {
   a->setFacing(facing);_costumeLoader->costumeDecodeData(a,a->_standFrame,(uint)-1);
   int heights[2]={};
   for(int pass=0;pass<2;++pass) {
    _currentRoom=pass ? 72 : 54;
    VirtScreen canvas={};canvas.create(320,128,Graphics::PixelFormat::createFormatCLUT8());
    memset(canvas.getPixels(0,0),255,canvas.pitch*canvas.h);
    ClassicCostumeRenderer renderer(this);a->prepareDrawActorCostume(&renderer);
    renderer._actorX=160;renderer._actorY=100;renderer._zbuf=0;
    memset(gfxUsageBits,0,sizeof(gfxUsageBits));
    renderer.drawCostume(canvas,40,a,false);
    int top=128,bottom=-1,count=0;
    for(int y=0;y<128;++y) for(int x=0;x<320;++x)
     if(*(byte *)canvas.getBasePtr(x,y)!=255) {top=MIN(top,y);bottom=MAX(bottom,y);++count;}
    if(pass && id!=VAR(VAR_EGO)) {
     int savedTop=a->_top,savedBottom=a->_bottom;
     a->_top=renderer._drawTop;a->_bottom=renderer._drawBottom;
     bool selected=false;
     for(int x=0;x<320;++x) {
      if(!testGfxUsageBit(x/8,id)) continue;
      if(getActorFromPos(x,(a->_top+a->_bottom-1)/2)==id) selected=true;
      if(getActorFromPos(x,a->_top-1)==id || getActorFromPos(x,a->_bottom)==id)
       error("Distant hit area extends beyond rendered actor %d",id);
     }
     if(!selected) error("Distant actor cannot be selected %d",id);
     a->_top=savedTop;a->_bottom=savedBottom;
    }
    heights[pass]=bottom-top+1;
    if(count<4 || bottom>104) error("Missing or unanchored actor %d facing %d",id,facing);
    canvas.free();
   }
   if(heights[1]>=heights[0]/2 || heights[1]>(heights[0]*5+22)/23+2) error("Distant actor still oversized %d %d/%d",id,heights[0],heights[1]);
  }
 }
 for(int room : {72,87}) {_currentRoom=room;if(!scummverseDistantScene()) error("Missing exterior policy");}
 for(int room : {64,97}) {_currentRoom=room;if(scummverseDistantScene()) error("Former temple room kept exterior policy");}
 for(int room : {1,54,58,73,88}) {_currentRoom=room;if(scummverseDistantScene()) error("Unrelated room scaled");}
 _currentRoom=72;_scummversePortrait=true;if(scummverseDistantScene()) error("Portrait inherits scene scale");
 _scummversePortrait=false;_currentRoom=savedRoom;
 warning("SCUMMVERSE_PERSPECTIVE_PASS enabled=1");quitGame();
