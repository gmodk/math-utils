# Changelog

## 2.0.0 — 2026-09-14

- Preserved the existing explorer layout, styling, controls, and import/export workflows.
- Replaced browser-side mathematics with a typed FastAPI numerical service.
- Added NumPy/SciPy/NetworkX implementations for stochastic analysis, graph structure, topology, simulation, robustness, Poisson generation, and matrix exponential Poissonization.
- Added a prebuilt static frontend served directly by Python, so Node.js/npm are not runtime requirements.
- Replaced the pseudo-3D projection with a real Three.js WebGL scene supporting orbit rotation, zoom, pan, draggable states, weighted directed transitions, hyperedge regions, and PNG capture.
- Added a one-command cross-platform Python launcher and backend/API regression tests.
- Added runtime-bundle regression coverage for the Python endpoints and genuine WebGL 3D controls.

## 1.0.0 — 2026-09-13

- Created the original Markov Chain Explorer and universal Markov CSV workflow.
