# Changelog

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
