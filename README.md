# Math Utils 1.2.0

Four locally runnable mathematical applications, on independent ports:

1. **Distributed Memory Architecture Atlas** — the existing distributed-memory laboratories.
2. **Markov Chain Explorer** — the existing Python engine and 2D/3D interface.
3. **Sₙ Explorer WebUI** — the existing permutation and dihedral-group interface.
4. **ML Knowledge Graph** — the supplied fork, with additive local CSV import, 2D/3D constellations, directed relations, graph/cellular persistent homology and export.

The first three modules are preserved byte-for-byte from the start of this integration, including pre-existing Sₙ work.

## Start

Requires Python 3.10+. Run `run-math-utils.bat` on Windows, `sh run-math-utils.sh` on macOS/Linux, or `python launch.py`.

The launcher creates/reuses the root `.venv` and checks requirements.txt. Initial dependency installation requires internet; installed applications require no hosted service. ML Knowledge Graph's browser libraries are included locally. Node is not required for interactive use. Stop with Ctrl+C.

| Surface | Default URL |
|---|---|
| Landing | http://127.0.0.1:8000 |
| Memory Atlas | http://127.0.0.1:8001 |
| Markov | http://127.0.0.1:8002 |
| Sₙ | http://127.0.0.1:8003 |
| ML Knowledge Graph | http://127.0.0.1:8004 |

Use `python launch.py --port 9000 --no-browser` for another consecutive range. `/api/status` on the landing origin lists four modules and readiness. ML exposes `/api/health`. `--skip-install` uses the current interpreter, useful for testing an extracted copy with an already-provisioned Python environment.

## CSV and TDA

Open **Settings → Import CSV / TDA**. **Download CSV template** provides a ZIP with `nodes.csv` and `edges.csv`. Select both, review mappings and diagnostics, and apply. Failed/canceled imports preserve the active graph. Single adjacency, node-only and edge-only CSVs are also supported.

Relation, directedness, legacy weight, strength, confidence, distance, sign and evidence_count remain independent. Arbitrary properties, Notion IDs, URLs and supplied provenance are retained. Browser-local snapshots survive reload. Controls include 2D/3D layouts, adaptive labels, semantic axes, relation filters, recursive traversal, gravity, filtration, area filling, JSON export and PNG capture. **Open this graph in ML explorer** loads the same graph in the fork's original interface.

TDA implements the supplied graph filtration and independent quadrilateral 2-cells over F₂: persistence intervals, Betti curves and Euler characteristic. It is not general simplicial TDA. Read `modules/ml-knowledge-graph/docs/INTEGRATION.md` for compatibility decisions and bounds.

## Structure

```text
math-utils/
├── launch.py
├── landing/
├── modules/
│   ├── distributed-memory-architecture-atlas/
│   ├── markov-chain-explorer-python-v2.0.0/
│   ├── s_n_explorer_web/
│   └── ml-knowledge-graph/
│       ├── app.py
│       ├── backend/
│       ├── js/
│       ├── constellation/
│       ├── reference/csv-importer/
│       ├── vendor/
│       ├── tests/
│       └── UPSTREAM.md
├── tests/
├── module-checksums.json
├── protected-module-checksums.json
├── requirements.txt
└── VALIDATION.md
```

## Validate and package

Use the root `.venv` Python and run suites separately to avoid vendored test-name collisions:

```text
python -B -X utf8 -m pytest -q -p no:cacheprovider tests/test_launcher.py
python -B -X utf8 -m pytest -q -p no:cacheprovider modules/distributed-memory-architecture-atlas/tests
python -B -X utf8 -m pytest -q -p no:cacheprovider modules/markov-chain-explorer-python-v2.0.0/tests
python -B -X utf8 -m pytest -q -p no:cacheprovider modules/ml-knowledge-graph/tests
node --test modules/ml-knowledge-graph/reference/csv-importer/tests/*.test.cjs
python -B tests/check_sources.py
python -B tests/build_release.py
```

Run Sₙ tests **from `modules/s_n_explorer_web`**: `../../.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider tests` on Windows; use `../../.venv/bin/python` on POSIX.

The release is `math-utils-v1.2.0-ml-knowledge-graph.zip`, with an adjacent SHA-256 sidecar and release-verification.json. Environments, Git metadata, installed Node packages, caches, logs and validation artifacts are excluded. Golden fixtures are included. Windows is the validated host; other operating systems require their own runtime validation.

The optional video CLI starts the Python backend automatically, accepts an existing backend via `--url`, and accepts `MATH_UTILS_PYTHON` to select Python. Its Node/browser/ffmpeg dependencies are optional developer tools.
