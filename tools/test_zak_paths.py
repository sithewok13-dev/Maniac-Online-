#!/usr/bin/env python3
"""Check Zak discovery with relative paths and the actual iOS chroot filesystem."""
import argparse
import json
from pathlib import Path
import shutil
import tempfile
from test_exploration import ROOT, run_probe
from test_ai_encounters import PRELUDE

EXTRA = r'''
#define FORBIDDEN_SYMBOL_EXCEPTION_unistd_h
#include <unistd.h>
#include "common/file.h"
#include "backends/fs/abstract-fs.h"
#include "backends/fs/chroot/chroot-fs-factory.h"
namespace Scumm {
static Common::FSNode scummverseZakFolder(const Common::FSNode &);
static Common::FSNode scummverseZakDirectory();
static bool readZakFile(const Common::FSNode &,int,const char *,Common::Array<byte> &,Common::String &);
}
'''

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('maniac',type=Path)
    parser.add_argument('--build',choices=('null','asan'),default='null')
    args=parser.parse_args()
    data=args.maniac.resolve()
    with tempfile.TemporaryDirectory(prefix='zak-path-data-',dir=ROOT/'build') as tmp:
        root=Path(tmp); zak=root/'zak'; zak.mkdir()
        for name in ('00.LFL','01.LFL','03.LFL','08.LFL'):
            shutil.copyfile(data.parent/'zak'/name,zak/name)
        # Prove that loose Maniac files never shadow explicit Zak files.
        shutil.copyfile(data/'00.LFL',root/'00.LFL')
        (root/'missing').mkdir(); (root/'bad').mkdir()
        (root/'bad/00.LFL').write_bytes(b'wrong edition')
        (root/'case/Zak').mkdir(parents=True)
        shutil.copyfile(zak/'00.LFL',root/'case/Zak/00.LFL')
        (root/'Zak').mkdir()
        shutil.copyfile(zak/'00.LFL',root/'Zak/00.lfl')
        code=(ROOT/'tools/probes/zak_paths.inc').read_text()
        code=code.replace('@ROOT@',str(root)).replace('"@MANIAC@"',json.dumps(str(data)))
        run_probe(data,code,'scummverse_roaming','SCUMMVERSE_ZAK_PATHS_PASS','zak-paths',PRELUDE+EXTRA,args.build)
