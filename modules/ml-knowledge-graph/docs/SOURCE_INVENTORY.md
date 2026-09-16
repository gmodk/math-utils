# Source inventory and integration map

Inspected before integration: root/ancestor AGENTS.md, launcher, landing assets, requirements, test suites, README, CHANGELOG and VALIDATION; fork tracked files and Git state; complete supplied importer source and tests. No nested AGENTS.md was present in either supplied project. Exact source locations, commit and license evidence are in UPSTREAM.md.

## Fork

The supplied fork was a static ES-module website: index.html → js/main.js, graph.js, layouts.js, renderer.js, ui.js and video scripts. It had no production server, build step, API or dedicated health endpoint. Its documented static-server root proved HTTP availability only. The added app.py serves those paths and an explicit /api/health check, using the root's existing Python/FastAPI/Uvicorn dependencies. Port offset 4 is reused. The launcher supplies --host, --port and --no-browser and inherits the existing UTF-8/unbuffered environment.

The original knowledge_graph.json contains 2,081 nodes and 5,149 projected directed edges. Bundled records use id, label, category, definition, long_description, from/to adjacency and precomputed metrics. Data and precomputed metrics are retained. The .claude graph-generation source is preserved, but its cycle removal and transitive reduction are deliberately not used on CSV input.

The existing interface retains search, category visibility, coloring/sizing, tooltips, prerequisites/dependents, four layouts, camera/selection controls, screenshots, sharing/embed controls, companion book and window.graphVideo. A validated bundled position cache avoids recomputing the 2,081-node default force view at startup. The optional Node render-graph-video.mjs command starts the new Python service; its timeline and capture interfaces remain. There was no supplied fork test suite. New API tests, browser smoke and the existing 12-action video example validate the integration.

## Importer feature inventory

Paths below are relative to reference/csv-importer, whose source is retained unchanged as the oracle. Active equivalents are in backend/ and constellation/.

| Feature | Supplied implementation | Integrated implementation and checks |
|---|---|---|
| CSV quoting, delimiters, arbitrary tables, mapping | src/csv-core.js: parseCSV, inferTable, normalizeTables | backend/csv_import.py: parse_table, normalize, preview; test_api.py; original tests |
| Nodes/edges and adjacency | csv-core.js: normalizeTables | One node-only, edge-only or adjacency file, or separate node/edge tables; test_single_file_modes and template round trip |
| Node properties and display schema | csv-core.js: inferDisplaySchema | graph_analysis.display_schema; arbitrary properties retained in inspector/export |
| Offline manual/drop import, preview | src/app.js: inspectFiles, review/apply workflow, storage helpers | constellation/csv-preview.js validates before Apply; IndexedDB/localStorage; malformed browser import tested |
| Default data and semantic modules/bridges | src/sample-data.js; examples/science_world_*.csv | Unmodified bundled sample and arbitrary semantic columns; original sample tests and browser sample view |
| Metrics and recursive traversal | src/graph-core.js: enrich, getUpstream/getDownstream/getNeighborhood | graph_analysis.enrich/traverse; directed adjacency stays separate from undirected topology; parity fixtures and API tests |
| 2D/3D, projection, camera, selection | src/app.js: project, drawNode, drawEdge, event handlers | Original canvas renderer retained; Python returns graph model/positions; browser both dimensions and search/traversal |
| Semantic/hierarchy/cluster/radial layouts | graph-core.js: semanticTargets, hierarchicalTargets, clusterTargets, radialTargets, homeTargets | graph_analysis.targets; original-source parity for deterministic coordinates |
| Gravity/elastic force | graph-core.js: forceStep; app.js: prepareWeights, buildAnchors, stir | Python weights, anchors, force_step and stir APIs; four-step parity; async presentation adapter |
| Adaptive labels | app.js: drawLabels, projected visibility/label-density controls | Same renderer and interaction; browser label toggle and density |
| Graph components/cycle rank | graph-core.js: components | graph_analysis.components; original oracle/golden parity |
| Filtration and cycle edges | src/topology.js: runFiltration | topology.run_filtration; union-find, same edge ordering; exact fixture comparison |
| Area candidates and independent boundaries | topology.js: detectFaces, independentFaces | topology.detect_faces/independent_faces; 800 candidate cap; dense fixture exercises the cap |
| Cellular persistence | topology.js: persistentHomology | topology.persistent_homology; F₂ reduction and interval parity |
| TDA controls, plots, component colors | topology.js: analyze; app.js: recomputeTDA/drawFaces | topology.analyze plus original drawing; enable, epsilon, fill controls tested; 80 rendered-face cap retained |
| Export and reload | app.js: snapshot/saveBrowserSnapshot/download and canvas PNG | Canonical local JSON export API plus original PNG; browser export/readback and reload checked |

Original tests: all five tests/*.test.cjs files, 26 tests, are preserved and run. New Python tests compare the actual original functions with eight committed golden fixtures; they do not compare two copies of the Python implementation.

## Accepted schemas and deliberate corrections

See CSV_SCHEMA.md for exact canonical fields and mapping rules. Relation, direction, weight, strength, confidence, distance, sign and evidence_count are distinct. Canonical templates and validation share field constants. Original columns and source row references survive parsing and export; source IDs/URLs/provenance are copied when present. Missing relations remain null. No default edge relation is asserted as fact.

The old parser accepted strength/distance as weight aliases, overwrote labels when adding edge endpoints, removed parallel edges/self-loops and merged conflicting IDs. Those lossy behaviors are corrected to satisfy this integration's explicit preservation requirements. Missing endpoint generation is retained with visible warnings and an optional strict API mode. The old browser required both tables despite core support for one-file modes; the added preview exposes every supported mode.

## Scope and risks

Implemented TDA is graph/cellular filtration with independent quadrilateral 2-cells. Betti curves shown are those already computed by the source; they do not claim general simplicial TDA. No cohomology, circular coordinates or roadmap mathematics was added. Independent face selection cannot create nontrivial H2.

Python is authoritative for math. Screen projection, coordinate interpolation, label collision avoidance and rendering remain browser presentation. See INTEGRATION.md for the fork force-layout numerical difference, large-graph latency and local-storage limits. Python uses deterministic Unicode code-point ordering where original localeCompare ordering could vary with browser locale; equal-weight tie representatives/labels can differ for mixed-case/non-ASCII IDs, while the same filtration's interval multiset is the invariant. Current golden coordinate fixtures use ASCII IDs.
