"""Shared release allowlist; excludes environments, secrets and validation output."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROOT_FILES=('.gitignore','AGENTS.md','README.md','CHANGELOG.md','VALIDATION.md','LICENSE','launch.py','requirements.txt','requirements-dev.txt','run-math-utils.bat','run-math-utils.sh','module-checksums.json','protected-module-checksums.json')
EXCLUDED={'.git','.venv','venv','env','node_modules','__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.cache','.codex','.agents','.github','.devcontainer','validation-results','tmp'}
DEV_ONLY={'integration_setup.py','wire_ml_integration.py','refine_ml_integration.py','vendor_ml_browser.py','finalize_ml_release.py'}
def retained(path):
    rel=path.relative_to(ROOT)
    if EXCLUDED.intersection(rel.parts) or path.name in DEV_ONLY:return False
    if path.suffix in ('.pyc','.pyo','.tmp','.log','.tgz','.zip','.mp4','.png') and 'assets' not in rel.parts and 'vendor' not in rel.parts:return False
    if path.name.startswith('.env') or path.name in ('settings.json','config.toml'):return False
    return True
def files():
    paths=[ROOT/name for name in ROOT_FILES]
    paths += [p for folder in ('landing','modules','tests') for p in (ROOT/folder).rglob('*') if p.is_file() and retained(p)]
    return sorted(set(paths))
