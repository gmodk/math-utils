# Software Architecture

## 1. Architectural objective

The Atlas replaces five parallel applications with a modular monolith. The central object is an `Experiment`; mathematical approaches are read-only analytical lenses over that shared object.

The dependency direction is intentionally one-way:

```text
browser shell
    ↓
HTTP API / experiment state
    ↓
approach registry
    ↓
combinatorial | spectral | probabilistic | sheaf | information
    ↓
shared core
```

The core never imports an approach module.

## 2. Canonical experiment

`core.experiment.Experiment` owns the cross-approach state:

- semantic token;
- token type;
- finite-field projection;
- projection rule;
- prime modulus;
- M/Q/R mode;
- aggregation rule;
- spectral policy;
- cover region limit;
- maximum topological/cohomological dimension;
- generator seed and metadata.

An approach may derive additional objects but must not silently mutate the experiment.

## 3. Shared core

### `token_generator.py`
One implementation for all seven token types. The generator always returns the semantic token and the finite-field projection separately.

### `combinatorics.py`
Owns M/Q/R layers, capacities, systematic contributor sequences, pure subset families and cover construction.

### `finite_field.py`
Exact dependency-free arithmetic over prime fields: RREF, rank, nullspace, matrix products, inverses and vector utilities.

### `polynomial.py`
Horner evaluation and CRT/evaluation-coordinate generation.

### `aggregation.py`
Semantic aggregation for the combinatorial lens, including permutation composition.

### `secret_sharing.py`

Implements the inspectable finite-field LSSS/MSP layer: threshold Vandermonde span programs, DNF monotone-span compilation, fresh randomized share generation, coalition authorization, reconstruction coefficients and exact secret reconstruction over `F_(2^521-1)`.

## 4. Approach contract

Each module exports:

```python
ID = "..."
NAME = "..."
def analyze(experiment, **parameters) -> dict:
    ...
```

`approaches.__init__.REGISTRY` is the only registry the UI/API needs to know.

Adding a future sixth mathematical approach therefore requires:

1. one module;
2. registration in `REGISTRY`;
3. optional specialized UI rendering.

It does not require another server, token generator, finite-field implementation, JSON schema or repository.

## 5. Approach boundaries

The shared core contains primitives, not theory-specific conclusions.

The following remain approach-local:

- minimum distance and coding diagnostics → combinatorial;
- local spectral projector constraints and rank-basis selection → spectral;
- Monte Carlo reliability and stopping times → probabilistic;
- nerves, coboundaries and cohomology → sheaf;
- entropy, mutual information, channel and rate–distortion functions → information theory.

This avoids replacing five duplicated projects with one oversized universal analysis engine.

## 6. Browser architecture

The browser is a single-page vanilla JavaScript shell. It maintains no independent mathematical source of truth.

The browser:

- edits experiment parameters;
- requests token generation;
- imports/exports experiment JSON;
- requests analyses;
- renders returned results.

Python remains the mathematical source of truth.

## 7. API

### Shared state

- `GET /api/catalog`
- `GET /api/experiment`
- `POST /api/experiment`
- `POST /api/experiment/import`
- `POST /api/experiment/reset`
- `POST /api/random-token`

### Analysis

- `GET|POST /api/analyze/combinatorial`
- `GET|POST /api/analyze/spectral`
- `GET|POST /api/analyze/probabilistic`
- `GET|POST /api/analyze/sheaf`
- `GET|POST /api/analyze/information`
- `GET|POST /api/analyze/comparison`

Probability-sensitive endpoints accept `q` and `trials` through POST payloads where relevant.

## 8. State model

Version 1 uses in-process state intentionally. It is a local research application, so there is a single active experiment per running server instance.

A future persistence layer can store a collection of experiments without changing approach APIs. The natural next abstraction is an `ExperimentRepository` with versioned snapshots.

## 9. Research reproducibility

An exported experiment JSON contains all state needed to reconstruct the deterministic architecture, including generator seed and the actual semantic token. Monte Carlo analyses additionally expose their analysis seed in returned results.

