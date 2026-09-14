# Security Model — Distributed Memory Architecture Atlas 2.1

## 1. Purpose

The Atlas Cryptography Lab is a research implementation of a **hybrid encrypted distributed-memory architecture**. It separates four concerns that were conflated in the earlier rank-invariance experiment:

1. confidentiality and integrity of the semantic token;
2. which region coalitions are authorized to recover the decryption key;
3. detection of modified issued shares;
4. stochastic availability and compromise risk.

The resulting protocol is

```text
semantic token T
      |
      | AES-256-GCM under fresh random K
      v
ciphertext C, tag, nonce, AAD

K -> randomized LSSS / MSP -> region shares
                              |
                              +-> Ed25519 signature per share
```

The old invertible monomial transform remains only as a comparison showing that algebraic rank invariance is not confidentiality.

## 2. Assets

The primary secret is the serialized semantic token `T`. The operational cryptographic secret is a fresh 256-bit AES key `K` used to encrypt `T`.

Region shares are not direct encodings of `T`; they are randomized linear shares of `K`.

## 3. Threat models

### 3.1 Read-only coalition compromise

An adversary reads all shares assigned to a coalition `U` of regions. The desired property is:

- if `U` is unauthorized, `I(K; X_U)=0` in the implemented LSSS model;
- if `A` is authorized, `H(K | X_A)=0` and the key reconstructs exactly.

### 3.2 Share modification

An adversary modifies a dealer-issued share after distribution. Atlas signs every share with Ed25519. Reconstruction is blocked if any selected share fails signature verification.

This is **share authentication**, not full verifiable secret sharing.

### 3.3 Region loss

Regions independently survive with probability `q`. Atlas estimates or computes the probability that the surviving coalition is authorized.

### 3.4 Region compromise

Regions independently become compromised with probability `c`. Atlas estimates or computes the probability that the compromised coalition is authorized.

## 4. Non-goals

Atlas 2.1 does not claim to solve:

- malicious-dealer consistency;
- proactive share refresh;
- asynchronous Byzantine agreement;
- secure multiparty computation;
- side-channel resistance;
- secure persistent key storage;
- authenticated transport;
- hardware-backed key protection;
- production key rotation/revocation;
- post-quantum public-key security;
- formal protocol composability.

## 5. AEAD layer

Atlas uses AES-256-GCM through the external `cryptography` package.

A fresh random key

`K <- {0,1}^256`

is generated for each run. A fresh 96-bit nonce is generated with the host OS CSPRNG. The authenticated associated data contains experiment/lens metadata but not the secret token.

The encrypted plaintext includes the experiment identity, semantic token, token type and finite-field projection.

No AES implementation is written by Atlas itself.

## 6. LSSS model

Let `F` be the prime field `F_(2^521-1)`. The AES key is interpreted as one field element because `2^256 < 2^521-1`.

A linear secret-sharing scheme is specified by a matrix

`M in F^(m x d)`

and a row-label map

`rho : {1,...,m} -> regions`.

For secret `s` and independent uniform masks `r_1,...,r_(d-1)`, define

`z = (s,r_1,...,r_(d-1))^T`

and share rows

`x = M z`.

A coalition `A` receives all rows whose labels belong to `A`.

### Authorization

Let `e_1=(1,0,...,0)`. Coalition `A` is authorized iff

`e_1` lies in the row span of `M_A`.

Equivalently there exists a reconstruction vector `lambda` such that

`lambda^T M_A = e_1^T`.

Then

`lambda^T X_A = s`.

### Privacy

If `U` is unauthorized, `e_1` is not in the row span of `M_U`. For the standard LSSS construction with independent uniform masks, the distribution of `X_U` is independent of `s`. Therefore

`I(S;X_U)=0`.

This is the exact mathematical secrecy claim made by the Atlas LSSS model.

## 7. Threshold LSSS

For `N` participants and threshold `t`, Atlas uses the Vandermonde/Shamir matrix

`M_(i,j)=alpha_i^(j-1)`

