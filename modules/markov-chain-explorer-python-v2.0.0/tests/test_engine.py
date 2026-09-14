from __future__ import annotations

import numpy as np

from backend.engine import (
    analyze_matrix, analyze_request, build_poisson_matrix, expected_hitting_times,
    ordered_product, poissonized_matrix, project_matrices, tda_at,
)
from backend.models import AnalysisRequest
from .conftest import load_project


def test_homogeneous_analysis_invariants() -> None:
    project = load_project("homogeneous-system-chain.csv", "homogeneous")
    built = project_matrices(project)
    assert len(built.matrices) == 1
    matrix = built.matrices[0]
    assert np.allclose(matrix.sum(axis=1), 1.0)
    analysis = analyze_matrix(matrix)
    assert np.isclose(sum(analysis["stationary"]), 1.0)
    assert analysis["irreducible"] is True


def test_poisson_constructions_are_stochastic() -> None:
    project = load_project("homogeneous-system-chain.csv", "homogeneous")
    matrix = project_matrices(project).matrices[0]
    count_matrix = build_poisson_matrix(7, 2.4, "cyclic")
    poissonized = poissonized_matrix(matrix, 1.7)
    assert np.allclose(count_matrix.sum(axis=1), 1.0)
    assert np.allclose(poissonized.sum(axis=1), 1.0)
    assert np.all(count_matrix >= 0)
    assert np.all(poissonized >= 0)


def test_expected_hitting_time_equations() -> None:
    project = load_project("homogeneous-system-chain.csv", "homogeneous")
    matrix = project_matrices(project).matrices[0]
    expected = expected_hitting_times(matrix, [2])
    assert expected[2] == 0.0
    finite = np.asarray([float(value) for value in expected])
    for i in range(len(expected)):
        if i != 2:
            assert np.isclose(finite[i], 1 + matrix[i] @ finite, atol=1e-8)


def test_period_and_homology_of_four_cycle() -> None:
    cycle = np.array([[0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1], [1, 0, 0, 0]], dtype=float)
    analysis = analyze_matrix(cycle)
    topology = tda_at(cycle, 0.5)
    assert analysis["irreducible"] is True
    assert analysis["aperiodic"] is False
    assert analysis["periods"] == [4]
    assert (topology["beta0"], topology["beta1"], topology["beta2"]) == (1, 1, 0)


def test_nonhomogeneous_ordered_product_and_response() -> None:
    project = load_project("nonhomogeneous-weather-chain.csv", "nonhomogeneous")
    built = project_matrices(project)
    assert len(built.matrices) == 3
    assert np.allclose(ordered_product(built.matrices, 0, 3), built.matrices[0] @ built.matrices[1] @ built.matrices[2])
    response = analyze_request(AnalysisRequest(project=project, horizon=8, currentStep=3, targetIds=["storm"], pathText="sun,cloud,rain"))
    assert len(response["trajectory"]) == 9
    assert 0 <= response["hit"]["probability"] <= 1
    assert len(response["layouts"]["spectral"]) == 4
