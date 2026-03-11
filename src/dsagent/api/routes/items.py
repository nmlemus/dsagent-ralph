"""Items and Experiments API routes"""
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dsagent.api.deps import get_db
from dsagent.db.schemas import ItemResponse, ExperimentResponse
from dsagent.db.repositories import ItemRepository, ExperimentRepository

router = APIRouter(prefix="/api/v1", tags=["items", "experiments"])


# === Items ===

@router.get("/projects/{project_id}/items", response_model=List[ItemResponse])
def get_project_items(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all items for a project"""
    repo = ItemRepository(db)
    return repo.get_by_project(project_id)


@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(
    item_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific item"""
    repo = ItemRepository(db)
    item = repo.get(item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    return item


# === Experiments ===

@router.get("/projects/{project_id}/experiments", response_model=List[ExperimentResponse])
def get_project_experiments(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all experiments for a project"""
    repo = ExperimentRepository(db)
    return repo.get_by_project(project_id)


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific experiment"""
    repo = ExperimentRepository(db)
    experiment = repo.get(experiment_id)
    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Experiment not found"
        )
    return experiment


@router.get("/projects/{project_id}/status")
def get_project_status(
    project_id: UUID,
    db: Session = Depends(get_db)
):
    """Get overall project status"""
    from dsagent.agents.ralph import Ralph
    
    ralph = Ralph(db)
    return ralph.get_status(project_id)
