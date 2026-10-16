#!/usr/bin/env python3
"""Run real DOS door scripts in an isolated instrumented null-backend executable.

Requires a completed build/null and locally supplied original game data. Compiles
one temporary translation unit and copies the engine archive; never modifies the
engine source, normal executable, game files, or existing saves.
"""
import argparse
import hashlib
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PROBE = r'''
	// Test-only injection, absent from the shipped engine and IPA.
	VAR(VAR_EGO) = 3;
	static const int cases[][3] = {
		{1,61,67}, {1,53,234}, {6,137,125}, {36,125,137},
		{16,143,138}, {30,255,267}, {52,108,138}
	};
	for (uint n = 0; n < ARRAYSIZE(cases); ++n) {
		for (uint s = 0; s < NUM_SCRIPT_SLOT; ++s)
			vm.slot[s].status = ssDead;
		const int room = cases[n][0], obj = cases[n][1], other = cases[n][2];
		startScene(room, nullptr, 0);
		_sound->processSound();
		VAR(VAR_ACTIVE_OBJECT1) = obj;
		VAR(VAR_ACTIVE_OBJECT2) = 0;
		VAR(VAR_ACTIVE_VERB) = 1;
		putState(obj, kObjectStateLocked);
		putState(other, 0);
		runObjectScript(obj, 1, false, false, nullptr);
		_sound->processSound();
		if (_scummverseExplorationDoors) {
			if ((getState(obj) & (kObjectStateLocked | kObjectStateIntrinsic)) != kObjectStateIntrinsic ||
				!(getState(other) & kObjectStateIntrinsic))
				error("Door probe failed: open %d in room %d", obj, room);
			runObjectScript(obj, 2, false, false, nullptr);
			_sound->processSound();
			if ((getState(obj) | getState(other)) & kObjectStateIntrinsic)
				error("Door probe failed: close %d", obj);
		} else if (!(getState(obj) & kObjectStateLocked) ||
			(getState(obj) & kObjectStateIntrinsic) || (getState(other) & kObjectStateIntrinsic)) {
			error("Door probe failed: disabled mode unlocked %d", obj);
		}
	}
	// Exercise both normal loadRoomWithEgo scripts, not an adapter teleport.
	if (_scummverseExplorationDoors) {
		for (uint s = 0; s < NUM_SCRIPT_SLOT; ++s)
			vm.slot[s].status = ssDead;
		startScene(1, nullptr, 0);
		derefActor(3, "door probe")->putActor(240, 120, 1);
		VAR(VAR_ACTIVE_OBJECT1) = 61;
		putState(61, kObjectStateLocked);
		runObjectScript(61, 1, false, false, nullptr);
		runObjectScript(61, 13, false, false, nullptr);
		if (_currentRoom != 10 || derefActor(3, "door probe")->_room != 10)
			error("Door probe failed: mansion entrance");
		VAR(VAR_ACTIVE_OBJECT1) = 67;
		runObjectScript(67, 13, false, false, nullptr);
		if (_currentRoom != 1 || derefActor(3, "door probe")->_room != 1)
			error("Door probe failed: mansion exit");
	}
	warning("SCUMMVERSE_DOOR_PROBE_PASS enabled=%d", _scummverseExplorationDoors);
	quitGame();
'''


def command_for(build, source, target):
    output = subprocess.check_output(['make', '-n', '-W', str(source), target], cwd=build, text=True)
    # Use the generated compiler invocation as argv, never execute shell text.
    for line in output.splitlines():
        if ';' in line and (' LINK ' if target == 'scummvm' else ' C++ ') in line:
            return shlex.split(line.split(';', 1)[1])
    raise RuntimeError(f'Cannot find compiler command for {target}')


