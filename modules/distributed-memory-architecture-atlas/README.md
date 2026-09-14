# Distributed Memory Architecture Atlas

**Distributed Memory Architecture Atlas** is a unified research platform for exploring one distributed-memory experiment through five mathematical lenses:

1. **Combinatorial** — contributor regions, hypergraphs, systematic coding, rank and distance.
2. **Spectral hypergraph** — finite-field polynomial/CRT coordinates, local invariant subspaces and projective reconstruction.
3. **Probabilistic** — random region survival, recovery probabilities, rank distributions and stopping times.
4. **Sheaf-theoretic** — local sections, restrictions, global compatibility and cohomology.
5. **Information-theoretic** — entropy, mutual information, leakage, redundancy, capacity and rate–distortion benchmarks.

The central design rule is **one experiment, many lenses**: create/import a token once, then move through all five approaches without losing state.

## Version 2.1 — cryptographic access structures

Atlas 2.1 replaces the earlier rank-invariance security demonstration with a real cryptographic research pipeline:

```text
semantic token T
      |
      | AES-256-GCM with fresh random key K
      v
 authenticated ciphertext C

K -- randomized LSSS / monotone span program --> region shares X_1,...,X_N
                                      |
                                      +-- Ed25519 signatures authenticate issued shares
```

The old invertible monomial/basis-hiding transform is retained only as an **algebraic-obfuscation comparison**. It is no longer presented as the security mechanism.

The Cryptography Lab supports:

- threshold LSSS (Shamir/Vandermonde form);
- Atlas-derived monotone span programs;
- custom DNF access structures specified by minimal authorized region sets;
- exact authorized/unauthorized coalition tests;
- AES-256-GCM encryption/decryption of the current semantic token;
- Ed25519 share-tampering detection;
- exact LSSS key-leakage classification under the implemented finite-field model;
- availability-versus-compromise analysis;
- lens-specific interpretation of the same access structure.

For an unauthorized coalition `U`, the implemented LSSS model has the perfect-secrecy condition

```text
I(K ; X_U) = 0,
```

while an authorized coalition `A` reconstructs the key exactly,

```text
H(K | X_A) = 0.
```

These statements concern the mathematical LSSS model and fresh uniform masks. The Atlas application itself is a research/teaching system and has **not** undergone production security audit, side-channel review, hardened key lifecycle engineering, or protocol certification.

## Run

Python 3.10+ is required. Atlas 2.1 uses the `cryptography` package for audited implementations of AES-GCM and Ed25519.

```bash
python -m pip install -r requirements.txt
python app.py
```

or use `setup_env.sh` / `setup_env.bat`.

Open:

```text
http://127.0.0.1:8000
```

Optional environment variables:

```text
ATLAS_HOST=127.0.0.1
ATLAS_PORT=8000
ATLAS_QUIET=1
ATLAS_DEBUG=1
```

## Shared experiment

An experiment stores:

- semantic token `T`;
- finite-field projection `pi_p(T)`;
- prime field `F_p`;
- M/Q/R architecture mode;
- aggregation rule;
- spectral physical-storage policy;
- random seed;
- region limit used by cover-based computations;
- maximum cohomological/TDA dimension.

Structured token types remain JSON objects. Their finite-field projections are explicit and may be non-injective.

## Random token generator

The shared generator supports characters, words, integers, natural numbers, configurable vectors, cyclic permutations and polynomial functions. Generation is reproducible from an integer seed.

## Research workspaces

Every primary lens exposes five workspaces:

- **Geometry** — circular coordinate layout, selectable region universe and local inspector.
- **Graph / TDA lab** — 2D/3D graph, deep zoom, multiple layouts, force controls, simplicial filtrations and Betti curves.
- **Core lab** — native mathematics of the selected lens.
- **Constraints / diagnostics** — detailed algebraic/probabilistic/topological/information diagnostics.
- **Cryptography lab** — AEAD + LSSS/MSP access structures, authenticated shares, leakage and risk experiments.

The graph/TDA renderer is implemented once and consumes lens-aware incidence payloads from the Python backend.

