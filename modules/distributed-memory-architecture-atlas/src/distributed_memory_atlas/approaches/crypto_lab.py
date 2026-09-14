from __future__ import annotations

"""Cryptography laboratory for Distributed Memory Architecture Atlas.

Security architecture
---------------------
1. The semantic token is serialized and encrypted with AES-256-GCM (AEAD).
2. The random 256-bit AEAD key is embedded as one element of F_(2^521-1).
3. A randomized linear secret-sharing scheme distributes that key across Atlas
   regions according to a threshold or monotone-span access structure.
4. Each share is signed by the dealer with Ed25519 so accidental/malicious
   modification of an issued share is detectable before reconstruction.

The Ed25519 layer is *authenticated sharing*, not full verifiable secret sharing:
it authenticates dealer-issued shares but does not prove that a malicious dealer
created mutually consistent shares.  The old invertible monomial transform is
retained only as an algebraic-obfuscation comparison.
"""

import base64
import hashlib
import json
import math
import os
import random
from typing import Iterable, Sequence

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from ..core.finite_field import inv, rank
from ..core.secret_sharing import (
    LSSS_PRIME,
    SpanProgram,
    dnf_span_program,
    policy_summary,
    reconstruct_secret,
    share_secret,
    threshold_span_program,
)
from . import combinatorial
from . import exploration


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def _canonical(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str).encode("utf-8")


def _rng_seed(*parts: str) -> int:
    return int.from_bytes(hashlib.sha256("|".join(parts).encode()).digest(), "big")


def _physical_regions(exp, approach: str, q: float) -> list[dict]:
    raw, _ = exploration.region_model(exp, approach, q)
    active = [r for r in raw if r.get("active", True)]
    return active or raw


def _greedy_rank_basis(blocks: Sequence[dict], target: int, p: int, order: Sequence[int]) -> list[int]:
    rows: list[list[int]] = []
    rr = 0
    chosen: list[int] = []
    for idx in order:
        block = blocks[idx]
        block_rows = block.get("rows", [])
        if not block_rows:
            continue
        tr = rank(rows + block_rows, p)
        if tr > rr:
            rows += block_rows
            rr = tr
            chosen.append(int(block["id"]))
            if rr >= target:
                break
    return sorted(set(chosen)) if rr >= target else []


