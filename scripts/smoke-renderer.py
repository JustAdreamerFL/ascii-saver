#!/usr/bin/env python3
"""Integration smoke test for the instrumented Rust ttfx CLI and JSON contracts.
Runs with no KDE dependencies. Noninteractive output is sent to /dev/null.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from frame_report import parse_frame_report


def verify(binary: Path, *, effect: str, fx_mode: str = None, timeout: float = 40):
    with tempfile.TemporaryDirectory(prefix="ttfx-smoke-") as temp:
        report = Path(temp) / "frames.json"
        argv = [str(binary), "--stats-file", str(report), "--frame-rate", "120",
                "--duration-factor", "1", "--time-scale", "1", effect]
        env = os.environ.copy()
        if fx_mode is not None:
            env["TTFX_FX"] = fx_mode
        with open(os.devnull, "wb") as output:
            proc = subprocess.run(argv, input=b"KDE ASCII\nSAVER\n", stdout=output,
                                  stderr=subprocess.PIPE, env=env, timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"{effect} returned {proc.returncode}: {proc.stderr.decode(errors='replace')[-800:]}")
        if not report.is_file():
            raise RuntimeError(f"{effect}: missing stats JSON file")
        raw = json.loads(report.read_text())
        parsed = parse_frame_report(raw, expected_effect=effect)
        if parsed is None or parsed['output_frames'] < 2:
            raise RuntimeError(f"{effect}: invalid or insufficient frame data: {raw}")
        print(f"PASS {effect} [{fx_mode or 'auto'}]: {parsed['output_frames']} frames, "
              f"{parsed['output_fps']:.1f} average output FPS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('binary', type=Path)
    p.add_argument('--timeout', type=float, default=40)
    args = p.parse_args()
    binary = args.binary.resolve()
    if not binary.is_file():
        p.error(f'Binary not found: {binary}')
    # Run original path and auto dispatch. 'beams' is deterministic enough
    # to exercise stats without a GUI; also test a different effect family.
    for effect, mode in [('beams', '0'), ('decrypt', None)]:
        verify(binary, effect=effect, fx_mode=mode, timeout=args.timeout)
    print('Instrumented renderer smoke checks passed.')

if __name__ == '__main__':
    main()
