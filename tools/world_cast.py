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
# has them; the mansion's each its own costume, the same number as its
# actor; Zak's in Zak's own costume numbers, each with the colour its
# scripts give its clothes, `tint`), with newly written personalities and
# lines (Zak's as the original engine's residents have them).
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
    ],    'zak': [
        {'costume': 1, 'name': 'Zak McKracken', 'rooms': [1], 'talkColor': 13, 'tint': 13,
         'personality': 'Zak McKracken, a tabloid reporter for the National Inquisitor who dreams of being a real writer; curious, wry, and suddenly in the middle of an alien plot',
         'lines': ["That would make a great headline.", "Off the record? Sure.", "My editor will never believe this."]},
        {'costume': 2, 'name': 'Annie Larris', 'rooms': [6], 'talkColor': 14, 'tint': 4,
         'personality': 'Annie Larris, an insightful archaeologist investigating ancient crystals and alien activity; thoughtful, brave, and practical',
         'lines': ["That fits with my research.", "Let's look for evidence first.", "The ancient builders knew something."]},
        {'costume': 3, 'name': 'Melissa China', 'rooms': [185], 'talkColor': 3, 'tint': 3,
         'personality': "Melissa China, an adventurous Yale student and Leslie's friend; curious, resourceful, and inclined to plan before exploring",
         'lines': ["Let's plan that properly.", "Leslie would love to hear that.", "I'll add it to our notes."]},
        {'costume': 4, 'name': 'Leslie Bennett', 'rooms': [185], 'talkColor': 8, 'tint': 7,
         'personality': "Leslie Bennett, an adventurous Yale student and Melissa's friend; enthusiastic, witty, and eager to explore unfamiliar places",
         'lines': ["Ha! Let's go find out.", "Melissa will want details.", "Now this is an adventure."]},
        {'costume': 28, 'name': 'Caponian', 'rooms': [16], 'talkColor': 10, 'tint': 10,
         'personality': 'a Caponian alien disguised as a telephone-company employee; evasive, bureaucratic, and comically suspicious',
         'lines': ["The phone company has no comment.", "Please hold. Your call is important.", "That is not a suspicious question at all."]},
        {'costume': 27, 'name': 'The King', 'rooms': [10], 'talkColor': 1, 'tint': 1,
         'personality': 'The King, a legendary rock-and-roll singer who has been living aboard an alien spacecraft in the Bermuda Triangle; warm, charming, nostalgic about touring, and grateful to his audience',
         'lines': ["Thank you. Thank you very much.", "I've played bigger rooms than this one.", "Those spaceships sure get lonely."]},
        {'costume': 21, 'name': 'Zaire shaman', 'rooms': [151], 'talkColor': 9, 'tint': 9,
         'personality': 'a knowledgeable shaman from the Zaire village, familiar with ancient crystals; observant and wry, speaking natural English without a caricature accent',
         'lines': ["The crystals would tell you more.", "Listen carefully. The jungle remembers.", "Patience. Answers come in time."]},
        {'costume': 26, 'name': 'Nepal guard', 'rooms': [17], 'talkColor': 4, 'tint': 4,
         'personality': "a guard posted at the Guru's temple door in Kathmandu; formal, watchful, and politely firm that only devotees of the Guru may enter",
         'lines': ["Only devotees of the Guru may enter.", "Keep moving, traveler.", "The Guru sees visitors in his own time."]},
        {'costume': 22, 'name': 'Guru', 'rooms': [19], 'talkColor': 15, 'tint': 1,
         'personality': 'the Guru of Kathmandu, a serene teacher who meditates above the floor and instructs devotees in the ways of the crystals; calm, cryptic, and kind',
         'lines': ["Patience. The crystal reveals itself slowly.", "You carry restless energy. Breathe.", "A clear mind travels farther than any plane."]},
        {'costume': 16, 'name': 'Lou', 'rooms': [7], 'talkColor': 1, 'tint': 1,
         'personality': "Lou, who runs Lou's Loans, the pawn shop on 14th Avenue in San Francisco; a fast-talking, sharp-eyed dealer who will take almost anything in and sell it back for more, friendly enough but never sentimental about a price",
         'lines': ["Everything in here is for sale. Everything.", "I'll give you two bucks for it. Final offer.", "No refunds, no exceptions, no kidding."]},
        {'costume': 11, 'name': 'Stewardess', 'rooms': [145], 'talkColor': 3, 'tint': 3,
         'personality': 'a stewardess on the airline that flies Zak around the world; cheerful, brisk and endlessly patient, with a practised smile for every passenger, even the ones who keep pressing the call button',
         'lines': ["Please keep your seat belt fastened.", "Peanuts? We have plenty of peanuts.", "We'll be landing shortly. Probably."]},
        {'costume': 23, 'name': 'Bum', 'rooms': [143], 'talkColor': 8, 'tint': 9,
         'personality': 'a down-on-his-luck man who has made the Miami airport terminal his home; chatty, philosophical, and sure that the next traveller will spare some change or at least a good story',
         'lines': ["Spare a little change for a fellow traveller?", "I've been to every gate in this airport. Never left.", "Nice day for not flying anywhere."]},
        {'costume': 25, 'name': 'Devotee', 'rooms': [145], 'talkColor': 8, 'tint': 9,
         'personality': 'a robed devotee who greets travellers at the San Francisco airport; serene, earnest and relentlessly cheerful, always hoping to share a flower and a few words about inner peace',
         'lines': ["Peace be with you, traveller.", "Would you like a flower? It's free.", "Every journey begins with a single step."]},
        {'costume': 24, 'name': 'Sentry', 'rooms': [134], 'talkColor': 8, 'tint': 9,
         'personality': 'a sentry who keeps watch at Stonehenge; stiff, serious and suspicious of anyone who comes near the stones, especially at night',
         'lines': ["Stay back from the stones, please.", "Nothing to see here. Just very old rocks.", "I've got my eye on you."]},
        {'costume': 29, 'name': 'Skolarian', 'rooms': [195], 'talkColor': 14, 'tint': 14,
         'personality': 'a Skolarian, one of the ancient guardians of Earth, appearing as a glowing projection deep inside Mars; solemn, wise, a little weary after ages of waiting, and determined to see the Caponians stopped',
         'lines': ["The crystals hold more power than you know.", "We have waited a very long time for you.", "Beware the Caponians and their machines."]},
        {'costume': 10, 'name': 'Pilot', 'rooms': [144], 'talkColor': 8, 'tint': 9,
         'personality': 'an airline pilot between flights, in dark glasses and a crisp uniform; laid-back, full of tall tales about turbulence, and in no hurry to get back to the cockpit',
         'lines': ["This is your captain speaking. Just kidding.", "Turbulence? I've seen worse.", "I could fly this route with my eyes closed."]},
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
    # The clothes colour of each of their costumes (the oldest games colour a
    # costume by its actor, set by their scripts).
    tints = [(ALL.index(g), c['costume'], c['tint']) for g in HOME for c in HOME[g] if 'tint' in c]
    lines.append('static const WorldOwnTint kWorldOwnTints[] = {')
    if not tints:
        lines.append('\t{-1, -1, -1},')
    for i in range(0, len(tints), 8):
        lines.append('\t' + ' '.join(f'{{{g}, {c}, {t}}},' for g, c, t in tints[i:i+8]))
    lines.append('};')
    (ROOT/'engine/common/scummverse_world_cast.inc').write_text('\n'.join(lines) + '\n')
    print(f'{total} characters')


if __name__ == '__main__':
    main()
