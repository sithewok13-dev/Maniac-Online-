#!/usr/bin/env python3
"""Generate engine/common/scummverse_world_cast.inc: every character of each
other-world game, placed in a room of that game.

Input is private research on the user's own copies (build/foreign/cast/
<game>.json: costume number, the character's name, newly written
personality and lines, talk color, and the rooms the character appears in),
plus the visitable rooms from build/foreign/links/<game>.json (see
tools/world_maps.py). Characters go to the first room of theirs that can be
visited (at most five per room); others join the named place with the fewest.
Sprites that cannot stand on their own (legs only, lying down, busts and so
on) are left out. Output: costume and room numbers, names, and the newly
written text; no game data.
"""
import json
import re
from pathlib import Path

from world_maps import ALL, load as load_map

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT/'engine/common/scummverse_world_catalog.h'
MAX_GUESTS = 5
# Notes the research marks on sprites that are not a standing figure.
UNUSABLE = re.compile(r'legs only|lying|upper[- ]body|\bbust\b|head-on-pillow|tiny sprite|broken line|2x4|'
                      r'riding pose|behind (the |his |her )?(counter|bar|cart|stand)|face in a window', re.I)
RANK = {'high': 0, 'medium': 1, 'low': 2}
# Costumes that export but draw only a few pixels in the sandbox.
SPECKS = {('dig', 153)}
# Characters drawn from another costume with their own animation set
# (engine catalog kWorldCostumeVariants); names, personalities and lines
# newly written. They replace research entries that rendered the same
# costume with its default animations.
EXTRA = {
    'monkey': [
        {'costume': 906, 'name': 'Sharptooth', 'rooms': [25], 'confidence': 'high', 'talkColor': 7,
         'personality': 'Sharptooth, one of the three cannibals of Monkey Island, in a grey shaggy mask full of pointed teeth; '
                        'fierce-looking, secretly a vegetarian, and fussy about the quality of the village fruit',
         'lines': ['Do not mind the teeth. Mostly decorative.', 'Have you tried the bananas this season? Superb.',
                   'We used to be scarier. Then we discovered salad.']},
        {'costume': 911, 'name': 'Red Skull', 'rooms': [25], 'confidence': 'high', 'talkColor': 12,
         'personality': 'Red Skull, one of the three cannibals of Monkey Island, in a red skull mask with a grin of square teeth; '
                        'theatrical, proud of his mask, and fond of dramatic pronouncements about the island',
         'lines': ['Behold! The mask of terror! It took me all week.', 'Monkey Island keeps its secrets. And its snacks.',
                   'Visitors come and go. Mostly go.']},
    ],
    'comi': [
        {'costume': 949, 'name': 'Murray (green)', 'rooms': [29], 'confidence': 'high', 'talkColor': 10,
         'personality': 'Murray, the disembodied talking skull, in the eerie green glow of the flooded ship\'s hold where he first '
                        'washed up; certain he is the most terrifying evil being alive, and baffled that nobody runs',
         'lines': ['Behold! A skull of pure menace, glowing with evil!', 'The green is my aura of doom. Also the bilge water.',
                   'Flee, mortal! Slowly, so I can watch.']},
    ],
}
REPLACED = {('monkey', 'Cannibals of Monkey Island')}
# The original engine's own games (no research: their people as that engine
# has them, each its own costume, the same number as its actor), with newly
# written personalities and lines.
HOME = {
    'maniac': [
        {'costume': 3, 'name': 'Dave', 'rooms': [1], 'talkColor': 15,
         'personality': 'Dave Miller, the teenager who leads the rescue into the Edison mansion to save his girlfriend Sandy; '
                        'steady, brave when it counts, and quick to keep his friends together',
         'lines': ['Sandy is in there somewhere. We are going in.', 'Stay close and keep your eyes open.', 'Anyone seen a key around here?']},
        {'costume': 1, 'name': 'Syd', 'rooms': [1], 'talkColor': 14,
         'personality': 'Syd, a keyboard player who dreams of making it big with his band; relaxed, music-mad, '
                        'and always hearing a tune in the creaks of an old house',
         'lines': ['This place has great acoustics. Spooky, but great.', 'I should write a song about this night.', 'Anyone got a piano?']},
        {'costume': 2, 'name': 'Razor', 'rooms': [1], 'talkColor': 13,
         'personality': 'Razor, lead singer of a punk band called the Scummettes; bold, sharp-tongued, '
                        'and not about to be scared off by a mad scientist',
         'lines': ['Mad scientists? Please. I have played tougher crowds.', 'Let us get this over with.', 'Nobody touches my microphone.']},
        {'costume': 4, 'name': 'Michael', 'rooms': [1], 'talkColor': 11,
         'personality': 'Michael, a photographer for the school paper; observant, calm, '
                        'and always looking for the right light and the strange detail everyone else misses',
         'lines': ['Hold still, that would make a great shot.', 'I need a darkroom for these.', 'Something about this house does not add up.']},
        {'costume': 5, 'name': 'Bernard', 'rooms': [44], 'talkColor': 10,
         'personality': 'Bernard, a nervous but brilliant electronics whiz; jumpy at every noise, '
                        'but the first to fix anything with wires in it',
         'lines': ['Did you hear that? I definitely heard that.', 'I could fix that radio in a minute.', 'Is it safe? It is not safe, is it?']},
        {'costume': 6, 'name': 'Wendy', 'rooms': [44], 'talkColor': 12,
         'personality': 'Wendy, an aspiring novelist; thoughtful, articulate, '
                        'and quietly collecting every odd thing about the Edisons for her next book',
         'lines': ['This would make a wonderful novel.', 'I wonder what the Edisons are really like.', 'Every old house has a story.']},
        {'costume': 7, 'name': 'Jeff', 'rooms': [44], 'talkColor': 9,
         'personality': 'Jeff, a laid-back surfer who would rather be at the beach; easygoing, cheerful, '
                        'and not entirely sure how he ended up indoors on such a fine night',
         'lines': ['Whoa, this place is gnarly.', 'Anybody seen a beach around here?', 'Totally tubular house, dude.']},
        {'costume': 9, 'name': 'Dr Fred', 'rooms': [30], 'talkColor': 10,
         'personality': 'Dr. Fred Edison, the eccentric scientist of the mansion, in thrall to the Purple Meteor; '
                        'brilliant, distracted, and forever in the middle of an experiment',
         'lines': ['Do not touch anything in my laboratory!', 'Science waits for no one.', 'The meteor knows best. Probably.']},
        {'costume': 23, 'name': 'Sandy', 'rooms': [30], 'talkColor': 14,
         'personality': "Sandy Pantz, the cheerleader Dave has come to rescue; spirited, impatient, "
                        'and very ready to be out of this laboratory',
         'lines': ['Dave! What took you so long?', 'Get me out of here!', 'I am never coming back to this house.']},
        {'costume': 10, 'name': 'Nurse Edna', 'rooms': [21], 'talkColor': 13,
         'personality': 'Nurse Edna Edison, Dr. Fred\'s formidable wife; sharp, suspicious, '
                        'and always watching the house for intruders',
         'lines': ['Who let you in here?', 'Wipe your feet, young man.', 'I will be watching you.']},
        {'costume': 11, 'name': 'Weird Ed', 'rooms': [26], 'talkColor': 11,
         'personality': 'Weird Ed Edison, the son of the house, a military buff with a secret plan; '
                        'stiff, suspicious, and very protective of his hamster and his package',
         'lines': ['Have you seen my package?', 'Stay out of my room.', 'My hamster is not for touching.']},
        {'costume': 12, 'name': 'Dead Cousin Ted', 'rooms': [24], 'talkColor': 7,
         'personality': 'Dead Cousin Ted, the Edisons\' long-dead cousin who keeps to the bathroom; '
                        'silent, serene, and somehow always there',
         'lines': ['...', '(says nothing at all)', '(stays exactly where he is)']},
        {'costume': 13, 'name': 'Purple Tentacle', 'rooms': [31], 'talkColor': 5,
         'personality': 'Purple Tentacle, the Edisons\' scheming guard; bossy, ambitious, '
                        'and not to be trusted with anything',
         'lines': ['Halt! Nobody goes past me.', 'One day I will rule the world.', 'What are you looking at?']},
        {'costume': 14, 'name': 'Green Tentacle', 'rooms': [20], 'talkColor': 2,
         'personality': 'Green Tentacle, a gentle tentacle who loves rock music; friendly, a little shy, '
                        'and dreaming of a big break with his band',
         'lines': ['Want to hear my demo tape?', 'I just love music.', 'Do not mind Purple, he is always like that.']},
        {'costume': 16, 'name': 'Purple Meteor', 'rooms': [51], 'talkColor': 13,
         'personality': 'the Purple Meteor, a glowing rock from deep space that rules the mansion from its chamber; '
                        'grandiose, scheming, and easily flattered',
         'lines': ['Kneel before me!', 'I came from beyond the stars.', 'Twenty years in a basement does things to a rock.']},
        {'costume': 15, 'name': 'Meteor Police', 'rooms': [51], 'talkColor': 5,
         'personality': 'an officer of the Meteor Police, a small alien who hunts runaway meteors; '
                        'by the book, proud of the badge, and suspicious of every rock in the room',
         'lines': ['Meteor Police. Nobody touch the glowing rocks.', 'Mind your speed, citizen.', 'I have my eye on that meteor.']},
        {'costume': 19, 'name': 'Man-Eating Plant', 'rooms': [27], 'talkColor': 5,
         'personality': 'the man-eating plant of the mansion; always hungry, cheerfully menacing, '
                        'and very fond of a drink of water or soda',
         'lines': ['Feed me!', 'Is that a snack? You look like a snack.', 'Water. Or soda. I am not fussy.']},
    ],
}


