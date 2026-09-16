# Math Utils integration rules

## Scope

- Replace only `modules/regression_geometry_explorers` with `modules/ml-knowledge-graph`.
- Integrate the supplied Universal CSV 2D/3D Constellation importer into ML Knowledge Graph.
- Changes to the root launcher, landing-page metadata, documentation, dependency files, packaging scripts, and tests are allowed only as required by this replacement.
- Do not alter the Distributed Memory Architecture Atlas, Markov Chain Explorer, or S_n Explorer code, routes, assets, interfaces, or behavior.

## Preservation

- Preserve every existing ML Knowledge Graph feature and interface. CSV/TDA support must be additive.
- Preserve all CSV-importer behavior proved by its source or tests: arbitrary node/connection tables, local/offline manual import, 2D/3D layouts, adaptive labels, semantic modules and bridges, directed traversal, persistent-homology controls and area filling, browser exploration, and export.
- Preserve typed directed relations, weights, provenance, Notion IDs, and source URLs where the imported data supplies them. Never fabricate unsupported relations.
- Keep `strength`, `confidence`, `distance`, `sign`, and `evidence_count` as separate semantics; never collapse them into a single weight.
- Python is the mathematical source of truth. JavaScript may render and manage interaction, but must consume explicit local JSON/API results rather than reimplementing the mathematics.
- Do not claim full simplicial TDA, Betti numbers, persistent cohomology, or circular coordinates unless those methods are present and working in the supplied importer source.

## Fork and license integrity

- Preserve the fork's license, notices, copyright headers, and attribution.
- Add `modules/ml-knowledge-graph/UPSTREAM.md` recording the fork URL, upstream URL, imported commit/tag, import date, and integration changes.
- Do not replace fork-specific behavior with upstream code.

## Working method

- Inspect before editing. First produce an inventory and integration map.
- Reuse the fourth launcher slot (`port_offset=4`) for ML Knowledge Graph.
- Use the fork's existing runtime and build approach unless a change is necessary and documented.
- Avoid new production dependencies when an existing dependency can do the job.
- Keep the application locally runnable; do not introduce a hosted service requirement.
- Never delete the old module until the new module starts and the automated checks pass.

## Validation

- Run the existing root tests and all relevant source-project tests.
- Add tests for launcher registration, health/readiness, CSV template download, template round-trip import, malformed CSV errors, preservation of relation semantics/provenance, and TDA parity with the original importer.
- Compare deterministic original-importer outputs against the integrated outputs with golden fixtures.
- Run a browser smoke test for the complete CSV-to-graph-to-TDA-to-export workflow.
- Report every changed file, command run, test result, known limitation, and unverified assumption.