## 10. Extension principles

A new mathematical lens should satisfy three conditions:

1. It consumes the canonical experiment or a mathematically explicit derived representation.
2. It does not redefine shared primitives such as M/Q/R or finite-field rank.
3. It documents which outputs are theorems, exact finite calculations, stochastic estimates, heuristics or external benchmarks.

---

# Atlas 2.1 exploratory and cryptographic laboratory layer

The unified Atlas adds two shared cross-lens services above the experiment core:

```text
Experiment
   |
   +--> five approach engines
   |
   +--> exploration.py  --> geometry / region / graph payloads
   |
   +--> crypto_lab.py   --> AEAD envelope + access-policy orchestration
                            |
                            +--> core/secret_sharing.py
                            +--> cryptography AESGCM / Ed25519
```

The exploratory layer does not replace approach mathematics. It translates each lens into coordinate nodes, region nodes, incidences, physical/virtual state, filtration scores and local detail payloads.

## Shared graph model

Every lens exports a bipartite incidence graph with coordinate nodes `C_i` and region nodes `R_j`. The common representation records incidence without asserting that contributor regions, spectral constraint blocks, sheaf patches and information observations are mathematically identical.

## Ordinary TDA versus sheaf cohomology

The Graph/TDA workspace constructs an ordinary simplicial lift from region supports and computes homology over `F_2` client-side. Sheaf cohomology is computed separately from stalks and restriction maps over the selected finite field.

## Cryptography architecture

### `core/secret_sharing.py`

This module is mathematical infrastructure, not an approach-specific lens. It provides:

- `SpanProgram`;
- threshold Vandermonde/Shamir matrices;
- DNF monotone-span compilation;
- fresh randomized sharing;
- row-labeled coalition authorization;
- reconstruction coefficients;
- exact reconstruction.

The prime field is `F_(2^521-1)`, chosen so a 256-bit AEAD key is one field element.

### `approaches/crypto_lab.py`

This module orchestrates the application-level cryptographic experiment:

1. serialize the current semantic token;
2. generate a fresh 256-bit AES key;
3. encrypt the token with AES-256-GCM and experiment metadata as AAD;
4. build a threshold, Atlas-derived or custom LSSS policy;
5. share the AES key using fresh masks;
6. sign every share with a fresh Ed25519 dealer key;
7. select/test a coalition;
8. verify signatures before reconstruction;
9. reconstruct and decrypt only for authenticated authorized coalitions;
10. compute availability/compromise statistics;
11. report lens-specific interpretation;
12. include the former monomial rank-invariance transform only as a non-security comparison.

AES-GCM and Ed25519 are supplied by `cryptography`; Atlas does not reimplement those primitives.

## Cryptography API boundary

The existing endpoint remains:

```text
POST /api/explore/<approach>/crypto
```

The request may contain:

```json
{
  "policy_type": "threshold",
  "threshold": 3,
  "coalition": "1,2,5",
  "coalition_fraction": 0.5,
  "survival_q": 0.9,
  "compromise_q": 0.1,
  "trials": 2000,
  "tamper": false,
  "custom_minimal_sets": null
}
```

`policy_type` can be `threshold`, `atlas-derived`, or `custom-dnf`.

The response deliberately does **not** expose the raw AEAD key or complete field share values. It returns ciphertext metadata/hashes, policy metadata, coalition authorization, leakage classification, truncated share-value previews, signatures/verification results and risk statistics.

## Security boundary

The LSSS privacy property is mathematical and exact under its stated model. The surrounding application remains a research prototype. In particular:

- Ed25519 share signatures are not full VSS;
- shares are not persistently stored/distributed by a hardened protocol;
- there is no malicious-dealer consistency proof;
- there is no key rotation/revocation/refresh protocol;
- there is no side-channel or secure-erasure guarantee;
- HTTP transport is not itself secured by Atlas.

The authoritative scope statement is `docs/SECURITY_MODEL.md`.
