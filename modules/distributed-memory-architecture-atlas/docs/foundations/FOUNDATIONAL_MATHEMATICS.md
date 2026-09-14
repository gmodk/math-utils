# Mathematical Foundations of the Distributed Memory Architecture Atlas

## 1. Purpose of the unified formalism

The Atlas studies one distributed-memory experiment through five mathematical representations. The goal is not to assert that the five theories are equivalent. Rather, they share a common underlying experiment and ask different questions about it.

The common data are:

- a semantic token `T = (t_1,...,t_n)`;
- an optional finite-field representation `x = pi_p(T) in F_p^n`;
- a graded region geometry M, Q or R;
- a choice of which regions are physically materialized.

The five lenses then study structure, constraints, uncertainty, local-to-global compatibility and information.

---

# Part I — Common foundations

## 2. Tokens

Let `X` be an arbitrary JSON-serializable semantic alphabet. A token is an element

`T in X^n`.

Examples used by the Atlas include scalar integers, natural numbers, characters, words, vectors, permutations and polynomial-function descriptors.

The semantic alphabet is deliberately not assumed to be a field.

## 3. Finite-field projection

Several analyses require linear algebra. For a prime `p`, the Atlas therefore stores an explicit map

`pi_p : X -> F_p`

and applies it coordinatewise:

`x = pi_p(T) in F_p^n`.

For native integer tokens, this can be ordinary reduction modulo `p`. For structured objects the built-in generator uses deterministic projections, for example weighted coordinate sums for vectors or a cyclic-shift exponent for generated cyclic permutations.

These projections need not be injective. Consequently `x` is an **analysis representation**, not an assertion that the semantic object and field vector are equivalent.

This distinction is essential. Algebraic reconstruction of `x` does not automatically imply semantic reconstruction of arbitrary `T` unless `pi_p` is injective on the source family or additional semantic data are retained.

## 4. Prime fields

For prime `p`,

`F_p = Z/pZ`

is a field. Every nonzero element has a multiplicative inverse. Gaussian elimination is therefore exact modulo `p`, giving well-defined notions of matrix rank, nullspace and invertibility.

The Atlas uses dependency-free modular RREF. No floating-point tolerance enters finite-field rank computations.

## 5. M/Q/R graded region families

For `[n] = {1,...,n}`, define

`F_K(n) = {S subseteq [n] : |S| in K}`.

The three standard layer sets are

`M : K = {0,2,4}`,

`Q : K = {0,1,2}`,

`R : K = {0,2,3}`.

Their abstract cardinalities are

`|F_K(n)| = sum_{k in K} C(n,k)`.

Thus

`M(n) = 1 + C(n,2) + C(n,4)`,

`Q(n) = 1 + n + C(n,2)`,

`R(n) = 1 + C(n,2) + C(n,3)`.

The grade-zero element has different semantics in different lenses. In the spectral model it is used as global anchor metadata; in cover-based sheaf computations it is excluded because its support is empty.

---

# Part II — Combinatorial lens

## 6. Systematic distributed memory

The Atlas preserves the systematic V3 interpretation from the combinatorial project.

The first `n` physical regions store the token coordinates directly. Remaining regions use contributor subsets until the declared M/Q/R capacity is reached.

For a field-valued token `x in F_p^n`, every region support `S` determines an incidence row

`a_S in F_p^n`,

where `(a_S)_i = 1` when `i in S` and zero otherwise.

The resulting systematic observation matrix has the form

`A = [ I_n ; B ]`.

Because `I_n` is present,

`rank(A) = n`

over every field.

This gives deterministic recovery from all direct regions and provides additional redundant aggregate observations.

## 7. Kernel/rank criterion

For a linear encoder

`E(x) = A x`,

injectivity is equivalent to

`ker A = {0}`,

which is equivalent to

`rank A = n`.

This is the central deterministic algebraic recovery test in the systematic lens.

## 8. Erasures

If a set of rows is erased and `A_S` denotes the surviving row matrix, then exact linear recovery is possible exactly when

`rank(A_S) = n`.

Thus region erasure is converted into a random or deterministic row-deletion problem.

## 9. Binary code and minimum distance

Over `F_2`, the map

`x -> A x`

defines a binary linear code. Its minimum distance is

`d_min = min_{x != 0} wt(Ax)`.

Then the code detects up to `d_min-1` errors, corrects up to

`floor((d_min-1)/2)`

errors, and tolerates any `d_min-1` erasures.

The Atlas exhaustively computes this invariant only for modest `n`, because enumerating all nonzero messages costs `2^n-1` evaluations.

