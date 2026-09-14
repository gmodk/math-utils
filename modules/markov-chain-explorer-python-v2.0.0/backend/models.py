from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class MarkovNode(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    label: str
    category: str = "state"
    initial: float = 0.0
    reward: float = 0.0
    x: float | None = None
    y: float | None = None
    z: float | None = None
    metadata: dict[str, Any] | None = None


class Transition(BaseModel):
    model_config = ConfigDict(extra="allow")

    source: str
    target: str
    probability: float
    time: int = 0
    relation: str = "transition"
    confidence: float = 1.0
    count: float | None = None
    enabled: bool = True
    metadata: dict[str, Any] | None = None


class ChainProject(BaseModel):
    model_config = ConfigDict(extra="allow")

    name: str = "Markov chain"
    kind: Literal["homogeneous", "nonhomogeneous"] = "homogeneous"
    nodes: list[MarkovNode]
    transitions: list[Transition]


class AnalysisRequest(BaseModel):
    project: ChainProject
    bayesian: bool = False
    alpha: float = Field(default=0.5, gt=0)
    selected_time_index: int = Field(default=0, alias="selectedTimeIndex", ge=0)
    horizon: int = Field(default=12, ge=0, le=1000)
    current_step: int = Field(default=4, alias="currentStep", ge=0, le=1000)
    target_ids: list[str] = Field(default_factory=list, alias="targetIds")
    discount: float = Field(default=0.95, ge=0, le=1)
    path_text: str = Field(default="", alias="pathText")
    lambda_rate: float = Field(default=1.4, alias="lambda", ge=0, le=100)
    threshold: float = Field(default=0.05, ge=0, le=1)

    model_config = ConfigDict(populate_by_name=True)


class PoissonRequest(BaseModel):
    project: ChainProject
    lambda_rate: float = Field(alias="lambda", ge=0, le=100)
    boundary: Literal["cyclic", "capped"] = "cyclic"
    slices: int = Field(default=1, ge=1, le=100)
    drift: float = Field(default=0.0, ge=-0.99, le=10)

    model_config = ConfigDict(populate_by_name=True)


class NormalizeRequest(BaseModel):
    project: ChainProject
    selected_time_index: int = Field(default=0, alias="selectedTimeIndex", ge=0)
    bayesian: bool = False
    alpha: float = Field(default=0.5, gt=0)

    model_config = ConfigDict(populate_by_name=True)
