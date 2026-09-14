# Distributed Memory Architecture Atlas — User Guide

## 1. Purpose

The Atlas is a research interface for studying one distributed-memory experiment through five mathematical lenses. It is designed for exploration, comparison and reproducible experiments rather than production storage.

The central workflow is:

1. create or import one token;
2. choose the shared architecture parameters;
3. open any mathematical approach;
4. run analyses;
5. switch approaches without losing the experiment;
6. compare invariants in the Comparison Lab;
7. export the complete experiment as JSON.

---

## 2. Starting the application

From the project root:

```bash
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8000`.

The project uses only the Python standard library at runtime.

---

## 3. The application shell

The left sidebar is global. It is not owned by any particular mathematical approach.

### Name

A human-readable experiment label. It is preserved on export.

### Dimension

The number of token coordinates:

`n = len(T)`.

Changing the dimension through **Generate token** creates a new token of that size.

### Field `p`

The prime modulus used by finite-field analyses. Spectral analysis additionally requires `p > n` for the default distinct evaluation points `1,...,n`.

### Mode

The three standard graded families are:

- `M = {0,2,4}`;
- `Q = {0,1,2}`;
- `R = {0,2,3}`.

Different lenses use these layers in slightly different but explicit ways. The combinatorial systematic lens uses the declared capacity as its region budget. The spectral lens uses the actual graded subset universe. The sheaf lens uses nonempty subsets as cover patches.

### Spectral policy

`full` materializes all eligible spectral regions.

`rank-basis` keeps the abstract universe but greedily activates only regions that increase the stacked spectral constraint rank until the projective target `n-1` is reached, together with the anchor.

### Token type

Seven generators are available:

- chars;
- words;
- integers;
- natural numbers;
- vectors;
- cyclic permutations;
- functions.

### Seed

Controls deterministic token generation. Reusing the same parameters and seed yields the same generated token.

### Structured-object parameter

The secondary input changes meaning according to token type:

- vectors → vector component dimension;
- cyclic permutations → permutation degree;
- functions → polynomial degree.

It is hidden for scalar token types.

---

## 4. Semantic token and field projection

The Atlas treats these as different objects.

The **semantic token** is what the user actually generated or imported. It can contain strings, vectors, permutations or function descriptors.

The **field projection** is a scalar vector in `F_p^n` used when an approach requires finite-field linear algebra.

The projection is displayed immediately below the semantic token preview.

Do not interpret it as a lossless encoding. For structured types, different semantic coordinates may project to the same field element.

---

## 5. Generate token

Choose dimension, field, token type, seed and any structured-object parameter, then select **Generate token**.

The generated token becomes the active experiment immediately. Cyclic permutation tokens use permutation composition when viewed through the combinatorial lens.

Generation does not change the formal source law assumed by the Information lens. That lens still uses its explicitly documented uniform finite-field model when applying exact entropy identities.

---

## 6. Apply settings

Use **Apply settings** when changing field, mode, spectral policy, experiment name or seed without regenerating the token.

If a field change would invalidate a spectral assumption, the Spectral workspace reports the issue instead of silently changing the data.

---

## 7. Import JSON

The Atlas accepts an exported Atlas experiment or another JSON object containing at least a `token` array.

If `field_projection` is absent, the importer derives a deterministic SHA-256-based projection modulo `p` for each coordinate. This provides a reproducible analysis representation, not a claim of semantic preservation.

Useful included examples are under `examples/`:

- `atlas_experiment.json`;
- `s3_permutation_token.json`;
- `s4_permutation_token.json`;
- `d6_order6_permutation_token.json`.

---

## 8. Export

**Export** downloads the active experiment state as JSON. It contains the actual semantic token, finite-field projection and architecture parameters, so deterministic analyses can be reproduced later.

---

# Part II — Mathematical workspaces

## 9. Combinatorial

This lens asks:

> Which regions exist, which token coordinates contribute to them, and what algebraic recovery structure follows from that incidence geometry?

The summary reports:

