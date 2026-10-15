#!/usr/bin/env python3
"""Verify the DOS V1 costume measurements behind the distant-scene ratio.
Requires user-supplied game files; emits measurements only, never extracted art.
"""
import argparse
import hashlib
import struct
from pathlib import Path


def u16(data, offset):
    if offset < 0 or offset + 2 > len(data):
        raise ValueError('Costume reference outside resource')
    return struct.unpack_from('<H', data, offset)[0]


def standing_span(index, folder, costume, animation):
    resource = folder / f'{index[960 + costume]:02}.LFL'
    source = bytes(b ^ 255 for b in resource.read_bytes())
    offset = u16(index, 997 + costume * 2)
    size = u16(source, offset)
    if offset + size > len(source):
        raise ValueError('Truncated costume')
    data = source[offset:offset + size]
    if data[5] & 127 != 0x57:
        raise ValueError('Unsupported costume encoding')
    base = 4
    commands = base + u16(data, 6)
    cursor = base + u16(data, 24 + animation * 2)
    mask = data[cursor] << 8
    cursor += 1
    top, bottom, ymove = 10000, -10000, 0
    signed = lambda n: n if n < 128 else n - 256
    for limb in range(8):
        if not mask & (0x8000 >> limb):
            continue
        command = data[cursor]
        cursor += 1
        if command == 255:
            continue
        cursor += 1
        code = data[commands + command] & 127
        if code >= 0x79:
            continue
        table = base + u16(data, 8 + limb * 2)
        cel = base + u16(data, table + code * 2)
        y = ymove - signed(data[cel + 3])
        top, bottom = min(top, y), max(bottom, y + data[cel + 1])
        ymove -= signed(data[cel + 5])
    return bottom - top


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('data', type=Path)
    args = p.parse_args()
    raw = (args.data / '00.LFL').read_bytes()
    if hashlib.md5(raw).hexdigest() != '7020931d5a2be0a49d68e7a1882363e4':
        raise SystemExit('Requires audited English DOS V1 Zak data')
    index = bytes(b ^ 255 for b in raw)
    assert standing_span(index, args.data, 1, 6) == 46
    assert standing_span(index, args.data, 9, 6) == 10
    print('PASS: normal standing reference 46px; original distant reference 10px')
