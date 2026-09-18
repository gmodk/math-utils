# Changelog

## Unreleased — three-module platform (2026-09-18)

- Intentionally remove the Correlation & Regression Explorers application, its tests, fixtures, and release artifacts without replacing it.
- Keep Atlas, Markov, and Sₙ in their existing order on ports 8001–8003; the landing page remains on 8000.
- Update launcher, landing copy, protected-file checks, tests, and release packaging for exactly three modules.

## Unreleased — Sₙ composition animation (2026-09-18)

- Add a Python-computed, one-based `i → τ(i) → σ(τ(i))` trace to the existing composition response.
- Add three-lane SVG playback, Cauchy notation, live trace text, example, speed, step, replay, and stop controls in the existing Composition view.
- Preserve current dihedral 2D/3D geometry, polygon selection, camera and label controls, and rotation/reflection animation.
- Add algebraic and HTTP tests for the composition trace and a module-local pytest import path fix.

## Unreleased — four-explorer statistical geometry rebuild (2026-09-16)

- Replace the fourth static server with one FastAPI application on the same port offset, using HOST/PORT and `/api/health`.
- Retain exactly correlation geometry, multiple-regression projection, polynomial bias–variance, and Bayesian posterior geometry.
- Move sampling, statistical formulas, regression, posterior computations, and mathematical plot data into deterministic Python engines with finite typed APIs.
- Preserve source controls, metric labels, plot surfaces, and quick-reference sections in a shared local dark Math Utils shell.
- Add cancellation/debouncing, explicit input/numerical errors, keyboard labels/focus, mobile layouts, and local-only asset policy.
- Add mathematical, API, source-contract and protected-file tests. Camera/highlight changes reuse regression results.
- Keep the incoming eight deletions (seven retired experiences plus the replaced correlation page) and preserve the new correlation source in a backup.
- Preserve all 173 pre-rebuild source files in the other three modules. Historical checksum differences are not silently rebaselined.
- Retain the source's Bayesian slider normalization (declared 0.8 becomes 0.81 in Chromium). Seeded redraws intentionally stabilize scatter and Monte Carlo estimates; numerical failures now produce errors instead of zero-coefficient fallbacks.
- Release packaging and backup removal remain pending browser approval. No new ZIP has been built.

## 1.0.0 — 2026-09-14

### Added

- Unified Math Utils launcher and responsive landing page.
- Shared first-run Python environment for all server-backed modules.
- Independent process and port isolation for the four original applications.
- Live landing-page readiness indicators.
- One-command Windows, macOS, and Linux startup.
- Integration tests and validation documentation.

### Integrated unchanged

- Distributed Memory Architecture Atlas 2.1.0 with all five distributed-memory approaches and laboratories.
- Markov Chain Explorer Python Edition 2.0.0 with its prebuilt JavaScript UI and interactive 3D hypergraph.
- Sₙ Explorer WebUI with its Python group-theory engine.
- Correlation & Regression Explorers bundle with all eleven standalone explorers.

No module interface, mathematical method, API endpoint, route, or internal source file was rewritten by the integration layer.

## 1.1.0 — 2026-09-14

- Rebuilt and validated the outer integration layer; all 180 vendored module files remain byte-identical.
- Always select the repository's shared `.venv`; check installed distribution versions before installing requirements.
- Correct the development manifest to include runtime dependencies and HTTPX.
- Reject invalid port ranges and unsupported IPv6 binds; check the actual bind address for occupied ports.
- Clean up children after partial startup failures, wait after forced shutdown, and stop the platform if a child exits.
- Report each module ready at startup, with a bounded startup timeout.
- Keep landing readiness polling active after startup and preserve keyboard focus during updates; improve narrow card wrapping.
- Add Windows Python-launcher fallback and UTF-8 startup mode.
- Add live integration checks, source/inline-JavaScript validation, retained-file checksums, and a verified clean ZIP builder.