def landmarks():
    """Named places per game, from the catalog (same order as GAMES)."""
    text = CATALOG.read_text()
    arrays = re.findall(r'SCUMMVERSE_WORLD\("(\w+)", "[^"]*", "\w+", \d, (\w+)(?:, \d+)?\)', text)
    if len(arrays) < 10:
        raise SystemExit('catalog games not found; update the pattern in landmarks()')
    out = {}
    for gameid, array in arrays:
        body = text[text.index(f'static const WorldScene {array}[] = {{'):]
        out[gameid] = [int(r) for r in re.findall(r'\{(\d+), "', body[:body.index('};')])]
    return out


def cstr(text):
    return '"' + str(text).replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    named = landmarks()
    lines = ['// Generated by tools/world_cast.py: the characters of each other-world',
             '// game and the room they are in. Names; personalities and lines are',
             '// newly written (not original script text). talkColor is a V1 color.',
             'static const WorldCastGuest kWorldCast[] = {']
    total = 0
    for gameIndex, game in enumerate(ALL):
        path = ROOT/'build/foreign/cast'/f'{game}.json'
        if game in HOME:
            cast = [dict(c, confidence='high') for c in HOME[game]]
        elif not path.exists():
            continue
        else:
            cast = [c for c in json.loads(path.read_text()) if (game, c.get('name')) not in REPLACED] + EXTRA.get(game, [])
        rooms, _ = load_map(game)
        visit = {r for r, _ in rooms} | set(named.get(game, []))
        places = named.get(game, [])
        crowd = {}
        chosen = []
        for c in sorted(cast, key=lambda c: RANK.get(c.get('confidence'), 3)):
            # Only the main sprite's description counts, not its listed
            # variants ("53 = lying down" is another costume).
            if UNUSABLE.search(re.split(r'\b\d+\s*=\s', c.get('note') or '')[0]) or not c.get('lines') or len(c['lines']) < 3:
                continue
            if (game, c.get('costume')) in SPECKS:
                continue
            home = [r for r in c.get('rooms', []) if r in visit and crowd.get(r, 0) < MAX_GUESTS]
            if not home:
                free = [r for r in places if crowd.get(r, 0) < MAX_GUESTS]
                if not free:
                    continue
                home = [min(free, key=lambda r: crowd.get(r, 0))]
            room = home[0]
            slot = crowd.get(room, 0)
            crowd[room] = slot + 1
            chosen.append((room, slot, c))
        for room, slot, c in sorted(chosen, key=lambda x: (x[0], x[1])):
            talk = int(c.get('talkColor') or 15) & 15
            lines.append(f'\t{{{gameIndex}, {room}, {slot}, {{{int(c["costume"])}, {cstr(c["name"])},')
            lines.append(f'\t\t{cstr(c["personality"])}, {talk},')
            lines.append('\t\t{' + ', '.join(cstr(l) for l in c['lines'][:3]) + '}}},')
        print(f'{game}: {len(chosen)} of {len(cast)} characters in {len(crowd)} rooms')
        total += len(chosen)
    lines.append('};')
    (ROOT/'engine/common/scummverse_world_cast.inc').write_text('\n'.join(lines) + '\n')
    print(f'{total} characters')


if __name__ == '__main__':
    main()
