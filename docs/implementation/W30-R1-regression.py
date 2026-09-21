"""Run the actual W30 validators in synthetic repositories, never mutate user code.

The tiny synthetic specification exercises runner exit handling, not the 114
contract tests or application acceptance. All historical outputs stay untouched.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[2]
OUTPUT = Path(__file__).resolve().parent
PWSH = Path('C:/Users/keima/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
DEPS = Path(tempfile.gettempdir()) / '4-me-not-W30-02-deps'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_files():
    paths = set()
    for name in ('W30-01-evidence.json', 'W30-07-validation.json'):
        record = json.loads((OUTPUT/name).read_text(encoding='utf-8-sig'))
        for item in record.get('code_files', []):
            paths.add(REPO/item['path'])
        for item in record.get('overlay_files', []):
            paths.add(REPO/'docs/spec/v0.4'/item['path'])
        archive = record.get('source_zip')
        if archive:
            paths.add(Path(archive))
    # Preserve every prior report, evidence JSON and log, including first failures.
    for n in range(1, 8):
        paths.update(p for p in OUTPUT.glob(f'W30-0{n}-*')
                     if p.suffix in {'.json', '.log', '.md'})
    return {str(p): sha(p) for p in sorted(paths)}


def run_case(root, task, case):
    repo = root/task/case
    impl = repo/'docs/implementation'
    impl.mkdir(parents=True)
    source_script = OUTPUT/f'{task}-validate.ps1'
    runner = impl/source_script.name
    runner.write_bytes(source_script.read_bytes())
    # Build only the overlay file names consumed by this exact runner.
    block = re.search(r'\$overlayFiles = @\((.*?)\n\)', runner.read_text(), re.S)[1]
    for relative in re.findall(r"'([^']+)'", block):
        target = repo/'docs/spec/v0.4'/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('{}\n' if target.suffix == '.json' else '\n', encoding='utf-8')
    code = repo/'sample.py'
    code.write_text('value = 1\n', encoding='utf-8')
    baseline_hash = sha(code)
    if case == 'before':
        code.write_text('value = 2\n', encoding='utf-8')
    archive = repo/'synthetic-spec.zip'
    mutation = f"Path({str(code)!r}).write_text('value = 2\\n', encoding='utf-8')" if case == 'during' else 'pass'
    probe = ('import unittest\nfrom pathlib import Path\n'
             'class Probe(unittest.TestCase):\n'
             '    def test_runner_probe(self):\n'
             f'        {mutation}\n'
             '        self.assertTrue(True)\n')
    with zipfile.ZipFile(archive, 'w') as z:
        for directory in ('docs', 'fixtures'):
            z.writestr('4-me-not-collab-v0.4/'+directory+'/.keep', '')
        for name, data in {
            'contracts/memory.schema.json':'{}',
            'tests/test_probe.py':probe,
            'scripts/check_baselines.py':"print('Synthetic baseline probe only')\n",
        }.items():
            z.writestr('4-me-not-collab-v0.4/'+name, data)
    baseline = {'archive_sha256':sha(archive),
                'code_files':[{'path':'sample.py', 'sha256':baseline_hash}]}
    (impl/'W30-01-evidence.json').write_text(json.dumps(baseline), encoding='utf-8')
    command = [str(PWSH), '-NoProfile', '-File', str(runner), '-Python', sys.executable,
               '-Dependencies', str(DEPS), '-SourceZip', str(archive)]
    proc = subprocess.run(command, cwd=repo, capture_output=True, text=True, encoding='utf-8')
    log = proc.stdout + proc.stderr
    (impl/'runner.log').write_text(log, encoding='utf-8')
    evidence = json.loads((impl/f'{task}-validation.json').read_text(encoding='utf-8-sig'))
    historical = len(evidence['code_changed_since_W30_01'])
    during = len(evidence['code_changed_during_run'])
    expected = {'clean':(0, 0, 0), 'before':(1, 1, 0), 'during':(1, 1, 1)}[case]
    assert (proc.returncode, historical, during) == expected, (task, case, log)
    assert all(r['exit_code'] == 0 for r in evidence['results']), evidence
    assert f'Existing code changed since W30-01: {historical}' in log
    assert f'Existing code changed during run: {during}' in log
    if historical:
        assert 'Changed since W30-01: sample.py' in log
        assert evidence['code_changed_since_W30_01'][0]['path'] == 'sample.py'
    if during:
        assert 'Changed during run: sample.py' in log
        assert evidence['code_changed_during_run'][0]['path'] == 'sample.py'
    assert json.loads((impl/'W30-01-evidence.json').read_text()) == baseline
    assert code.read_text(encoding='utf-8') == ('value = 1\n' if case == 'clean' else 'value = 2\n')
    assert sha(runner) == sha(source_script)
    print(f'{task} {case}: exit={proc.returncode}, since={historical}, during={during}', flush=True)
    return {'task':task, 'case':case, 'exit_code':proc.returncode,
            'historical_count':historical, 'during_count':during,
            'runner_sha256':sha(runner), 'command':command, 'cwd':str(repo),
            'log':str(impl/'runner.log'), 'log_text':log,
            'evidence_path':str(impl/f'{task}-validation.json'), 'evidence':evidence}


def main():
    before = protected_files()
    root = Path(tempfile.mkdtemp(prefix='4-me-not-W30-R1-'))
    results = [run_case(root, f'W30-0{n}', case)
               for n in range(2, 8) for case in ('clean', 'before', 'during')]
    after = protected_files()
    assert before == after, 'Protected real repo/history/archive changed'
    record = {'review':'R1', 'scope':'Synthetic runner regression only; no application acceptance',
              'synthetic_root':str(root), 'cases_passed':len(results),
              'protected_files_unchanged':True, 'protected_file_hashes':before, 'results':results}
    (OUTPUT/'W30-R1-regression.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'PASS: {len(results)} cases; {len(before)} protected files unchanged', flush=True)


if __name__ == '__main__':
    main()
