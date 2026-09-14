from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import exp, gcd, log2, pi, sin, cos, sqrt
import re
from typing import Any, Iterable

import networkx as nx
import numpy as np
from scipy.linalg import expm

from .models import AnalysisRequest, ChainProject, Transition


EPS = 1e-12


def normalize_vector(values: Iterable[float]) -> np.ndarray:
    vector = np.asarray(list(values), dtype=float)
    vector = np.where(np.isfinite(vector), np.maximum(vector, 0.0), 0.0)
    total = float(vector.sum())
    if total <= EPS:
        return np.full(len(vector), 1.0 / max(len(vector), 1), dtype=float)
    return vector / total


def normalize_rows(matrix: np.ndarray) -> np.ndarray:
    result = np.asarray(matrix, dtype=float).copy()
    result = np.where(np.isfinite(result), np.maximum(result, 0.0), 0.0)
    for i, row in enumerate(result):
        total = float(row.sum())
        if total <= EPS:
            row[:] = 0.0
            row[i] = 1.0
        else:
            row[:] = row / total
    return result


def poisson_weights(lambda_rate: float, tolerance: float = 1e-14, max_terms: int = 1024) -> np.ndarray:
    rate = max(0.0, float(lambda_rate))
    weights = [exp(-rate)]
    cumulative = weights[0]
    for k in range(1, max_terms):
        if 1.0 - cumulative <= tolerance:
            break
        weights.append(weights[-1] * rate / k)
        cumulative += weights[-1]
    array = np.asarray(weights, dtype=float)
    total = float(array.sum())
    return array / total if total > EPS else np.array([1.0])


def build_poisson_matrix(n: int, lambda_rate: float, boundary: str) -> np.ndarray:
    weights = poisson_weights(lambda_rate)
    matrix = np.zeros((n, n), dtype=float)
    for i in range(n):
        for count, weight in enumerate(weights):
            j = (i + count) % n if boundary == "cyclic" else min(i + count, n - 1)
            matrix[i, j] += weight
    return normalize_rows(matrix)


def poissonized_matrix(matrix: np.ndarray, lambda_rate: float) -> np.ndarray:
    generator = float(lambda_rate) * (matrix - np.eye(matrix.shape[0]))
    result = np.real_if_close(expm(generator)).astype(float)
    result[np.abs(result) < 1e-15] = 0.0
    return normalize_rows(result)


def ordered_product(matrices: list[np.ndarray], start: int, steps: int) -> np.ndarray:
    if not matrices:
        return np.empty((0, 0))
    result = np.eye(matrices[0].shape[0])
    for k in range(max(0, int(steps))):
        result = result @ matrices[(start + k) % len(matrices)]
    return result


def matrices_to_transitions(project: ChainProject, matrices: list[np.ndarray], relation: str) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    for time, matrix in enumerate(matrices):
        for i, row in enumerate(matrix):
            for j, probability in enumerate(row):
                if probability > 1e-14:
                    transitions.append({
                        "source": project.nodes[i].id,
                        "target": project.nodes[j].id,
                        "probability": float(probability),
                        "time": time,
                        "relation": relation,
                        "confidence": 1.0,
                        "count": int(round(float(probability) * 1000)),
                        "enabled": True,
                    })
    return transitions


@dataclass
class MatrixBuild:
    matrices: list[np.ndarray]
    times: list[int]
    issues: list[dict[str, Any]]


