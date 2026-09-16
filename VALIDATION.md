# Validation — Math Utils 1.2.0

Windows; Python 3.12; Node 24.19.0. Initial validation was performed 2026-09-15 and final diff review on 2026-09-16 local time. `PY` below means `.venv/Scripts/python.exe -B -X utf8`; commands run at repository root unless stated otherwise.

## Automated results

| Command | Final result |
|---|---|
| `PY -m pytest -q -p no:cacheprovider tests/test_launcher.py` | 10 passed |
| `PY -m pytest -q -p no:cacheprovider modules/distributed-memory-architecture-atlas/tests` | 23 passed |
| `PY -m pytest -q -p no:cacheprovider modules/markov-chain-explorer-python-v2.0.0/tests` | 11 passed; 2 deprecation warnings |
| From `modules/s_n_explorer_web`: `../../.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider tests` | 49 passed |
| `PY -m pytest -q -p no:cacheprovider modules/ml-knowledge-graph/tests` | 36 passed; 2 deprecation warnings |
| `node --test modules/ml-knowledge-graph/reference/csv-importer/tests/*.test.cjs` | 26 passed |
| `PY -m pip check` | No broken requirements |

**155 tests passed**: 129 Python and 26 original importer tests. Earlier runs also recorded JUnit XML in `validation-results/ml-integration/`; final review counts above come from fresh console runs. The supplied fork had no test suite; its new API tests, browser checks and original video example are covered below.

Warnings concern Starlette's HTTPX test-client integration and AnyIO's BlockingPortal alias. Intermediate failures: Sₙ collected from root had two import errors; its correct working directory passed 49 tests. A root readiness probe timed out during concurrent software-rendered video capture; after capture the unchanged suite passed. An expanded parity normalizer initially dropped the numeric components.edges field; fixing the test harness resolved it. During final diff review, a new alias-isolation test showed that `Source URL` was also inferred as content `url`; strict semantic matching fixed it before the 36-test pass. These failures are not counted as successful runs.

## Acceptance matrix

| Requirement | Evidence |
|---|---|
| Four modules; fourth ID and port offset 4 | Registry test and live /api/status: four ready |
| Real readiness | /api/health parses bundled data, validates cached positions against exact node IDs, and checks required assets; invalid/missing-asset tests return 503 |
| Preserve other modules | 173 starting file hashes match; all suites pass; all three UIs opened |
| Canonical templates | CSV/ZIP content types, attachment names, exact headers, example rows, download and round-trip import tested |
| CSV modes | Separate nodes/edges; single adjacency, node-only and edge-only files tested |
| Errors | Empty/malformed/ragged CSV, duplicate headers/conflicting IDs, missing endpoints, invalid booleans/numbers/evidence counts, constrained relations, quoted commas/newlines |
| Independent semantics and provenance | Normalization/model/projection/export tests, including zero force weight and strict URL/source URL isolation; browser evidence inspection and JSON download readback |
| Preview failure preserves graph | Invalid directed/strength row displayed row/column messages, disabled Apply, retained the valid four-node graph |
| Exploration | Browser 2D/3D, search, upstream/downstream, semantic/hierarchical/cluster/radial layouts, adaptive labels/density, relation evidence |
| Every deterministic source TDA method | Eight committed golden fixtures compare actual original JS with Python: filtration, faces, independent boundaries, persistence, analyze and components |
| Other source math | Weights, four force steps, metrics and deterministic layouts compared; relative tolerance 1e-11/absolute 1e-12 for floating-point arithmetic |
| TDA controls | Enable/disable, epsilon 0/1, fill on/off, all six field choices, strength/distance ordering; square β1=1 unfilled and 0 filled |
| Export/reload | Browser JSON downloaded/read back; four nodes/edges and measurements retained; snapshot survives reload and opens in fork UI |
| Fork video API | Original 12-action example executed; 14 captured PNG frames encoded into MP4; exit 0 |
| Offline ML runtime | Pinned local Three/KaTeX/Marked; CSP limits executable resources and API connections to local origin |
| Provenance/license | Original MIT retained; UPSTREAM.md records fork/upstream/commit/date and importer licensing evidence; notices retained |
| Source/static | `PY tests/check_sources.py`; final result in validation-results/ml-integration/static.json |
| ZIP/extraction | `PY tests/build_release.py` and `PY tests/verify_release.py`; final results in release-verification.json and validation-results/ml-integration/extraction.json |

