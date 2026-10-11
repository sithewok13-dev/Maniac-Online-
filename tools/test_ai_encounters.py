#!/usr/bin/env python3
"""Test asynchronous encounter integration in the real VM using a controlled worker."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe

PRELUDE = r'''
#define SCUMMVERSE_LOCAL_AI 1
#include <cstring>
namespace FakeAI { bool accept = false, complete = false; int actor = 0, room = 0, cancels = 0, talk = 0; unsigned roster = 0, group = 0; bool reply = false; }
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
void scummverseWorldRequest(int) {}
int scummverseWorldPoll() { return 0; }
void scummverseWorldReport(const char *) {}
void scummverseAICancel() { ++FakeAI::cancels; FakeAI::complete = false; }
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    data = parser.parse_args().data.resolve()
    run_probe(data, (ROOT/'tools/probes/ai-encounters.inc').read_text(),
              'scummverse_roaming', 'SCUMMVERSE_AI_ENCOUNTER_PASS', 'ai-encounters', PRELUDE)
