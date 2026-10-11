#define SCUMMVERSE_LOCAL_AI 1
#include "backends/platform/ios7/scummverse_ai_runtime.inc"
#include <cassert>
#include <iostream>
int main() {
 scummverseTravelScene(53,3,(1u<<24)|(1u<<10),55,1u<<24);
 using namespace ScummverseLocalAI;
 assert(follows(24) && !follows(14));
 assert(sceneToken()==((53*32+3)<<8));
 std::string context=travelContext(53,3);
 assert(context.find("Zak McKracken")!=std::string::npos);
 assert(context.find("Nurse Edna")==std::string::npos); // Present companion is not necessarily an arrival.
 assert(travelContext(54,3).empty() && travelContext(53,5).empty());
 std::vector<ChatLine> history{ChatLine(0,"Where did we come from?")};
 std::string prompt=chatPrompt(24,53,3,1u<<24,history,false);
 assert(prompt.find(context)!=std::string::npos && prompt.find("Where did we come from?")!=std::string::npos);
 scummverseTravelScene(54,3,0,0,0);
 assert(travelContext(54,3).empty() && !follows(24));
 std::cout << "PASS: arrival facts, companion state, scene isolation and shared chat prompt\n";
}
