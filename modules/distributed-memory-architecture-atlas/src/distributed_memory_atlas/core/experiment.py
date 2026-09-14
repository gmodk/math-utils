from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any
import uuid
from .finite_field import require_prime
from .token_generator import generate_random_token

@dataclass
class Experiment:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = "Untitled experiment"
    token_type: str = "natural_numbers"
    token: list[Any] = field(default_factory=lambda: [1,2,3,4,5,6])
    field_projection: list[int] = field(default_factory=lambda: [1,2,3,4,5,6])
    projection_method: str = "integer residue modulo p"
    seed: int = 1
    p: int = 101
    mode: str = "M"
    aggregation: str = "mixed"
    spectral_policy: str = "rank-basis"
    region_limit: int = 18
    max_dim: int = 2
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def n(self) -> int:
        return len(self.token)

    def validate(self):
        if not self.token:
            raise ValueError("token must not be empty")
        require_prime(self.p)
        if self.mode.upper() not in {"M","Q","R"}:
            raise ValueError("mode must be M, Q, or R")
        if self.spectral_policy not in {"full","rank-basis"}:
            raise ValueError("spectral_policy must be full or rank-basis")
        if len(self.field_projection) != len(self.token):
            raise ValueError("field_projection length must equal token length")
        self.field_projection = [int(x) % self.p for x in self.field_projection]
        return self

    def payload(self) -> dict:
        d = asdict(self)
        d["n"] = self.n
        d["field"] = f"F_{self.p}"
        return d

    def regenerate(self, *, dimension: int | None = None, token_type: str | None = None,
                   seed: int | None = None, object_dimension: int | None = None) -> dict:
        result = generate_random_token(
            dimension or self.n,
            token_type or self.token_type,
            seed=self.seed if seed is None else seed,
            p=self.p,
            object_dimension=object_dimension,
        )
        self.token_type = result["type"]
        self.token = result["token"]
        self.field_projection = result["field_projection"]
        self.projection_method = result["projection_method"]
        self.seed = result["seed"]
        self.metadata["generator"] = result.get("parameters", {})
        if self.token_type == "cyclic_permutations":
            self.aggregation = "compose"
        elif self.aggregation == "compose":
            self.aggregation = "mixed"
        self.validate()
        return result

    @classmethod
    def from_payload(cls, data: dict) -> "Experiment":
        token = data.get("token")
        p = int(data.get("p", 101))
        if token is None:
            e = cls(p=p)
            e.regenerate(
                dimension=int(data.get("dimension", 6)),
                token_type=data.get("token_type", "natural_numbers"),
                seed=int(data.get("seed", 1)),
                object_dimension=data.get("object_dimension"),
            )
        else:
            projection = data.get("field_projection")
            if projection is None:
                # Imported arbitrary JSON is projected deterministically through the generator hash rule.
                import hashlib, json
                projection = [int.from_bytes(hashlib.sha256(json.dumps(v, sort_keys=True, ensure_ascii=False).encode()).digest(), "big") % p for v in token]
            e = cls(
                id=str(data.get("id") or uuid.uuid4().hex[:12]),
                name=str(data.get("name", "Imported experiment")),
                token_type=str(data.get("token_type", "imported")),
                token=list(token),
                field_projection=list(projection),
                projection_method=str(data.get("projection_method", "SHA-256 canonical JSON hash modulo p")),
                seed=int(data.get("seed", 1)), p=p,
                mode=str(data.get("mode", "M")).upper(),
                aggregation=str(data.get("aggregation", "mixed")),
                spectral_policy=str(data.get("spectral_policy", "rank-basis")),
                region_limit=int(data.get("region_limit", 18)),
                max_dim=int(data.get("max_dim", 2)),
                metadata=dict(data.get("metadata", {})),
            )
        e.name = str(data.get("name", e.name))
        e.mode = str(data.get("mode", e.mode)).upper()
        e.aggregation = str(data.get("aggregation", e.aggregation))
        e.spectral_policy = str(data.get("spectral_policy", e.spectral_policy))
        e.region_limit = int(data.get("region_limit", e.region_limit))
        e.max_dim = int(data.get("max_dim", e.max_dim))
        return e.validate()
