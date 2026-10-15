#!/usr/bin/env python3
"""Compare all Mexico temple variants and door routes with original Zak execution.
Requires private English DOS V1 data. Does not exercise original puzzle solving.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data',type=Path)
p.add_argument('--legacy-save',type=Path,help='Private room-88 save captured from patch 0037')
p.add_argument('--build',choices=('null','asan'),default='null')
a=p.parse_args()
subprocess.run([sys.executable,str(ROOT/'tools/test_temple_reference.py'),str(a.data.resolve().parent/'zak-dos'),'--build',a.build],check=True)
scenes=json.loads((ROOT/'build/temple-reference.json').read_text())['scenes']
def sandbox(n):
 return {39:87,130:89,156:88}.get(n,n-58 if 157<=n<=167 else 0)
checks=[]
routes=[]
exit_pairs={741:2,742:3,743:4,744:0,745:1,746:1,747:5}
for scene in scenes:
 room=sandbox(scene['logical_room'])
 checks.append(f'if(!scummverseTravel({room-50})) error("Temple {room} import failed");')
 checks.append(f'if(VAR(VAR_CAMERA_MIN_X)!=160 || VAR(VAR_CAMERA_MAX_X)!={scene["camera"][1]}) error("Temple camera limits");')
 for i,o in enumerate(scene['objects']):
  checks.append(f'{{int n=getObjectIndex({732+i});if(n<0 || _objs[n].x_pos!={o["x"]} || _objs[n].y_pos!={o["y"]} || _objs[n].walk_x!={o["walk_x"]} || _objs[n].walk_y!={o["walk_y"]} || getState({732+i})!={o["state"]}) error("Temple {room} original object {o["id"]} mismatch");}}')
  if o['id'] in exit_pairs and o['state']&8 and not o['state']&2:
   arrival,target=scene['transition_pairs'][exit_pairs[o['id']]]
   routes.append(f'if(!scummverseTravel({room-50})) error("Route origin failed");\nrunObjectScript({732+i},13,false,false,nullptr);if(_currentRoom!={sandbox(target)}) error("Temple {room} door {o["id"]} failed");')
 for i,flag in enumerate(scene['box_flags']):
  checks.append(f'if(getBoxFlags({i})!={flag}) error("Temple {room} walkbox {i} mismatch");')
 checks.append(f'capture({scene["logical_room"]});')
 checks.append('{stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);Common::String file;_saveLoadDescription="Temple variant";if(!saveState(12,false,file) || !loadState(12,false)) error("Temple save/load");}')
 checks.append(f'if(_currentRoom!={room} || VAR(VAR_CAMERA_MAX_X)!={scene["camera"][1]}) error("Temple save identity lost");')
legacy=''
if a.legacy_save:
 path=json.dumps(str(a.legacy_save.resolve()))
 legacy=f'''{{
 Common::File in;if(!in.open(Common::FSNode(Common::Path({path})))) error("Cannot read legacy fixture");
 Common::OutSaveFile *out=_system->getSavefileManager()->openForSaving(makeSavegameName(13,false));
 if(!out) error("Cannot stage legacy save");byte buf[4096];while(!in.eos()) {{uint n=in.read(buf,sizeof(buf));out->write(buf,n);}}out->finalize();delete out;
 if(!loadState(13,false) || _currentRoom!=88 || _scummVars[527]!=1 || getObjectIndex(745)<0 || _numRooms!=ScummverseContent::kRoomCount) error("Previous-build temple migration failed");
 for(int id : {{3,8}}) {{Actor *a=derefActor(id,"migrated temple actor");if(a->_room!=88 || a->getRealPos().x<100) error("Legacy visitor lost");}}
 scummverseRestoreTemple();if(derefActor(3,"migration repeat")->getRealPos().x<100) error("Migration not idempotent");
 }}'''
probe=(ROOT/'tools/probes/temple.inc').read_text().replace('@LEGACY_CHECKS@',legacy).replace('@SCENE_CHECKS@','\n'.join(checks)).replace('@ROUTE_CHECKS@','\n'.join(routes))
run_probe(a.data.resolve(),probe,'scummverse_roaming','SCUMMVERSE_TEMPLE_PASS','temple',PRELUDE+'\nnamespace ProbeCatalog {\n#include "scumm/scummverse_places.inc"\n}\n',a.build)
for scene in scenes:
 n=scene['logical_room']
 assert (ROOT/f'build/temple-reference-{n}.ppm').read_bytes()==(ROOT/f'build/temple-sandbox-{n}.ppm').read_bytes(),f'Temple {n} background differs'
print(f'PASS: twelve distinct temple scenes, original background pixels, save identities and {len(routes)} doorway routes')