def _rank_access_sets(exp, approach: str, q: float, max_sets: int = 4) -> list[list[int]]:
    raw, _ = exploration.region_model(exp, approach, q)
    # Access policies are compiled over physically materialized share holders.
    # Virtual regions remain available to geometry/TDA exploration but do not
    # silently become cryptographic participants.
    raw = [r for r in raw if r.get("active", True)]
    # Systematic lenses share the same linear row model.
    if approach in {"combinatorial", "probabilistic", "information"}:
        blocks = [r for r in raw if r.get("rows")]
        target = exp.n
        orders = [
            list(range(len(blocks))),
            list(reversed(range(len(blocks)))),
            sorted(range(len(blocks)), key=lambda i: (len(blocks[i].get("subset0", ())), blocks[i]["id"])),
            sorted(range(len(blocks)), key=lambda i: (-len(blocks[i].get("subset0", ())), blocks[i]["id"])),
        ]
        sets = [_greedy_rank_basis(blocks, target, exp.p, o) for o in orders]
    elif approach == "spectral":
        anchor_ids = [int(r["id"]) for r in raw if r.get("kind") == "anchor"]
        blocks = [r for r in raw if r.get("kind") == "spectral" and r.get("rows")]
        target = max(0, exp.n - 1)
        orders = [
            list(range(len(blocks))),
            list(reversed(range(len(blocks)))),
            sorted(range(len(blocks)), key=lambda i: (len(blocks[i].get("subset0", ())), blocks[i]["id"])),
            sorted(range(len(blocks)), key=lambda i: (-len(blocks[i].get("subset0", ())), blocks[i]["id"])),
        ]
        sets = []
        for order in orders:
            base = _greedy_rank_basis(blocks, target, exp.p, order)
            if target == 0 or base:
                sets.append(sorted(set(anchor_ids + base)))
    else:  # sheaf: authorized examples are coordinate-covering patch families.
        regs = [r for r in raw if r.get("subset0")]
        universe = set(range(exp.n))
        variants = [
            sorted(range(len(regs)), key=lambda i: (-len(regs[i]["subset0"]), regs[i]["id"])),
            sorted(range(len(regs)), key=lambda i: (len(regs[i]["subset0"]), regs[i]["id"])),
            list(range(len(regs))),
            list(reversed(range(len(regs)))),
        ]
        sets = []
        for order in variants:
            covered: set[int] = set(); chosen: list[int] = []
            remaining = list(order)
            while covered != universe and remaining:
                # Among the remaining order, choose the first region giving maximal new cover.
                best = max(remaining, key=lambda i: (len(set(regs[i]["subset0"]) - covered), -remaining.index(i)))
                gain = set(regs[best]["subset0"]) - covered
                remaining.remove(best)
                if not gain:
                    continue
                covered |= set(regs[best]["subset0"])
                chosen.append(int(regs[best]["id"]))
            if covered == universe:
                # Delete redundant patches to make the set inclusion-minimal.
                for rid in chosen[:]:
                    trial = [x for x in chosen if x != rid]
                    cov = set()
                    for x in trial:
                        rr = next(r for r in regs if int(r["id"]) == x)
                        cov |= set(rr["subset0"])
                    if cov == universe:
                        chosen.remove(rid)
                sets.append(sorted(chosen))
    unique: list[list[int]] = []
    for s in sets:
        if s and s not in unique:
            unique.append(s)
        if len(unique) >= max_sets:
            break
    return unique


def _parse_custom_sets(value) -> list[list[int]]:
    if value is None or value == "":
        return []
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        raise ValueError("custom minimal sets must be a JSON array of region-ID arrays")
    return [[int(x) for x in row] for row in value]


def _build_policy(exp, approach: str, policy_type: str, threshold: int | None, q: float, custom_sets=None) -> SpanProgram:
    physical = _physical_regions(exp, approach, q)
    participants = sorted({int(r["id"]) for r in physical})
    if not participants:
        raise ValueError("the current lens has no physical regions to receive shares")
    policy_type = str(policy_type or "threshold").lower()
    if policy_type == "threshold":
        default_t = max(1, min(len(participants), math.ceil(0.6 * len(participants))))
        t = default_t if threshold in (None, "", 0) else int(threshold)
        return threshold_span_program(participants, max(1, min(t, len(participants))))
    if policy_type == "atlas-derived":
        minimal = _rank_access_sets(exp, approach, q)
        if not minimal:
            raise ValueError("could not derive an authorized family from this architecture")
        return dnf_span_program(minimal)
    if policy_type == "custom-dnf":
        minimal = _parse_custom_sets(custom_sets)
        known = set(participants)
        if any(not set(row) <= known for row in minimal):
            raise ValueError("custom authorized sets reference non-physical/unknown region IDs")
        return dnf_span_program(minimal)
    raise ValueError("policy_type must be threshold, atlas-derived, or custom-dnf")


def _policy_commitment(program: SpanProgram) -> str:
    h = hashlib.sha256()
    h.update(str(program.prime).encode())
    for label, row in zip(program.labels, program.matrix):
        h.update(str(label).encode()); h.update(b":")
        for x in row:
            h.update(int(x).to_bytes(66, "big"))
    return h.hexdigest()


def _signed_shares(program: SpanProgram, secret: int):
    shares = share_secret(secret, program)
    commitment = _policy_commitment(program)
    signer = Ed25519PrivateKey.generate()
    public = signer.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    for sh in shares:
        payload = _canonical({"policy": commitment, "row_id": sh["row_id"], "region": sh["region"], "occurrence": sh["occurrence"], "value": str(sh["value"])})
        sh["signature"] = _b64(signer.sign(payload))
    return shares, commitment, public


