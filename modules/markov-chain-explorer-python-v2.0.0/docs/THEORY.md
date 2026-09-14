# Mathematical model

## Finite Markov chain

Let `S = {1,…,n}` be the state space. A row-stochastic matrix `P` satisfies `P_ij ≥ 0` and `Σ_j P_ij = 1`. A homogeneous Markov chain obeys

`Pr(X_{t+1}=j | X_t=i, X_{t-1},…,X_0) = P_ij`.

For a non-homogeneous chain the kernel depends on time: `P_t(i,j)`. Its transition law from time `s` to `t` is the ordered product `P(s,t) = P_s P_{s+1} ··· P_{t-1}`.

## Stochastic hypergraph interpretation

For each source state `i` and time `t`, define `H(t,i) = {i} ∪ supp P_t(i,·)`. Thus the translucent hyperedge is the complete outgoing transition context of `i` above the selected filtration threshold. Directed pairwise edges remain present and carry the exact transition probabilities. This is an enriched representation of the Markov kernel; it does not replace the matrix with a higher-order Markov law.

## Poisson constructions

Draw `N ~ Poisson(λ)`. From state `i`, move `N` positions. The cyclic rule uses `j = i + N (mod n)`; the capped rule uses `j = min(i+N,n-1)`. In both cases `P_ij = Σ exp(-λ) λ^k/k!`, where the sum is over counts mapped from `i` to `j`.

If the number of discrete jumps through an existing chain is independently `N ~ Poisson(λ)`, then `P_λ = E[P^N] = Σ_{k≥0} exp(-λ) λ^k/k! P^k = exp(λ(P-I))`.

## Classification and asymptotics

Communicating classes are the strongly connected components of the positive-probability digraph. A class is closed if it has no positive-probability edge leaving it. In a finite chain, states in closed classes are recurrent; all other states are transient. An irreducible, aperiodic finite chain is ergodic and has a unique stationary distribution `π` satisfying `πP=π`.

The entropy rate is `H = -Σ_i π_i Σ_j P_ij log₂ P_ij`. The Dobrushin coefficient is `δ(P)=1-min_{i,k}Σ_j min(P_ij,P_kj)`. The spectral diagnostic uses the additive reversibilization with respect to the computed stationary law.

## Hitting and reward calculations

For target set `A`, finite-horizon hitting probabilities are computed by dynamic programming with target mass removed after first arrival. Expected hitting times solve `h_i = 0` for `i ∈ A`, and `h_i = 1 + Σ_j P_ij h_j` for `i ∉ A`.

For rewards `r_i`, discount `γ`, and horizon `T`, the explorer computes `E[Σ_{t=0}^T γ^t r(X_t)] = Σ_{t=0}^T γ^t π_t r`.

## Topological filtration

At threshold `τ`, the directed chain is symmetrized with edge weight `max(P_ij,P_ji)`. The clique complex contains every clique whose edges survive `τ`. Boundary ranks over `GF(2)` yield `β₀`, `β₁`, and `β₂`. These invariants describe the thresholded support geometry, not recurrence by themselves.
