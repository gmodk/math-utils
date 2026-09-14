# Markov Chain Explorer — Python Edition

A local stochastic-process laboratory with a Python numerical engine, an unchanged JavaScript interface, and a genuine interactive 3D weighted hypergraph.

## Start it

Requires Python 3.10 or newer. Node.js and npm are **not required** to run the explorer.

```bash
python launch.py
```

On Windows, double-click `run-markov-explorer.bat`. On macOS/Linux, run `./run-markov-explorer.sh`. The first launch creates `.venv`, installs the Python packages, starts the API at `http://127.0.0.1:8765`, and opens the browser. Later launches reuse the environment. Internet access is needed only for that first Python-package installation.

For a manual installation:

```bash
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Use `python app.py --no-browser`, `--port 9000`, or `--host 0.0.0.0` when needed.

## Included workflows

- Unified CSV import with delimiter detection, quoted/multiline parsing, field mapping, metadata preservation, validation-before-apply, and included examples.
- Homogeneous chains and ordered time-indexed non-homogeneous kernels.
- Cyclic or capped Poisson count-chain generation, lambda schedules, and Poissonization of an existing kernel.
- Editable transition matrices, row normalization, optional Dirichlet smoothing from counts, and CSV/JSON/PNG export.
- Distribution evolution, exact paths, finite-horizon hitting and first-passage probabilities, expected hitting times, discounted rewards, and deterministic Monte Carlo occupancy.
- Stationary laws, communicating/closed classes, transient and recurrent states, periods, absorbing states, entropy rate, Dobrushin contraction, reversibilized spectral gap, dropout sensitivity, Forman curvature, and GF(2) clique homology.
- Local named snapshots containing chain data, camera, manual positions, layout, threshold, Bayesian settings, and Poisson settings.
- 2D SVG hypergraph with pan, extreme zoom, and draggable states.
- Real WebGL 3D hypergraph: drag the background to rotate, scroll/pinch to zoom, right-drag to pan, and drag state spheres to reposition them. Shift-click still edits the target set.

## Architecture

- `backend/engine.py` — all Markov-chain mathematics (NumPy, SciPy, NetworkX).
- `backend/api.py` — typed FastAPI endpoints and static-UI serving.
- `frontend_dist/` — prebuilt JavaScript UI served by Python; no Node runtime.
- `frontend_source/` — optional React/Three.js source for UI development only.
- `examples/` — homogeneous and non-homogeneous unified CSV datasets.
- `tests/` — numerical and API regression tests.
- `docs/` — theory, CSV contract, architecture, and importer adaptation notes.

The frontend only parses CSV text for schema review, manages interaction state, and renders results. Validation and every stochastic, linear-algebraic, graph, simulation, and topology calculation are requested from the Python API.

## API

- `GET /api/health`
- `POST /api/analyze`
- `POST /api/poisson`
- `POST /api/normalize`

FastAPI also exposes interactive API documentation at `/docs`.

## Development and tests

```bash
python -m pip install -r requirements-dev.txt
pytest -q
```

The prebuilt frontend is ready to run. Rebuilding it is optional and is the only workflow that uses a JavaScript package manager:

```bash
cd frontend_source
pnpm install
pnpm run typecheck
pnpm run build
```

## Privacy

The app binds to `127.0.0.1` by default. Imported projects are processed by the Python service on your own computer. Browser snapshots use local storage; no application database or external analytics service is used.
