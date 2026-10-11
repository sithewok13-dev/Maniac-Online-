#!/usr/bin/env python3
"""Exercise patch-stack detection using the real pinned source and patches."""
from pathlib import Path
import subprocess
import tempfile
from bootstrap import ROOT, applied_prefix


def main():
    patches = sorted((ROOT/'patches').glob('*.patch'))
    paths = set()
    for patch in patches:
        output = subprocess.check_output(['git', 'apply', '--numstat', str(patch)], text=True)
        paths.update(line.split('\t', 2)[2] for line in output.splitlines())
    with tempfile.TemporaryDirectory(prefix='scummverse-bootstrap-test-') as tmp:
        source = Path(tmp)
        for name in paths:
            path = source/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=ROOT/'engine'))
        for count in range(len(patches)+1):
            before = {n: (source/n).read_bytes() for n in paths}
            assert applied_prefix(source, patches) == count, f'prefix {count}'
            assert before == {n: (source/n).read_bytes() for n in paths}, 'source changed during detection'
            if count < len(patches):
                subprocess.run(['git', 'apply', str(patches[count])], cwd=source, check=True)
        target = source/'engines/scumm/scumm.cpp'
        target.write_text(target.read_text()+'\n// Local unrelated user edit.\n')
        before = target.read_bytes()
        assert applied_prefix(source, patches) == len(patches)
        assert target.read_bytes() == before, 'local edit lost'
        target.write_text(target.read_text().replace('scummverse_exploration_safety', 'local_modified_safety'))
        before = target.read_bytes()
        assert applied_prefix(source, patches) < len(patches), 'conflicting modification accepted'
        assert target.read_bytes() == before, 'conflicting edit changed'
    print('PASS: clean source, every patch prefix, idempotence and preservation of local/conflicting edits')


if __name__ == '__main__':
    main()