def project_matrices(project: ChainProject, bayesian: bool = False, alpha: float = 0.5) -> MatrixBuild:
    n = len(project.nodes)
    indexes = {node.id: i for i, node in enumerate(project.nodes)}
    if project.kind == "homogeneous":
        times = [0]
    else:
        times = sorted({edge.time for edge in project.transitions if edge.enabled}) or [0]
    issues: list[dict[str, Any]] = []
    matrices: list[np.ndarray] = []
    for time in times:
        matrix = np.zeros((n, n), dtype=float)
        row_counts = np.zeros(n, dtype=float)
        has_counts = np.zeros(n, dtype=bool)
        for row_number, edge in enumerate(project.transitions, start=2):
            if not edge.enabled or (project.kind == "nonhomogeneous" and edge.time != time):
                continue
            i = indexes.get(edge.source)
            j = indexes.get(edge.target)
            if i is None or j is None:
                issues.append({"severity": "error", "message": f"Unknown state in {edge.source} → {edge.target}.", "row": row_number})
                continue
            if not np.isfinite(edge.probability) or edge.probability < 0:
                issues.append({"severity": "error", "message": "Probabilities must be finite and non-negative.", "row": row_number})
                continue
            if bayesian and edge.count is not None and np.isfinite(edge.count):
                count = max(0.0, float(edge.count))
                matrix[i, j] += count
                row_counts[i] += count
                has_counts[i] = True
            else:
                matrix[i, j] += edge.probability
        for i in range(n):
            if bayesian and has_counts[i]:
                matrix[i, :] = (matrix[i, :] + alpha) / (row_counts[i] + alpha * n)
            total = float(matrix[i].sum())
            if total <= EPS:
                issues.append({"severity": "error", "message": f'State “{project.nodes[i].label}” has no outgoing probability at time {time}.'})
            elif abs(total - 1.0) > 1e-7:
                issues.append({"severity": "warning", "message": f'Row “{project.nodes[i].label}” sums to {total:.6f} at time {time}; preview normalization is shown.'})
        matrices.append(normalize_rows(matrix))
    return MatrixBuild(matrices=matrices, times=times, issues=issues)


def validate_project(project: ChainProject) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not project.nodes:
        issues.append({"severity": "error", "message": "At least one state is required."})
    ids: set[str] = set()
    for row, node in enumerate(project.nodes, start=2):
        if not node.id.strip():
            issues.append({"severity": "error", "message": "State id cannot be empty.", "row": row})
        if node.id in ids:
            issues.append({"severity": "error", "message": f'Duplicate state id “{node.id}”.', "row": row})
        if not np.isfinite(node.initial) or node.initial < 0:
            issues.append({"severity": "error", "message": f'Invalid initial probability for “{node.label}”.', "row": row})
        ids.add(node.id)
    initial_total = sum(max(0.0, node.initial) for node in project.nodes if np.isfinite(node.initial))
    if project.nodes and initial_total <= EPS:
        issues.append({"severity": "warning", "message": "Initial probabilities contain no positive mass; the Python engine uses a uniform initial distribution."})
    elif abs(initial_total - 1.0) > 1e-8:
        issues.append({"severity": "warning", "message": f"Initial probabilities sum to {initial_total:.6f}; the Python engine normalizes them for analysis."})
    for row, edge in enumerate(project.transitions, start=2):
        if edge.source not in ids or edge.target not in ids:
            issues.append({"severity": "error", "message": f"Unknown endpoint in {edge.source} → {edge.target}.", "row": row})
        if not np.isfinite(edge.probability) or edge.probability < 0 or edge.probability > 1 + EPS:
            issues.append({"severity": "error", "message": f"Invalid probability {edge.probability}.", "row": row})
    return issues


def graph_from_matrix(matrix: np.ndarray, threshold: float = EPS) -> nx.DiGraph:
    graph = nx.DiGraph()
    graph.add_nodes_from(range(matrix.shape[0]))
    for i, row in enumerate(matrix):
        for j, probability in enumerate(row):
            if probability > threshold:
                graph.add_edge(i, j, weight=float(probability))
    return graph


def strongly_connected_components(matrix: np.ndarray) -> list[list[int]]:
    components = [sorted(component) for component in nx.strongly_connected_components(graph_from_matrix(matrix))]
    return sorted(components, key=lambda component: (component[0] if component else -1))


def closed_classes(matrix: np.ndarray, components: list[list[int]]) -> list[list[int]]:
    closed: list[list[int]] = []
    for component in components:
        members = set(component)
        if all(matrix[i, j] <= EPS or j in members for i in component for j in range(matrix.shape[0])):
            closed.append(component)
    return closed


