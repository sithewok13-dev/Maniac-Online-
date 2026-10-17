#!/usr/bin/env python3
"""Generate engine/common/scummverse_world_maps.inc: the visitable rooms of
each other-world game, the doors between them, and named entrances to the
areas a game reaches only through its story.

Input is private analysis of the user's own copies (build/foreign/links/
<game>.json: rooms with a kind, door links found in object scripts, and the
reachable set; <game>-vars.json: template instances' door variables). The output holds only room and object numbers for the
audited editions and the newly written area names below; no game data. Run
after updating the analysis, then rebuild.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Same order as kWorldGames in engine/common/scummverse_world_catalog.h.
GAMES = ['monkey', 'monkey2', 'loom', 'indy3', 'atlantis', 'tentacle', 'samnmax', 'ft', 'dig', 'comi']
KINDS = {'scene': 0, 'map': 1, 'floor plan': 2}
# Floor plans: overhead maps a small figure walks around (unlike map rooms,
# whose hotspots travel at once). The exporter reveals all of their sections.
FLOOR_PLANS = {('indy3', 20), ('indy3', 28), ('indy3', 32)}  # Castle Brunwald's three floors
# Doors of v3 template rooms (instanced as pseudo rooms 128+) call
# loadRoomWithEgo(arrival object, room) with variables each instance's entry
# script sets. Per game and template resource: door object -> (arrival,
# room), each a variable name or a number, read from the door scripts of the
# audited edition. Values per instance come from the private analysis
# (build/foreign/links/<game>-vars.json: the variables after the entry script).
# These replace the analysis's links for those objects; a room of 0 means the
# instance has no such door. Windows ('paired') count only where the room
# outside has a window leading back in (the template has two, one is real).
TEMPLATE_DOORS = {
    'indy3': {
        17: {224: ('V99', 'V100'), 225: ('V101', 'V102')},                                    # Venice library stacks
        18: {246: (225, 'V99'), 247: (225, 'V100'), 248: (224, 'V101'), 249: (224, 'V102')},  # library reading rooms
        21: {311: ('V101', 'V102'), 312: ('V99', 'V100'), 313: ('V99', 'V100')},              # castle corridors
        23: {323: ('V100', 'V103'), 326: ('V99', 'V102'), 328: ('V101', 'V104'),              # castle rooms (type A)
             334: ('V105', 13, 'paired'), 336: ('V105', 13, 'paired')},
        24: {343: ('V103', 'V107'), 346: ('V102', 'V106'), 347: ('V100', 'V104'), 354: ('V101', 'V105')},  # type B
        33: {500: (311, 'V99'), 501: ('V100', 13, 'paired')},                                 # castle tower rooms
    },
}
# Travel the player starts with a tap: doors, exits, map hotspots, vehicles
# and actions on objects (story, cutscene and debug transitions are left out).
TRAVEL = {'door', 'exit', 'walk', 'map', 'action', 'car', 'chron-o-john'}
VERSIONS = {'monkey': 4, 'monkey2': 5, 'loom': 3, 'indy3': 3, 'atlantis': 5, 'tentacle': 6, 'samnmax': 6, 'ft': 7, 'dig': 7, 'comi': 8}


def exportable(game, info):
    """The exporter takes rooms at least a screen wide and at most a screen tall."""
    width, height = int((info or {}).get('width') or 0), int((info or {}).get('height') or 0)
    screen = (640, 480) if VERSIONS[game] == 8 else (320, 200)
    return not width or (width >= screen[0] and height <= screen[1])


def template_doors(game, rooms, travel):
    """The doors of each template instance, resolved with its variables, and
    the (room, object) pairs they replace."""
    doors = TEMPLATE_DOORS.get(game)
    path = ROOT/'build/foreign/links'/f'{game}-vars.json'
    if not doors or not path.exists():
        return [], set()
    values = {int(k): v for k, v in json.loads(path.read_text()).items()}
    value = lambda room, x: values[room].get(x, 0) if isinstance(x, str) else x
    inward = {(int(l['target']), int(l.get('arrivalObject') or 0)) for l in travel}
    out, replaced = [], set()
    for room, info in sorted(values.items()):
        for obj, rule in doors.get(int(info['resource']), {}).items():
            replaced.add((room, obj))
            target, arrival = int(value(room, rule[1])), int(value(room, rule[0]))
            if 'paired' in rule[2:] and (room, obj) not in inward:
                continue
            if 0 < target < 256 and str(target) in rooms and target != room:
                out.append({'room': room, 'object': obj, 'target': target, 'arrivalObject': arrival, 'kind': 'door'})
    return out, replaced


def load(game):
    path = ROOT/'build/foreign/links'/f'{game}.json'
    if not path.exists():
        return [], []
    data = json.loads(path.read_text())
    rooms = data.get('rooms', {})
    if isinstance(rooms, list):  # [{"room": N, "kind": ...}, ...]
        rooms = {str(r.get('room')): r for r in rooms}
    # Locations that reuse one physical room fold into it, except v3/v4
    # pseudo rooms (128+): the exporter furnishes each such instance of a
    # template room with the room's entry script, so they stay places.
    instances = VERSIONS[game] <= 4
    physical = {int(k): int(k) if instances and int(k) >= 128 else int((v or {}).get('physicalRoom') or k) for k, v in rooms.items()}
    kinds = {}
    for k, v in rooms.items():
        room, kind = physical[int(k)], (v or {}).get('kind', 'scene')
        if (game, room) in FLOOR_PLANS:
            kind = 'floor plan'
        if kinds.get(room) not in KINDS:
            kinds[room] = kind
    travel = []
    for l in data.get('links', []):
        kind = l.get('kind') or l.get('class') or 'door'
        if kind not in TRAVEL or int(l.get('object') or 0) <= 0 or l.get('room') is None or l.get('target') is None:
            continue
        travel.append(dict(l, room=physical.get(int(l['room']), int(l['room'])), target=physical.get(int(l['target']), int(l['target']))))
    resolved, replaced = template_doors(game, rooms, travel)
    travel = resolved + [l for l in travel if (int(l['room']), int(l['object'])) not in replaced]
    # Every scene or map joined to another by such travel, whichever
    # island or period it belongs to, plus everything reachable from the start.
    joined = set(physical.get(int(r), int(r)) for r in data.get('reachable', []))
    for l in travel:
        joined |= {int(l['room']), int(l['target'])}
    visit = {}
    for room in joined:
        info = rooms.get(str(room)) or {}
        kind = kinds.get(room)
        resource = int(info.get('physicalRoom') or room) if room >= 128 else room
        if kind in KINDS and 0 < room < 1000 and exportable(game, info):
            visit[room] = (KINDS[kind], resource)
    links, seen = [], set()
    for link in travel:
        room, obj, target = int(link['room']), int(link['object']), int(link['target'])
        if room not in visit or target not in visit or room == target or (room, obj) in seen:
            continue
        seen.add((room, obj))
        arrival = int(link.get('arrivalObject') or 0)
        switched = 1 if link.get('needsObjectState') else 0
        links.append((room, obj, target, arrival if 0 < arrival < 32768 else 0, switched))
    return sorted(visit.items()), links


# Areas the game reaches only through its story (voyages, cutscenes, rides):
# the scene menu offers one entrance per such area, named here (newly written
# descriptions, not game text). Every entrance must be named.
AREA_NAMES = {
    ('monkey', 70): 'Catacombs and the ghost ship', ('monkey', 21): 'Monkey Island jungle', ('monkey', 1): 'Monkey Island beach',
    ('monkey', 30): 'Melee Island shop', ('monkey', 31): 'Melee Island jail',
    ('monkey', 32): 'Melee Island back alley', ('monkey', 42): 'Under the harbor',
    ('monkey', 60): 'Gym', ('monkey', 80): 'Fort',
    ('monkey2', 73): "LeChuck's fortress", ('monkey2', 24): "Captain Dread's deck",
    ('monkey2', 40): 'Basement', ('monkey2', 66): 'Galleon', ('monkey2', 75): "LeChuck's dungeon",
    ('monkey2', 90): 'Storage room', ('monkey2', 96): 'Jungle',
    ('loom', 43): 'The castle', ('loom', 13): 'Waterspout', ('loom', 65): 'Cave',
    ('indy3', 12): 'Castle Brunwald', ('indy3', 81): 'Grail temple', ('indy3', 3): 'Lecture hall',
    ('indy3', 7): "Henry's house", ('indy3', 86): 'Grail chamber', ('indy3', 132): 'Castle Brunwald corridor',
    ('atlantis', 32): 'Desert by balloon', ('atlantis', 36): 'Atlantis', ('atlantis', 37): 'Pool',
    ('atlantis', 42): 'Submarine, surfaced', ('atlantis', 56): 'Labyrinth elevator',
    ('atlantis', 71): 'Machine room', ('atlantis', 82): 'Submarine, submerged', ('atlantis', 95): 'Balloon over the sea',
    ('samnmax', 22): 'Swan ride', ('samnmax', 38): 'Magnet room', ('samnmax', 49): 'Virtual reality',
    ('ft', 47): 'Highway vista and mine road', ('ft', 53): 'Vulture Rock', ('ft', 70): 'Cargo plane',
    ('ft', 107): 'Trailer bar', ('ft', 49): 'Cave ramp', ('ft', 56): 'Derby arena', ('ft', 174): 'Tunnel and finale',
    ('ft', 12): 'Road', ('ft', 25): "Todd's basement", ('ft', 45): 'Gorge', ('ft', 95): 'Minefield',
    ('dig', 46): 'Sarcophagus chamber', ('dig', 8): 'Asteroid', ('dig', 58): 'Tomb',
    ('comi', 39): 'Sea map and ship deck', ('comi', 9): 'Cannon', ('comi', 80): "Smugglers' cave",
    ('comi', 12): 'Buried treasure', ('comi', 31): 'Snake', ('comi', 81): 'Gondola',
}


def landmarks(game_index):
    """The catalog's named places of a game, in order (scummverse_world_catalog.h)."""
    text = (ROOT/'engine/common/scummverse_world_catalog.h').read_text()
    arrays = re.findall(r'static const WorldScene (kWorld\w+)\[\] = \{(.*?)\};', text, re.S)
    names = re.search(r'kWorldGames\[\] = \{(.*?)\n\};', text, re.S).group(1)
    order = re.findall(r'(kWorld\w+), ARRAYSIZE', names) or re.findall(r'\b(kWorld(?!Games)\w+)\b', names)
    body = dict(arrays)[order[game_index]]
    return [int(r) for r in re.findall(r'\{(\d+), "', body)]


