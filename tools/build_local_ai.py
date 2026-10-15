#!/usr/bin/env python3
"""Build pinned llama.cpp for an arm64 iPhone, keeping weights out of the IPA."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def main():
    if sys.platform != 'darwin':
        raise SystemExit('This device-library build requires macOS/Xcode; use hosted iOS CI.')
    pin = json.loads((ROOT/'local-ai.json').read_text())['runtime']
    source = ROOT/'build/llama-src'
    if not source.exists():
        run('git', 'clone', '--depth', '1', '--branch', pin['tag'], pin['repository'], source)
    head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if head != pin['commit']:
        raise SystemExit(f'Refusing unexpected llama.cpp revision: {head}')
    # Apply audited local fixes to the pinned runtime, idempotently. Reject
    # conflicts rather than silently building without the ownership repair.
    for patch in sorted((ROOT/'tools/runtime-patches').glob('*.patch')):
        applied = subprocess.run(['git', '-C', str(source), 'apply', '--reverse', '--check', str(patch)], capture_output=True)
        if applied.returncode:
            run('git', '-C', source, 'apply', '--check', patch)
            run('git', '-C', source, 'apply', patch)
    run(sys.executable, ROOT/'tools/test_metal_ownership.py', source)
    output = ROOT/'build/llama-ios'
    run('cmake', '-S', source, '-B', output,
        '-DCMAKE_SYSTEM_NAME=iOS', '-DCMAKE_OSX_SYSROOT=iphoneos',
        '-DCMAKE_OSX_ARCHITECTURES=arm64', '-DCMAKE_OSX_DEPLOYMENT_TARGET=13.0',
        '-DCMAKE_BUILD_TYPE=Release', '-DBUILD_SHARED_LIBS=OFF',
        '-DLLAMA_BUILD_TESTS=OFF', '-DLLAMA_BUILD_EXAMPLES=OFF',
        '-DLLAMA_BUILD_TOOLS=OFF', '-DLLAMA_BUILD_SERVER=OFF',
        '-DLLAMA_BUILD_COMMON=OFF', '-DLLAMA_CURL=OFF',
        '-DGGML_NATIVE=OFF', '-DGGML_CPU_ARM_ARCH=armv8-a',
        '-DGGML_OPENMP=OFF', '-DGGML_BLAS=OFF', '-DGGML_ACCELERATE=ON',
        '-DGGML_METAL=ON', '-DGGML_METAL_EMBED_LIBRARY=ON',
        '-DGGML_BACKEND_DL=OFF')
    run('cmake', '--build', output, '--target', 'llama', '--parallel', '3')
    libraries = [output/'src/libllama.a'] + sorted((output/'ggml/src').rglob('*.a'))
    if len(libraries) < 5:
        raise SystemExit('Missing llama/ggml/CPU/Metal static libraries')
    run('xcrun', 'libtool', '-static', '-o', output/'libscummverse-ai.a', *libraries)
    run('lipo', output/'libscummverse-ai.a', '-verify_arch', 'arm64')
    print('Built pinned CPU/Metal inference library; no model weights included')


if __name__ == '__main__':
    main()