- token dimension;
- M/Q/R mode and layers;
- declared capacity;
- physical region count;
- direct versus aggregate regions;
- rank over the selected field;
- dimension-per-region rate;
- contributor degree range.

### Coding analysis

For practical small `n`, the Atlas exhaustively computes the minimum Hamming distance of the binary systematic code induced by the region-incidence matrix.

The result includes detection, correction and erasure bounds derived from `d_min`.

For larger dimensions exhaustive enumeration is intentionally skipped.

### Region preview

Each region shows its contributors, semantic aggregate and CRC32 checksum. CRC is a serialization-integrity diagnostic; it is not the same as structural recovery from redundant regions.

---

## 10. Spectral Hypergraph

This lens asks:

> Can overlapping local invariant-subspace constraints determine the finite-field token globally?

The finite-field projection becomes the polynomial coefficient vector. It is evaluated at the points `1,...,n`, producing CRT/evaluation coordinates.

For every eligible region with at least two coordinates, the Atlas creates local projector constraints and lifts them into the global coordinate system.

### Main quantities

- abstract region count;
- active physical region count;
- stacked constraint rank;
- target rank `n-1`;
- projective recoverability;
- physical/abstract compression ratio.

### Rank-basis policy

With `rank-basis`, the Atlas greedily selects regions that increase rank. The algorithm is a practical basis-selection heuristic; it is not stated as a global minimum theorem.

### Topological overlay

The active nonempty spectral supports are treated as simplices and a small finite-field TDA summary reports simplex counts and Betti numbers up to the configured low dimension.

---

## 11. Probabilistic

This lens asks:

> If physical regions survive randomly, how likely is reconstruction?

Set the survival probability `q` and Monte Carlo trial count in the workspace header.

The Atlas runs both:

- systematic combinatorial recovery;
- spectral projective recovery.

The spectral event additionally requires survival of the anchor.

### Outputs

- estimated recovery probability;
- 95% Wilson interval;
- expected surviving rank;
- rank histogram;
- number of spectral physical regions;
- random-reveal stopping-time summary for the systematic model.

`q=1` should recover deterministically when the underlying architecture has full required rank. `q=0` cannot recover.

A Monte Carlo estimate is not a theorem. Reproducibility depends on the reported simulation seed and trial count.

---

## 12. Sheaf / Local-to-global

This lens asks:

> Do local states on overlapping regions glue to one globally consistent memory state, and are there higher obstruction spaces?

The nonempty M/Q/R subsets form a region cover. For computational control, the current experiment's `region_limit` may truncate the cover, after which missing coordinates are covered by singleton patches.

The Atlas constructs the nerve and computes the cochain dimensions, coboundary ranks and cohomology dimensions.

### Compatibility

The active finite-field token is restricted to each local patch. Pairwise overlaps are checked explicitly. An unmodified global token should produce compatible local coordinate sections.

### Cohomology

`H^0` describes global compatible sections in the chosen sheaf model. Higher cohomology records local-to-global obstruction structure.

When the complex is truncated at a maximum dimension, interpret the highest displayed cohomology degree with care because an omitted next coboundary can alter it.

---

## 13. Information-Theoretic

This lens asks:

> How many bits of uncertainty does a given observation remove, and how efficiently are regions being used?

For the exact linear identity, the source model is

`T ~ Uniform(F_p^n)`.

If the observed linear rows have rank `r`, then

`I(T;Y) = r log2(p)`

and

`H(T|Y) = (n-r) log2(p)`.

The workspace reports:

- source entropy;
- full observed rank;
- revealed information;
- remaining conditional entropy;
- storage redundancy factor;
- dimension-per-region rate.

### Greedy information profile

Regions are added greedily according to marginal rank gain. The graph-like bars show cumulative information and marginal information contribution.

### Survival information

Under iid region survival, the Atlas estimates expected rank, expected mutual information, expected conditional entropy and full-recovery probability.

### Channel and rate–distortion curves

These are exact classical `p`-ary benchmark formulas. They are reference curves, not measured operational capacities of the complete Atlas memory architecture.

---

# Part III — Comparison Lab

## 14. Why comparison is separate

