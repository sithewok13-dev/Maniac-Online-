	if (!_scummverseRoaming) { warning("SCUMMVERSE_LEGACY_TEMPLE_PASS enabled=0"); quitGame(); return; }
	_scummVars[47]=3; _scummVars[48]=2; _scummVars[49]=5; _scummVars[110]=1; _scummVars[111]=3;
	for(int n=0;n<100 && !_scummverseRoamingReady;++n) {
		for(uint i=0;i<NUM_SCRIPT_SLOT;++i) if(vm.slot[i].status==ssPaused) {vm.slot[i].delay=0;vm.slot[i].status=ssRunning;}
		VAR(VAR_HAVE_MSG)=0; _talkDelay=0; runAllScripts(); scummverseUpdateRoaming(4); walkActors(); _sound->processSound();
	}
	for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
	_currentScript=0xFF; _userPut=1; VAR(VAR_EGO)=3; _scummverseLastEgo=3;




 if(_numRooms!=99) error("Capture requires the patch-0037 engine and build");
 if(!scummverseTravel(38)) error("Legacy corridor unavailable");
 derefActor(8,"legacy companion")->putActor(30,60,88);
 stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);
 Common::String file;_saveLoadDescription="Pre-0038 temple";
 if(!saveState(12,false,file)) error("Cannot capture legacy save");
 Common::InSaveFile *in=_system->getSavefileManager()->openForLoading(file);
 if(!in) error("Cannot read legacy save");
 Common::DumpFile out;if(!out.open(Common::Path("/workspace/Maniac-Online/build/legacy-temple.s12"))) error("Cannot export legacy fixture");
 byte buf[4096];while(!in->eos()) {uint n=in->read(buf,sizeof(buf));out.write(buf,n);}delete in;out.close();
 warning("SCUMMVERSE_LEGACY_TEMPLE_PASS enabled=1");quitGame();