def _verify_shares(shares: Sequence[dict], commitment: str, public_key_bytes: bytes) -> tuple[list[int], list[int]]:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    verifier = Ed25519PublicKey.from_public_bytes(public_key_bytes)
    valid, invalid = [], []
    for sh in shares:
        payload = _canonical({"policy": commitment, "row_id": sh["row_id"], "region": sh["region"], "occurrence": sh["occurrence"], "value": str(sh["value"])})
        try:
            verifier.verify(base64.b64decode(sh["signature"]), payload)
            valid.append(int(sh["row_id"]))
        except (InvalidSignature, ValueError):
            invalid.append(int(sh["row_id"]))
    return valid, invalid


def _coalition_from_input(program: SpanProgram, coalition, fraction: float, exp_id: str, approach: str) -> list[int]:
    participants = program.participants
    if coalition not in (None, "", []):
        if isinstance(coalition, str):
            parts = [x.strip() for x in coalition.split(",") if x.strip()]
            chosen = sorted(set(int(x) for x in parts))
        else:
            chosen = sorted(set(int(x) for x in coalition))
        unknown = set(chosen) - set(participants)
        if unknown:
            raise ValueError(f"coalition contains unknown/non-physical regions: {sorted(unknown)}")
        return chosen
    k = max(0, min(len(participants), int(round(max(0.0, min(1.0, float(fraction))) * len(participants)))))
    if fraction > 0 and participants and k == 0:
        k = 1
    rng = random.Random(_rng_seed(exp_id, approach, "coalition"))
    return sorted(rng.sample(participants, k)) if k else []


def _authorized_fast(program: SpanProgram, coalition: Iterable[int]) -> bool:
    chosen = set(int(x) for x in coalition)
    meta = program.metadata or {}
    if meta.get("type") == "threshold":
        return len(chosen & set(program.participants)) >= int(meta["threshold"])
    if meta.get("type") == "dnf":
        return any(set(s) <= chosen for s in meta.get("minimal_authorized_sets", []))
    return program.authorized(chosen)


def _risk(program: SpanProgram, survival_q: float, compromise_q: float, trials: int, seed: int) -> dict:
    n = len(program.participants)
    survival_q = max(0.0, min(1.0, float(survival_q)))
    compromise_q = max(0.0, min(1.0, float(compromise_q)))
    meta = program.metadata or {}
    if meta.get("type") == "threshold":
        t = int(meta["threshold"])
        def tail(prob: float):
            return sum(math.comb(n, k) * prob**k * (1-prob)**(n-k) for k in range(t, n+1))
        avail, comp = tail(survival_q), tail(compromise_q)
        method = "exact binomial threshold calculation"
        used = None
    else:
        used = max(100, min(10000, int(trials)))
        rng = random.Random(seed)
        avail_hits = comp_hits = 0
        ids = program.participants
        for _ in range(used):
            surviving = [x for x in ids if rng.random() < survival_q]
            compromised = [x for x in ids if rng.random() < compromise_q]
            avail_hits += int(_authorized_fast(program, surviving))
            comp_hits += int(_authorized_fast(program, compromised))
        avail, comp = avail_hits / used, comp_hits / used
        method = "Monte Carlo over independent region events"
    return {
        "survival_probability_per_region": survival_q,
        "compromise_probability_per_region": compromise_q,
        "availability_probability": avail,
        "catastrophic_compromise_probability": comp,
        "secure_and_available_independence_proxy": avail * (1-comp),
        "method": method,
        "trials": used,
        "model_assumption": "independent homogeneous region survival and compromise events",
    }


