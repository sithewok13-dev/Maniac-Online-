// SPDX-License-Identifier: GPL-3.0-or-later
#include "engines/scumm/scummverse_portrait.h"
#include <cassert>
#include <cstdlib>
#include <iostream>
using namespace ScummversePresentation;
int main() {
 // Tall humans, broad aliens, narrow sprites and large future source art.
 for (int width : {1, 12, 24, 64, 320, 4096})
  for (int height : {1, 24, 64, 128, 4096})
   for (int target : {32, 64, 96, 128}) {
    const auto f = fitPortrait(width, height, target, 2);
    assert(f.valid());
    assert(f.x >= 2 && f.y >= 2);
    assert(f.x + f.width <= target - 2 && f.y + f.height <= target - 2);
    assert(std::abs(2 * f.x + f.width - target) <= 1);
    assert(std::abs(2 * f.y + f.height - target) <= 1);
    // Aspect distortion is bounded by one destination pixel of quantization.
    assert(std::abs(f.width * height - f.height * width) <= (width > height ? width : height));
   }
 auto tall = fitPortrait(20, 100, 64, 2);
 assert(tall.width == 12 && tall.height == 60 && tall.x == 26 && tall.y == 2);
 auto wide = fitPortrait(100, 20, 64, 2);
 assert(wide.width == 60 && wide.height == 12);
 assert(!fitPortrait(0, 24, 64, 2).valid());
 assert(!fitPortrait(24, -1, 64, 2).valid());
 assert(!fitPortrait(24, 24, 64, 32).valid());
 assert(!fitPortrait(24, 24, 64, -1).valid());
 std::cout << "PASS: portable portrait contract (144 aspect/size combinations and invalid inputs)\n";
}