with distinct nonzero evaluation points `alpha_i`.

Any `t` rows reconstruct; fewer than `t` are unauthorized.

## 8. DNF monotone span programs

A custom or Atlas-derived policy is expressed as minimal authorized sets

`A_1,...,A_k`.

The policy is

`A_1 OR A_2 OR ... OR A_k`,

where each `A_j` is an AND of its regions.

Atlas compiles each AND clause as an independent additive sharing of the same secret. The OR is realized by distributing all clause shares. A region may therefore receive multiple share rows if it occurs in multiple clauses.

This construction is transparent and general, but not share-size optimal.

## 9. Atlas-derived access structures

Atlas may derive candidate minimal authorized sets from a selected mathematical lens.

- **Combinatorial / Probabilistic / Information:** greedy region families whose systematic rows reach rank `n`.
- **Spectral:** region families whose spectral constraint rows reach rank `n-1`, together with the scale anchor.
- **Sheaf:** inclusion-minimal patch families whose union covers every token coordinate.

These are **policy-generation heuristics**, not cryptographic theorems asserting that these are the only or optimal policies.

Once a policy is compiled into an LSSS, enforcement of that policy is exact in the LSSS model.

## 10. Share authentication

Each issued share record contains region ID, row ID, occurrence number and field value. Atlas computes a SHA-256 commitment to the span program and signs the canonical share record with a fresh Ed25519 dealer key.

The public verification key is safe to disclose.

If a selected share is modified after issuance while retaining its old signature, Ed25519 verification fails and Atlas blocks reconstruction.

### Not VSS

A malicious dealer could still sign mutually inconsistent shares. The current signature layer proves origin/integrity of issued shares, not global consistency of the dealer's sharing polynomial/span-program execution.

A future VSS module would require commitments/proofs or a protocol specifically designed for malicious-dealer security.

## 11. Information leakage reporting

For the 256-bit uniformly generated AEAD key, Atlas reports the ideal LSSS leakage profile:

- unauthorized coalition: mutual information `0` bits, conditional entropy `256` bits;
- authorized coalition: mutual information `256` bits, conditional entropy `0` bits.

This binary profile is appropriate for perfect linear secret sharing. Ramp schemes could later expose intermediate leakage levels.

## 12. Availability and compromise

Let `Gamma` denote the access structure.

For a random surviving region set `S`,

`P_avail = P(S in Gamma)`.

For a random compromised region set `C`,

`P_comp = P(C in Gamma)`.

Threshold policies admit exact binomial-tail calculations under homogeneous independent events. General DNF policies are estimated by Monte Carlo.

The displayed quantity

`P_avail * (1-P_comp)`

is only an independence proxy, not a formal system-security metric.

## 13. Lens-specific role

### Combinatorial

The region hypergraph supplies candidate cryptographic participants and minimal authorized coalitions.

### Spectral

Spectral rank identifies candidate reconstruction families, but spectral basis hiding is not the confidentiality primitive. Encryption and LSSS remain separate from the spectral representation.

### Probabilistic

The probability lens evaluates availability and compromise risk induced by the access structure.

### Sheaf

Patches can act as share holders and covering families can seed access policies. Sheaf cohomology is not itself assumed to be cryptographic hardness.

### Information

The information lens supplies the appropriate secrecy language: unauthorized coalitions should have zero mutual information about the key.

## 14. Why rank invariance was removed as the security mechanism

An invertible deterministic map `z=Mx` preserves all information about `x`. It may hide coordinates syntactically, but it does not create information-theoretic uncertainty. Rank preservation is therefore an algebraic invariant, not a confidentiality guarantee.

Atlas keeps that experiment only to make the contrast explicit.

## 15. Production warning

Do not use Atlas as a production KMS, secret-sharing service or encrypted storage protocol without independent cryptographic review. A production system would need secure persistent storage, authenticated transport, nonce/key lifecycle guarantees, access control around the dealer/reconstructor, audit logging, share revocation/refresh, side-channel analysis, malicious-dealer protection and operational recovery procedures.