def component_period(matrix: np.ndarray, component: list[int]) -> int:
    if not component:
        return 0
    members = set(component)
    distance = {component[0]: 0}
    queue = [component[0]]
    while queue:
        u = queue.pop(0)
        for v, probability in enumerate(matrix[u]):
            if probability > EPS and v in members and v not in distance:
                distance[v] = distance[u] + 1
                queue.append(v)
    period = 0
    for u in component:
        for v, probability in enumerate(matrix[u]):
            if probability > EPS and v in members:
                period = gcd(period, abs(distance.get(u, 0) + 1 - distance.get(v, 0)))
    return period or 1


def stationary_distribution(matrix: np.ndarray) -> np.ndarray:
    n = matrix.shape[0]
    system = np.vstack((matrix.T - np.eye(n), np.ones((1, n))))
    target = np.concatenate((np.zeros(n), np.ones(1)))
    solution, *_ = np.linalg.lstsq(system, target, rcond=None)
    solution[np.abs(solution) < 1e-14] = 0.0
    solution = np.maximum(solution, 0.0)
    return normalize_vector(solution)


def entropy_rate(matrix: np.ndarray, stationary: np.ndarray) -> float:
    entropy = 0.0
    for i, row in enumerate(matrix):
        entropy += stationary[i] * sum(-p * log2(p) for p in row if p > EPS)
    return float(entropy)


def dobrushin_coefficient(matrix: np.ndarray) -> float:
    if matrix.shape[0] < 2:
        return 0.0
    overlap = min(float(np.minimum(matrix[i], matrix[k]).sum()) for i in range(matrix.shape[0]) for k in range(i + 1, matrix.shape[0]))
    return float(np.clip(1.0 - overlap, 0.0, 1.0))


def reversibilized_gap(matrix: np.ndarray, stationary: np.ndarray) -> float:
    n = matrix.shape[0]
    if n < 2 or np.any(stationary <= EPS):
        return 0.0
    reverse = np.diag(1.0 / stationary) @ matrix.T @ np.diag(stationary)
    reversible = 0.5 * (matrix + reverse)
    similarity = np.diag(np.sqrt(stationary)) @ reversible @ np.diag(1.0 / np.sqrt(stationary))
    eigenvalues = np.sort(np.abs(np.linalg.eigvalsh(0.5 * (similarity + similarity.T))))[::-1]
    return float(np.clip(1.0 - (eigenvalues[1] if len(eigenvalues) > 1 else 0.0), 0.0, 1.0))


def analyze_matrix(matrix: np.ndarray) -> dict[str, Any]:
    components = strongly_connected_components(matrix)
    recurrent_classes = closed_classes(matrix, components)
    recurrent = {state for component in recurrent_classes for state in component}
    transient = [i for i in range(matrix.shape[0]) if i not in recurrent]
    absorbing = [i for i, row in enumerate(matrix) if np.allclose(row, np.eye(matrix.shape[0])[i], atol=1e-9)]
    periods = [component_period(matrix, component) for component in recurrent_classes]
    stationary = stationary_distribution(matrix)
    irreducible = len(components) == 1
    aperiodic = all(period == 1 for period in periods)
    return {
        "stationary": stationary.tolist(),
        "recurrentClasses": recurrent_classes,
        "transientStates": transient,
        "absorbingStates": absorbing,
        "irreducible": irreducible,
        "periods": periods,
        "aperiodic": aperiodic,
        "ergodic": irreducible and aperiodic,
        "entropyRate": entropy_rate(matrix, stationary),
        "dobrushin": dobrushin_coefficient(matrix),
        "reversibilizedGap": reversibilized_gap(matrix, stationary),
        "rowResidual": float(np.max(np.abs(matrix.sum(axis=1) - 1.0))),
    }


def evolution(matrices: list[np.ndarray], initial: np.ndarray, horizon: int) -> np.ndarray:
    rows = [initial]
    for time in range(max(0, horizon)):
        rows.append(rows[-1] @ matrices[time % len(matrices)])
    return np.asarray(rows)


