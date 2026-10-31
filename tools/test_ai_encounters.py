#!/usr/bin/env python3
"""Test asynchronous encounter integration in the real VM using a controlled worker."""
import argparse
from pathlib import Path
from test_exploration import ROOT, run_probe

PRELUDE = r'''
#define SCUMMVERSE_LOCAL_AI 1
#include <cstring>
namespace FakeAI { bool accept = false, complete = false; int actor = 0, room = 0, cancels = 0, talk = 0; unsigned long long roster = 0, group = 0; bool reply = false; int worldRequest = 0, airportOffers = 0; }
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
unsigned long long scummverseTalkScene(int, int, unsigned long long actors, bool canSpeak, int &speaker, char *line, int capacity) {
 FakeAI::roster = actors; line[0] = 0; speaker = 0;
 if (FakeAI::talk && !(actors & (1ull << FakeAI::talk))) FakeAI::talk = 0;
 if (FakeAI::talk && FakeAI::reply && canSpeak) { std::strncpy(line, "Keep out of my refrigerator!", capacity); speaker = FakeAI::talk; FakeAI::reply = false; }
 return (FakeAI::group ? FakeAI::group : FakeAI::talk ? 1ull << FakeAI::talk : 0) & actors;
}
void scummverseRosterFace(int,const unsigned char *) {}
void scummverseRosterShow(int,unsigned) {}
void scummverseAirportOffer(int) { ++FakeAI::airportOffers; }
void scummverseWorldRequest(int destination) { FakeAI::worldRequest=destination; }
int scummverseWorldPoll() { int request=FakeAI::worldRequest; FakeAI::worldRequest=0; return request; }
int scummverseWorldPeek() { return FakeAI::worldRequest; }
static int fakeStoryPlaying = -1;
void scummverseStoryPlaying(int game) { fakeStoryPlaying = game; }
int scummverseStoryPlaying() { return fakeStoryPlaying; }
void scummverseWorldReport(const char *) {}
void scummverseTravelScene(int, int, unsigned, int, unsigned) {}
namespace FakeAI { int appearance[25] = {}; }
void scummverseTalkAppearance(int actor, int key) { if (actor > 0 && actor < 25) FakeAI::appearance[actor] = key; }
namespace FakeAI { int wanderers[26] = {}; }
void scummverseTalkVisitor(int slot, int key) { if (slot >= 0 && slot < 26) FakeAI::wanderers[slot] = key; }
void scummverseAICancel() { ++FakeAI::cancels; FakeAI::complete = false; }
namespace FakeAI { int castGames = 0, castFaces = 0, castShown = 0; int castMembers[12] = {}, castLead[12] = {}; }
void scummverseCastGame(int slot, const char *, const char *, const unsigned char *rgba) {
 if (slot == 0) { FakeAI::castGames = FakeAI::castFaces = 0; for (int &m : FakeAI::castMembers) m = 0; }
 ++FakeAI::castGames; if (rgba) ++FakeAI::castFaces;
}
void scummverseCastMember(int slot, const char *, int request) {
 if (slot < 0 || slot >= 12) return;
 if (!FakeAI::castMembers[slot]) FakeAI::castLead[slot] = request;
 ++FakeAI::castMembers[slot];
}
void scummverseCastShow() { ++FakeAI::castShown; }
namespace FakeAI { char placesTitle[64] = ""; int places = 0, placesShown = 0, placeRequest[200] = {}; char placeName[200][64] = {}; }
static void fakeCopy(char *to, const char *from, int size) { int i = 0; for (; from[i] && i < size - 1; ++i) to[i] = from[i]; to[i] = 0; }
void scummversePlacesBegin(const char *title) { fakeCopy(FakeAI::placesTitle, title, sizeof(FakeAI::placesTitle)); FakeAI::places = 0; }
void scummversePlacesItem(const char *name, int request) {
 if (FakeAI::places < 200) { fakeCopy(FakeAI::placeName[FakeAI::places], name, 64); FakeAI::placeRequest[FakeAI::places] = request; }
 ++FakeAI::places;
}
void scummversePlacesShow() { ++FakeAI::placesShown; }
// (Defined here too: an optimised or sanitizer build inlines the desktop's
// empty ones away, and the probe would not link.)
void scummverseStoryModeOn(bool) {}
bool scummverseStoryModeOn() { return false; }
void scummverseSandboxActive(bool) {}
bool scummverseSandboxActive() { return false; }
'''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    data = parser.parse_args().data.resolve()
    run_probe(data, (ROOT/'tools/probes/ai-encounters.inc').read_text(),
              'scummverse_roaming', 'SCUMMVERSE_AI_ENCOUNTER_PASS', 'ai-encounters', PRELUDE)