The five approaches do not produce interchangeable scores. The Comparison Lab therefore does not normalize everything into a ranking.

Instead it places characteristic invariants side by side and checks known bridge identities.

Current rows include:

- combinatorial physical-region count and rank;
- spectral physical constraints and projective rank;
- probabilistic recovery probability at the selected `q`;
- sheaf `dim H^0` and `H^1`;
- information-theoretic source entropy and revealed information.

### Bridge invariants

Version 1 checks, among other things, that the rank seen by the combinatorial systematic matrix agrees with the rank used by the information lens.

This cross-lens testing is one of the main reasons the Atlas exists.

---

## 15. Recommended experiments

### Experiment A — M/Q/R comparison

Generate one numeric token and run every lens under M, Q and R. Record region counts, spectral rank-basis sizes, recovery probabilities and information redundancy factors.

### Experiment B — semantic token invariance

Generate words, vectors and cyclic permutations with the same `n`. Compare how the Combinatorial lens retains semantic structure while finite-field lenses operate on projections.

### Experiment C — physical redundancy versus stochastic reliability

Compare Spectral `full` and `rank-basis` policies. Then inspect how the reduced physical region set changes recovery probability under `q < 1`.

### Experiment D — topology and gluing

Compare spectral TDA Betti numbers with sheaf cohomology on related region families. Do not assume equality: they are invariants of different constructions.

### Experiment E — information threshold

Watch the greedy information profile reach rank `n`, and compare that threshold with deterministic recovery and probabilistic stopping-time experiments.

---

## 16. Performance boundaries

Subset universes grow combinatorially. Full M/Q/R spectral families can become large rapidly.

Exhaustive binary minimum-distance computation is limited to small token dimensions.

Monte Carlo cost scales approximately with `trials × number_of_regions × rank_cost`.

Sheaf nerve size can grow much faster than the underlying cover because it includes intersecting collections of patches; `region_limit` and `max_dim` exist to control this.

---

## 17. Mathematical status labels

When interpreting Atlas results, distinguish:

- **definition** — establishes the model;
- **exact finite computation** — e.g. rank over `F_p`;
- **theorem-derived identity** — e.g. `I(T;Y)=r log2 p` under the stated source model;
- **Monte Carlo estimate** — probability and expectation estimates;
- **heuristic** — rank-basis greedy selection;
- **benchmark** — classical channel/rate–distortion curves;
- **research direction** — conjectural cross-lens relationships.

---

## 18. Troubleshooting

### Spectral analysis says `p > n` is required
Choose a prime modulus larger than the token dimension. The default CRT points are `1,...,n`, which must be distinct in the field.

### Imported structured token has an unexpected projection
The importer cannot infer semantic mathematics from arbitrary JSON. Supply `field_projection` explicitly when a mathematically meaningful projection is known.

### A large experiment becomes slow
Reduce dimension, use Spectral `rank-basis`, lower `region_limit`, lower `max_dim`, or reduce Monte Carlo trials.

### The highest sheaf cohomology number looks strange
If `max_dim` truncates the next cochain group, the final displayed group can be provisional.

### Permutation aggregation does not apply
Use a token generated as `cyclic_permutations`; the Atlas automatically sets combinatorial aggregation to `compose` for that type.

---

## 19. Research extension points

Natural next modules include:

- dynamical-systems / attractor memory;
- representation-theoretic memory for group-valued tokens;
- geometric/manifold local chart memory;
- category-theoretic comparison of the five current representations;
- correlated failure models;
- Bayesian decoding;
- persistent sheaf cohomology;
- optimization of region families under joint rate/reliability/locality objectives.

The approach registry is designed to support such additions without reproducing the platform infrastructure.

---

# Atlas 2.1 research laboratories

Atlas 2.1 retains the exploratory depth of the standalone applications and makes it available from every primary mathematical lens.

Each approach now contains five tabs.

## Geometry

The Geometry tab displays token coordinates on a circle and the current region universe in a paginated table. Selecting a region highlights exactly its support and opens an approach-specific inspector.

The same support is interpreted differently by each lens:

