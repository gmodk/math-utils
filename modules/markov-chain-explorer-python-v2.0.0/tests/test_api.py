from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.api import app
from .conftest import load_project


client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "engine": "python"}


def test_python_serves_prebuilt_javascript_ui() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Markov Chain Explorer" in response.text
    assert "/assets/" in response.text


def test_runtime_bundle_targets_python_api_and_contains_real_3d_controls() -> None:
    bundle = next((Path(__file__).parents[1] / "frontend_dist" / "assets").glob("*.js")).read_text()
    assert "/api/analyze" in bundle
    assert "/api/poisson" in bundle
    assert "markov-hypergraph-3d" in bundle
    assert "zoomToCursor" in bundle
    assert "Interactive three-dimensional weighted state-transition hypergraph" in bundle


def test_analysis_endpoint() -> None:
    project = load_project("homogeneous-system-chain.csv", "homogeneous")
    response = client.post("/api/analyze", json={
        "project": project.model_dump(), "horizon": 12, "currentStep": 4,
        "targetIds": ["incident"], "pathText": "nominal,degraded,incident",
        "lambda": 1.4, "threshold": 0.05,
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis"]["irreducible"] is True
    assert len(payload["trajectory"]) == 13
    assert len(payload["currentMatrix"]) == 5


def test_poisson_endpoint() -> None:
    project = load_project("nonhomogeneous-weather-chain.csv", "nonhomogeneous")
    response = client.post("/api/poisson", json={
        "project": project.model_dump(), "lambda": 2.0, "boundary": "cyclic", "slices": 4, "drift": 0.1,
    })
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["matrices"]) == 4
    assert len(payload["lambdaSchedule"]) == 4


def test_normalize_endpoint_retains_other_time_slices() -> None:
    project = load_project("nonhomogeneous-weather-chain.csv", "nonhomogeneous")
    response = client.post("/api/normalize", json={
        "project": project.model_dump(), "selectedTimeIndex": 1,
    })
    assert response.status_code == 200
    payload = response.json()
    assert payload["time"] == 1
    assert all(abs(sum(row) - 1.0) < 1e-10 for row in payload["matrix"])
    assert {edge["time"] for edge in payload["transitions"]} == {0, 1, 2}
