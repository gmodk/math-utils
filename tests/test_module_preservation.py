"""Protect the exact paths and bytes of the three retained modules."""

from pathlib import Path
import hashlib
import json


ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"
SKIP = {"__pycache__", ".pytest_cache", ".venv", "node_modules"}


def test_retained_modules_have_identical_paths_and_bytes():
    baseline = json.loads((ROOT / "tests/fixtures/protected-module-files.json").read_text(encoding="utf-8"))
    expected = {item["path"]: item["sha256"] for item in baseline}
    assert len(expected) == len(baseline), "Duplicate protected path"
    actual = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in MODULES.rglob("*")
        if path.is_file()
        and not SKIP.intersection(path.relative_to(ROOT).parts)
        and path.suffix not in (".pyc", ".pyo")
    }
    assert actual == expected
