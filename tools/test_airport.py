#!/usr/bin/env python3
"""Verify free airport travel with privately supplied original English DOS V1 data."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('maniac', type=Path)
    parser.add_argument('--build', choices=('null', 'asan'), default='null')
    parser.add_argument('--snapshot', type=Path, help='Optional private airport PPM screenshot')
    parser.add_argument('--old-save', type=Path, help='Optional save produced by the previous apartment-only build')
    args = parser.parse_args()
    data = args.maniac.resolve()
    with tempfile.TemporaryDirectory(prefix='airport-invalid-', dir=ROOT/'build') as tmp:
        for name in ('00.LFL', '01.LFL'):
            shutil.copyfile(data.parent/'zak'/name, Path(tmp)/name)
        (Path(tmp)/'08.LFL').write_bytes(b'not the verified airport')
        code = (ROOT/'tools/probes/airport.inc').read_text()
        code = code.replace('"@BAD_ZAK@"', json.dumps(tmp))
        code = code.replace('"@SNAPSHOT@"', json.dumps(str(args.snapshot.resolve()) if args.snapshot else ''))
        code = code.replace('"@OLD_SAVE@"', json.dumps(str(args.old_save.resolve()) if args.old_save else ''))
        # The game starts with the bad copy too: the boot reaches the sandbox
        # (mounting Zak from it) before the probe runs.
        run_probe(data, code, 'scummverse_roaming', 'SCUMMVERSE_AIRPORT_PASS', 'airport', PRELUDE + '\n#include "common/savefile.h"\n', args.build,
                  extra_config=f'scummverse_zak_path={tmp}\n')
