# Changelog — Distributed Memory Architecture Atlas

## [2.1.0] — 2026-09-13

### Replaced the former rank-invariance security demonstration

The Cryptography Lab is now centered on **authenticated encryption plus randomized linear secret sharing**, rather than treating an invertible rank-preserving coordinate transform as a confidentiality mechanism.

### Added

- `core/secret_sharing.py` with exact finite-field LSSS/MSP machinery over the prime field `F_(2^521-1)`.
- Threshold span programs in Shamir/Vandermonde form.
- DNF monotone-span compiler from minimal authorized region sets.
- Exact coalition authorization by testing whether the target vector lies in the coalition row span.
- LSSS share generation with fresh OS-backed randomness.
- Exact linear reconstruction coefficients and secret reconstruction.
- AES-256-GCM encryption of the current semantic token using a fresh random 256-bit key.
- Secret sharing of the AEAD key rather than deterministic transformation of the plaintext token.
- Ed25519 signatures on every issued share.
- Tamper simulation and signature-failure detection before reconstruction.
- Three access-policy modes:
  - threshold LSSS;
  - Atlas-derived monotone span program;
  - custom DNF/MSP supplied as minimal authorized sets.
- Atlas-derived access policies for every lens:
  - full-rank systematic bases for combinatorial/probabilistic/information lenses;
  - spectral rank-`n-1` region families plus anchor;
  - coordinate-covering patch families for the sheaf lens.
- Coalition leakage reporting for the shared 256-bit key:
  - unauthorized: `I(K;X_U)=0` under the LSSS model;
  - authorized: `H(K|X_A)=0` after valid reconstruction.
- Availability-versus-compromise analysis:
  - exact binomial probabilities for threshold policies;
  - Monte Carlo evaluation for general monotone access structures.
- A dedicated `docs/SECURITY_MODEL.md`.
- New theorem/regression tests for LSSS reconstruction, DNF policies, AEAD round trips, perfect-secrecy classification, tamper detection, Atlas-derived policies and risk endpoints.

### Changed

- Atlas version advanced to 2.1.
- Runtime now depends on `cryptography>=46.0.0` for AES-GCM and Ed25519.
- The Cryptography Lab UI now exposes policy type, threshold, coalition selection, survival probability, compromise probability, risk trials, custom minimal authorized sets and share-tampering simulation.
- The old key/master-key input and visible-fraction rank-invariance workflow were removed.
- The old invertible monomial coordinate transform remains only in the result payload as an **algebraic-obfuscation comparison** explaining why rank invariance is not secrecy.
- Documentation now distinguishes:
  - cryptographic confidentiality/integrity;
  - access-control structure;
  - share authentication;
  - stochastic availability/compromise;
  - algebraic invariance experiments.

### Security scope

Atlas 2.1 makes a stronger and more precise distinction between mathematical security properties and production security. The LSSS privacy statement is exact under the implemented linear model with fresh uniform masks, while AES-GCM and Ed25519 are provided by the external `cryptography` implementation. The Atlas protocol/application has not been independently audited and is not a production KMS, VSS system or MPC framework.

---

## [2.0.0] — 2026-09-13

### Restored and generalized exploratory laboratories

Version 2.0 rebuilt the unified Atlas after the first consolidation preserved the five mathematical engines but reduced several exploratory capabilities from the standalone Spectral Hypergraph Memory V5 application.

Every primary mathematical lens received five research workspaces: Geometry, Graph/TDA, Core, Constraints/Diagnostics and Cryptography.

### Added

- Shared `approaches/exploration.py` for lens-aware geometry, region inspection and graph payloads.
- Shared graph/TDA renderer for all five lenses.
- Circular geometry, physical/virtual spectral regions, selectable region inspector and compact incidence view.
- 2D/3D graph rendering, deep zoom, six layouts, force controls, simplicial filtrations, Betti numbers and persistent Betti curves.
- Explicit distinction between ordinary simplicial homology and sheaf cohomology.
- Initial educational cryptography workspace based on invertible monomial transformations and access diagnostics.

### Limitation corrected by 2.1

The 2.0 cryptography workspace demonstrated structural invariance but did not supply confidentiality. Version 2.1 replaces it with AEAD + randomized LSSS/MSP key distribution and demotes the old transform to a comparison experiment.

---

## [1.0.0] — 2026-09-13

### Added

- Initial unified Atlas project.
- One persistent experiment shared by five mathematical approaches.
- Shared token generator, finite-field primitives, M/Q/R combinatorics and JSON import/export.
- Combinatorial, spectral, probabilistic, sheaf and information-theoretic analysis modules.
- Cross-approach Comparison Lab.
- Migration compatibility with legacy permutation-token JSON examples.