def run_probe(data, probe_code, config_key, marker, label, prelude="", build_name="null", reference_game=None):
    if reference_game not in (None, "zak"):
        raise ValueError("Only the audited Zak source-reference launcher is supported")
    build = ROOT/'build'/build_name
    source = ROOT/'engine/engines/scumm/scumm.cpp'
    with tempfile.TemporaryDirectory(prefix=f'scummverse-{label}-', dir=ROOT/'build') as tmp:
        work = Path(tmp)
        code = prelude + source.read_text()
        boundary = '\n}\n\n#ifdef ENABLE_HE\nvoid ScummEngine_v90he::runBootscript()'
        if code.count(boundary) != 1:
            raise RuntimeError('Pinned runBootscript boundary changed')
        probe = work/'scumm.cpp'
        # Probes write private captures to <checkout>/build, wherever it lives.
        probe_code = probe_code.replace('/workspace/Maniac-Online/build', str(ROOT/'build'))
        probe.write_text(code.replace(boundary, '\n' + probe_code + boundary))
        cmd = command_for(build, source, 'engines/scumm/scumm.o')
        cmd[cmd.index(str(source))] = str(probe)
        cmd[cmd.index('-o')+1] = str(work/'scumm.o')
        cmd[cmd.index('-MF')+1] = str(work/'scumm.d')
        subprocess.run(cmd, cwd=build, check=True)
        archive = work/'libscumm.a'
        shutil.copy2(build/'engines/scumm/libscumm.a', archive)
        subprocess.run(['ar', 'r', str(archive), str(work/'scumm.o')], check=True)
        cmd = command_for(build, 'engines/scumm/libscumm.a', 'scummvm')
        cmd[cmd.index('engines/scumm/libscumm.a')] = str(archive)
        if reference_game:
            # Reference-only launcher: compile into the temporary archive. Never
            # relax the distributed application's standalone startup restriction.
            main_source = ROOT/'engine/base/main.cpp'
            main_text = main_source.read_text()
            replacements = {
                'command = "scumm:maniac";': 'command = "scumm:zak";',
                'ConfMan.get("gameid") != "maniac"': 'ConfMan.get("gameid") != "zak"',
            }
            for before, after in replacements.items():
                if main_text.count(before) != 1:
                    raise RuntimeError('Pinned reference-launcher boundary changed')
                main_text = main_text.replace(before, after)
            main_probe = work/'main.cpp'
            main_probe.write_text(main_text)
            main_cmd = command_for(build, main_source, 'base/main.o')
            main_cmd[main_cmd.index(str(main_source))] = str(main_probe)
            main_cmd[main_cmd.index('-o')+1] = str(work/'main.o')
            main_cmd[main_cmd.index('-MF')+1] = str(work/'main.d')
            subprocess.run(main_cmd, cwd=build, check=True)
            base = work/'libbase.a'
            shutil.copy2(build/'base/libbase.a', base)
            subprocess.run(['ar', 'r', str(base), str(work/'main.o')], check=True)
            cmd[cmd.index('base/libbase.a')] = str(base)
        exe = work/'scummvm-probe'
        cmd[cmd.index('-o')+1] = str(exe)
        subprocess.run(cmd, cwd=build, check=True)
        for enabled in (False, True):
            config = work/'probe.ini'
            config.write_text('[scummvm]\n' + ('scummverse_roaming=false\n' if config_key != 'scummverse_roaming' else '') + config_key + '=' + str(enabled).lower() + '\n')
            result = subprocess.run([str(exe), f'--config={config}', f'--path={data}',
                                     f'--savepath={work}', '--debuglevel=1'],
                                    cwd=work, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=45)
            output = result.stdout + result.stderr
            (ROOT/f'build/{label}-probe-{enabled}.log').write_text(output)
            if result.returncode or f'{marker} enabled={int(enabled)}' not in output:
                raise RuntimeError(output[-6000:])
            print(f'PASS: {label} real-script probe, override enabled={enabled}')
        print('Normal source, executable, game data and saves unchanged')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path)
    args = parser.parse_args()
    data = args.data.resolve()
    if hashlib.md5((data/'00.LFL').read_bytes()).hexdigest() != '7f45ddd6dbfbf8f80c0c0efea4c295bc':
        parser.error('This probe requires the audited English DOS V1 edition')
    run_probe(data, PROBE, 'scummverse_exploration_doors', 'SCUMMVERSE_DOOR_PROBE_PASS', 'door')


if __name__ == '__main__':
    main()