def _legacy_monomial_comparison(exp, approach: str) -> dict:
    """Keep the old transform only to demonstrate why it is not the security layer."""
    seed = _rng_seed(exp.id, approach, "legacy-obfuscation")
    rng = random.Random(seed)
    perm = list(range(exp.n)); rng.shuffle(perm)
    diag = [rng.randrange(1, exp.p) for _ in range(exp.n)]
    matrix, _ = combinatorial.systematic_matrix(exp.n, exp.mode)
    dinv = [inv(d, exp.p) for d in diag]
    transformed = [[int(row[perm[i]]) * dinv[i] % exp.p for i in range(exp.n)] for row in matrix]
    return {
        "label": "algebraic obfuscation comparison only",
        "rank_before": rank(matrix, exp.p),
        "rank_after": rank(transformed, exp.p),
        "rank_invariant": rank(matrix, exp.p) == rank(transformed, exp.p),
        "security_status": "not a confidentiality primitive",
        "reason": "An invertible deterministic coordinate transform preserves information and many structural invariants; it does not introduce the fresh randomness required for secret-sharing secrecy.",
    }


def _lens_interpretation(approach: str) -> str:
    return {
        "combinatorial": "Regions are cryptographic participants. The access hypergraph is now an explicit monotone access structure; minimal authorized coalitions can be derived from systematic rank bases or selected independently.",
        "spectral": "Spectral rank and projective recovery remain representation diagnostics. Confidentiality comes from AEAD + randomized LSSS; spectral basis hiding is retained only as an obfuscation comparison.",
        "probabilistic": "The access structure induces two stochastic quantities: availability P(surviving coalition is authorized) and catastrophic compromise P(compromised coalition is authorized).",
        "sheaf": "Patches act as share holders. Atlas-derived policies use coordinate-covering patch families; sheaf gluing/cohomology can be compared with, but is not used as, a cryptographic hardness assumption.",
        "information": "Unauthorized coalitions of the LSSS have zero mutual information about the shared scalar key under fresh uniform masks; authorized coalitions reconstruct it exactly. This is the appropriate leakage criterion, unlike rank invariance.",
    }[approach]


