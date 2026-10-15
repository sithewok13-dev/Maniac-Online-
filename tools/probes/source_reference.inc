 // Test-only source scene fixture. Original startup has run to its first yield;
 // stop its cinematic before arranging the audited plane seat state directly.
 if(_game.id!=GID_ZAK || _game.version!=1 || _scummverseRoaming)
  error("Reference launcher did not isolate original Zak");
 for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
 _currentScript=0xFF;_userPut=1;VAR(VAR_EGO)=1;
 Actor *a=derefActor(1,"source seat reference");
 a->setActorCostume(1);a->setPalette(1,13);
 a->putActor(63,52,11);startScene(11,a,0);
 for(uint i=0;i<NUM_SCRIPT_SLOT;++i) vm.slot[i].status=ssDead;
 _currentScript=0xFF;VAR(VAR_CURRENT_LIGHTS)=11;
 setBoxFlags(4,160);a->putActor(63,52,11);a->setElevation(-4);
 a->animateActor(249);a->startAnimActor(11);a->startAnimActor(13);
 putState(263,getState(263)&~8);
 setCameraAt(a->getPos().x,a->getPos().y);setCameraFollows(a);
 stopTalk();VAR(VAR_HAVE_MSG)=0;_fullRedraw=true;
 for(int i=0;i<3;++i) scummLoop(0);
 if(_currentRoom!=11 || getNumBoxes()!=7 || !a->_visible ||
    a->_room!=11 || a->_costume!=1 || a->getRealPos().x!=63 ||
    a->getRealPos().y!=52 || a->_walkbox!=4 || a->getFacing()!=90 ||
    a->getElevation()!=-4 || a->_bottom<=a->_top)
  error("Original plane reference failed scene/actor invariants");
 warning("Source plane reference: box=%d, actor bounds=%d..%d",a->_walkbox,a->_top,a->_bottom);
 warning("SCUMMVERSE_SOURCE_REFERENCE_PASS enabled=%d",ConfMan.getBool("scummverse_roaming"));
 quitGame();
