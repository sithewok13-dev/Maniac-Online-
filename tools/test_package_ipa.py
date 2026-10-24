#!/usr/bin/env python3
"""Build stamps of the unsigned IPA (tools/package_ipa.py), without Xcode."""
from pathlib import Path
from package_ipa import build_stamp

ROOT = Path(__file__).resolve().parents[1]
version, label = build_stamp(sorted((ROOT / 'patches').glob('*.patch')), {'GITHUB_RUN_NUMBER': '68', 'GITHUB_SHA': 'abcdef0123'})
latest = max(int(p.name[:4]) for p in (ROOT / 'patches').glob('*.patch'))
assert version == f'{latest}.68' and label == f'patch {latest:04d}, build 68 (abcdef0)', (version, label)
# Later builds compare higher, as sideloading tools expect of an update.
later, _ = build_stamp([Path('9999-x.patch')], {'GITHUB_RUN_NUMBER': '1'})
assert tuple(map(int, later.split('.'))) > tuple(map(int, version.split('.')))
assert build_stamp([], {}) == ('0.0', 'patch 0000, build 0 (local)')
print(f'PASS: IPA build stamp ({label})')
