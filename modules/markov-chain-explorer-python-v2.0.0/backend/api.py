from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .engine import (
    analyze_request,
    build_poisson_matrix,
    matrices_to_transitions,
    normalize_rows,
    project_matrices,
)
from .models import AnalysisRequest, NormalizeRequest, PoissonRequest


ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend_dist"

app = FastAPI(
    title="Markov Chain Explorer API",
    description="Python numerical engine for finite homogeneous and non-homogeneous Markov chains.",
    version="2.0.0",
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "engine": "python"}


@app.post("/api/analyze")
def analyze(request: AnalysisRequest) -> dict:
    try:
        return analyze_request(request)
    except (ValueError, IndexError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/api/poisson")
def poisson(request: PoissonRequest) -> dict:
    slice_count = 1 if request.project.kind == "homogeneous" else request.slices
    matrices = [
        build_poisson_matrix(
            len(request.project.nodes),
            max(0.0, request.lambda_rate * (1.0 + request.drift * time)),
            request.boundary,
        )
        for time in range(slice_count)
    ]
    return {
        "transitions": matrices_to_transitions(request.project, matrices, "poisson-count"),
        "matrices": [matrix.tolist() for matrix in matrices],
        "lambdaSchedule": [max(0.0, request.lambda_rate * (1.0 + request.drift * time)) for time in range(slice_count)],
    }


@app.post("/api/normalize")
def normalize(request: NormalizeRequest) -> dict:
    built = project_matrices(request.project, request.bayesian, request.alpha)
    if not built.matrices:
        raise HTTPException(status_code=422, detail="No transition matrix is available.")
    time_index = min(request.selected_time_index, len(built.matrices) - 1)
    time = built.times[time_index]
    matrix = normalize_rows(built.matrices[time_index])
    retained = []
    if request.project.kind == "nonhomogeneous":
        retained = [edge.model_dump() for edge in request.project.transitions if edge.time != time]
    normalized = matrices_to_transitions(request.project, [matrix], "normalized")
    for edge in normalized:
        edge["time"] = time
    return {"transitions": retained + normalized, "matrix": matrix.tolist(), "time": time}


@app.exception_handler(Exception)
async def unexpected_error(_, error: Exception):
    return JSONResponse(status_code=500, content={"detail": f"Numerical engine error: {error}"})


if FRONTEND.exists():
    app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="frontend")