| Lens | Region interpretation |
|---|---|
| Combinatorial | contributor subset / systematic region |
| Spectral | anchor, CRT share or local spectral constraint |
| Probabilistic | region survival block |
| Sheaf | cover patch carrying a local section |
| Information | linear observation row |

The compact incidence overview beneath the circle renders the current page of regions and their coordinate incidences.

### Spectral geometry

The spectral lens preserves the original CRT-circle interpretation. Coordinate labels show evaluation points and CRT values. Rank-basis storage distinguishes **physical** regions from the larger **virtual** region universe.

## Graph / TDA lab

The Graph / TDA lab is shared by all five approaches.

### Navigation

- mouse wheel: continuous deep zoom;
- drag empty background: pan;
- drag node: reposition;
- double click: fit graph;
- 3D mode + right/Shift-drag: orbit camera.

### Layouts

Available layouts are:

- force-directed;
- hierarchical;
- radial;
- circular;
- concentric;
- grid.

### Force controls

The right panel exposes center gravity, repulsion, link strength, link distance, damping, collision radius and 3D depth gravity. Physics can be paused or disabled.

### Scope

`physical only` shows the materialized/active region family. `all virtual + physical` also shows virtual regions where the approach has such a distinction, most notably spectral rank-basis storage.

### TDA

Enable the TDA overlay to build the simplicial lift of region supports. The lab reports

`beta_0, beta_1, beta_2, beta_3`

and persistent Betti curves across the filtration threshold.

Filtration choices:

- **approach-specific metric**;
- subset cardinality;
- region order;
- physical-first.

Optional overlays include connected-component coloring, projected coordinate 1-skeleton, filled 2-simplices, cycle-edge emphasis and hiding regions born after the current threshold.

**Important:** this is ordinary simplicial homology over `F_2`. In the sheaf lens it is separate from the sheaf cohomology shown in Core/Diagnostics.

## Core lab

This is the native mathematical workspace for the current lens.

### Combinatorial

Displays systematic-code metrics, binary minimum distance where exhaustive computation is feasible, region preview and contributor structure.

### Spectral

Displays polynomial coefficients, CRT evaluation points and values, spectral rank/recovery, topology summary and region state. It replaces the old separate `Polynomial / CRT` tab without removing the underlying exploration.

### Probabilistic

Displays systematic and spectral recovery estimates, Wilson intervals, rank histograms and stopping-time statistics.

### Sheaf

Displays cochain dimensions, coboundary ranks, cohomology dimensions, local-section compatibility and sections.

### Information

Displays source entropy, mutual information, conditional entropy, greedy marginal information gain, survival information and classical channel/rate-distortion benchmark curves.

## Constraints / diagnostics

This tab gives the detailed numerical payload behind the Core lab. Its meaning changes with the lens:

- combinatorial: code/rank diagnostics;
- spectral: stacked constraint rank and CRT diagnostics;
- probabilistic: recovery/rank/stopping diagnostics;
- sheaf: coboundary/cohomology and restriction diagnostics;
- information: entropy/rank and leakage diagnostics.

## Cryptography lab

Atlas 2.1 replaces the former rank-invariance security demonstration with a hybrid encrypted-memory experiment:

1. the current semantic token is encrypted with a fresh AES-256-GCM key;
2. that key is converted to one element of `F_(2^521-1)`;
3. a randomized LSSS / monotone span program distributes the key across regions;
4. each issued share is signed with Ed25519;
5. the selected coalition is tested for authorization, leakage and authenticated reconstruction;
6. survival/compromise probabilities are evaluated against the same access policy.

The old invertible coordinate transform still appears in the results as **Why the old rank-invariance transform is not the cryptosystem**. It is informational comparison only.

### Access policy

Choose one of three policy types.

#### Threshold LSSS

Set threshold `t`. If there are `N` physical share-holding regions, any `t` regions reconstruct the key. Coalitions with fewer than `t` regions are unauthorized.

This policy is implemented in Shamir/Vandermonde linear-span form.

#### Atlas-derived minimal sets