Golden fixtures cover triangle, filled/partial square, equal-weight ties, parallel edges, isolated/empty graphs and a complete 14-node graph reaching the original 800-face bound. Each test executes unchanged original JS, compares its saved golden, then compares Python; tests never generate goldens. The supplied independent quadrilateral-cell method remains limited; no roadmap mathematics was added.

## Browser and optional video workflow

Platform command: `PY launch.py --port 8800 --no-browser`. In-app browser checks opened ML from the landing link, downloaded the template ZIP, uploaded its files, previewed/applied, used the controls above, inspected/exported and reloaded. A malformed second import kept the valid graph. Atlas, Markov and Sₙ roots rendered. Final review reloaded the cached 2,081-node graph, confirmed canonical schema help, switched 3D→2D→3D, enabled topology and area filling, and found no browser warnings/errors. The 2026-09-16 restart again showed all four ready and 2,081 cached positions; the additive CSV control and help rendered. Some original fork toolbar controls are outside a narrow browser pane; a temporary 1440×900 desktop viewport was used and then reset.

The iframe ZIP click did not emit the automation download event. Browser download-media succeeded; independent HTTP checks verified headers/content. The actual browser JSON export was found in Downloads and verified. These are separate delivery/content checks.

Development setup: `pnpm install --ignore-scripts --lockfile=false` in the ML module, then `node modules/ml-knowledge-graph/node_modules/ffmpeg-static/install.js`. Network access required sandbox escalation. The existing package declarations/lockfile stayed unchanged. Optional binaries/node_modules are excluded from the release.

With `PUPPETEER_EXECUTABLE_PATH=C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`:

```text
node modules/ml-knowledge-graph/scripts/render-graph-video.mjs --script modules/ml-knowledge-graph/scripts/video-script.example.json --fps 1 --width 640 --height 360 --output validation-results/ml-integration/fork-video.mp4
```

The sandbox browser launch failed; an approved retry outside it succeeded. The 13.3-second timeline produced 14 frames, verifying runScript/seek/captureFrame/getDuration and the 12 supplied actions. Software capture averaged about 11.3 seconds per frame. This does not test every possible video script.

## Preservation and release checks

The starting tree already had Sₙ/dihedral, AGENTS.md and validation changes. They were preserved. protected-module-checksums.json records the actual starting Atlas (43), Markov (112) and Sₙ (18) files; module-checksums.json records the final retained tree.

Every old-module file was byte-verified against the recoverable backup `C:\Users\danie\AppData\Local\Temp\math-utils-regression-backup-yjumumei\regression_geometry_explorers.zip`. The new module started and automated checks passed before removal; the resolved removal target was verified inside this repository.

`math-utils-v1.2.0-ml-knowledge-graph.zip` has a complete member listing, CRC/byte checks and module-hash checks. Environments, Git, node_modules, local settings/secrets, caches, logs, prior archives and generated test artifacts are excluded. Required runtime assets and golden fixtures are included. SHA-256 and size stay beside the ZIP to avoid a self-referential checksum.

The extraction verifier creates a fresh temporary source tree, checks hashes, launches all five servers, requires four modules ready, checks each root, downloads/imports templates, computes filled-square TDA, round-trips export, shuts down and checks released ports. It uses the provisioned Python interpreter with --skip-install; it does not perform a fresh dependency installation.

## Limits and untested scope

- Fork force coordinates use seeded positions and exact pairwise forces instead of randomized D3 Barnes–Hut forces. Coordinates differ. The shipped bundled graph uses a validated precomputed cache; an uncached 2,081-node exact layout took about 41 seconds during review, so synchronous layout requests can block the UI on similarly large uncached graphs.
- Unicode locale-dependent tie ordering is not a cross-locale coordinate guarantee. Golden coordinate fixtures use ASCII; original IDs/fields themselves are preserved.
- Storage is local to an origin/port and subject to browser quota/policy. Moving ports does not move IndexedDB data. Save errors are surfaced.
- Imported betweenness is not synthesized; bundled values remain. No general simplicial TDA, cohomology or circular coordinates are claimed.
- Importer MIT licensing relies on explicit user confirmation. Supplied files had no copyright holder/commit; no attribution is invented.
- macOS/Linux, fresh dependency installation, very large adversarial CSVs and every possible video action combination were not tested. No commit is created.
