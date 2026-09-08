#!/usr/bin/env python3
"""Replay the archived Round 4 strategy with an explicit expiry assumption.

The retained team notes map day 1/2/3 to 7/6/5 days to expiry.
This is an explicit assumption; the CSV day label alone does not prove expiry.
The upload artifact itself starts at 7. Keep it unchanged and materialize a
configured copy plus a hash/parameter manifest under ignored run artifacts.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BACKTESTER = ROOT / 'prosperity_rust_backtester'
SOURCE = ROOT / 'submissions/r4_final_v01_imc_upload.py'


def configure_trader(source: str, days: float) -> str:
    if not math.isfinite(days) or days <= 0:
        raise ValueError('starting expiry must be finite and positive')
    configured, count = re.subn(r'^START_TTE_DAYS = [0-9.]+$', f'START_TTE_DAYS = {days!r}', source, flags=re.MULTILINE)
    if count != 1:
        raise ValueError('expected exactly one START_TTE_DAYS assignment in the archive')
    return '# Generated post-competition replay configuration; historical docstring results are not results of this run.\n' + configured


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--day', type=int, choices=(1, 2, 3), required=True)
    parser.add_argument('--start-tte-days', type=float, help='Explicit sensitivity override; default is 8 minus day')
    args = parser.parse_args()
    days = float(8-args.day) if args.start_tte_days is None else args.start_tte_days
    source = SOURCE.read_text()
    configured = configure_trader(source, days)
    digest = hashlib.sha256(source.encode()).hexdigest()
    generated_dir = BACKTESTER / 'runs/configured_traders'
    generated_dir.mkdir(parents=True, exist_ok=True)
    trader = generated_dir / f'r4_{digest[:12]}_tte_{days:g}.py'
    trader.write_text(configured)
    manifest = {
        'source': str(SOURCE.relative_to(ROOT)), 'source_sha256': digest,
        'configured_sha256': hashlib.sha256(configured.encode()).hexdigest(),
        'day': args.day, 'start_tte_days': days,
        'parameter_changes': ['START_TTE_DAYS'],
        'comparison_scope': 'post-competition expiry sensitivity, not original submitted results',
    }
    trader.with_suffix('.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Configured day {args.day}: TTE={days:g}; manifest={trader.with_suffix(".json")}', flush=True)
    return subprocess.call(['./scripts/cargo_local.sh', 'run', '--', '--trader', str(trader),
                            '--dataset', 'round4', '--day', str(args.day), '--products', 'full'], cwd=BACKTESTER)


if __name__ == '__main__':
    raise SystemExit(main())
