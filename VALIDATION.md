# Validation — three-module Math Utils

## Current platform (2026-09-18)

Math Utils now registers exactly `memory-atlas`, `markov`, and `symmetric-groups`, in that order. The landing page uses port 8000, and the modules keep ports 8001, 8002, and 8003. The Correlation & Regression Explorers application, its dedicated tests, fixtures, backup, and old distributable ZIP have been removed. The landing page continues to render module cards from `/api/status`; its loading placeholder contains three cards.

No files in the three retained module trees were edited for this removal. Root requirements are unchanged: Atlas requires `cryptography`, Markov requires `fastapi`, `networkx`, `numpy`, `pydantic`, `scipy`, and `uvicorn`; the launcher requires `packaging`. Development tests require `pytest` and `httpx`.

## Executed checks

Commands were run from the repository root unless otherwise noted, using the shared Windows virtual environment:

```powershell
$env:MATH_UTILS_TEST_PORT = '9100'
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=validation-results/pytest-three-root tests
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=validation-results/pytest-three-atlas modules/distributed-memory-architecture-atlas/tests
.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=validation-results/pytest-three-markov modules/markov-chain-explorer-python-v2.0.0/tests
Push-Location modules/s_n_explorer_web
../../.venv/Scripts/python.exe -B -X utf8 -m pytest -q -p no:cacheprovider --basetemp=../../validation-results/pytest-three-sn tests
Pop-Location
.venv/Scripts/python.exe -B -X utf8 tests/check_sources.py
node --check landing/app.js
.venv/Scripts/python.exe -u -B -X utf8 launch.py --no-browser --port 8000
```

| Check | Result |
|---|---|
| Root integration and preservation tests | 11 passed |
| Atlas tests | 23 passed |
| Markov tests | 11 passed, with two dependency deprecation warnings from installed Starlette/AnyIO test-client code |
| Sₙ tests | 53 passed |
| In-memory Python compilation and source protection | 42 Python files compiled; exact paths and SHA-256 hashes of 170 retained module files matched |
| Landing JavaScript syntax | `node --check landing/app.js` passed; Node is used only for this optional validation, not installation or runtime |
| Live platform | Landing page and status endpoint on 8000, module roots and health endpoints on 8001–8003, and landing assets all returned HTTP 200 |
| `/api/status` | Exactly three ready entries: `memory-atlas:8001`, `markov:8002`, `symmetric-groups:8003` |
| Fourth process | Startup printed three module launches; connection to 127.0.0.1:8004 was refused with Windows socket error 10061 |
| Browser landing page | Three rendered module cards titled Distributed Memory Architecture Atlas, Markov Chain Explorer, and Sₙ Explorer WebUI |
| Browser console | No warning or error messages captured in the local landing tab |

The initial Windows Chrome control attempt could not establish that window's URL, so the browser check used a fresh in-app tab opened directly at `http://127.0.0.1:8000/`. The tab's rendered DOM contained exactly three module cards, and its captured console warnings/errors list was empty.

## Protected-file baseline

`tests/fixtures/protected-module-files.json` and `module-checksums.json` record the same exact 170 retained module paths and SHA-256 hashes. The preservation test and `tests/check_sources.py` compare the entire path-to-hash mapping, including added or removed paths. The release builder compares the archived module path set to the manifest and verifies every byte and hash.

The prior 173-entry protection fixture listed six absent documentation paths and eight Sₙ files whose committed bytes differed from that older snapshot. The prior 180-entry release manifest also listed 15 files from the removed module, plus absent paths and changed hashes. The new 170-file manifest was generated from the clean pre-removal Git checkout of the retained trees; none of those trees was edited in this change. The historical `validation-results/dihedral-baseline.json` has had its 15 deleted-module entries removed and is not used as the active protection source.

The release command is:

```powershell
.venv/Scripts/python.exe -B -X utf8 tests/build_release.py
```

It writes `math-utils-rebuilt.zip`, `math-utils-rebuilt.zip.sha256`, and `release-verification.json`. The archive excludes the historical `validation-results/` directory and the deleted backup. The release verification JSON records its final byte size, SHA-256, entry count, and module-file verification count.
