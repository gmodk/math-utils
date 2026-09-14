"""Launch the Math Utils platform and its unchanged explorer modules.

The integration layer deliberately runs each application on its own origin.
That preserves the modules' existing root-relative assets and API endpoints.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version, PackageNotFoundError
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
from threading import Timer
import time
from typing import Callable
from urllib.error import URLError
from urllib.request import urlopen
import venv
import webbrowser


ROOT = Path(__file__).resolve().parent
LANDING = ROOT / "landing"
MODULES = ROOT / "modules"
ENVIRONMENT = ROOT / ".venv"


@dataclass(frozen=True)
class ModuleSpec:
    id: str
    title: str
    description: str
    port_offset: int
    directory: Path
    health_path: str
    command: Callable[[str, int], list[str]]
    environment: Callable[[str, int], dict[str, str]]


def environment_python() -> Path:
    if os.name == "nt":
        return ENVIRONMENT / "Scripts" / "python.exe"
    return ENVIRONMENT / "bin" / "python"


def python_command(*arguments: str) -> list[str]:
    return [sys.executable, *arguments]


def inherited_environment(**updates: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update(updates)
    environment["PYTHONUNBUFFERED"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUTF8"] = "1"
    return environment


def module_specs() -> tuple[ModuleSpec, ...]:
    return (
        ModuleSpec(
            id="memory-atlas",
            title="Distributed Memory Architecture Atlas",
            description="Five mathematical lenses with geometry, graph/TDA, recovery, diagnostics, and cryptography laboratories.",
            port_offset=1,
            directory=MODULES / "distributed-memory-architecture-atlas",
            health_path="/api/catalog",
            command=lambda _host, _port: python_command("app.py"),
            environment=lambda host, port: inherited_environment(
                ATLAS_HOST=host,
                ATLAS_PORT=str(port),
            ),
        ),
        ModuleSpec(
            id="markov",
            title="Markov Chain Explorer",
            description="Homogeneous and non-homogeneous chains, Poisson kernels, stochastic analysis, and interactive weighted hypergraphs.",
            port_offset=2,
            directory=MODULES / "markov-chain-explorer-python-v2.0.0",
            health_path="/api/health",
            command=lambda host, port: python_command(
                "app.py",
                "--host",
                host,
                "--port",
                str(port),
                "--no-browser",
            ),
            environment=lambda _host, _port: inherited_environment(),
        ),
        ModuleSpec(
            id="symmetric-groups",
            title="Sₙ Explorer WebUI",
            description="Permutations, cycle structure, Cayley tables, dihedral groups, subgroups, quotients, and conjugacy classes.",
            port_offset=3,
            directory=MODULES / "s_n_explorer_web",
            health_path="/api/health",
            command=lambda _host, _port: python_command("app.py"),
            environment=lambda host, port: inherited_environment(
                HOST=host,
                PORT=str(port),
            ),
        ),
        ModuleSpec(
            id="statistical-geometry",
            title="Correlation & Regression Explorers",
            description="Eleven self-contained visual laboratories for correlation, covariance, PCA, regression, regularization, and Bayesian geometry.",
            port_offset=4,
            directory=MODULES / "regression_geometry_explorers",
            health_path="/",
            command=lambda host, port: python_command(
                "-m",
                "http.server",
                str(port),
                "--bind",
                host,
            ),
            environment=lambda _host, _port: inherited_environment(),
        ),
    )


def ensure_environment(skip_install: bool) -> None:
    if skip_install:
        return

    if Path(sys.prefix).resolve() != ENVIRONMENT.resolve():
        executable = environment_python()
        if not executable.exists():
            print("Creating the shared Math Utils Python environment…")
            venv.EnvBuilder(with_pip=True).create(ENVIRONMENT)
        arguments = [str(executable), "-X", "utf8", str(Path(__file__).resolve()), *sys.argv[1:]]
        os.execv(str(executable), arguments)

    if not requirements_satisfied():
        print("Installing or updating the shared numerical runtime…")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")]
        )


def requirements_satisfied() -> bool:
    try:
        from packaging.requirements import Requirement
        for line in (ROOT / "requirements.txt").read_text().splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            requirement = Requirement(line)
            if requirement.marker and not requirement.marker.evaluate():
                continue
            if version(requirement.name) not in requirement.specifier:
                return False
        return True
    except (ImportError, PackageNotFoundError):
        return False


def ensure_project_layout() -> None:
    required = [LANDING / name for name in ("index.html", "app.js", "styles.css", "favicon.svg")]
    for spec in module_specs():
        required.append(spec.directory)
        required.append(spec.directory / ("index.html" if spec.port_offset == 4 else "app.py"))
    required.append(MODULES / "markov-chain-explorer-python-v2.0.0/frontend_dist/index.html")
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"The platform package is incomplete; missing: {joined}")


def ensure_ports_available(host: str, ports: list[int]) -> None:
    check_host = host
    unavailable: list[int] = []
    for port in ports:
        family = socket.AF_INET6 if ":" in check_host else socket.AF_INET
        with socket.socket(family, socket.SOCK_STREAM) as probe:
            if os.name == "nt":
                probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            try:
                probe.bind((check_host, port))
            except OSError:
                unavailable.append(port)
    if unavailable:
        values = ", ".join(str(port) for port in unavailable)
        raise RuntimeError(f"These ports are already in use: {values}. Choose another --port.")


def browser_host(host: str) -> str:
    return "127.0.0.1" if host in {"0.0.0.0", "::"} else host


def is_ready(host: str, port: int, path: str) -> bool:
    try:
        with urlopen(f"http://{browser_host(host)}:{port}{path}", timeout=0.7) as response:
            return response.status == 200
    except (OSError, URLError):
        return False


class LandingHandler(SimpleHTTPRequestHandler):
    server_version = "MathUtils/1.0"

    def __init__(self, *arguments, host: str, base_port: int, **keywords):
        self.platform_host = host
        self.base_port = base_port
        super().__init__(*arguments, directory=str(LANDING), **keywords)

    def log_message(self, format_string: str, *arguments) -> None:
        if os.environ.get("MATH_UTILS_QUIET") != "1":
            super().log_message(format_string, *arguments)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.split("?", 1)[0] == "/api/status":
            self.send_status()
            return
        super().do_GET()

    def send_status(self) -> None:
        modules = []
        public_host = browser_host(self.platform_host)
        for spec in module_specs():
            port = self.base_port + spec.port_offset
            modules.append(
                {
                    "id": spec.id,
                    "title": spec.title,
                    "description": spec.description,
                    "port": port,
                    "url": f"http://{public_host}:{port}/",
                    "ready": is_ready(self.platform_host, port, spec.health_path),
                }
            )
        payload = json.dumps(
            {
                "platform": "Math Utils",
                "version": "1.1.0",
                "modules": modules,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def start_modules(host: str, base_port: int) -> list[subprocess.Popen]:
    processes: list[subprocess.Popen] = []
    try:
        return _start_modules(host, base_port, processes)
    except BaseException:
        stop_modules(processes)
        raise


def _start_modules(host: str, base_port: int, processes: list[subprocess.Popen]) -> list[subprocess.Popen]:
    for spec in module_specs():
        port = base_port + spec.port_offset
        process = subprocess.Popen(
            spec.command(host, port),
            cwd=spec.directory,
            env=spec.environment(host, port),
        )
        processes.append(process)
        print(f"  {spec.title}: http://{browser_host(host)}:{port}")
    return processes


def stop_modules(processes: list[subprocess.Popen]) -> None:
    for process in processes:
        if process.poll() is None:
            process.terminate()
    deadline = time.monotonic() + 4.0
    for process in processes:
        if process.poll() is not None:
            continue
        timeout = max(0.0, deadline - time.monotonic())
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the unified Math Utils explorer platform.")
    parser.add_argument("--host", default=os.getenv("MATH_UTILS_HOST", "127.0.0.1"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MATH_UTILS_PORT", "8000")),
        help="Landing-page port; module ports use the next four consecutive values.",
    )
    parser.add_argument("--no-browser", action="store_true", help="Do not open the landing page automatically.")
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip the first-run dependency check (intended for validation environments).",
    )
    arguments = parser.parse_args()

    if not 1 <= arguments.port <= 65531:
        parser.error("--port must be between 1 and 65531 (five consecutive ports are required)")
    if ":" in arguments.host:
        parser.error("Use an IPv4 address or hostname; the vendored servers require IPv4")

    ensure_project_layout()
    ports = [arguments.port + offset for offset in range(5)]
    ensure_ports_available(arguments.host, ports)
    ensure_environment(arguments.skip_install)

    processes: list[subprocess.Popen] = []
    server: ThreadingHTTPServer | None = None
    browser_timer: Timer | None = None

    def request_shutdown(_signum, _frame) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, request_shutdown)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, request_shutdown)
    try:
        print("Starting Math Utils modules:")
        processes = start_modules(arguments.host, arguments.port)
        handler = partial(LandingHandler, host=arguments.host, base_port=arguments.port)
        server = ThreadingHTTPServer((arguments.host, arguments.port), handler)
        landing_url = f"http://{browser_host(arguments.host)}:{arguments.port}"
        print(f"\nMath Utils landing page: {landing_url}")
        print("Press Ctrl+C to stop the complete platform.")
        deadline = time.monotonic() + 60
        pending = list(module_specs())
        while pending:
            for spec, process in zip(module_specs(), processes):
                if process.poll() is not None:
                    raise RuntimeError(f"{spec.title} exited during startup ({process.returncode})")
            for spec in pending[:]:
                if is_ready(arguments.host, arguments.port + spec.port_offset, spec.health_path):
                    print(f"  Ready: {spec.title}")
                    pending.remove(spec)
            if pending and time.monotonic() >= deadline:
                raise RuntimeError("Timed out waiting for: " + ", ".join(spec.title for spec in pending))
            if pending:
                time.sleep(0.2)
        if not arguments.no_browser:
            browser_timer = Timer(1.2, lambda: webbrowser.open(landing_url))
            browser_timer.start()
        server.timeout = 0.5
        while True:
            server.handle_request()
            for spec, process in zip(module_specs(), processes):
                if process.poll() is not None:
                    raise RuntimeError(f"{spec.title} exited ({process.returncode})")
    except KeyboardInterrupt:
        print("\nStopping Math Utils…")
    finally:
        if browser_timer is not None:
            browser_timer.cancel()
        if server is not None:
            server.server_close()
        stop_modules(processes)


if __name__ == "__main__":
    main()