def hitting_probability(matrices: list[np.ndarray], initial: np.ndarray, targets: list[int], horizon: int) -> dict[str, Any]:
    target_set = set(targets)
    survival = initial.copy()
    initially_hit = float(sum(survival[i] for i in target_set))
    for i in target_set:
        survival[i] = 0.0
    first_passage = [initially_hit]
    for time in range(max(0, horizon)):
        next_distribution = survival @ matrices[time % len(matrices)]
        hit = float(sum(next_distribution[i] for i in target_set))
        first_passage.append(hit)
        for i in target_set:
            next_distribution[i] = 0.0
        survival = next_distribution
    return {"probability": float(np.clip(sum(first_passage), 0.0, 1.0)), "firstPassage": first_passage}


def expected_hitting_times(matrix: np.ndarray, targets: list[int]) -> list[float | None]:
    n = matrix.shape[0]
    if not targets:
        return [None] * n
    target_set = set(targets)
    graph = graph_from_matrix(matrix)
    can_reach = {state for state in range(n) if any(nx.has_path(graph, state, target) for target in target_set)}
    probabilities = np.array([1.0 if i in target_set else 0.0 for i in range(n)])
    for _ in range(10000):
        updated = probabilities.copy()
        for i in range(n):
            if i not in target_set:
                updated[i] = float(matrix[i] @ probabilities)
        if np.max(np.abs(updated - probabilities)) < 1e-13:
            probabilities = updated
            break
        probabilities = updated
    finite_states = [i for i in range(n) if i not in target_set and i in can_reach and probabilities[i] >= 1 - 1e-9]
    result: list[float | None] = [0.0 if i in target_set else None for i in range(n)]
    if finite_states:
        q = matrix[np.ix_(finite_states, finite_states)]
        try:
            solved = np.linalg.solve(np.eye(len(finite_states)) - q, np.ones(len(finite_states)))
            for state, value in zip(finite_states, solved, strict=True):
                result[state] = float(max(0.0, value))
        except np.linalg.LinAlgError:
            pass
    return result


def expected_reward(matrices: list[np.ndarray], trajectory: np.ndarray, rewards: np.ndarray, horizon: int, discount: float) -> float:
    del matrices
    return float(sum((discount ** time) * float(trajectory[time] @ rewards) for time in range(min(horizon + 1, len(trajectory)))))


def path_probability(matrices: list[np.ndarray], project: ChainProject, path_text: str) -> float:
    path = [part for part in re.split(r"[>,\s]+", path_text.strip()) if part]
    indexes = {node.id: i for i, node in enumerate(project.nodes)}
    probability = 1.0
    for step, (source, target) in enumerate(zip(path, path[1:])):
        if source not in indexes or target not in indexes:
            return 0.0
        probability *= matrices[step % len(matrices)][indexes[source], indexes[target]]
    return float(probability)


def gf2_rank(matrix: np.ndarray) -> int:
    if matrix.size == 0:
        return 0
    work = (matrix.astype(np.uint8) & 1).copy()
    rows, cols = work.shape
    rank = 0
    for col in range(cols):
        candidates = np.where(work[rank:, col] == 1)[0]
        if not len(candidates):
            continue
        pivot = rank + int(candidates[0])
        work[[rank, pivot]] = work[[pivot, rank]]
        for row in range(rows):
            if row != rank and work[row, col]:
                work[row] ^= work[rank]
        rank += 1
        if rank == rows:
            break
    return rank


