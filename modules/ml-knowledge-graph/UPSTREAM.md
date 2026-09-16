# Source provenance

- Fork: https://github.com/gmodk/ml-knowledge-graph.git
- Upstream: https://github.com/the-palindrome/ml-knowledge-graph (confirmed by the user).
- Imported branch: `csv-template-importer`.
- Imported commit: `c7e20bf18490f3f1ba0afd8f3181f595e0407ca7` (`dynamic opacity updated`).
- Import date: 2026-09-15.
- Source checkout: `C:\Users\danie\OneDrive\_projects\ml-knowledge-graph`.
- Fork license: MIT, Copyright (c) 2026 Palindrome Labs; LICENSE retained verbatim.
- No upstream remote was configured in the supplied checkout. No upstream code was substituted.

## CSV importer

- Supplied source: `C:\Users\danie\OneDrive\_wip\notion constellation\universal-csv-graph-importer-project`.
- Package version: 2.0.0; no Git metadata or commit/tag supplied.
- License: MIT, explicitly confirmed by the user. The supplied source had no LICENSE or named copyright holder. No holder has been invented.
- Unchanged source, examples and tests are retained under `reference/csv-importer/` as a numerical oracle; a LICENSE and this integration attribution are additions.
- Original topology SHA-256: `88e7e5d49851544cbc57110a736efd6316bb2ec7d911c25d6953062789678edd`.
- Original CSV core SHA-256: `ee283ebd553b3f45547440394ca58c9781c0fc66b7b5aa93c154b4487d890c2e`.

## Integration changes

The original UI, static paths, bundled ML data and browser video API remain. A settings entry opens the additional CSV constellation and can load that snapshot into the original explorer. A local Python API now performs CSV parsing, graph analysis, layouts, force updates and cellular persistence. Browser libraries are pinned and vendored. CSV schemas preserve distinct relation/measurement/provenance fields. See `docs/INTEGRATION.md` for compatibility decisions and numerical limitations.
