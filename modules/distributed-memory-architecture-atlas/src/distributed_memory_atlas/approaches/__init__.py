from . import combinatorial, spectral, probabilistic, sheaf, information, comparison
REGISTRY={m.ID:m for m in (combinatorial,spectral,probabilistic,sheaf,information,comparison)}
def get(name):
    if name not in REGISTRY: raise KeyError(name)
    return REGISTRY[name]
def catalog():
    descriptions={
      "combinatorial":"Regions, contributor hypergraphs, systematic coding and recovery.",
      "spectral":"Finite-field CRT coordinates, local eigenspaces and projective reconstruction.",
      "probabilistic":"Random failures, rank distributions, recovery probability and stopping time.",
      "sheaf":"Local sections, restriction consistency, global sections and cohomology.",
      "information":"Entropy, mutual information, leakage, redundancy and channel benchmarks.",
      "comparison":"Compare invariants from all five lenses on the same experiment."
    }
    return [{"id":k,"name":v.NAME,"description":descriptions[k]} for k,v in REGISTRY.items()]
