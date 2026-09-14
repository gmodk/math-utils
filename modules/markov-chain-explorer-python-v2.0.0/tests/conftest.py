from __future__ import annotations

import csv
from pathlib import Path

from backend.models import ChainProject, MarkovNode, Transition


ROOT = Path(__file__).resolve().parent.parent


def load_project(filename: str, kind: str) -> ChainProject:
    nodes: list[MarkovNode] = []
    transitions: list[Transition] = []
    with (ROOT / "examples" / filename).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["record_type"] == "node":
                nodes.append(MarkovNode(
                    id=row["id"], label=row["label"], category=row["category"],
                    initial=float(row["initial_probability"] or 0), reward=float(row["reward"] or 0),
                ))
            elif row["record_type"] == "transition":
                transitions.append(Transition(
                    source=row["source"], target=row["target"], probability=float(row["probability"]),
                    time=int(row["time"] or 0), relation=row["relation"], confidence=float(row["confidence"] or 1),
                    count=float(row["count"]) if row["count"] else None, enabled=row["enabled"].lower() != "false",
                ))
    return ChainProject(name=filename, kind=kind, nodes=nodes, transitions=transitions)
