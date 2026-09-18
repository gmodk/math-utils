# Validation — Four-explorer rebuild

## Sₙ composition merge — 2026-09-18

The module-local Sₙ suite passed **53 tests**. Atlas passed **23 tests**; Markov passed **11 tests** with two existing dependency deprecation warnings. In-memory compilation passed for **48 Python sources**. The root suite ran **99 tests: 97 passed, 2 failed**. One failure is the pre-existing small-scale full-rank predictor check in the unrelated regression engine; the other is the historical protected-file baseline, which already lists six absent documents and omits the untracked Sₙ `AGENTS.md`, and now also detects the intentional composition edits. Neither test nor unrelated module was changed to hide those failures.

`tests/check_sources.py` fails on that same historical protected-file comparison. A module-local `conftest.py` fixes `symmetric_group` discovery from the root, and qualified test imports avoid the regression application's `app` module-name collision. Root and Sₙ tests now collect together (**152 tests**); the suites remain independently runnable as documented.

The complete platform started on ports 9100–9104. The landing page, status endpoint, and all four module roots returned HTTP 200; all four readiness flags were true. Through port 9103, `/api/compose` returned `(213)` and the three expected one-based rows for `(231) ∘ (132)`. Browser checks exercised the example, Previous, Replay, Next, Play all/Stop, Fast speed, direct trace selection, repeated Compose clicks, and changing `n` during playback. The dihedral browser checks exercised polygon choice, 2D/3D mode, zoom in/out/reset, numeric/Greek labels, rotation/replay, and reflection selection; no browser warnings or errors were reported. Reduced-motion behavior is implemented but still requires a browser session with that preference enabled for a manual check.

A clean `math-utils-composition-animation.zip` was built from the launcher, landing page, modules, tests, and documentation, with CRC and byte-for-byte entry verification. It excludes Git metadata, `.venv`, `node_modules`, caches, compiled Python, backups, the reference ZIP, and temporary validation outputs. The historical `tests/build_release.py` cannot verify this checkout until `module-checksums.json` is reconciled, so the archive's integrity is reported by its separate SHA-256 sidecar rather than by the stale module manifest.

Commands run from the repository root, except the indicated module command:

```powershell
Push-Location modules/s_n_explorer_web
../../.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider tests
Pop-Location
$env:MATH_UTILS_TEST_PORT='9100'
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=validation-results/pytest-root-composition-1 tests
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=validation-results/pytest-atlas-composition-1 modules/distributed-memory-architecture-atlas/tests
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=validation-results/pytest-markov-composition-1 modules/markov-chain-explorer-python-v2.0.0/tests
.venv/Scripts/python.exe -u -B -X utf8 launch.py --no-browser --port 9100
```


Date: 2026-09-16. Branch: `regression-exploerers-alignment`. Starting HEAD: `c19b3f97cf564f9c9dc199b1dc4294f980d3b28a`. No commit or archive created.

## Validated results

| Check | Result |
|---|---|
| Root suite, including statistical engines/API/source contracts and concurrent full-platform test | **65 passed**, 2 dependency deprecation warnings |
| Atlas tests, unchanged | **23 passed** |
| Markov tests, unchanged | **11 passed**, 2 dependency deprecation warnings |
| Sₙ tests, unchanged, from its module directory | **49 passed** |
| Total | **148 passed** |
| Python compileall | Passed |
| In-memory source checker | 45 Python files compiled; 173 protected source files match |
| Full platform, ports 9100–9104 | Every application returns HTTP 200; all four readiness flags true |
| Browser interaction | All 19 sliders and all 3 resample buttons exercised |
| Responsive layout | Four pages checked at 390×844; document scroll width equals client width |
| Original controls/metrics/plots/guides | All source-contract comparisons pass |
| Other module implementations | No changed, added, or removed source files against the pre-rebuild baseline |

The root XML is `validation-results/four-explorer-root.xml`. The old XML/static/ZIP artifacts describe previous work and are not this rebuild's evidence.

## Exact executed test commands

From the repository root, using the shared environment:

```powershell
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider tests/test_regression_engines.py
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider tests/test_regression_engines.py tests/test_regression_api.py
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider tests/test_regression_engines.py tests/test_regression_api.py tests/test_regression_preservation.py
```

Checkpoint results: engine 37 passed; engine/API 51 passed, repeated after each explorer migration; final focused suite 54 passed after static-contract and preservation checks were added.

