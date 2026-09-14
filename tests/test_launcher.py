from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import launch  # noqa: E402


def test_module_registry_is_complete_and_uses_distinct_ports() -> None:
    specs = launch.module_specs()
    assert [spec.id for spec in specs] == [
        "memory-atlas",
        "markov",
        "symmetric-groups",
        "statistical-geometry",
    ]
    assert len({spec.port_offset for spec in specs}) == len(specs)
    assert all(spec.directory.is_dir() for spec in specs)


def test_landing_assets_are_present() -> None:
    assert (launch.LANDING / "index.html").is_file()
    assert (launch.LANDING / "styles.css").is_file()
    assert (launch.LANDING / "app.js").is_file()
    assert (launch.LANDING / "favicon.svg").is_file()

import json
import os
import signal
import socket
import subprocess
import time
from unittest.mock import Mock
from urllib.request import urlopen

import pytest


def test_occupied_port_is_rejected():
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        listener.listen()
        with pytest.raises(RuntimeError, match='already in use'):
            launch.ensure_ports_available('127.0.0.1', [listener.getsockname()[1]])


def test_partial_startup_cleans_children(monkeypatch):
    child = Mock()
    child.poll.return_value = None
    factory = Mock(side_effect=[child, OSError('spawn failed')])
    monkeypatch.setattr(launch.subprocess, 'Popen', factory)
    with pytest.raises(OSError, match='spawn failed'):
        launch.start_modules('127.0.0.1', 8000)
    child.terminate.assert_called_once()
    child.wait.assert_called_once()


def test_dependency_versions_are_checked(monkeypatch):
    monkeypatch.setattr(launch, 'version', lambda name: '0.0.1')
    assert not launch.requirements_satisfied()


def test_shared_environment_is_ready():
    assert launch.requirements_satisfied()


@pytest.mark.parametrize('port', ['0', '65532', '-1'])
def test_invalid_port_fails_before_startup(port):
    result = subprocess.run([sys.executable, str(ROOT / 'launch.py'), '--port', port], capture_output=True, text=True)
    assert result.returncode == 2
    assert 'five consecutive ports' in result.stderr


def test_complete_platform(tmp_path):
    base = int(os.environ.get('MATH_UTILS_TEST_PORT', '8000'))
    launch.ensure_ports_available('127.0.0.1', list(range(base, base + 5)))
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    with (tmp_path / 'platform.log').open('w+', encoding='utf-8') as log:
        process = subprocess.Popen([sys.executable, str(ROOT / 'launch.py'), '--no-browser', '--port', str(base)], cwd=ROOT, env=env, stdout=log, stderr=log, creationflags=flags)
        try:
            deadline = time.monotonic() + 90
            while True:
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(log.read())
                if launch.is_ready('127.0.0.1', base, '/api/status'):
                    break
                assert time.monotonic() < deadline, 'startup timed out'
                time.sleep(0.25)
            for path in ['/', '/styles.css', '/app.js', '/favicon.svg', '/api/status']:
                with urlopen(f'http://127.0.0.1:{base}{path}') as response:
                    assert response.status == 200
            with urlopen(f'http://127.0.0.1:{base}/api/status') as response:
                status = json.load(response)
            assert len(status['modules']) == 4
            assert all(item['ready'] for item in status['modules'])
            for spec in launch.module_specs():
                for path in ['/', spec.health_path]:
                    assert launch.is_ready('127.0.0.1', base + spec.port_offset, path)
            explorers = list((launch.MODULES / 'regression_geometry_explorers').glob('explorer_*.html'))
            assert len(explorers) == 11
            for explorer in explorers:
                assert launch.is_ready('127.0.0.1', base + 4, '/' + explorer.name)
            # An occupied range must reject a second launch without disturbing the first.
            second = subprocess.run([sys.executable, str(ROOT / 'launch.py'), '--no-browser', '--port', str(base)], capture_output=True, text=True, timeout=10)
            assert second.returncode != 0
            assert 'already in use' in second.stderr
            assert process.poll() is None
        finally:
            if process.poll() is None:
                process.send_signal(signal.CTRL_BREAK_EVENT if os.name == 'nt' else signal.SIGTERM)
                process.wait(timeout=15)
        assert process.returncode == 0
    launch.ensure_ports_available('127.0.0.1', list(range(base, base + 5)))