## 10. Hypergraph viewpoint

Token coordinates are vertices and contributor subsets are hyperedges. Vertex degree measures how many regions depend on a coordinate. This incidence structure is independent of the semantic aggregation used to display region values.

This separation is useful: one may investigate the same contributor geometry with numerical sums, string-like aggregates, vector sums or permutation composition.

---

# Part III — Spectral hypergraph lens

## 11. Polynomial coordinates

Let

`x = (x_0,...,x_{n-1}) in F_p^n`.

Associate the polynomial

`f_x(z) = sum_{j=0}^{n-1} x_j z^j`.

When `p > n`, choose distinct evaluation points

`alpha_i = i`, `i=1,...,n`.

Define

`y_i = f_x(alpha_i)`.

The vector `y` is an evaluation/CRT representation of the same coefficient polynomial. Because the evaluation points are distinct, the Vandermonde map from coefficients to evaluations is invertible.

Equivalently, the linear factors `z-alpha_i` are pairwise coprime and the polynomial CRT gives an isomorphism on the degree-`< n` class.

## 12. Local spectral lines

For a region `S`, restrict the CRT vector:

`y_S = (y_i)_{i in S}`.

The local memory condition is not primarily an aggregate scalar. It is the one-dimensional subspace

`L_S = span(y_S)`.

One convenient operator realizing this line is a rank-one idempotent

`P_S = y_S w_S^T`

with

`w_S^T y_S = 1`.

Then

`P_S y_S = y_S`

and

`ker(P_S-I) = span(y_S)`.

The implementation chooses a pivot coordinate of `y_S` to construct a dual vector `w_S` exactly over `F_p`.

## 13. Lifted constraints

Let `E_S` denote restriction from global CRT coordinates to region `S`. A local condition can be written

`(P_S-I) E_S y = 0`.

Stacking all active region constraints gives

`H y = 0`.

If

`rank H = n-1`,

then

`dim ker H = 1`,

so the surviving constraints determine the projective line `span(y)`.

A scalar anchor fixes scale, after which interpolation recovers the polynomial coefficients `x`.

Thus the characteristic deterministic target of the spectral lens is

`rank H = n-1`,

not `rank H = n`.

## 14. Rank-basis physical storage

The abstract M/Q/R universe can contain many local constraints. The `rank-basis` policy keeps the full universe conceptually but greedily activates only regions that increase the rank of the stacked constraint system until the target `n-1` is reached.

This is a matroid-like independence heuristic over row spaces. It provides a compact physical realization but is not claimed to minimize every possible storage objective globally.

## 15. TDA overlay

Every active nonempty region support may be viewed as a simplex. Closing under faces yields a simplicial complex. Over `F_2`, boundary matrices produce Betti numbers

`beta_k = dim C_k - rank partial_k - rank partial_{k+1}`.

The resulting topology describes the incidence shape of active spectral supports; it is not the same invariant as sheaf cohomology below.

---

# Part IV — Probabilistic lens

## 16. Probability space of region survival

Let the physical regions be indexed by `1,...,N`. A survival state is

`omega in {0,1}^N`.

Under an iid Bernoulli survival model with parameter `q`,

`P(omega) = q^{|omega|}(1-q)^{N-|omega|}`.

Because the sample space is finite, all events are measurable under the power-set sigma algebra.

## 17. Systematic recovery event

For a survival state `omega`, let `A_omega` contain the surviving systematic rows. The recovery event is

`R_sys = {omega : rank(A_omega)=n}`.

The reliability function is

`P_rec(q) = P_q(R_sys)`.

This differs from minimum distance. Minimum distance is a worst-case threshold. `P_rec(q)` weights erasure patterns by a probability law.

Two codes with equal minimum distance can therefore have different reliability curves.

## 18. Spectral recovery event

For the spectral model, let `H_omega` be the stack of surviving active local constraints. Reconstruction additionally requires the global anchor.

The event is

`R_spec = {omega : anchor survives and rank(H_omega)>=n-1}`.

This exposes a tradeoff in rank-basis storage: fewer physical regions reduce storage, but can reduce stochastic redundancy.

## 19. Monte Carlo estimator

For iid trials with recovery indicators `Z_1,...,Z_m`, define

`P_hat = (1/m) sum Z_i`.

Then

`E[P_hat] = P_rec`

and by the law of large numbers `P_hat` converges to `P_rec` as `m` grows.

The Atlas reports a Wilson interval rather than relying on the simplest normal approximation near probabilities close to zero or one.

## 20. Random rank

The surviving rank

`R(omega)=rank(A_omega)`

