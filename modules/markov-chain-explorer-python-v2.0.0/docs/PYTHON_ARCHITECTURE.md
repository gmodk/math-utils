# Python/JavaScript architecture

## Runtime boundary

`launch.py` creates a project-local virtual environment on first use. `app.py` then starts Uvicorn, and `backend/api.py` serves both the API and the prebuilt files in `frontend_dist/` from the same origin. This design needs Python at runtime but does not need Node.js, npm, pnpm, a JavaScript server, or a cloud service.

The browser is responsible for interaction and presentation: CSV text parsing for the mapping preview, local snapshots, state selection, filters, SVG rendering, and Three.js rendering. It sends the complete active project plus calculation settings to `POST /api/analyze`. The server returns matrices, diagnostics, probability results, topology, simulation results, curvature, and Python-generated layout coordinates.

## Numerical stack

- NumPy: stochastic vectors, matrices, products, least-squares stationary laws, and GF(2) boundary operations.
- SciPy: matrix exponential for exact finite-state Poissonization, `exp(λ(P-I))`.
- NetworkX: directed reachability and strongly connected components.
- FastAPI/Pydantic: request validation, API schema, and local static-file delivery.

## Endpoints

`POST /api/analyze` is the main pure-analysis endpoint. Its inputs contain the project, active time slice, horizon, target set, reward discount, path, Poisson rate, Bayesian settings, and filtration threshold. It does not mutate server state.

`POST /api/poisson` generates one or more transition kernels and serializes them as transition records. `POST /api/normalize` replaces only the selected kernel, retaining the other time slices for a non-homogeneous project. `GET /api/health` identifies the active engine.

## 3D renderer

The WebGL scene uses perspective projection, lit probability-scaled spheres, curved directed transition tubes, arrowheads, translucent outgoing-support regions, and billboard labels. `OrbitControls` supplies rotation, dolly/zoom, touch gestures, and pan. `DragControls` allows direct state repositioning. Camera state is retained while the analytical response updates.

## Extension point

Add a computation to `backend/engine.py`, serialize its output in `analyze_request`, extend the response contract in `frontend_source/lib/api.ts`, and render it in the existing inspector. This keeps mathematical provenance on the Python side.
