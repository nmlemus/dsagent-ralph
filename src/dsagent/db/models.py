"""Database models for DSAgent"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    target_column = Column(String(255))
    success_metric = Column(String(100))
    metric_threshold = Column(Float)
    status = Column(String(50), default="initializing")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    datasets = relationship("Dataset", back_populates="project")
    plans = relationship("Plan", back_populates="project")
    experiments = relationship("Experiment", back_populates="project")
    conversations = relationship("Conversation", back_populates="project")
    hitl_requests = relationship("HITLRequest", back_populates="project")
    learnings = relationship("Learning", back_populates="project")


class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    storage_type = Column(String(50), default="local")
    n_rows = Column(Integer)
    n_columns = Column(Integer)
    columns = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="datasets")


class Plan(Base):
    __tablename__ = "plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    items = Column(JSON, nullable=False)
    status = Column(String(50), default="draft")
    approved_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="plans")
    items_rel = relationship("Item", back_populates="plan")


class Item(Base):
    __tablename__ = "items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id"))
    skill_name = Column(String(100), nullable=False)
    skill_params = Column(JSON)
    phase = Column(String(50))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="pending")
    result = Column(JSON)
    error = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)
    
    plan = relationship("Plan", back_populates="items_rel")


class Experiment(Base):
    __tablename__ = "experiments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    iteration = Column(Integer, nullable=False)
    status = Column(String(50), default="running")
    approach = Column(Text)
    metrics = Column(JSON)
    best_model_id = Column(UUID(as_uuid=True))
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    project = relationship("Project", back_populates="experiments")
    models = relationship("Model", back_populates="experiment")


class Model(Base):
    __tablename__ = "models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100))
    hyperparameters = Column(JSON)
    metrics = Column(JSON)
    feature_importance = Column(JSON)
    artifact_path = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    experiment = relationship("Experiment", back_populates="models")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    messages = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="conversations")


class HITLRequest(Base):
    __tablename__ = "hitl_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"))
    type = Column(String(50), nullable=False)
    question = Column(Text, nullable=False)
    context = Column(JSON)
    options = Column(JSON)
    response = Column(Text)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)
    
    project = relationship("Project", back_populates="hitl_requests")


class Learning(Base):
    __tablename__ = "learnings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("experiments.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="learnings")