def tda_at(matrix: np.ndarray, threshold: float) -> dict[str, Any]:
    n = matrix.shape[0]
    weight = np.maximum(matrix, matrix.T)
    edges = [(i, j) for i, j in combinations(range(n), 2) if weight[i, j] >= threshold]
    edge_index = {edge: index for index, edge in enumerate(edges)}
    triangles = [triple for triple in combinations(range(n), 3) if all(tuple(sorted(edge)) in edge_index for edge in combinations(triple, 2))]
    triangle_index = {triangle: index for index, triangle in enumerate(triangles)}
    tetrahedra = [quad for quad in combinations(range(n), 4) if all(tuple(sorted(edge)) in edge_index for edge in combinations(quad, 2))]
    boundary1 = np.zeros((n, len(edges)), dtype=np.uint8)
    for edge_column, (i, j) in enumerate(edges):
        boundary1[i, edge_column] = boundary1[j, edge_column] = 1
    boundary2 = np.zeros((len(edges), len(triangles)), dtype=np.uint8)
    for triangle_column, triangle in enumerate(triangles):
        for edge in combinations(triangle, 2):
            boundary2[edge_index[tuple(sorted(edge))], triangle_column] = 1
    boundary3 = np.zeros((len(triangles), len(tetrahedra)), dtype=np.uint8)
    for tetrahedron_column, tetrahedron in enumerate(tetrahedra):
        for face in combinations(tetrahedron, 3):
            boundary3[triangle_index[tuple(sorted(face))], tetrahedron_column] = 1
    rank1, rank2, rank3 = gf2_rank(boundary1), gf2_rank(boundary2), gf2_rank(boundary3)
    return {
        "threshold": float(threshold),
        "beta0": n - rank1,
        "beta1": len(edges) - rank1 - rank2,
        "beta2": len(triangles) - rank2 - rank3,
        "edges": len(edges),
    }


def tda_filtration(matrix: np.ndarray, steps: int = 13) -> list[dict[str, Any]]:
    return [tda_at(matrix, index / max(steps - 1, 1)) for index in range(steps)]


def temporal_diagnostics(matrices: list[np.ndarray]) -> dict[str, Any]:
    variation = 0.0
    for current, previous in zip(matrices[1:], matrices[:-1]):
        variation = max(variation, float(np.max(np.sum(np.abs(current - previous), axis=1))))
    return {
        "slices": len(matrices),
        "maxRowVariation": variation,
        "complete": all(np.allclose(matrix.sum(axis=1), 1.0, atol=1e-7) for matrix in matrices),
    }


def edge_dropout_sensitivity(matrix: np.ndarray) -> float:
    baseline = stationary_distribution(matrix)
    worst = 0.0
    for i, j in zip(*np.where((matrix > EPS) & (~np.eye(matrix.shape[0], dtype=bool)))):
        dropped = matrix.copy()
        dropped[i, j] = 0.0
        shifted = stationary_distribution(normalize_rows(dropped))
        worst = max(worst, float(0.5 * np.abs(shifted - baseline).sum()))
    return worst


def weighted_forman_curvature(matrix: np.ndarray, source: int, target: int) -> float:
    weight = max(matrix[source, target], matrix[target, source])
    if weight <= EPS:
        return 0.0
    incident = 0.0
    for k in range(matrix.shape[0]):
        if k != target:
            adjacent = max(matrix[source, k], matrix[k, source])
            if adjacent > EPS:
                incident += sqrt(weight / adjacent)
        if k != source:
            adjacent = max(matrix[target, k], matrix[k, target])
            if adjacent > EPS:
                incident += sqrt(weight / adjacent)
    return float(2.0 - incident)


def seeded_simulation(matrices: list[np.ndarray], initial: np.ndarray, steps: int, runs: int = 1600, seed: int = 2026) -> np.ndarray:
    rng = np.random.default_rng(seed)
    occupancy = np.zeros(len(initial), dtype=float)
    states = np.arange(len(initial))
    for _ in range(runs):
        current = int(rng.choice(states, p=initial))
        occupancy[current] += 1
        for time in range(steps):
            current = int(rng.choice(states, p=matrices[time % len(matrices)][current]))
            occupancy[current] += 1
    return normalize_vector(occupancy)


def spectral_coordinates(matrix: np.ndarray) -> np.ndarray:
    n = matrix.shape[0]
    if n == 1:
        return np.array([[500.0, 340.0, 0.0]])
    adjacency = np.maximum(matrix, matrix.T).copy()
    np.fill_diagonal(adjacency, 0.0)
    laplacian = np.diag(adjacency.sum(axis=1)) - adjacency
    _, vectors = np.linalg.eigh(laplacian)
    x = vectors[:, min(1, n - 1)]
    y = vectors[:, min(2, n - 1)] if n > 2 else np.array([sin(2 * pi * i / n) for i in range(n)])
    z = vectors[:, min(3, n - 1)] if n > 3 else np.array([cos(4 * pi * i / n) for i in range(n)])
    def scale(values: np.ndarray, amplitude: float) -> np.ndarray:
        maximum = max(float(np.max(np.abs(values))), EPS)
        return amplitude * values / maximum
    return np.column_stack((500 + scale(x, 310), 340 + scale(y, 235), scale(z, 130)))