or

`rank(H_omega)`

is itself a random variable. Its distribution reveals partial information even when full recovery fails.

## 21. Random reveal and stopping time

Reveal regions in random order and let `R_k` be the rank after `k` regions. Define

`tau = inf{k : R_k reaches the recovery target}`.

With the natural filtration generated by the revealed regions, `tau` is a stopping time. Its expected value measures how many randomly encountered regions are typically needed before the memory becomes reconstructible.

---

# Part V — Sheaf-theoretic lens

## 22. Region cover and nerve

Use nonempty memory supports `U_1,...,U_m` as a cover of the coordinate set. The nerve `N(U)` has one vertex per region and a simplex

`{i_0,...,i_k}`

whenever

`U_{i_0} cap ... cap U_{i_k} != empty`.

Thus topology is generated by overlap relations among memory regions rather than directly by token coordinates.

## 23. Coordinate sheaf

To every nerve simplex `sigma`, associate the vector space

`F(sigma) = F_p^{intersection(sigma)}`.

If `sigma` is a face of `tau`, then

`intersection(tau) subseteq intersection(sigma)`,

and the restriction map projects coordinates from the larger support space to the smaller intersection.

This defines a cellular sheaf over the finite nerve.

## 24. Cochains and coboundaries

The degree-`k` cochain group is the direct sum

`C^k = direct_sum_{sigma in N_k} F(sigma)`.

Signed restriction maps define

`delta^k : C^k -> C^{k+1}`.

The compatibility of restrictions implies

`delta^{k+1} delta^k = 0`.

Therefore the cohomology groups are

`H^k = ker(delta^k) / im(delta^{k-1})`.

The Atlas computes their dimensions using exact finite-field ranks:

`dim H^k = dim C^k - rank(delta^k) - rank(delta^{k-1})`.

## 25. Global sections

`H^0` is the space of globally compatible local sections. A concrete global token `x` restricts to local vectors `x|_{U_i}`. On overlaps these restrictions agree identically, so the uncorrupted token-derived sections pass the Atlas compatibility check.

Higher cohomology records obstruction structure associated with the chosen sheaf and overlap geometry.

## 26. Truncation caveat

If the complex is computed only through degree `d`, then `H^d` depends in principle on `delta^d : C^d -> C^{d+1}`. If `C^{d+1}` is omitted, the final reported degree should be treated as provisional.

---

# Part VI — Information-theoretic lens

## 27. Source model

The exact rank-information identity assumes

`T ~ Uniform(F_p^n)`.

Then every source vector has probability `p^{-n}` and

`H(T) = log_2(p^n) = n log_2 p` bits.

## 28. Linear observations

Let

`Y = A T`

with `rank A = r`.

The image of `A` has `p^r` elements. Because a uniform finite-field source maps uniformly onto the image,

`H(Y) = r log_2 p`.

Because `Y` is deterministic given `T`,

`H(Y|T)=0`.

Therefore

`I(T;Y)=H(Y)-H(Y|T)=r log_2 p`.

The kernel has dimension `n-r`, and every observation is consistent with `p^{n-r}` source states. Hence

`H(T|Y)=(n-r) log_2 p`.

This gives the exact decomposition

`H(T) = I(T;Y) + H(T|Y)`.

## 29. Marginal information gain

Adding a region row can increase rank by zero or more. For a scalar systematic row it increases rank by at most one. A rank increment `Delta r` contributes exactly

`Delta I = Delta r log_2 p`

bits under the uniform source model.

The greedy information profile therefore parallels greedy rank-basis selection, although it operates on the systematic observation matrix and optimizes a different object than the spectral constraints.

## 30. Information under erasure

When rows survive randomly, rank becomes random. Because the information formula is linear in rank,

`E[I(T;Y_omega)] = E[rank(A_omega)] log_2 p`.

Likewise

`E[H(T|Y_omega)] = (n-E[rank(A_omega)]) log_2 p`.

Thus the probabilistic and information-theoretic lenses meet exactly through expected random rank under the stated linear source model.

## 31. p-ary symmetric-channel benchmark

For symbol error probability `e`, the classical symmetric `p`-ary channel capacity per source symbol is

`C(e) = log_2 p - H_b(e) - e log_2(p-1)`

for the usual range up to `(p-1)/p`.

This is a benchmark channel model. It is not derived from the Atlas region-failure architecture.

## 32. p-ary Hamming rate–distortion benchmark

For a uniform `p`-ary source under Hamming distortion,

`R(D) = log_2 p - H_b(D) - D log_2(p-1)`

