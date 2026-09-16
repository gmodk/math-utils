# Local CSV and topology integration

Start with the Math Utils root launcher, or `python app.py --port 8004 --no-browser` after installing the root Python requirements. No Node build and no internet connection are required for interactive exploration. The Python server serves the existing frontend and JSON APIs. `GET /api/health` checks bundled data and essential assets. Browser CSP restricts executable resources and API connections to the local origin.

Open Settings → Import CSV / TDA. Download CSV template provides a ZIP containing nodes.csv and edges.csv, generated from the validator's field constants. Select both, review mappings and errors, and apply. Single adjacency, node-only and edge-only tables are also supported. Missing endpoint nodes are visibly diagnosed; they do not imply new relations. The current graph and stored snapshot remain intact if validation fails or the dialog is canceled.

The additional view preserves the supplied constellation controls, sample, semantic module data, labels, navigation, traversal, filtering, layouts, gravity and persistence controls. Open this graph in ML explorer shares the browser-local snapshot with the original fork UI. Show bundled ML graph restores the original ML dataset without deleting the CSV snapshot. IndexedDB and legacy localStorage remain supported.

## Mathematical boundary

Python implements parsing, normalization, metrics, traversal, layouts, force steps and topology. JavaScript draws scenes, manages controls, projects coordinates, interpolates returned positions and performs screen-label collision avoidance. Synchronous local calls preserve the original synchronous control interfaces; force updates use batched asynchronous calls. Large imports may temporarily block the interface during analysis.

Importer PageRank retains 24 iterations and damping 0.85. Importer layout formulas and graph/cellular persistence are ports of the supplied source. Golden fixtures compare the original JavaScript directly with Python. Combinatorial results are exact; floating-point metrics/layouts use relative tolerance 1e-11 and absolute tolerance 1e-12.

The fork's precomputed bundled metrics are preserved because its generation pipeline computed them before transitive reduction. Its cycle elimination and transitive reduction are never applied to CSV input. Imported metric definitions are those of the importer. Betweenness is not fabricated for CSV nodes.

The fork's force layout keeps link length/strength, axis force, cluster force, charge and stopping parameters. The Python implementation uses seeded initial positions and exact pairwise charge instead of D3's Barnes–Hut approximation. Therefore its coordinates are not a byte-for-byte reproduction of the original random layout. The bundled graph ships with a validated cache of those Python positions so its initial view is immediate; uncached graphs still use the Python calculation. Existing layout names, animation, selection and video interfaces are retained. This numerical difference is explicit and requires visual acceptance if exact layout reproduction is required.

## Topology scope

Nodes enter at zero; edges enter at normalized selected-field weight. Strength order enters high values first; distance order enters low values first. Constant values enter at 0.5. Missing selected measurements use the source's uniform default 1 for derived filtration only; source fields remain null. Fields are never combined. Direction affects traversal but not the homology boundary operator.

Area filling attaches a filtration-compatible independent basis of quadrilateral boundaries over F_2. At most 800 candidate faces are considered and 80 active faces drawn, matching the source. The source's independent-face construction does not produce nontrivial H2. No simplicial completion, Vietoris–Rips complex, persistent cohomology or circular coordinates were added. Zero-duration intervals are omitted; infinite deaths are null and displayed to scale 1. Cycle-edge highlighting refers to the graph before face filling.

## Intentional normalization fixes

- Node labels are not overwritten when referenced by edges.
- Distinct evidence/parallel edges and self-loops are retained.
- Conflicting duplicate node IDs are errors; identical duplicates retain all source row references.
- Invalid booleans/nonfinite numbers, malformed quotes, duplicate headers and ragged rows are actionable errors.
- All original cells, independent measurements, relation detail, Notion IDs, source URLs and supplied provenance survive export.
- Missing relation is null (the UI uses an explicit `unspecified` display group). No factual relation or evidence provenance is generated.
- Export includes stable edge IDs and import metadata.

The reference standalone importer remains unmodified for comparison. Its old UI limitations and data-loss bugs are not silently treated as desired behavior.
