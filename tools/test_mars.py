#!/usr/bin/env python3
"""Compare the Mars interior graph with independently executed original scenes.
Private English DOS V1 data required. The fixture opens original doors/tunnels;
this tests an exploration state, not the original puzzle progression.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from test_exploration import ROOT,run_probe
from test_ai_encounters import PRELUDE
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('data',type=Path)
p.add_argument('--build',choices=('null','asan'),default='null')
a=p.parse_args()
subprocess.run([sys.executable,str(ROOT/'tools/test_mars_reference.py'),str(a.data.resolve().parent/'zak-dos'),'--build',a.build],check=True)
scenes={s['logical_room']:s for s in json.loads((ROOT/'build/mars-reference.json').read_text())['scenes']}
rooms={32:82,182:83,194:93,189:110,190:111,191:112,195:113,192:124,193:125,34:126,185:79}
rooms.update({n:n-82 for n in range(196,206)})
# Source object handlers: fixed exits and explicit arrival overrides.
routes=[(182,534,185,444,-1,-1),(182,538,32,507,4,52),(32,507,182,538,24,50)]
for n,door in ((189,508),(190,509),(191,510)):
 routes.extend([(32,door,n,515,65,5),(n,515,32,door,-1,-1),(n,516,32,door,-1,-1),(n,517,{189:198,190:197,191:196}[n],563,-1,-1)])
routes.extend([(194,555,200,565,-1,-1),(195,543,196,566,-1,-1),(192,297,197,568,-1,-1),(193,300,202,564,-1,-1),(193,302,199,565,-1,-1),(193,304,204,564,-1,-1),(34,542,205,564,-1,-1)])
# Original maze entry handlers independently determine the six exit pairs.
for n in range(196,206):
 for o in scenes[n]['objects']:
  if 563<=o['id']<=568 and o['state']&8 and not o['state']&2:
   arrival,target=scenes[n]['transition_pairs'][o['id']-563]
   assert target in rooms
   routes.append((n,o['id'],target,arrival,-1,-1))
seen={182}
while True:
 more=seen|{t for f,_,t,*_ in routes if f in seen}
 if more==seen:break
 seen=more
assert set(rooms)<=seen,'Interior graph has unreachable scenes'
code=[]
for n,room in rooms.items():
 if n==185:continue
 s=scenes[n]
 code.append(f'if(!scummverseTravel({room-50})) error("Mars scene {n} mount failed");')
 code.append(f'if(VAR(VAR_CAMERA_MIN_X)!={s["camera"][0]} || VAR(VAR_CAMERA_MAX_X)!={s["camera"][1]}) error("Mars {n} camera mismatch");')
 for i,o in enumerate(s['objects']):
  code.append(f'{{int i=getObjectIndex({732+i});if(i<0 || _objs[i].x_pos!={o["x"]} || _objs[i].y_pos!={o["y"]} || _objs[i].walk_x!={o["walk_x"]} || _objs[i].walk_y!={o["walk_y"]} || getState({732+i})!={o["state"]}) error("Mars {n} object {o["id"]} mismatch");}}')
 for i,flag in enumerate(s['box_flags']):code.append(f'if(getBoxFlags({i})!={flag}) error("Mars {n} box {i} mismatch");')
 code.append(f'capture({n});')
 code.append('{stopTalk();VAR(VAR_HAVE_MSG)=0;scummLoop(0);Common::String file;_saveLoadDescription="Mars logical scene";if(!saveState(14,false,file)||!loadState(14,false)) error("Mars save/load failed");}')
 code.append(f'if(_currentRoom!={room} || VAR(VAR_CAMERA_MIN_X)!={s["camera"][0]}) error("Mars save identity lost");')
for origin,obj,target,arrival,x,y in routes:
 idx=next(i for i,o in enumerate(scenes[origin]['objects']) if o['id']==obj)
 code.append(f'if(!scummverseTravel({rooms[origin]-50})) error("Mars route origin failed");\nrunObjectScript({732+idx},13,false,false,nullptr);if(_currentRoom!={rooms[target]}) error("Mars {origin} exit {obj} failed");')
 if x>=0:
  code.append(f'{{Actor *a=derefActor(VAR(VAR_EGO),"Mars arrival");auto expected=a->adjustXYToBeInBox({x},{y});if(a->getRealPos().x!=expected.x || a->getRealPos().y!=expected.y) error("Mars {origin} arrival override lost");}}')
probe=(ROOT/'tools/probes/mars.inc').read_text().replace('@SCENE_CHECKS@','\n'.join(code))
run_probe(a.data.resolve(),probe,'scummverse_roaming','SCUMMVERSE_MARS_PASS','mars',PRELUDE,a.build)
for n in rooms:
 if n!=185:assert (ROOT/f'build/mars-reference-{n}.ppm').read_bytes()==(ROOT/f'build/mars-sandbox-{n}.ppm').read_bytes(),f'Mars {n} visible background differs'
print(f'PASS: {len(rooms)-1} Mars interior scenes, source pixels, saves, and {len(routes)} routes')