on the nontrivial range, clipped at zero beyond the maximal useful distortion.

Again, this is included as a theoretical reference curve.

---

# Part VII — Bridges among the approaches

## 33. Combinatorial rank and information

For the same systematic matrix `A`, the combinatorial lens computes

`r = rank(A)`.

The information lens converts that same invariant into bits:

`I(T;AT) = r log_2 p`.

The Atlas comparison module explicitly tests that both lenses use the same `r`.

## 34. Rank and probabilistic recovery

The deterministic condition

`rank(A_S)=n`

becomes a random event when `S` is selected by a failure process.

Probability therefore does not replace the combinatorial rank criterion; it puts a measure on the family of rank-sufficient subsets.

The same relation holds for the spectral target `rank(H_S)=n-1` plus anchor survival.

## 35. Spectral constraints and sheaf language

The spectral lens associates local lines or constraint spaces to hyperedges. The sheaf lens asks whether local data on overlapping patches are compatible and what global-section space remains.

A deeper future construction could define a data-dependent spectral sheaf whose stalks are the local spectral lines themselves. The current Atlas keeps the two constructions separate so their invariants remain interpretable.

## 36. TDA and sheaf cohomology

Spectral TDA computes ordinary simplicial homology of active region supports. Sheaf cohomology computes cohomology of data spaces attached to the nerve of a cover.

They may respond to related incidence geometry, but there is no general equality between the displayed Betti numbers and sheaf cohomology dimensions.

## 37. Shared research question

The unified platform makes it possible to ask when different thresholds coincide. Examples include:

- the smallest region family with full systematic rank;
- the smallest spectral family with rank `n-1`;
- the region count at which `H^0` becomes uniquely constrained;
- the point at which conditional entropy becomes zero;
- stochastic thresholds where recovery probability rapidly transitions from near zero to near one.

Discovering structural hypotheses under which these thresholds are related is a research problem, not an assumption built into the software.

---

# Part VIII — Scope and status

The Atlas is an exploratory mathematical platform. Exact finite-field, rank, cohomology and LSSS calculations are exact within their stated models. Monte Carlo outputs are estimates. Greedy rank-basis/access-policy selection is heuristic. Classical channel and rate–distortion curves are benchmarks. Structured-token projections may lose semantic information.

Atlas 2.1 contains a genuine cryptographic construction at the level of **AEAD + randomized linear secret sharing**, but the application/protocol as a whole is not claimed to be production hardened or independently audited.

---

# Part IX — Shared geometric and topological exploration

## 38. Incidence geometry

For coordinate set `V={1,...,n}` and region family `R`, every approach admits an incidence relation `i in S`. The browser renders a bipartite coordinate-region graph. This is a common incidence skeleton, not a claim that contributor regions, spectral constraints, random survival blocks, sheaf patches and information observations are identical mathematical objects.

## 39. Simplicial lift and ordinary homology

A nonempty support `S` is treated as a simplex together with its faces. A filtration value `tau(S)` yields a family `K_t`. Boundary ranks are computed over `F_2`, and

`beta_k(t)=dim ker(partial_k)-dim im(partial_(k+1))`.

This ordinary homology is distinct from sheaf cohomology `H^k(X;F)`.

## 40. Lens-specific filtrations

The common TDA engine can use support cardinality, region order, physical-first order or a lens-specific scalar score. Unless separately supported by a theorem, these scores are exploratory filtration choices.

---

# Part X — Cryptographic access structures

## 41. Why deterministic basis hiding is not secrecy

An invertible transformation

`z=Mx`,  `M in GL_n(F_p)`

preserves the information content of `x`. It may preserve rank intentionally and generally leaks many algebraic invariants. It therefore cannot serve as the Atlas confidentiality primitive merely because the matrix is key-derived.

Atlas 2.1 retains such transforms only as an algebraic-obfuscation comparison.

## 42. Hybrid encryption architecture

Let `T` be the semantic token. Generate a fresh random 256-bit key `K` and compute

`C = AEAD_Enc_K(T; AAD)`

using AES-256-GCM. The token is therefore protected by a standard authenticated-encryption primitive.

The distributed-memory problem is moved to the key: regions receive secret shares of `K`, not deterministic transforms of `T`.

## 43. Linear secret sharing

Work over the prime field

`F_q`,  `q=2^521-1`.

The 256-bit AES key can be embedded as one element `s in F_q`.

Let

`M in F_q^(m x d)`

be a share-generating matrix with row-label map `rho`. Choose independent uniform masks

`r_1,...,r_(d-1) in F_q`

and define

`z=(s,r_1,...,r_(d-1))^T`.