def areas(game, rooms, links, named):
    """Entrances so every room is reachable: by doors from a named place or
    an entrance, or by walking between neighboring named places."""
    doors = defaultdict(set)
    for room, _obj, target, _arrival, _switched in links:
        doors[room].add(target)
    for a, b in zip(named, named[1:]):
        doors[a].add(b); doors[b].add(a)

    def reach(starts):
        seen, todo = set(starts), list(starts)
        while todo:
            for t in doors[todo.pop()] - seen:
                seen.add(t); todo.append(t)
        return seen
    seen, entrances = reach(named), []
    while True:
        left = [r for r, _kind in rooms if r not in seen]
        if not left:
            return entrances
        best = max(left, key=lambda r: (len(reach([r]) & set(left)), -r))
        if (game, best) not in AREA_NAMES:
            raise SystemExit(f'name the area entrance {game} room {best} in AREA_NAMES')
        entrances.append((best, AREA_NAMES[(game, best)]))
        seen |= reach([best])


def main():
    out = ['// Generated by tools/world_maps.py; one map per kWorldGames entry, in order.',
           '// Room and object numbers of the audited editions only.']
    entries = []
    for index, game in enumerate(GAMES):
        rooms, links = load(game)
        entrances = areas(game, rooms, links, landmarks(index)) if rooms else []
        name = 'kWorldMap_' + game
        if rooms:
            out.append(f'static const WorldRoom {name}Rooms[] = {{')
            for i in range(0, len(rooms), 10):
                out.append('\t' + ' '.join(f'{{{r}, {k}, {res}}},' for r, (k, res) in rooms[i:i+10]))
            out.append('};')
        if links:
            out.append(f'static const WorldLink {name}Links[] = {{')
            for i in range(0, len(links), 6):
                out.append('\t' + ' '.join(f'{{{r}, {o}, {t}, {a}, {w}}},' for r, o, t, a, w in links[i:i+6]))
            out.append('};')
        if entrances:
            out.append(f'static const WorldArea {name}Areas[] = {{')
            out += [f'\t{{{room}, "{label}"}},' for room, label in entrances]
            out.append('};')
        entries.append(f'{{{name + "Rooms" if rooms else "nullptr"}, {len(rooms)}, {name + "Links" if links else "nullptr"}, {len(links)}, '
                       f'{name + "Areas" if entrances else "nullptr"}, {len(entrances)}}}')
        print(f'{game}: {len(rooms)} rooms, {len(links)} doors, {len(entrances)} story areas')
    out.append('static const WorldMap kWorldMaps[] = {')
    out += ['\t' + e + ',' for e in entries]
    out.append('};')
    (ROOT/'engine/common/scummverse_world_maps.inc').write_text('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