def layouts(matrix: np.ndarray, project: ChainProject) -> dict[str, list[dict[str, float | str]]]:
    n = len(project.nodes)
    orbital = np.array([[500 + cos(-pi / 2 + 2 * pi * i / max(n, 1)) * 285,
                         340 + sin(-pi / 2 + 2 * pi * i / max(n, 1)) * 230,
                         sin((-pi / 2 + 2 * pi * i / max(n, 1)) * 2) * 120] for i in range(n)])
    components = strongly_connected_components(matrix)
    class_points = np.zeros((n, 3), dtype=float)
    for class_index, component in enumerate(components):
        x = 500.0 if len(components) == 1 else 150 + class_index * 700 / max(len(components) - 1, 1)
        for within, state in enumerate(component):
            class_points[state] = [x, 150 + (within + 1) * 390 / (len(component) + 1), (class_index - len(components) / 2) * 90]
    spectral = spectral_coordinates(matrix)
    def serialize(points: np.ndarray) -> list[dict[str, float | str]]:
        return [{"id": node.id, "x": float(points[i, 0]), "y": float(points[i, 1]), "z": float(points[i, 2])} for i, node in enumerate(project.nodes)]
    return {"orbital": serialize(orbital), "classes": serialize(class_points), "spectral": serialize(spectral)}


def analyze_request(request: AnalysisRequest) -> dict[str, Any]:
    structural_issues = validate_project(request.project)
    built = project_matrices(request.project, request.bayesian, request.alpha)
    issues = structural_issues + built.issues
    if not built.matrices:
        raise ValueError("The project contains no transition matrix.")
    time_index = min(request.selected_time_index, len(built.matrices) - 1)
    matrix = built.matrices[time_index]
    initial = normalize_vector(node.initial for node in request.project.nodes)
    trajectory = evolution(built.matrices, initial, request.horizon)
    step = min(request.current_step, request.horizon)
    target_indexes = [i for i, node in enumerate(request.project.nodes) if node.id in set(request.target_ids)]
    analysis = analyze_matrix(matrix)
    horizon_matrix = np.linalg.matrix_power(matrix, request.horizon) if request.project.kind == "homogeneous" else ordered_product(built.matrices, time_index, request.horizon)
    curvature_values = [
        {"i": i, "j": j, "value": weighted_forman_curvature(matrix, i, j)}
        for i in range(matrix.shape[0]) for j in range(matrix.shape[0])
        if i != j and matrix[i, j] > request.threshold
    ]
    curvature_values.sort(key=lambda item: item["value"])
    return {
        "issues": issues,
        "times": built.times,
        "matrices": [item.tolist() for item in built.matrices],
        "currentMatrix": matrix.tolist(),
        "currentTime": built.times[time_index],
        "analysis": analysis,
        "initial": initial.tolist(),
        "trajectory": trajectory.tolist(),
        "distribution": trajectory[step].tolist(),
        "hit": hitting_probability(built.matrices, initial, target_indexes, request.horizon),
        "expectedHits": expected_hitting_times(matrix, target_indexes),
        "reward": expected_reward(built.matrices, trajectory, np.asarray([node.reward for node in request.project.nodes]), request.horizon, request.discount),
        "pathValue": path_probability(built.matrices, request.project, request.path_text),
        "tda": tda_at(matrix, request.threshold),
        "filtration": tda_filtration(matrix),
        "temporal": temporal_diagnostics(built.matrices),
        "dropout": edge_dropout_sensitivity(matrix),
        "simulation": seeded_simulation(built.matrices, initial, request.horizon).tolist(),
        "curvatureValues": curvature_values,
        "horizonMatrix": horizon_matrix.tolist(),
        "poissonizedMatrix": poissonized_matrix(matrix, request.lambda_rate).tolist(),
        "layouts": layouts(matrix, request.project),
    }
