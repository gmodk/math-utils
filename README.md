# Math Utils

Math Utils gathers the existing mathematical explorer projects behind one local landing page while preserving every module's own interface, mathematics, routes, assets, and behavior.

## Included applications

1. **Distributed Memory Architecture Atlas 2.1.0** — the five distributed-memory approaches in one complete suite: combinatorial, spectral-hypergraph, probabilistic, sheaf-theoretic, and information-theoretic. The original geometry, graph/TDA, recovery, diagnostic, and cryptography laboratories are included.
2. **Markov Chain Explorer — Python Edition 2.0.0** — the Python numerical backend, unchanged prebuilt JavaScript interface, CSV workflows, stochastic calculations, and interactive 2D/3D weighted hypergraphs.
3. **Sₙ Explorer WebUI** — the Python group-theory engine and original web interface for permutations, dihedral groups, subgroups, quotients, Cayley tables, and conjugacy classes.
4. **Correlation & Regression Explorers** — all eleven self-contained statistical-geometry explorers and their mathematical documentation.

The applications remain isolated under `modules/`. The root integration layer only launches them and provides navigation, so their original root-relative API and asset paths do not collide.

## Start the complete platform

Requires Python 3.10 or newer.

### Windows

Double-click:

```text
run-math-utils.bat
```

### macOS or Linux

```bash
./run-math-utils.sh
```

Or on any platform:

```bash
python launch.py
```

The first launch creates one shared `.venv`, installs the numerical dependencies, starts every module, and opens the landing page at `http://127.0.0.1:8000`. Later launches reuse the environment.

Internet access is required for initial installation and any later required dependency updates. Node.js and npm are not required at runtime.

Stop the entire platform with `Ctrl+C` in the terminal that started it.

## Ports

| Surface | Default URL |
| --- | --- |
| Math Utils landing page | `http://127.0.0.1:8000` |
| Distributed Memory Architecture Atlas | `http://127.0.0.1:8001` |
| Markov Chain Explorer | `http://127.0.0.1:8002` |
| Sₙ Explorer WebUI | `http://127.0.0.1:8003` |
| Correlation & Regression Explorers | `http://127.0.0.1:8004` |

To use another consecutive port range:

```bash
python launch.py --port 9000
```

This puts the landing page on `9000` and the four applications on `9001` through `9004`.

Use `python launch.py --no-browser` to start without opening a browser window. Use `--host 0.0.0.0` only when you deliberately want the services reachable from other devices on the same network.

## Project structure

```text
math-utils/
├── launch.py
├── landing/
├── modules/
│   ├── distributed-memory-architecture-atlas/
│   ├── markov-chain-explorer-python-v2.0.0/
│   ├── s_n_explorer_web/
│   └── regression_geometry_explorers/
├── tests/
├── requirements.txt
├── run-math-utils.bat
├── run-math-utils.sh
├── CHANGELOG.md
└── VALIDATION.md
```

Each module retains its own README and technical documentation.

## Development validation

From the project root:

```bash
python -m pip install -r requirements-dev.txt
python -B -X utf8 -m pytest -q -p no:cacheprovider tests
python -B tests/check_sources.py
```

The original test suites can also be run independently from their module directories.

## Rebuilt integration (1.1.0)

The launcher always uses this repository's shared `.venv`, even when invoked from another virtual environment. It installs runtime requirements only when a required distribution is missing or outside its declared version range. Dependency changes may require internet access on a later launch. `--skip-install` is an explicit validation-only bypass that uses the current interpreter.

All five ports are checked before startup. Invalid base ports (outside 1–65531) are rejected. The isolated vendored servers support IPv4 addresses and hostnames; IPv6 binds are rejected. The console reports module readiness, fails after a 60-second health-check deadline, and shuts down the platform if any child exits. The landing page continues checking readiness every five seconds after startup.

For a ZIP extraction on macOS/Linux, `sh run-math-utils.sh` works without changing executable permissions. Windows users can run `run-math-utils.bat`; it prefers `py -3` and falls back to `python`. All wrappers forward launcher arguments. Python 3.10+ must be installed and available to the wrapper. The first setup needs internet access; Node.js is used only for developer syntax checks, never for startup.

### Reproduce validation

After a normal first launch has created `.venv`, stop the platform. Use `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on macOS/Linux as `PYTHON` below (replace the word with the actual path). Run from the repository root:

```text
PYTHON -m pip install -r requirements-dev.txt
PYTHON -B -X utf8 -m pytest -q -p no:cacheprovider tests
PYTHON -B -X utf8 -m pytest -q -p no:cacheprovider modules/distributed-memory-architecture-atlas/tests
PYTHON -B -X utf8 -m pytest -q -p no:cacheprovider modules/markov-chain-explorer-python-v2.0.0/tests
PYTHON -B -X utf8 -m pytest -q -p no:cacheprovider modules/s_n_explorer_web/tests
PYTHON -B tests/check_sources.py
PYTHON -m pip check
PYTHON -B tests/build_release.py
```

Run module suites separately to avoid identically named vendored test modules colliding. The live root test requires ports 8000–8004 to be free; set `MATH_UTILS_TEST_PORT` to choose another range. UTF-8 mode lets the unchanged Markov test read its UTF-8 JavaScript bundle on Windows. The source checker compiles Python in memory and checks external and inline JavaScript with Node; it writes nothing under `modules/`. The statistical bundle contains eleven standalone explorers and has no automated test suite.

`module-checksums.json` records every retained module file's original path, byte size and SHA-256. `validation-results/` contains the test XML, static-check counts and tested dependency versions. `tests/build_release.py` packages only the listed integration files and retained content, verifies archive CRCs and every member's bytes, and emits a checksum sidecar and `release-verification.json` outside the ZIP (avoiding a self-referential archive hash).

