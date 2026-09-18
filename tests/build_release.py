"""Build and byte-verify a clean release from an explicit integration allowlist."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ('AGENTS.md', 'README.md', 'CHANGELOG.md', 'VALIDATION.md', 'launch.py',
         'requirements.txt', 'requirements-dev.txt', 'run-math-utils.bat',
         'run-math-utils.sh', 'module-checksums.json')
FOLDERS = ('landing', 'modules', 'tests')
EXCLUDED = {'.git', '.venv', 'venv', 'env', 'node_modules', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.cache', '.codex', '.agents'}


def main():
    files = [ROOT / name for name in FILES]
    files += [p for folder in FOLDERS for p in (ROOT / folder).rglob('*')
              if p.is_file() and not EXCLUDED.intersection(p.relative_to(ROOT).parts)
              and p.suffix not in ('.pyc', '.pyo', '.tmp', '.log')]
    files.sort()
    archive = ROOT / 'math-utils-rebuilt.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in files:
            info = zipfile.ZipInfo('math-utils/' + path.relative_to(ROOT).as_posix())
            info.create_system = 3
            info.external_attr = (0o100755 if path.suffix == '.sh' else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        assert len(bundle.namelist()) == len(files)
        for path in files:
            assert bundle.read('math-utils/' + path.relative_to(ROOT).as_posix()) == path.read_bytes()
        baseline = json.loads((ROOT / 'module-checksums.json').read_text(encoding='utf-8-sig'))
        assert len({item['path'] for item in baseline}) == len(baseline), 'Duplicate module checksum path'
        archived_modules = {name.removeprefix('math-utils/') for name in bundle.namelist()
                            if name.startswith('math-utils/modules/')}
        assert archived_modules == {item['path'] for item in baseline}, 'Module checksum path set differs from archive'
        for item in baseline:
            assert hashlib.sha256(bundle.read('math-utils/' + item['path'])).hexdigest() == item['sha256']
    result = {'file': archive.name, 'bytes': archive.stat().st_size,
              'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
              'entries': len(files), 'module_files_verified': len(baseline),
              'crc_and_byte_comparison': 'passed'}
    (ROOT / 'math-utils-rebuilt.zip.sha256').write_text(result['sha256'] + '  ' + archive.name + '\n')
    (ROOT / 'release-verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