Atlas derives several candidate minimal authorized coalitions from the current lens and compiles their OR-of-AND rule into a DNF monotone span program.

- **Combinatorial:** greedy full-rank systematic row families.
- **Spectral:** constraint-rank `n-1` families plus the anchor.
- **Probabilistic:** systematic rank-basis families, then probability is applied to the resulting access rule.
- **Sheaf:** inclusion-minimal patch families covering every token coordinate.
- **Information:** systematic rank-basis families, interpreted through key leakage and conditional entropy.

The derivation is a policy heuristic; the resulting LSSS enforces the derived access structure exactly.

#### Custom DNF / MSP

Enter minimal authorized sets as JSON, for example:

```json
[[1,2,3],[2,4,5]]
```

This means:

`(R1 AND R2 AND R3) OR (R2 AND R4 AND R5)`.

A region can receive more than one share row if it appears in more than one clause.

### Coalition regions

Enter a comma-separated coalition such as:

```text
1,2,5
```

Leave the field blank to have Atlas sample a coalition according to **Sampled coalition fraction**.

The result distinguishes:

- `structurally_authorized` — the access structure accepts the coalition;
- `authenticated_for_reconstruction` — the coalition is authorized and all selected shares verify;
- `reconstructed_key_matches` — the reconstructed 256-bit key equals the encryption key;
- `token_decryption_verified` — AES-GCM decryption reproduces the exact serialized token.

### Perfect-secrecy display

For the LSSS model, an unauthorized coalition receives fresh-randomness linear shares whose distribution is independent of the shared key. Atlas therefore displays:

```text
I(K ; X_U) = 0 bits
H(K | X_U) = 256 bits
```

For an authorized coalition:

```text
I(K ; X_A) = 256 bits
H(K | X_A) = 0 bits
```

These statements describe the implemented ideal LSSS model for the random 256-bit key; they are not empirical leakage estimates.

### Share tampering

Enable **tamper one selected share** to modify one selected share value after its Ed25519 signature has been issued.

Expected behavior:

- the access structure may still say the coalition is structurally authorized;
- Ed25519 verification fails on the altered row;
- authenticated reconstruction is blocked;
- token decryption does not occur.

The signature layer is not full VSS. It detects modification of dealer-issued shares, but it does not prove that a malicious dealer originally issued mutually consistent shares.

### Survival and compromise

Set:

- **Region survival q** — per-region probability of being available;
- **Region compromise c** — per-region probability of being read by the attacker;
- **Risk trials** — Monte Carlo trials for non-threshold policies.

Atlas reports:

```text
P_avail = P(surviving coalition is authorized)
P_comp  = P(compromised coalition is authorized)
```

Threshold policies use exact binomial tails. DNF/MSP policies use Monte Carlo simulation.

### Lens-specific meaning

#### Combinatorial

Regions are share holders and the contributor/rank geometry can seed minimal authorized coalitions.

#### Spectral

Spectral rank can seed an access policy, but confidentiality is supplied by AEAD + LSSS. Spectral basis hiding is no longer treated as encryption.

#### Probabilistic

The main cryptographic quantities are availability and catastrophic compromise probabilities induced by the access structure.

#### Sheaf

Patches can hold shares and coordinate-covering patch families can seed access policies. Sheaf cohomology is not treated as a cryptographic hardness assumption.

#### Information

The central security statement is information leakage: unauthorized coalitions have zero mutual information about the LSSS key under the model.

### Cryptographic implementation boundary

AES-256-GCM and Ed25519 come from the `cryptography` package. Atlas directly implements the LSSS/MSP finite-field layer so the share mathematics remains inspectable.

The application is a research prototype, not a production KMS. It does not provide secure persistent share storage, authenticated network distribution, malicious-dealer VSS, proactive refresh, revocation, hardware key protection or independent security audit. Read `docs/SECURITY_MODEL.md` before interpreting results operationally.

## Large graph behavior

Very large virtual universes can contain tens of thousands of regions. To keep the browser interactive, the Graph/TDA renderer caps the number of rendered regions and displays a warning when truncation occurs. Python analysis remains independent of this rendering cap.