## Cryptography Lab policy modes

### Threshold LSSS

A `t`-of-`N` Shamir/Vandermonde span program assigns one share row to each physical region. Any `t` regions reconstruct the AEAD key; fewer than `t` reveal no information about it in the LSSS model.

### Atlas-derived MSP

Atlas derives several inclusion-minimal authorized families from the current lens and compiles their OR-of-AND access rule into a DNF linear secret-sharing scheme.

- combinatorial / probabilistic / information: greedy full-rank systematic bases;
- spectral: local-constraint rank `n-1` plus the anchor;
- sheaf: inclusion-minimal patch families covering all token coordinates.

These are **policy-generation heuristics**. The resulting LSSS enforces the generated access policy exactly; the fact that a particular policy is desirable for a real deployment is a separate design question.

### Custom DNF/MSP

Users can enter minimal authorized sets such as:

```json
[[1,2,3],[2,4,5]]
```

which means `(R1 AND R2 AND R3) OR (R2 AND R4 AND R5)`. Atlas compiles this monotone formula into an explicit LSSS with fresh masks.

## Authenticated shares

Each issued share is signed with a fresh Ed25519 dealer signing key. A modified share fails signature verification and reconstruction is blocked.

This is **authenticated sharing, not full verifiable secret sharing (VSS)**: it detects post-issuance modification of dealer-issued shares but does not prove that a malicious dealer originally produced mutually consistent shares.

## Availability and compromise

The Cryptography Lab assigns independent per-region probabilities

- `q = P(region survives)`,
- `c = P(region is compromised)`.

It reports

```text
P_avail = P(surviving coalition is authorized)
P_comp  = P(compromised coalition is authorized).
```

Threshold policies use an exact binomial calculation. General monotone-span policies use Monte Carlo simulation.

## Comparison Lab

The Comparison Lab evaluates the same experiment through all five mathematical lenses and checks bridge invariants. For example, a uniform finite-field source observed through a rank-`r` linear map satisfies

```text
I(T;Y) = r log2(p).
```

## Project layout

```text
distributed-memory-architecture-atlas/
├── app.py
├── src/distributed_memory_atlas/
│   ├── core/
│   │   ├── experiment.py
│   │   ├── token_generator.py
│   │   ├── combinatorics.py
│   │   ├── finite_field.py
│   │   ├── polynomial.py
│   │   ├── aggregation.py
│   │   └── secret_sharing.py
│   └── approaches/
│       ├── combinatorial.py
│       ├── spectral.py
│       ├── probabilistic.py
│       ├── sheaf.py
│       ├── information.py
│       ├── comparison.py
│       ├── exploration.py
│       └── crypto_lab.py
├── static/
├── docs/
├── examples/
└── tests/
```

`core/secret_sharing.py` contains finite-field LSSS/MSP mechanics. `approaches/crypto_lab.py` orchestrates token encryption, region policies, share authentication, leakage/risk experiments and lens-specific interpretation. AES-GCM and Ed25519 themselves are delegated to `cryptography` rather than reimplemented.

## Documentation

- `docs/user-guide/ATLAS_USER_GUIDE.md` — complete application guide.
- `docs/foundations/FOUNDATIONAL_MATHEMATICS.md` — common and approach-specific mathematics, including LSSS/MSP foundations.
- `docs/SECURITY_MODEL.md` — threat model, security claims, non-claims and cryptographic protocol details.
- `docs/ARCHITECTURE.md` — software architecture and extension rules.
- `docs/MIGRATION_MAP.md` — mapping from Projects 1–5 into the Atlas.
- `VALIDATION.md` — validation results.
- `CHANGELOG.md` — Atlas history.

## Scope

Atlas is a mathematical research environment, not a production storage/key-management service. Exact finite-field and LSSS calculations are exact within their stated models; Monte Carlo values are estimates; derived access policies are research heuristics; classical channel/rate–distortion curves are benchmarks. Production use would require a full protocol and deployment threat model, persistent secure key storage, authenticated transport, side-channel hardening, lifecycle controls, independent cryptographic review and audit.
