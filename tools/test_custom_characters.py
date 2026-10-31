#!/usr/bin/env python3
"""The custom characters' include is what tools/custom_characters.py makes:
written again into a temporary file, it must be byte for byte the committed
engine/common/scummverse_custom_cast.inc (from 0200: a frame or a mark
added only to the include would be lost the next time it is generated)."""
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/'tools'))
import custom_characters  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp)/'scummverse_custom_cast.inc'
    custom_characters.write_inc(out)
    made, kept = out.read_bytes(), (ROOT/'engine/common/scummverse_custom_cast.inc').read_bytes()
if made != kept:
    raise SystemExit('FAIL: engine/common/scummverse_custom_cast.inc is not what tools/custom_characters.py writes; run it again')
print(f'PASS: the custom characters\' include is what tools/custom_characters.py writes ({len(custom_characters.CUSTOM)} characters)')
