# Validation — Distributed Memory Architecture Atlas 2.1

Date: 2026-09-13

## Automated Python suite

**23/23 tests passed.**

The suite covers the previously validated Atlas mathematics plus the new cryptographic layer.

### Existing mathematical/core coverage

- random-token reproducibility for all seven semantic token types;
- experiment regeneration and legacy permutation-token import;
- combinatorial full-rank systematic encoding and binary-distance analysis;
- spectral rank-`(n-1)` projective reconstruction and spectral TDA summary;
- probabilistic `q=0` / `q=1` recovery endpoints;
- sheaf gluing compatibility;
- information-theoretic rank/entropy identity;
- cross-approach comparison invariants;
- geometry and graph payloads for all five lenses;
- physical/virtual spectral geometry under rank-basis storage;
- local region inspectors for all five lenses.

### Cryptography 2.1 coverage

- threshold LSSS authorization and exact reconstruction;
- unauthorized threshold coalition rejection;
- DNF monotone-span access policy with multiple minimal authorized sets;
- AEAD + LSSS round-trip token recovery for **all five lenses**;
- unauthorized-coalition leakage classification (`I(K;X_U)=0` in the LSSS model);
- Ed25519 share-tampering detection;
- reconstruction blocking after invalid share authentication;
- Atlas-derived DNF/MSP policy generation for all five lenses;
- exact threshold availability/compromise endpoints;
- explicit regression ensuring the legacy rank-preserving transform is labeled `not a confidentiality primitive`.

## Cryptographic runtime primitives

Atlas does not implement block ciphers, GCM or Ed25519 itself. Runtime validation used:

- `cryptography` 46.0.4;
- AES-256-GCM through `cryptography.hazmat.primitives.ciphers.aead.AESGCM`;
- Ed25519 through `cryptography.hazmat.primitives.asymmetric.ed25519`.

The inspectable LSSS/MSP layer is implemented by Atlas in `core/secret_sharing.py` over the prime field `F_(2^521-1)`.

## Static/runtime validation

Passed:

- Python `compileall` for application, source and tests;
- JavaScript syntax checks for `app.js`, `graph_lab.js`, and `tda_core.js`;
- Cryptography Lab DOM selector coverage;
- verification that obsolete `cryptoKey` / `visibleFraction` controls are no longer present;
- HTTP serving of the application shell and shared JavaScript assets.

## TDA sanity checks

The shared client-side TDA engine was executed under Node:

- unfilled triangle: `beta_0=1`, `beta_1=1`;
- filled triangle: `beta_0=1`, `beta_1=0`, `beta_2=0`.

## Live HTTP/API cryptography smoke tests

For each primary lens — combinatorial, spectral, probabilistic, sheaf and information — a running Atlas 2.1 server successfully completed:

1. fresh AES-256-GCM token encryption;
2. threshold LSSS key distribution;
3. authorized full-coalition reconstruction;
4. Ed25519 verification;
5. exact AES-key recovery;
6. authenticated token decryption;
7. legacy-transform comparison marked non-confidential;
8. Atlas-derived DNF/MSP policy generation and authorized reconstruction.

Additional live checks verified:

- unauthorized `1`-region coalition under a `3`-of-`N` policy reports zero key leakage in the LSSS model and cannot decrypt;
- deliberate modification of a selected share is detected by Ed25519 and blocks decryption;
- custom DNF policy `[[1,2],[3,4,5]]` authorizes coalition `{1,2}`;
- the same policy rejects `{1,3}` and reports zero key leakage.

## Access-policy mathematics validated

For a span program `(M,rho)` the implementation tests authorization by solving

```text
lambda^T M_A = e_1^T.
```

Authorized reconstruction verifies

```text
lambda^T X_A = s.
```

The DNF compiler is tested with multiple independent AND clauses sharing the same secret through independent randomness.

## Availability/compromise validation

Threshold policies use exact binomial tails. Tests verify:

- `q=1` gives availability `1` when the threshold is feasible;
- compromise probability `c=0` gives catastrophic compromise probability `0`.

General monotone policies use deterministic-seeded Monte Carlo for reproducible risk estimates.

## UI feature checklist

Atlas 2.1 retains all Atlas 2.0 research laboratories:

- circular/local geometry exploration;
- paginated selectable region universe;
- region inspector;
- compact incidence graph;
- 2D/3D Graph/TDA laboratory;
- continuous deep zoom and pan;
- 3D orbit controls;
- draggable nodes;
- force, hierarchical, radial, circular, concentric and grid layouts;
- gravity/repulsion/link/damping/collision controls;
- physical-only versus full virtual+physical graph scope;
- ordinary simplicial filtration controls;
- `beta_0` through `beta_3` display;
- persistent Betti curves;
- native Core and Constraints/Diagnostics labs for every approach.

The Cryptography Lab now additionally contains:

- threshold / Atlas-derived / custom-DNF policy selection;
- coalition selection;
- survival and compromise parameters;
- risk-trial control;
- tamper simulation;
- encrypted-envelope diagnostics;
- access-policy diagnostics;
- information leakage diagnostics;
- authenticated-share diagnostics;
- availability-versus-compromise diagnostics.

## Interpretation boundaries

1. Client-side TDA computes ordinary simplicial homology over `F_2`; it is not sheaf cohomology.
2. Approach-specific TDA filtration values are exploratory ordering functions unless separately backed by an operational theorem.
3. `I(K;X_U)=0` is an exact property of the implemented ideal LSSS model for unauthorized coalitions with fresh uniform masks; it is not a claim that the complete Atlas deployment is production-secure.
4. Ed25519 signatures authenticate issued shares but do not constitute malicious-dealer VSS.
5. AES-GCM/Ed25519 correctness is delegated to the external cryptography library; Atlas has not independently audited those primitives or its own protocol integration.
6. Atlas-derived minimal authorized families are heuristics derived from the mathematical lenses, not proofs of operational optimality.
7. The former invertible monomial/rank-invariance experiment remains only as an algebraic comparison and must not be interpreted as encryption.
