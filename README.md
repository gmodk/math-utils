# Math Utils

Math Utils launches three isolated mathematical applications from one local landing page:

1. Distributed Memory Architecture Atlas.
2. Markov Chain Explorer.
3. Sₙ Explorer WebUI.

Atlas and Markov retain their existing implementation files. The Sₙ module adds an animated permutation-composition trace while preserving its dihedral explorer. Each application keeps a separate process and origin.

## Startup

Requires Python 3.10 or newer. From this directory:

```text
python launch.py
```

Windows: `run-math-utils.bat`. macOS/Linux: `sh run-math-utils.sh`.

The launcher creates and reuses one `.venv`, installs root runtime requirements only when needed, checks all four ports, starts the applications, waits for readiness, and opens the landing page. Initial dependency installation or required updates may need internet access. Installed applications and their assets run locally without a frontend build or runtime internet dependency. No Node.js or npm is required.

```text
python launch.py --no-browser
python launch.py --host 127.0.0.1 --port 9100 --no-browser
```

| Application | Default port |
|---|---:|
| Landing | 8000 |
| Atlas | 8001 |
| Markov | 8002 |
| Sₙ | 8003 |

`--port` selects the landing port; the three applications use the next three ports. Ctrl+C stops the platform. IPv4 addresses/hostnames are supported. `--host 0.0.0.0` exposes the applications to your network. `--skip-install` is a validation-only bypass that uses the current interpreter.

## Sₙ composition animation

The Composition view shows `σ ∘ τ` as `i → τ(i) → σ(τ(i))`. Python computes the one-based trace and adds it to the existing `/api/compose` response. Vanilla browser JavaScript draws and animates the three-lane diagram, with a worked `(231) ∘ (132) = (213)` example and playback controls. The separate dihedral 2D/3D diagrams and controls remain available.

## Validation

Use `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on macOS/Linux. Install development requirements with that interpreter and `-m pip install -r requirements-dev.txt`.

```text
python -B -X utf8 -m pytest -q -p no:cacheprovider tests
python -B -X utf8 -m pytest -q -p no:cacheprovider modules/distributed-memory-architecture-atlas/tests
python -B -X utf8 -m pytest -q -p no:cacheprovider modules/markov-chain-explorer-python-v2.0.0/tests
```

Run Sₙ's tests from `modules/s_n_explorer_web` with `../../.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider tests` (use `.venv/bin/python` on Unix).

Set `MATH_UTILS_TEST_PORT=9100` when default ports are occupied. Use a fresh `--basetemp` path if the host's default pytest temporary directory is inaccessible. Run suites separately to avoid their module-name collisions.

`python -B tests/check_sources.py` compiles Python in memory and compares the paths and SHA-256 hashes of all three retained modules against the protected baseline. Browser loading and control checks verify JavaScript syntax and behavior without a JavaScript command-line runtime. Exact executed commands, results, limitations, and browser observations are in [VALIDATION.md](VALIDATION.md).

## Release

`python -B tests/build_release.py` builds a byte-verified ZIP containing the launcher, landing page, three modules, tests, and current documentation. The archived module paths and hashes must match `module-checksums.json`.
