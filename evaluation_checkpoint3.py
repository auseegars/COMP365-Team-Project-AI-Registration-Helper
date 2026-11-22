# Owner: Jarren Woodward
"""Evaluation Lead: reproducible Checkpoint 3 evidence runner.
Run from repository root: python evaluation_checkpoint3.py
Does not present synthetic tests as real student or production performance.
"""
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results' / 'checkpoint3_evaluation.json'

def command(args):
    p = subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True)
    return {'command': 'python ' + ' '.join(args), 'returncode': p.returncode,
            'stdout': p.stdout.strip()[-3500:], 'stderr': p.stderr.strip()[-1200:]}

def main():
    report = {'created_utc': datetime.now(timezone.utc).isoformat(),
              'data_note': 'Repository unit tests and synthetic demonstration profiles; NOT production AI accuracy.',
              'evaluation_lead': 'Jarren Woodward', 'checks': {}}
    report['checks']['metric_selftest'] = command(['evaluate.py', 'selftest'])
    report['checks']['audit_tests'] = command(['-m', 'pytest', '-q', 'tests/test_degree_audit.py', 'tests/test_real_data.py'])
    if importlib.util.find_spec('ortools') is None:
        report['checks']['schedule_comparison'] = {'status': 'NOT RUN', 'reason': 'OR-Tools dependency not installed; run pip install -r requirements.txt'}
    else:
        report['checks']['schedule_comparison'] = command(['src/schedule/evaluate_schedules.py'])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    for name, result in report['checks'].items():
        status = 'SKIPPED' if result.get('status') == 'NOT RUN' else ('PASS' if result['returncode'] == 0 else 'FAIL')
        print(f'{name}: {status}')
        if result.get('stdout'): print(result['stdout'])
        if result.get('reason'): print(result['reason'])
    print(f'Report saved: {OUT}')
    return 1 if any(r.get('returncode', 0) != 0 for r in report['checks'].values()) else 0

if __name__ == '__main__':
    raise SystemExit(main())
