"""Pydantic schemas for DSAgent API"""
from uuid import UUID
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# === Project Schemas ===
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    target_column: Optional[str] = None
    success_metric: Optional[str] = None
    metric_threshold: Optional[float] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_column: Optional[str] = None
    success_metric: Optional[str] = None
    metric_threshold: Optional[float] = None
    status: Optional[str] = None


class ProjectResponse(ProjectBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Dataset Schemas ===
class DatasetBase(BaseModel):
    name: str
    file_path: str
    storage_type: str = "local"


class DatasetCreate(DatasetBase):
    project_id: UUID


class DatasetResponse(DatasetBase):
    id: UUID
    project_id: UUID
    n_rows: Optional[int] = None
    n_columns: Optional[int] = None
    columns: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Plan Schemas ===
class PlanItem(BaseModel):
    id: str
    skill_name: str
    skill_params: Optional[dict] = None
    phase: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str = "pending"


class PlanBase(BaseModel):
    items: list[PlanItem]


class PlanCreate(PlanBase):
    project_id: UUID


class PlanResponse(PlanBase):
    id: UUID
    project_id: UUID
    status: str
    approved_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Item Schemas ===
class ItemBase(BaseModel):
    skill_name: str
    skill_params: Optional[dict] = None
    phase: Optional[str] = None
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    project_id: UUID
    plan_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None


class ItemUpdate(BaseModel):
    status: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


class ItemResponse(ItemBase):
    id: UUID
    project_id: UUID
    plan_id: Optional[UUID] = None
    experiment_id: Optional[UUID] = None
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None

    class Config:
        from_attributes = True


# === Experiment Schemas ===
class ExperimentBase(BaseModel):
    iteration: int
    approach: Optional[str] = None


class ExperimentCreate(ExperimentBase):
    project_id: UUID


class ExperimentUpdate(BaseModel):
    status: Optional[str] = None
    approach: Optional[str] = None
    metrics: Optional[dict] = None
    best_model_id: Optional[UUID] = None


class ExperimentResponse(ExperimentBase):
    id: UUID
    project_id: UUID
    status: str
    metrics: Optional[dict] = None
    best_model_id: Optional[UUID] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# === Model Schemas ===
class ModelBase(BaseModel):
    name: str
    type: Optional[str] = None
    hyperparameters: Optional[dict] = None
    metrics: Optional[dict] = None
    feature_importance: Optional[dict] = None
    artifact_path: Optional[str] = None


class ModelCreate(ModelBase):
    experiment_id: UUID


class ModelResponse(ModelBase):
    id: UUID
    experiment_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# === Conversation Schemas ===
class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None


class ConversationCreate(BaseModel):
    project_id: UUID


class ConversationResponse(BaseModel):
    id: UUID
    project_id: UUID
    messages: list[dict] = []
    created_at: datetime

    class Config:
        from_attributes = True


# === HITL Schemas ===
class HITLRequestCreate(BaseModel):
    project_id: UUID
    item_id: Optional[UUID] = None
    type: str
    question: str
    context: Optional[dict] = None
    options: Optional[list[str]] = None


class HITLRequestRespond(BaseModel):
    response: str
    status: str = "approved"


class HITLRequestResponse(BaseModel):
    id: UUID
    project_id: UUID
    item_id: Optional[UUID] = None
    type: str
    question: str
    context: Optional[dict] = None
    options: Optional[list[str]] = None
    response: Optional[str] = None
    status: str
    created_at: datetime
    responded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# === Learning Schemas ===
class LearningCreate(BaseModel):
    project_id: UUID
    experiment_id: Optional[UUID] = None
    content: str


class LearningResponse(BaseModel):
    id: UUID
    project_id: UUID
    experiment_id: Optional[UUID] = None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# === Chat Schemas ===
class ChatMessage(BaseModel):
    message: str
    project_id: Optional[UUID] = None


class ChatResponse(BaseModel):
    response: str
    project_id: Optional[UUID] = None
    needs_hitl: bool = False
    hitl_request_id: Optional[UUID] = None
