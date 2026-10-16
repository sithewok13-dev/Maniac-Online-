#!/usr/bin/env python3
"""Build pinned llama.cpp for the host CPU and run weight-free dialogue runtime tests.

Exercises the real iOS dialogue runtime (worker thread, scheduling, classic
fallback) with a scripted provider under AddressSanitizer and ThreadSanitizer.
No model weights or game data. Not an iPhone, Metal or model-quality test.
"""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kw):
    subprocess.run([str(a) for a in args], check=True, **kw)


def main():
    pin = json.loads((ROOT/'local-ai.json').read_text())['runtime']
    source, build = ROOT/'build/llama-src', ROOT/'build/llama-host'
    if not source.exists():
        run('git', 'clone', '--depth', '1', '--branch', pin['tag'], pin['repository'], source)
    head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if head != pin['commit']:
        raise SystemExit(f'Refusing unexpected llama.cpp revision: {head}')
    for patch in sorted((ROOT/'tools/runtime-patches').glob('*.patch')):
        if subprocess.run(['git', '-C', str(source), 'apply', '--reverse', '--check', str(patch)],
                          capture_output=True).returncode:
            run('git', '-C', source, 'apply', patch)
    run('cmake', '-S', source, '-B', build, '-DBUILD_SHARED_LIBS=OFF', '-DLLAMA_CURL=OFF',
        '-DGGML_NATIVE=OFF', '-DGGML_OPENMP=OFF', '-DLLAMA_BUILD_TESTS=OFF',
        '-DLLAMA_BUILD_EXAMPLES=OFF', '-DLLAMA_BUILD_SERVER=OFF', '-DLLAMA_BUILD_TOOLS=OFF',
        stdout=subprocess.DEVNULL)
    run('cmake', '--build', build, '-j2', '--target', 'llama', stdout=subprocess.DEVNULL)
    libs = [build/'src/libllama.a', build/'ggml/src/libggml.a',
            build/'ggml/src/libggml-cpu.a', build/'ggml/src/libggml-base.a', '-lpthread', '-ldl']
    include = ['-I', ROOT/'engine', '-I', source/'include', '-I', source/'ggml/include']
    for test, sanitizer in (('test_scene_talk', 'address,undefined'),
                            ('test_talk_provider', 'address,undefined'),
                            ('test_talk_provider', 'thread')):
        binary = ROOT/'build'/f'{test}-{sanitizer.split(",")[0]}'
        run('c++', '-std=c++17', '-g', f'-fsanitize={sanitizer}', *include,
            ROOT/'tools'/f'{test}.cpp', *libs, '-o', binary)
        run(binary, env={'TSAN_OPTIONS': 'halt_on_error=1', 'PATH': '/usr/bin:/bin'})
    # Real-model probes need a verified GGUF; compile them so API drift is caught.
    for test in ('test_talk', 'test_group_talk', 'test_local_ai'):
        run('c++', '-std=c++17', '-fsyntax-only', *include, ROOT/'tools'/f'{test}.cpp')
    print('PASS: dialogue runtime tests (scripted provider; no weights, device or Metal)')


if __name__ == '__main__':
    main()