Final complete root invocation (the inline environment selection avoids changing the user's shell settings):

```powershell
.venv/Scripts/python.exe -B -X utf8 -c "import os,pytest; os.environ['MATH_UTILS_TEST_PORT']='9100'; raise SystemExit(pytest.main(['-q','-p','no:cacheprovider','--basetemp=backups/four-explorer-rebuild/pytest-root-final','--junitxml=validation-results/four-explorer-root.xml','tests']))"
```

Use a new `--basetemp` directory when reproducing; pytest manages its contents.

```powershell
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=backups/four-explorer-rebuild/pytest-atlas-1 modules/distributed-memory-architecture-atlas/tests
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=backups/four-explorer-rebuild/pytest-markov-1 modules/markov-chain-explorer-python-v2.0.0/tests
```

From `modules/s_n_explorer_web`:

```powershell
../../.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider tests
```

From root:

```powershell
.venv/Scripts/python.exe -m compileall -q launch.py modules
.venv/Scripts/python.exe -B tests/check_sources.py
.venv/Scripts/python.exe -u -B -X utf8 launch.py --no-browser --port 9100
```

## Browser observations

The four pages were navigated and tested through the browser UI. Keyboard ArrowRight/ArrowLeft exercised every slider; all resample buttons were clicked. Each page returned to its Ready state, displayed finite metrics, and drew all source plot surfaces. Multiple-regression yaw, pitch and highlight changed the view with the same seed and identical metrics. Bayesian tau/x0 retained the sample seed; data-generation controls and resample advanced it.

All six ES modules loaded and executed, establishing browser syntax compatibility without Node/npm. Console inspection returned no JavaScript warnings or errors. An initial automatic `/favicon.ico` request returned 404; explicit local SVG favicon links were added to all five pages. The final pass reloaded the pages successfully; the server recorded `/static/favicon.svg` as HTTP 200, all four analysis requests succeeded, and console inspection remained clean. The in-app browser does not expose a complete Network-panel export; local asset responses are checked by API tests/server access logs and a same-origin Content Security Policy. Do not interpret that as a captured browser HAR.

Desktop screenshots confirmed dark plot backgrounds and visible colored labels/curves. Mobile checks found no document-level horizontal overflow; reference tables scroll within their panels. Keyboard focus is visible. Reduced-motion CSS is present; OS-level reduced-motion preference switching and screen-reader narration were not separately exercised.

## Mathematical scope and tolerances

- Correlation angles and two-asset variance use source formulas. The seeded 450-pair empirical correlation is tested at rho −0.95, −0.5, 0, 0.2, 0.95 with absolute tolerance 0.12 for finite-sample variation.
- Multiple regression is compared with NumPy least squares; normal-equation residuals are within 1e-10. SST decomposition and squared-cosine identity are checked.
- Polynomial degrees 1, 4 and 12 (including n=15 and n=100 cases) match explicit regularized normal equations at coefficient atol 1e-7/rtol 1e-6. Training and noiseless-grid MSE, 80 predictions, variance denominator 79 and sigma² are checked.
- Bayesian means/covariance match closed form at 1e-12; predictive variance includes noise; all covariance matrices are symmetric positive definite. Contours have squared Mahalanobis distance 4 within 1e-9.
- All engines repeat exactly for identical complete requests in this numerical runtime. This does not promise bitwise identity across different NumPy/BLAS/platform versions.
- The original JavaScript engines were inspected and formula/reference tests were written before removing them. Original unseeded JavaScript outputs were not compared bit-for-bit with Python; sampling now follows the documented deterministic protocol.

## Behavior differences and retained ambiguities

1. Local Python service is required; direct filesystem opening no longer computes results.
2. Samples use explicit seeds. Correlation redraws reuse the underlying sample; bias–variance repeats the same Monte Carlo sample ensemble for a fixed request. Those originally varied on every calculation.
3. Singular/ill-conditioned solves return structured errors rather than source zero-coefficient/tiny-pivot fallbacks. Stable NumPy solves can differ in last bits from hand-written elimination.
4. The source's Bayesian sigma attributes remain min=0.15, max=2.5, step=0.02, declared value=0.8. Browser inspection confirms effective initial value **0.81**, matching normal range-input normalization. API default remains 0.8.
5. Colors, axis tick presentation, camera arrow styling and annotation placement changed for the dark theme. Mathematical plot arrays and chart meanings are retained.
6. Original explanatory sections remain unchanged. Added notes clarify the source's beta-only interval, OLS comparison, two-SD joint contours, determinant indicator, and numerical regularization.
7. Theory Markdown/Word documents remain byte-identical historical references to the former broader collection; they are not the current four-explorer catalog.

## Environment failures resolved or isolated

- Initial `.venv` lacked pytest/httpx; installed only the already-declared development requirements.
- The host's existing pytest temporary directory denied access even outside the sandbox; a fresh repository-local test temporary directory resolved it.
- Default ports 8000–8004 were already occupied by an existing platform. Validation used 9100–9104 and left the existing platform running. **The rebuilt API on actual port 8004 has not yet been verified; restarting the existing platform awaits the user's choice.** The root registry test confirms port_offset=4 and HOST/PORT propagation.
- Running Sₙ tests from root failed imports; running its unchanged suite from its module directory passed all 49 tests.
- Remaining warnings are dependency deprecations from Starlette's HTTPX test-client and the AnyIO BlockingPortal alias; no unrelated dependency migration was made.

## Preservation, rollback and release gate

Incoming user state had eight deleted legacy HTML files and one untracked replacement correlation source. These were preserved. The eight paths represent seven retired experiences and replacement of the old correlation-vectors page; this rebuild did not perform the incoming deletions.

`tests/fixtures/regression-source-contract.json` records source hashes, controls, metrics, plots and quick-reference contents. `tests/fixtures/regression-protected-files.json` captures the actual pre-rebuild 173 protected source files. Tests compare both their path set and bytes, excluding generated bytecode. The old `module-checksums.json` already disagreed with the incoming checkout and has not been silently rewritten.

`backups/four-explorer-rebuild/` retains the original four HTML files, module index/README, incoming Git status, protected hashes and migration helpers. Rollback must restore that captured working state, including the replacement correlation source and prior deletions, rather than reset blindly to HEAD.

No new ZIP, checksum, commit, or backup deletion was made. Browser approval is required before release packaging or backup removal, per the user's explicit instruction. The historical archive builder/manifests still require reconciliation in that later release step.