The share vector is

`x=Mz`.

Region `R_i` receives all rows whose label equals `i`.

## 44. Authorization theorem

Let `M_A` denote the rows labeled by coalition `A`, and let

`e_1=(1,0,...,0)`.

Coalition `A` is authorized iff

`e_1 in rowspan(M_A)`.

If authorized, there exists `lambda` satisfying

`lambda^T M_A=e_1^T`.

Therefore

`lambda^T X_A = lambda^T M_A z = e_1^T z = s`.

Thus authorized reconstruction is exact.

## 45. Privacy of unauthorized coalitions

If `U` is unauthorized then `e_1` is not in `rowspan(M_U)`. By finite-dimensional linear algebra, there exists a kernel direction of the observation map whose first coordinate is nonzero. Shifting the sharing vector along that direction changes the secret while leaving `X_U` unchanged.

With independent uniform masks, every possible secret induces the same distribution on `X_U`. Hence

`I(S;X_U)=0`

and

`H(S|X_U)=H(S)`.

This is the central secrecy theorem used by the Atlas LSSS model.

## 46. Threshold span programs

For participants indexed by distinct nonzero field elements `alpha_i`, the threshold matrix is Vandermonde:

`M_(i,j)=alpha_i^(j-1)`,  `j=1,...,t`.

This is Shamir secret sharing in linear-span form. Any `t` participants reconstruct; every coalition of size less than `t` is perfectly private.

## 47. DNF monotone span programs

Suppose the minimal authorized sets are

`A_1,...,A_k`.

The access function is the monotone formula

`A_1 OR ... OR A_k`,

where each `A_j` is an AND-clause.

Atlas compiles each AND clause by independent additive sharing of the same secret. The final member of a clause receives

`s - sum r_i`,

while the preceding members receive fresh random masks. Since different clauses use independent randomness, any coalition that fails every complete clause remains independent of the secret.

The construction is general and transparent, although not share-size optimal.

## 48. Atlas-derived access structures

Atlas can derive candidate minimal authorized coalitions from each lens:

- combinatorial/probabilistic/information: systematic row families reaching rank `n`;
- spectral: constraint families reaching rank `n-1` together with the anchor;
- sheaf: inclusion-minimal patch families covering all token coordinates.

These derived families define an **access-policy heuristic**. Once compiled into an LSSS, the cryptographic enforcement of that policy is exact; the claim that the chosen policy is operationally optimal is not.

## 49. Authenticated shares

Every share row is signed using Ed25519 together with a SHA-256 commitment to the span program. If a share value is altered after issuance, signature verification fails and Atlas blocks reconstruction.

This provides origin/integrity of dealer-issued shares. It is not full verifiable secret sharing because a malicious dealer could still issue and sign inconsistent shares.

## 50. Leakage in bits

The AES key is generated uniformly from `2^256` possibilities. Under perfect LSSS:

Unauthorized coalition `U`:

`I(K;X_U)=0`,  `H(K|X_U)=256` bits.

Authorized coalition `A`:

`I(K;X_A)=256`,  `H(K|X_A)=0` bits.

Unlike the earlier rank-invariance display, these are secrecy/reconstruction statements for the sharing model.

## 51. Availability and compromise

Let `Gamma` be the access structure. If `S(omega)` is the random surviving region set,

`P_avail = P(S in Gamma)`.

If `C(omega)` is the random compromised region set,

`P_comp = P(C in Gamma)`.

Under homogeneous independent events, threshold policies give exact binomial tails. General DNF policies are evaluated by Monte Carlo.

This creates a natural design tension: increasing the number of authorized coalitions generally improves availability while potentially increasing compromise probability.

## 52. Cryptographic role of the five lenses

The combinatorial lens designs participant/access geometry. The spectral lens can propose reconstruction-based authorized sets but does not supply confidentiality. The probabilistic lens studies availability/compromise. The sheaf lens supplies cover-based policy candidates and local-to-global structure. The information lens supplies the secrecy criterion `I(K;X_U)=0`.

This is one of the clearest examples in the Atlas where all five mathematical approaches operate on the same underlying distributed-memory object without being collapsed into one theory.

## 53. Security boundary

AES-GCM and Ed25519 are delegated to the external `cryptography` implementation. Atlas implements the educational LSSS/MSP layer directly so its finite-field mathematics remains inspectable.

The code has not undergone independent security audit, constant-time/side-channel review, hardened secret erasure, secure persistence, transport security or lifecycle analysis. The Cryptography Lab should therefore be interpreted as a mathematically serious research prototype, not a production key-management service.
