"""Isolated local/spec validation. Immutable per-task baseline; no app or DB access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'docs/implementation'
PACK = Path.home() / '.codex/.chatgpt-projects/g-p-696486f280d081918418aa6ea3658d1c/deliverables/4-me-not-v0.4-codex-task-pack'
ZIP = PACK / 'reference/4-me-not-collab-v0.4.zip'
FILES = {
    'W43-01': ['backend/requirements.txt', 'backend/services/memory_contracts.py',
        'backend/services/schema_roles.py', 'tests/memory/test_schema_roles.py',
        'docs/implementation/validate_local_tasks.py', 'docs/implementation/test_local_validation.py'],
    'W42-01': ['backend/services/memory_features.py', 'tests/memory/test_memory_features.py'],
    'W31-01': ['backend/services/source_evidence.py', 'tests/memory/test_source_evidence.py'],
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def snapshot():
    result = subprocess.run(['git', '-c', 'core.quotepath=false', 'ls-files', '-z',
        '--cached', '--others', '--exclude-standard'], cwd=REPO, capture_output=True, check=True)
    return {p: digest(REPO / p) for p in sorted(set(result.stdout.decode('utf-8').split('\0')))
            if p and (REPO / p).is_file()}

def differences(before, after):
    return sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))

def unexpected_changes(before, after, allowed):
    return [p for p in differences(before, after) if p not in allowed]

def write_new(path, data):
    # An earlier result is history, even when validation failed.
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(data)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('task', choices=FILES)
    parser.add_argument('--begin', action='store_true')
    args = parser.parse_args()
    baseline = OUT / (args.task + '-start.json')
    if args.begin:
        write_new(baseline, json.dumps({'task':args.task, 'files':[
            {'path':p, 'sha256':h} for p,h in snapshot().items()]}, indent=2))
        return 0
    start = {f['path']:f['sha256'] for f in json.loads(baseline.read_text(encoding='utf-8-sig'))['files']}
    run = Path(tempfile.mkdtemp(prefix='4-me-not-' + args.task + '-'))
    tag = run.name.rsplit('-', 1)[-1]
    evidence = OUT / (args.task + '-validation-' + tag + '.json')
    allowed = set(FILES[args.task]) | {
        'docs/implementation/' + args.task + suffix for suffix in ('-start.json','-report.md','-contract.md')}
    allowed.add(evidence.relative_to(REPO).as_posix())
    before = snapshot()
    zip_hash = digest(ZIP)
    expected_zip = json.loads((OUT/'W30-01-evidence.json').read_text(encoding='utf-8-sig'))['archive_sha256']
    if zip_hash != expected_zip:
        raise RuntimeError('REFERENCE_ZIP_CHANGED')
    with zipfile.ZipFile(ZIP) as archive:
        archive.extractall(run)
    spec = run/'4-me-not-collab-v0.4'
    shutil.copyfile(spec/'contracts/memory.schema.json', spec/'w30-02-baseline-memory.schema.json')
    overlay = REPO/'docs/spec/v0.4'
    for path in overlay.rglob('*'):
        if path.is_file():
            target = spec/path.relative_to(overlay)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
    env = {**os.environ, 'PYTHONUTF8':'1', 'PYTHONDONTWRITEBYTECODE':'1',
        'PYTHONPATH':os.pathsep.join([str(Path(tempfile.gettempdir())/'4-me-not-W30-02-deps'), str(REPO)]),
        'MEMORY_SPEC_ROOT':str(spec), 'W30_REPO':str(REPO)}
    results = []
    for name, cwd, argv in (
        ('local', REPO, ['-m','unittest','discover','-s','tests/memory','-p','test_*.py','-v']),
        ('runner', REPO, ['-m','unittest','discover','-s','docs/implementation','-p','test_local_validation.py','-v']),
        ('active', spec, ['-m','unittest','discover','-s','tests','-p','test_*.py','-v']),
        ('baselines', spec, ['scripts/check_baselines.py']),
        ('whitespace', REPO, None),
    ):
        command = [sys.executable,'-X','utf8',*argv] if argv else ['git','diff','--check']
        proc = subprocess.run(command, cwd=cwd, env=env, capture_output=True, encoding='utf-8', errors='replace')
        log = OUT / (args.task + '-' + name + '-' + tag + '.log')
        write_new(log, proc.stdout + proc.stderr)
        allowed.add(log.relative_to(REPO).as_posix())
        counts = [int(n) for n in re.findall(r'Ran (\d+) tests? in', proc.stdout+proc.stderr)]
        results.append({'layer':name,'cwd':str(cwd),'command':command,'exit_code':proc.returncode,
            'counts':counts,'log':str(log)})
        print(name, proc.returncode, counts)
    after = snapshot()
    changes = differences(start, after)
    unexpected = unexpected_changes(start, after, allowed)
    during = unexpected_changes(before, after, {p for p in allowed if p.endswith('.log')})
    zip_unchanged = zip_hash == digest(ZIP)
    passed = not unexpected and not during and zip_unchanged and all(r['exit_code']==0 for r in results)
    write_new(evidence, json.dumps({'task':args.task,'passed':passed,'baseline':str(baseline),
        'spec_root':str(spec),'zip_sha256':zip_hash,'zip_unchanged':zip_unchanged,
        'planned_changes': [p for p in changes if p in allowed], 'unexpected_changes':unexpected,
        'unexpected_during_run':during,'results':results,
        'tested_files':{p:after[p] for p in sorted(allowed) if p in after and not p.endswith('.log')},
        'overlay_hashes':{p.relative_to(overlay).as_posix():digest(p) for p in overlay.rglob('*') if p.is_file()},
        'acceptance':'local/spec only; no app, DB, Gate or authentication integration'}, ensure_ascii=False, indent=2))
    print('unexpected:', unexpected, 'during:', during, 'evidence:', evidence)
    return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
