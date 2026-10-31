#!/usr/bin/env python3
"""Generate engine/common/scummverse_world_maps.inc: the visitable rooms of
each other-world game, the doors between them, and named entrances to the
areas a game reaches only through its story.

The games the original engine plays itself (HOME: the mansion) come
after them, their rooms and doors read from that engine's own tables
(engines/scumm/scummverse_tour.inc's rooms and scummverse_roaming.inc's
passages: room and object numbers only).

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
# Then the original engine's own games (catalog worldHome), in order.
HOME = ['maniac', 'zak']
ALL = GAMES + HOME
KINDS = {'scene': 0, 'map': 1, 'floor plan': 2}
# Floor plans: overhead maps a small figure walks around (unlike map rooms,
# whose hotspots travel at once). The exporter reveals all of their sections.
FLOOR_PLANS = {('indy3', 20), ('indy3', 28), ('indy3', 32)}  # Castle Brunwald's three floors
# Overhead plans whose walk paths are thin lines (Fate of Atlantis's four
# ring plans, 85-88, a tiny figure walked between their doorways): maps here,
# their doorways travelled to at a tap.
MAP_ROOMS = {('atlantis', 85), ('atlantis', 86), ('atlantis', 87), ('atlantis', 88)}
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
# From 0297 close-ups that a place's answer takes the one played to (0283's
# answers that go elsewhere) and that are walked in and left as places:
# kept as scenes, reached (for the story areas below) from that place, with
# their own doors as their scripts take them with the story as that answer
# leaves it, the analysis's other doors out of and into them left out (the
# ways in are story routes, cut-scenes or actions on things, not doors).
# Monkey Island's dock (room 83): the idol picked up under the harbour (42)
# and the ladder climbed; its two ends lead back to the harbour street (33)
# while its last part is not begun (bit 453 clear).
STORY_PLACES = {('monkey', 83): (42, {862: 33, 863: 33})}
# From 0298 people's objects whose verbs play their talk where they stand,
# not doors: the analysis's link out of them is the place their game's
# script plays the talk in, and the one played is back where they were after
# it. Monkey Island's Sword Master (room 61, 720: global script 113 takes
# the one played to room 44 for her talk and fight and back to 61; the new
# engine plays them where she stands, kWorldDuels; room 44 a story area of
# its own now, AREA_NAMES).
TALKS = {('monkey', 61, 720)}
# Travel the player starts with a tap: doors, exits, map hotspots, vehicles
# and actions on objects (story, cutscene and debug transitions are left out).
TRAVEL = {'door', 'exit', 'walk', 'map', 'action', 'car', 'chron-o-john'}
VERSIONS = {'monkey': 4, 'monkey2': 5, 'loom': 3, 'indy3': 3, 'atlantis': 5, 'tentacle': 6, 'samnmax': 6, 'ft': 7, 'dig': 7, 'comi': 8,
            'maniac': 1, 'zak': 1}
SCUMM = ROOT/'engine/engines/scumm'
WORLDS = ROOT/'build/worlds'


def shown(game, room):
    """Whether the export has a scene of a room (build/worlds; an emptied
    scene, a room whose export failed, is none). Without a cache, any."""
    scene = WORLDS/f'{game}-{room}.svw'
    return not WORLDS.exists() or (scene.exists() and scene.stat().st_size > 0)


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


def fixed_doors(game, travel):
    """Doors the game decides only at run time (a random jungle, a corridor of
    pseudo rooms, a shuffled ring), fixed for exploration: the checked tables
    in build/foreign/dynamic/<game>-final.json (each door's target and arrival
    from the game's own scripts in one of its states, or chosen to pair exits
    by side where the original rolls a room; see the progress notes, 0190).
    They replace the analysis's links for those objects; listed removals
    drop links that are not doors. A door into a room with no exported scene
    yet (build/worlds) is left out."""
    path = ROOT/'build/foreign/dynamic'/f'{game}-final.json'
    if not path.exists():
        return travel
    table = json.loads(path.read_text())
    drop = {(d['room'], d['object']) for d in table['doors']} | {(r['room'], r['object']) for r in table.get('remove', [])}
    # (A template room exported as one of its instances has that instance's
    # doors only.)
    replaced = set(table.get('replaceRooms', []))
    fixed = [{'room': d['room'], 'object': d['object'], 'target': d['target'], 'arrivalObject': d['arrival'],
              'needsObjectState': bool(d.get('switched')), 'kind': 'door'}
             for d in table['doors'] if shown(game, d['target']) and shown(game, d['room'])]
    return fixed + [l for l in travel if (int(l['room']), int(l['object'])) not in drop and int(l['room']) not in replaced]


def load_home(game):
    """The mansion's rooms (the tour's stops) and doors (its passages, but the
    rides out of it), as the original engine has them."""
    tour = (SCUMM/'scummverse_tour.inc').read_text()
    body = tour[tour.index('kTourManiacRooms[] = {'):]
    stops = [int(r) for r in re.findall(r'\{\s*(\d+),\s*-?\d+,\s*-?\d+,\s*"', body[:body.index('};')])]
    roaming = (SCUMM/'scummverse_roaming.inc').read_text()
    body = roaming[roaming.index('mansionPassages[] = {'):]
    passages = re.findall(r'\{\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(?:true|false),\s*-?\d+,\s*-?\d+,\s*-?\d+,\s*-?\d+,\s*(true|false)\s*\}',
                          body[:body.index('};')])
    if not stops or not passages:
        raise SystemExit('mansion tables not found; update the patterns in load_home()')
    passages = [tuple(map(int, p[:4])) for p in passages if p[4] == 'false']
    visit = set(stops) | {p[0] for p in passages} | {p[2] for p in passages}
    links, seen = [], set()
    for room, obj, target, arrival in passages:
        if obj <= 0 or room == target or (room, obj) in seen:
            continue
        seen.add((room, obj))
        links.append((room, obj, target, arrival, 0))
    return sorted((r, (0, r)) for r in visit), links


def scene_objects(path):
    """The object numbers an exported scene shows (an SVW5 file)."""
    import gzip
    import struct
    data = path.read_bytes()
    if data[:2] == b'\x1f\x8b':
        data = gzip.decompress(data)
    if data[:4] != b'SVW5':
        return None
    _room, width, height = struct.unpack_from('<HHH', data, 4)
    p = 12 + 768 + width * height + data[10] * 18
    count = struct.unpack_from('<H', data, p)[0]
    return {struct.unpack_from('<H', data, p + 2 + i * 16)[0] for i in range(count)}


def load_zak():
    """Zak's places and doors, from the original engine's Zak tables
    (scummverse_places.inc), which number Zak's rooms and objects as that
    engine imports them into the mansion, back in Zak's own numbers: its
    rooms (or the logical rooms 128+ its scripts make of one resource), and
    each room's objects in their order there (private analysis of the
    user's copy, build/foreign/links/zak-objects.json, from zak_objects.py).
    The rides (the plane, the van's cockpit) are left out, and, where Zak's
    places are exported (build/worlds), a door whose object its place does
    not show (cut out of its window) or an arrival at one."""
    path = ROOT/'build/foreign/links/zak-objects.json'
    if not path.exists():
        return [], []
    objects = {int(k): v for k, v in json.loads(path.read_text()).items()}
    text = (SCUMM/'scummverse_places.inc').read_text()
    def table(name):
        body = text[text.index(name + '[] = {'):]
        return body[:body.index('\n};')]
    places = re.findall(r'\{\s*(\d+),\s*"[0-9a-f]{32}",\s*"([^"]*)"', table('zakPlaces'))
    files = [int(f) for f, _name in places]
    retired = {56 + i for i, (_f, name) in enumerate(places) if 'retired' in name}
    logical = {int(r): int(p) for r, p in re.findall(r'\{\s*(\d+),\s*(\d+),\s*"', table('zakLogicalScenes'))}
    setups = {int(r): int(l) for r, l in re.findall(r'^\s*\{(\d+),(\d+),\d+,\d+,\d+,\d+,\{', table('zakSceneSetups'), re.M)}
    views = {int(r): int(l) for r, l in re.findall(r'\{(\d+),(\d+),\d+,\d+,\d+,\d+\}', table('zakSceneViews'))}
    links = re.findall(r'\{\s*(\d+),\s*(\d+),\s*(\d+)(?:,\s*(\d+))?(?:,\s*-?\d+,\s*-?\d+)?\s*\}', table('zakLinks'))
    rides = {56, 81, 221}  # (the plane, the van's cockpit, the van in flight)
    # The import's own rooms: 53 the San Francisco airport (resource 8, its
    # logical 145), 54 the apartment (1), 55 the street (3); 56.. a slot each.
    first = {54: 650, 53: 683, 55: 712}
    def resource(room):
        if room in (53, 54, 55):
            return {53: 8, 54: 1, 55: 3}[room]
        if room in logical:
            return resource(logical[room])
        return files[room - 56] if 56 <= room < 56 + len(files) else None
    def native(room):
        if room in rides or resource(room) is None:
            return None
        if room in logical or room >= 128:
            return room
        if room == 53:
            return 145
        return setups.get(room) or views.get(room) or resource(room)
    def native_object(room, obj):
        file = resource(room)
        index = obj - first.get(room if room < 56 else 0, 732)
        table_ = objects.get(file, [])
        return table_[index] if 0 <= index < len(table_) else None
    # Every place of the import's (but the rides and the retired), whether or
    # not a door leads there (the airports: by plane).
    exported = {}
    def shows(room, obj):
        if room not in exported:
            path = WORLDS/f'zak-{room}.svw'
            exported[room] = scene_objects(path) if path.exists() else None
        return exported[room] is None or obj in exported[room]
    visit, out, seen = {}, [], set()
    for room in [53, 54, 55] + list(range(56, 56 + len(files))) + list(logical):
        if room not in retired and native(room) is not None:
            visit[native(room)] = resource(room)
    for room, obj, target, arrival in links:
        room, obj, target, arrival = int(room), int(obj), int(target), int(arrival or 0)
        a, b = native(room), native(target)
        if a is None or b is None or a == b:
            continue
        o = native_object(room, obj)
        if not o or (a, o) in seen or not shows(a, o):
            continue
        seen.add((a, o))
        visit[a] = resource(room); visit[b] = resource(target)
        out.append((a, o, b, arrival if shows(b, arrival) else 0, 0))
    return sorted((r, (0, res)) for r, res in visit.items()), out


def load(game):
    if game == 'zak':
        return load_zak()
    if game in HOME:
        return load_home(game)
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
        if (game, room) in MAP_ROOMS:
            kind = 'map'
        if (game, room) in STORY_PLACES:
            kind = 'scene'
        if kinds.get(room) not in KINDS:
            kinds[room] = kind
    travel = []
    for l in data.get('links', []):
        kind = l.get('kind') or l.get('class') or 'door'
        if kind not in TRAVEL or int(l.get('object') or 0) <= 0 or l.get('room') is None or l.get('target') is None:
            continue
        travel.append(dict(l, room=physical.get(int(l['room']), int(l['room'])), target=physical.get(int(l['target']), int(l['target']))))
    travel = [l for l in travel if (game, int(l['room']), int(l['object'])) not in TALKS]  # (from 0298)
    resolved, replaced = template_doors(game, rooms, travel)
    travel = resolved + [l for l in travel if (int(l['room']), int(l['object'])) not in replaced]
    travel = fixed_doors(game, travel)
    # Every scene or map joined to another by such travel, whichever
    # island or period it belongs to, plus everything reachable from the start.
    joined = set(physical.get(int(r), int(r)) for r in data.get('reachable', []))
    for l in travel:
        joined |= {int(l['room']), int(l['target'])}
    # (From 0297 a story place's own doors only: STORY_PLACES.)
    story = {room: doors for (g, room), (_from, doors) in STORY_PLACES.items() if g == game}
    travel = [l for l in travel if int(l['room']) not in story and int(l['target']) not in story] + \
        [{'room': room, 'object': obj, 'target': target, 'kind': 'door'} for room, doors in sorted(story.items()) for obj, target in sorted(doors.items())]
    # (Only rooms the export has a scene of (Loom's 65 and Full Throttle's 13
    # come out blank), and doors their scenes show (those with no rectangle
    # are not exported), as for Zak's below.)
    visit = {}
    for room in joined:
        info = rooms.get(str(room)) or {}
        kind = kinds.get(room)
        resource = int(info.get('physicalRoom') or room) if room >= 128 else room
        if kind in KINDS and 0 < room < 1000 and exportable(game, info) and shown(game, room):
            visit[room] = (KINDS[kind], resource)
    exported = {}
    def shows(room, obj):
        if room not in exported:
            path = WORLDS/f'{game}-{room}.svw'
            exported[room] = scene_objects(path) if path.exists() and path.stat().st_size > 0 else None
        return exported[room] is None or obj in exported[room]
    links, seen = [], set()
    for link in travel:
        room, obj, target = int(link['room']), int(link['object']), int(link['target'])
        if room not in visit or target not in visit or room == target or (room, obj) in seen or not shows(room, obj):
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
    ('maniac', 52): 'Gate approach',
    ('zak', 20): 'Egypt: the Sphinx and pyramids', ('zak', 39): 'Mexico: the temple', ('zak', 136): 'Peru: inside the giant carving',
    ('zak', 183): 'Mars: the pyramid', ('zak', 12): 'Seattle: the forest', ('zak', 17): 'Nepal: Kathmandu', ('zak', 143): 'Miami airport',
    ('monkey', 70): 'Catacombs and the ghost ship', ('monkey', 21): 'Monkey Island jungle', ('monkey', 1): 'Monkey Island beach',
    ('monkey', 30): 'Melee Island shop', ('monkey', 31): 'Melee Island jail',
    ('monkey', 32): 'Melee Island back alley', ('monkey', 42): 'Under the harbor',
    ('monkey', 60): 'Gym', ('monkey', 80): 'Fort', ('monkey', 44): "Sword Master's clearing",
    ('monkey2', 73): "LeChuck's fortress", ('monkey2', 24): "Captain Dread's deck",
    ('monkey2', 40): 'Basement', ('monkey2', 66): 'Galleon', ('monkey2', 75): "LeChuck's dungeon",
    ('monkey2', 90): 'Storage room', ('monkey2', 96): 'Jungle', ('monkey2', 61): 'Up the great tree', ('monkey2', 82): 'Sea map',
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
    seen |= {room for (g, room) in STORY_PLACES if g == game}  # (reached by their place's answer)
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
    for index, game in enumerate(ALL):
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
