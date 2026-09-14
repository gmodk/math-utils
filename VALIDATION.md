# Validation — Math Utils 1.1.0

Date: 2026-09-14. Host: Windows; Python 3.12; Node.js 24.19.0 used only for syntax validation.

## Final results

| Suite | Result |
| --- | --- |
| Root integration, including concurrent platform and shutdown | 10 passed |
| Distributed Memory Architecture Atlas | 23 passed |
| Markov Chain Explorer | 11 passed, 2 deprecation warnings |
| S_n Explorer WebUI | 8 passed |
| Total | 52 passed |

The statistical bundle has no automated suite. All eleven explorer pages were checked over HTTP. All discovered Python suites were run; Markov frontend source provides build/typecheck scripts, not a separate automated test suite. Its prebuilt runtime was preserved and syntax-checked without rebuilding it.

Machine-readable suite results are in `validation-results/{root,atlas,markov,sn}.xml`; exact installed versions are in `validation-results/dependencies.txt`. `pip check` reported no broken requirements.

The initial Markov run had one Windows CP1252 decoding failure while reading its UTF-8 JavaScript bundle. Re-running the unchanged suite with Python `-X utf8` passed all eleven tests. Its two remaining warnings concern Starlette's HTTPX test-client deprecation and the AnyIO BlockingPortal alias. No vendored file was edited to resolve the failure.

## Concurrent live verification

The root integration test launched the actual root launcher with `--no-browser` using the shared `.venv`, with all five servers running concurrently:

| Port | Paths | Result |
| --- | --- | --- |
| 8000 | `/`, `/styles.css`, `/app.js`, `/favicon.svg`, `/api/status` | HTTP 200 |
| 8001 Atlas | `/`, `/api/catalog` | HTTP 200 |
| 8002 Markov | `/`, `/api/health` | HTTP 200 |
| 8003 S_n | `/`, `/api/health` | HTTP 200 |
| 8004 Regression | `/` and all eleven `explorer_*.html` paths | HTTP 200 |

`/api/status` returned exactly four modules, all with `ready: true`. Atlas's catalog and the static regression index are their existing readiness probes; no new module endpoints were introduced.

A second launcher was rejected on the occupied ports without disturbing the running platform. Sending Windows CTRL_BREAK to the launcher returned exit code 0, and all five ports were available afterward. Unit tests additionally verified partial-startup cleanup, incompatible dependency detection and invalid-port rejection.

## Static and preservation checks

- 37 Python files compiled successfully in memory, including all retained module Python, root launcher and validation/integration helpers. No module bytecode was generated.
- 7 JavaScript/MJS files passed Node syntax checks, including landing, Atlas, S_n, Markov's prebuilt runtime and PostCSS configuration.
- 20 inline executable script blocks across HTML files passed syntax checks, including the regression explorers. TypeScript/TSX is preserved source, not the runtime and was not rebuilt.
- The initial inventory recorded 180 retained module files: Atlas 43, Markov 112, S_n 10, regression 15. Final path-set and SHA-256 comparison matched all 180; no additions, removals or changed bytes under `modules/`.
- `module-checksums.json` contains initial per-file sizes and hashes. `tests/check_sources.py` reproduces the comparison and static checks; its counts are in `validation-results/static.json`.
- No Git repository metadata was present, so preservation was verified against the initial full file inventory rather than Git history.

## Release verification

`tests/build_release.py` creates `math-utils-rebuilt.zip` with a single `math-utils/` top-level directory. It excludes environments, dependency directories, caches, bytecode, Git metadata, temporary files and existing archives through an explicit file/folder allowlist and exclusion filter. Every archive member is compared byte-for-byte with its retained source, all 180 archived module hashes are compared to the initial baseline, and the ZIP CRC test must pass.

The final archive byte size, SHA-256, entry count and verification outcome are in the adjacent `release-verification.json`; `math-utils-rebuilt.zip.sha256` provides a standard checksum sidecar. These files remain outside the archive to avoid self-referential checksums.

## Startup and validation scope

Extract the ZIP. On Windows run `run-math-utils.bat`. On macOS/Linux run `sh run-math-utils.sh`. Or run `python launch.py --no-browser` with Python 3.10+ available. Open `http://127.0.0.1:8000`; Ctrl+C stops the complete platform. The first run installs dependencies into `.venv`; subsequent runs check and reuse it. Node is not required at runtime.

Actual runtime and shutdown verification was performed on Windows. macOS/Linux startup was reviewed but not executed on those operating systems. Browser rendering and graphical interactions inside the vendored applications were not automated; this report establishes tests, syntax, HTTP readiness and byte preservation. The landing page retains its responsive layout and adds narrow-screen wrapping and continuous status polling.
