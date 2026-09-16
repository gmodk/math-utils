"""Compile Python in memory and verify the protected module sources, without a JS runtime.

JavaScript syntax and behavior are verified by loading the six local ES modules in
browser validation. This command does not claim to parse JavaScript.
"""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'__pycache__', '.pytest_cache', '.venv', 'node_modules'}


def main():
    baseline = json.loads((ROOT / 'tests/fixtures/regression-protected-files.json').read_text(encoding='utf-8'))
    expected = {item['path']: item['sha256'] for item in baseline}
    actual = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for directory in (ROOT / 'modules').iterdir() if directory.name != 'regression_geometry_explorers'
              for p in directory.rglob('*') if p.is_file() and not SKIP.intersection(p.parts) and p.suffix not in ('.pyc', '.pyo')}
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
