"""Data models for MotionForge.

Contains both Pydantic schemas for API/serialization and SQLAlchemy ORM models
for persistence.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Float, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from orchestrator.database import Base
from orchestrator.state import ExperimentState


# ── Pydantic Schemas ──────────────────────────────────────────────


class ExperimentCreate(BaseModel):
    """Schema for creating a new experiment."""

    prompt: str = Field(..., min_length=1, description="Generation prompt")
    negative_prompt: str = Field(default="", description="Negative prompt")
    workflow_template: str = Field(
        default="", description="Workflow template name or path"
    )
    target_score: float = Field(default=0.8, ge=0.0, le=1.0)
    max_iterations: int = Field(default=10, ge=1, le=100)
    seed: Optional[int] = Field(default=None, description="Random seed")
    cfg: float = Field(default=7.0, description="Classifier-free guidance scale")
    noise: float = Field(default=0.1, ge=0.0, le=1.0, description="Noise level")


class Experiment(BaseModel):
    """Full experiment schema."""

    id: str
    prompt: str
    negative_prompt: str
    workflow_template: str
    target_score: float
    max_iterations: int
    seed: Optional[int]
    cfg: float
    noise: float
    status: ExperimentState = ExperimentState.NEW
    current_iteration: int = 0
    score: Optional[float] = None
    best_score: Optional[float] = None
    best_iteration: int = 0
    best_prompt: str = ""
    best_parameters: dict = Field(default_factory=dict)
    stopping_reason: Optional[str] = None
    optimizer_confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class Job(BaseModel):
    """Schema for a single job within an experiment."""

    id: str
    experiment_id: str
    iteration: int
    status: str = "pending"
    created_at: datetime


class Iteration(BaseModel):
    """Schema for a single iteration."""

    id: str
    experiment_id: str
    number: int
    score: Optional[float] = None
    artifact_path: Optional[str] = None
    report_path: Optional[str] = None
    output_path: Optional[str] = None
    status: str = "pending"
    created_at: datetime


class QAReport(BaseModel):
    """Quality analysis report schema.

    Contains per-dimension scores, detected issues, strengths,
    and actionable recommendations produced by video analysis.
    """

    iteration_id: str
    overall_score: float = Field(ge=0.0, le=1.0, description="Overall quality score")
    identity_score: float = Field(ge=0.0, le=1.0, description="Subject identity consistency")
    motion_score: float = Field(ge=0.0, le=1.0, description="Motion quality and naturalness")
    camera_score: float = Field(ge=0.0, le=1.0, description="Camera movement quality")
    hands_score: float = Field(ge=0.0, le=1.0, description="Hand rendering quality")
    face_score: float = Field(ge=0.0, le=1.0, description="Face rendering quality")
    lighting_score: float = Field(ge=0.0, le=1.0, description="Lighting consistency")
    physics_score: float = Field(ge=0.0, le=1.0, description="Physical plausibility")
    lip_sync_score: float = Field(ge=0.0, le=1.0, description="Lip synchronization quality")
    continuity_score: float = Field(ge=0.0, le=1.0, description="Temporal continuity")
    issues: list[str] = Field(default_factory=list, description="Detected quality issues")
    strengths: list[str] = Field(default_factory=list, description="Identified strengths")
    summary: str = Field(default="", description="Analysis summary")
    recommendations: list[str] = Field(default_factory=list, description="Actionable recommendations")
    raw_response: str = Field(default="", description="Raw LLM response")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OptimizationResult(BaseModel):
    """Result of an optimization step.

    Produced by the optimizer after receiving the current generation
    parameters and QA report. Returns improved prompt, updated generation
    parameters, and reasoning for the next iteration.
    """

    new_prompt: str = Field(..., min_length=1, description="Optimized generation prompt")
    new_negative_prompt: str = Field(default="", description="Optimized negative prompt")
    new_seed: int = Field(..., gt=0, description="New random seed (positive integer)")
    new_cfg: float = Field(..., ge=0.5, le=10.0, description="New CFG scale (0.5-10)")
    new_noise: float = Field(..., ge=0.0, le=1.0, description="New noise level (0-1)")
    new_steps: int = Field(..., ge=1, le=100, description="New generation steps (1-100)")
    reasoning: str = Field(..., min_length=1, description="Optimizer reasoning")
    parameter_changes: dict = Field(
        default_factory=dict,
        description="Key-value map of parameter name -> (old, new) or description",
    )
    expected_improvements: list[str] = Field(
        default_factory=list,
        description="List of expected quality improvements",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    raw_response: str = Field(default="", description="Raw LLM response")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # ── Adaptive strategy fields ──────────────────────────────────

    optimization_mode: str = Field(
        default="REFINE",
        description="Optimization mode: TARGETED, REFINE, EXPLORE, RECOVER",
    )
    focus_areas: list[str] = Field(
        default_factory=list,
        description="QA dimensions this optimization focuses on",
    )
    parameters_modified: list[str] = Field(
        default_factory=list,
        description="Parameters that were modified in this step",
    )
    parameters_preserved: list[str] = Field(
        default_factory=list,
        description="Parameters that were intentionally preserved",
    )


class Candidate(BaseModel):
    """Schema for a candidate video within an iteration."""

    candidate_id: str
    iteration: int
    seed: int
    workflow: str = ""
    output_video: Optional[str] = None
    qa_report: Optional[dict] = None
    optimization_score: Optional[float] = None
    artifact_directory: Optional[str] = None
    generation_time: Optional[float] = None
    status: str = "pending"
    is_best_in_iteration: bool = False
    is_best_in_experiment: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── SQLAlchemy ORM Models ─────────────────────────────────────────


class ExperimentORM(Base):
    """ORM model for experiments."""

    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt = Column(Text, nullable=False)
    negative_prompt = Column(Text, default="")
    workflow_template = Column(String(256), default="")
    target_score = Column(Float, default=0.8)
    max_iterations = Column(Integer, default=10)
    seed = Column(Integer, nullable=True)
    cfg = Column(Float, default=7.0)
    noise = Column(Float, default=0.1)
    status = Column(String(32), default=ExperimentState.NEW.value)
    current_iteration = Column(Integer, default=0)
    score = Column(Float, nullable=True)
    best_score = Column(Float, nullable=True)
    best_iteration = Column(Integer, default=0)
    best_prompt = Column(Text, default="")
    best_parameters = Column(Text, default="{}")
    stopping_reason = Column(String(64), nullable=True)
    optimizer_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    iterations = relationship(
        "IterationORM", back_populates="experiment", cascade="all, delete-orphan"
    )


class IterationORM(Base):
    """ORM model for iterations."""

    __tablename__ = "iterations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    experiment_id = Column(
        String(36), ForeignKey("experiments.id"), nullable=False
    )
    number = Column(Integer, nullable=False)
    score = Column(Float, nullable=True)
    artifact_path = Column(String(512), nullable=True)
    report_path = Column(String(512), nullable=True)
    output_path = Column(String(512), nullable=True)
    status = Column(String(32), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    experiment = relationship("ExperimentORM", back_populates="iterations")
    candidates = relationship(
        "CandidateORM", back_populates="iteration", cascade="all, delete-orphan"
    )


class CandidateORM(Base):
    """ORM model for candidates within an iteration."""

    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    iteration_id = Column(
        String(36), ForeignKey("iterations.id"), nullable=False
    )
    number = Column(Integer, nullable=False)
    seed = Column(Integer, nullable=False)
    workflow = Column(Text, default="")
    output_video = Column(String(512), nullable=True)
    qa_report = Column(Text, nullable=True)
    optimization_score = Column(Float, nullable=True)
    artifact_directory = Column(String(512), nullable=True)
    generation_time = Column(Float, nullable=True)
    status = Column(String(32), default="pending")
    is_best_in_iteration = Column(Integer, default=0)
    is_best_in_experiment = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    iteration = relationship("IterationORM", back_populates="candidates")