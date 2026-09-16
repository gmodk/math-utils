# Science atlas scope

## Dataset scale

- 3,815 nodes
- 4,669 normalized connections
- 37 broad domain labels
- 238 discipline and subdiscipline labels
- 23 node categories
- 773 research-frontier nodes
- 784 nodes categorized as theories, theorems, hypotheses, conjectures, laws, principles, theses, or models

## Structural design

The map combines a manually curated core with a systematic hierarchy:

1. broad scientific domain;
2. research field;
3. scientific subject or topic;
4. theoretical foundations;
5. methods and instruments;
6. open questions and research frontiers;
7. applications and implications;
8. named scientific landmarks and cross-disciplinary frontier programs.

The hierarchy is designed for exploratory visualization rather than bibliographic indexing. Generic nodes such as “methods and instruments” or “open questions” are research lenses attached to a concrete topic; they do not assert that a single canonical method or open problem exists.

## Semantic modules

The atlas is also emitted as 27 semantic node/edge pairs in `examples/science_modules/`. Each node belongs to exactly one semantic module, and each ordinary edge file contains only relations whose endpoints belong to that same module. Cross-domain relations are stored separately in `cross_domain_edges.csv`; `cross_domain_nodes.csv` makes that bridge layer independently importable. The `module_manifest.csv` file records filenames and counts.

The complete modular partition contains the same 3,815 nodes and 4,669 connections as the monolithic pair. The current partition assigns 192 relations to the cross-domain bridge layer, connecting 168 distinct endpoint nodes.

## Taxonomy anchors

The domain coverage was aligned conceptually with authoritative classification systems and research-program structures:

- [OECD Frascati Manual 2015](https://www.oecd.org/en/publications/frascati-manual-2015_9789264239012-en.html): broad fields of research and development.
- [arXiv category taxonomy](https://arxiv.org/category_taxonomy): contemporary mathematical, physical, computational, quantitative-biological, statistical, economic, and engineering subject families.
- [NIH Research, Condition, and Disease Categorization](https://report.nih.gov/funding/categorical-spending#/): biomedical and health-research coverage.
- [U.S. National Science Foundation focus areas](https://www.nsf.gov/focus-areas): cross-disciplinary research and technology areas.

These sources anchor scope and terminology; they do not individually certify every generated node or edge.

## Interpretation limits

- The atlas is broad, but no finite dataset is literally exhaustive of science.
- `importance`, `complexity`, and `weight` are synthetic visualization parameters.
- “Frontier” means active or emerging research direction, not a claim that a topic began recently or has equal priority across disciplines.
- A connection expresses a useful conceptual, structural, methodological, or application relationship. It is not automatically causal.
- The generated hierarchy should be treated as a navigational ontology that can be edited, specialized, or replaced through CSV—not as a definitive philosophy of scientific knowledge.
