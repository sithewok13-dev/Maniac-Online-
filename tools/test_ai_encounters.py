#!/usr/bin/env python3
"""Test asynchronous encounter integration in the real VM using a controlled worker."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe

PRELUDE = r'''
#define SCUMMVERSE_LOCAL_AI 1
#include <cstring>
namespace FakeAI { bool accept = false, complete = false; int actor = 0, room = 0, cancels = 0, talk = 0; unsigned roster = 0, group = 0; bool reply = false; int worldRequest = 0, airportOffers = 0; }
bool scummverseTalkPick(int) { return false; }
bool scummverseAIRequest(int actor, int room, int) {
 if (!FakeAI::accept) return false;
 FakeAI::actor = actor; FakeAI::room = room; return true;
}
bool scummverseAIPoll(int &actor, int &room, char *text, int capacity) {
 if (!FakeAI::complete) return false;
 actor = FakeAI::actor; room = FakeAI::room;
 std::strncpy(text, "Who left the refrigerator open?", capacity); FakeAI::complete = false; return true;
}
unsigned scummverseTalkScene(int, int, unsigned actors, bool canSpeak, int &speaker, char *line, int capacity) {
 FakeAI::roster = actors; line[0] = 0; speaker = 0;
 if (FakeAI::talk && !(actors & (1u << FakeAI::talk))) FakeAI::talk = 0;
 if (FakeAI::talk && FakeAI::reply && canSpeak) { std::strncpy(line, "Keep out of my refrigerator!", capacity); speaker = FakeAI::talk; FakeAI::reply = false; }
 return (FakeAI::group ? FakeAI::group : FakeAI::talk ? 1u << FakeAI::talk : 0) & actors;
}
void scummverseRosterFace(int,const unsigned char *) {}
void scummverseRosterShow(int,unsigned) {}
void scummverseAirportOffer(int) { ++FakeAI::airportOffers; }
void scummverseWorldRequest(int destination) { FakeAI::worldRequest=destination; }
int scummverseWorldPoll() { int request=FakeAI::worldRequest; FakeAI::worldRequest=0; return request; }
void scummverseWorldReport(const char *) {}
void scummverseTravelScene(int, int, unsigned, int, unsigned) {}
namespace FakeAI { int appearance[25] = {}; }
void scummverseTalkAppearance(int actor, int key) { if (actor > 0 && actor < 25) FakeAI::appearance[actor] = key; }
void scummverseAICancel() { ++FakeAI::cancels; FakeAI::complete = false; }
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    data = parser.parse_args().data.resolve()
    run_probe(data, (ROOT/'tools/probes/ai-encounters.inc').read_text(),
              'scummverse_roaming', 'SCUMMVERSE_AI_ENCOUNTER_PASS', 'ai-encounters', PRELUDE)