def analyze(
    exp,
    approach: str,
    *,
    policy_type: str = "threshold",
    threshold: int | None = None,
    coalition=None,
    coalition_fraction: float = 0.5,
    survival_q: float = 0.9,
    compromise_q: float = 0.1,
    trials: int = 2000,
    tamper: bool = False,
    custom_minimal_sets=None,
):
    approach = str(approach).lower()
    if approach not in {"combinatorial", "spectral", "probabilistic", "sheaf", "information"}:
        raise KeyError(approach)

    program = _build_policy(exp, approach, policy_type, threshold, survival_q, custom_minimal_sets)
    policy = policy_summary(program)
    selected = _coalition_from_input(program, coalition, coalition_fraction, exp.id, approach)
    structural_authorized = program.authorized(selected)

    # Encrypt the semantic token with a genuinely random AEAD key.
    key = AESGCM.generate_key(bit_length=256)
    key_int = int.from_bytes(key, "big")
    if key_int >= LSSS_PRIME:
        raise RuntimeError("internal key embedding failure")
    plaintext_obj = {
        "experiment_id": exp.id,
        "name": exp.name,
        "token_type": exp.token_type,
        "semantic_token": exp.token,
        "field_projection": exp.field_projection,
    }
    plaintext = _canonical(plaintext_obj)
    aad_obj = {"experiment_id": exp.id, "n": exp.n, "mode": exp.mode, "lens": approach}
    aad = _canonical(aad_obj)
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)

    shares, commitment, public_key = _signed_shares(program, key_int)
    selected_rows = [dict(s) for s in shares if int(s["region"]) in set(selected)]
    tampered_row = None
    if tamper and selected_rows:
        tampered_row = int(selected_rows[0]["row_id"])
        selected_rows[0]["value"] = (int(selected_rows[0]["value"]) + 1) % program.prime
    valid_rows, invalid_rows = _verify_shares(selected_rows, commitment, public_key)
    signatures_valid = not invalid_rows

    reconstructed_int = None
    decrypted_matches = False
    if structural_authorized and signatures_valid:
        reconstructed_int = reconstruct_secret(program, selected_rows, selected)
        if reconstructed_int is not None:
            recovered_key = int(reconstructed_int).to_bytes(32, "big")
            recovered_plaintext = AESGCM(recovered_key).decrypt(nonce, ciphertext, aad)
            decrypted_matches = recovered_plaintext == plaintext

    key_entropy_bits = 256
    leakage = key_entropy_bits if structural_authorized else 0
    residual = 0 if structural_authorized else key_entropy_bits
    risk = _risk(program, survival_q, compromise_q, trials, _rng_seed(exp.id, approach, "risk"))

    # Do not expose the raw key or exact share field elements in ordinary output.
    share_preview = [
        {
            "row_id": int(s["row_id"]),
            "region": int(s["region"]),
            "occurrence": int(s["occurrence"]),
            "value_hex_prefix": hex(int(s["value"]))[:22] + "…",
            "signature_b64_prefix": str(s["signature"])[:24] + "…",
            "signature_valid": int(s["row_id"]) in valid_rows,
        }
        for s in selected_rows[:80]
    ]

    return {
        "approach": approach,
        "primitive_stack": {
            "payload_confidentiality_integrity": "AES-256-GCM",
            "key_distribution": policy["name"],
            "share_authentication": "Ed25519 dealer signatures",
            "secret_sharing_field": policy["field"],
            "shared_secret": "random 256-bit AEAD key",
            "security_separation": "The semantic token is encrypted; regions receive randomized shares of the encryption key, not deterministic transforms of the plaintext token.",
        },
        "envelope": {
            "plaintext_bytes": len(plaintext),
            "ciphertext_and_tag_bytes": len(ciphertext),
            "nonce_b64": _b64(nonce),
            "aad": aad_obj,
            "ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
            "ciphertext_b64_prefix": _b64(ciphertext)[:72] + "…",
            "decryption_with_authenticated_authorized_coalition_succeeds": decrypted_matches,
        },
        "policy": {**policy, "policy_commitment_sha256": commitment},
        "coalition": {
            "regions": selected,
            "region_count": len(selected),
            "structurally_authorized": structural_authorized,
            "authenticated_for_reconstruction": structural_authorized and signatures_valid,
            "reconstructed_key_matches": reconstructed_int == key_int if reconstructed_int is not None else False,
            "token_decryption_verified": decrypted_matches,
            "key_entropy_bits": key_entropy_bits,
            "mutual_information_about_key_bits": leakage,
            "conditional_key_entropy_bits": residual,
            "perfect_secrecy_statement": "I(K; X_U)=0 for an unauthorized coalition U under the LSSS model with fresh uniform masks." if not structural_authorized else "Authorized coalition: H(K | X_A)=0 after valid reconstruction.",
        },
        "authenticated_shares": {
            "verification_public_key_b64": _b64(public_key),
            "selected_share_rows": len(selected_rows),
            "valid_share_rows": len(valid_rows),
            "invalid_share_rows": invalid_rows,
            "tamper_requested": bool(tamper),
            "tampered_row": tampered_row,
            "tamper_detected": bool(invalid_rows),
            "share_preview": share_preview,
            "scope_note": "Ed25519 authenticates dealer-issued shares and detects post-issuance modification. This is not full VSS and does not prove that a malicious dealer distributed mutually consistent shares.",
        },
        "availability_and_compromise": risk,
        "lens_interpretation": _lens_interpretation(approach),
        "legacy_obfuscation_comparison": _legacy_monomial_comparison(exp, approach),
        "security_notes": [
            "AES-GCM and Ed25519 are supplied by the cryptography package; the Atlas does not implement those primitives itself.",
            "The LSSS/MSP layer is an educational/research implementation and has not undergone independent security audit or side-channel review.",
            "The default threat model assumes honest share generation, independent region failures/compromises for the risk simulation, and secure random number generation by the host OS.",
            "Do not use the Atlas as a production key-management system without protocol review, hardened key lifecycle controls, authenticated transport, persistent secure storage, and independent audit.",
        ],
    }
