"""Compile Python in memory and verify all retained module paths and bytes.

JavaScript syntax and behavior are verified separately in the browser.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'__pycache__', '.pytest_cache', '.venv', 'node_modules'}


def main():
    baseline = json.loads((ROOT / 'tests/fixtures/protected-module-files.json').read_text(encoding='utf-8'))
    expected = {item['path']: item['sha256'] for item in baseline}
    assert len(expected) == len(baseline), 'Duplicate protected path'
    actual = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (ROOT / 'modules').rglob('*')
              if p.is_file() and not SKIP.intersection(p.relative_to(ROOT).parts)
              and p.suffix not in ('.pyc', '.pyo')}
    assert actual == expected, 'A protected module source or path changed'
    files = [p for folder in ('modules', 'landing', 'tests') for p in (ROOT / folder).rglob('*')
             if p.is_file() and not SKIP.intersection(p.parts)] + [ROOT / 'launch.py']
    python_count = 0
    for path in files:
        if path.suffix == '.py':
            compile(path.read_bytes(), str(path), 'exec')
            python_count += 1
    result = {'protected_module_files': len(actual), 'python_compiled': python_count,
              'javascript_validation': 'Separate browser loading and interaction checks; no Node dependency'}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
