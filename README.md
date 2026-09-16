# Math Utils

Math Utils launches four isolated mathematical applications from one local landing page:

1. Distributed Memory Architecture Atlas.
2. Markov Chain Explorer.
3. Sₙ Explorer WebUI.
4. Correlation & Regression Explorers: **Correlation as Geometry**, **Multiple Regression as Projection onto a Subspace**, **Bias–Variance Tradeoff and Polynomial Complexity**, and **Bayesian Linear Regression Posterior Geometry**.

The first three applications retain their existing implementation files. Statistical geometry now uses one FastAPI application with Python numerical engines and a local HTML/CSS/vanilla-JavaScript interface. Each application keeps a separate process and origin.

## Startup

Requires Python 3.10 or newer. From this directory:

```text
python launch.py
```

Windows: `run-math-utils.bat`. macOS/Linux: `sh run-math-utils.sh`.

The launcher creates and reuses one `.venv`, installs root runtime requirements only when needed, checks all five ports, starts the applications, waits for readiness, and opens the landing page. Initial dependency installation or required updates may need internet access. Installed applications and their assets run locally without a frontend build or runtime internet dependency. No Node.js or npm is required.

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
| Statistical geometry | 8004 |

`--port` selects the landing port; the four applications use the next four ports. Ctrl+C stops the platform. IPv4 addresses/hostnames are supported. `--host 0.0.0.0` exposes the applications to your network. `--skip-install` is a validation-only bypass that uses the current interpreter.

## Statistical geometry rebuild

The fourth module keeps ID `statistical-geometry`, title `Correlation & Regression Explorers`, and port offset 4. Its Python app receives `HOST`/`PORT` and exposes `/api/health`, `/api/catalog`, and four typed `/api/v1/{explorer}/analyze` endpoints. All statistical calculations and generated plot coordinates run in Python. Browser code handles input, request cancellation, formatting, drawing, and camera/pixel transforms.

The four original control definitions, metrics, chart surfaces, and explanatory sections are preserved. See [module README](modules/regression_geometry_explorers/README.md) for the seed protocol, mathematical conventions, and deliberate differences. The theory Markdown and Word documents are retained as historical broader references; they do not introduce additional explorer experiences.

## Validation

Use `.venv/Scripts/python.exe` on Windows or `.venv/bin/python` on macOS/Linux. Install development requirements with that interpreter and `-m pip install -r requirements-dev.txt`.

```text
python -B -X utf8 -m pytest -q -p no:cacheprovider tests
python -B -X utf8 -m pytest -q -p no:cacheprovider modules/distributed-memory-architecture-atlas/tests
python -B -X utf8 -m pytest -q -p no:cacheprovider modules/markov-chain-explorer-python-v2.0.0/tests
```

Run Sₙ's tests from `modules/s_n_explorer_web` with `../../.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider tests` (use `.venv/bin/python` on Unix).

Set `MATH_UTILS_TEST_PORT=9100` when default ports are occupied. Use a fresh `--basetemp` path if the host's default pytest temporary directory is inaccessible. Run suites separately to avoid their module-name collisions.

`python -B tests/check_sources.py` compiles Python in memory and verifies all 173 protected files against the pre-rebuild baseline. Browser loading and control checks verify the new JavaScript syntax and behavior without a JavaScript command-line runtime. Exact executed commands, results, limitations, and browser observations are in [VALIDATION.md](VALIDATION.md).

## Review and release status

The source backup is retained in `backups/four-explorer-rebuild/`. Do not delete it or create a release archive before browser approval. The seven retired pages and replaced old correlation page were already deleted in the incoming working tree. The replacement correlation source was untracked; its bytes were captured before migration.

The old `module-checksums.json`, ZIP/checksum, `release-verification.json`, and historical validation artifacts predate this rebuild. They are not evidence for it. The old archive builder still uses the historical manifest; reconcile release manifests and packaging only after browser approval. No new archive was produced.
