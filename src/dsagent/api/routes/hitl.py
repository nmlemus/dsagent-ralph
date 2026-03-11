"""HITL (Human-in-the-Loop) API routes"""
from uuid import UUID
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from dsagent.api.deps import get_db
from dsagent.db.models import HITLRequest
from dsagent.db.repositories import HITLRequestRepository
from dsagent.db.schemas import HITLRequestCreate, HITLRequestRespond, HITLRequestResponse
from dsagent.agents.ralph import Ralph

router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])


@router.get("/pending", response_model=List[HITLRequestResponse])
def get_pending_hitl_requests(
    project_id: UUID = None,
    db: Session = Depends(get_db)
):
    """Get all pending HITL requests"""
    repo = HITLRequestRepository(db)
    requests = repo.get_pending(project_id)
    return requests


@router.get("/{hitl_id}", response_model=HITLRequestResponse)
def get_hitl_request(
    hitl_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific HITL request"""
    repo = HITLRequestRepository(db)
    request = repo.get(hitl_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HITL request not found"
        )
    return request


@router.post("/{hitl_id}/respond")
def respond_to_hitl(
    hitl_id: UUID,
    response: HITLRequestRespond,
    db: Session = Depends(get_db)
):
    """Respond to a HITL request (approve or reject)"""
    repo = HITLRequestRepository(db)
    hitl = repo.get(hitl_id)
    
    if not hitl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HITL request not found"
        )
    
    if hitl.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HITL request already responded"
        )
    
    # Update HITL
    hitl.response = response.response
    hitl.status = response.status
    hitl.responded_at = datetime.utcnow()
    repo.update(hitl)
    
    # Handle through Ralph
    ralph = Ralph(db)
    result = ralph.handle_hitl_response(
        hitl_id=hitl_id,
        response=response.response,
        approved=(response.status == "approved")
    )
    
    return {
        "status": "success",
        "hitl_id": str(hitl_id),
        "response": response.response,
        "approved": response.status == "approved"
    }


@router.post("/{hitl_id}/approve")
def approve_hitl(
    hitl_id: UUID,
    response: str = "Approved",
    db: Session = Depends(get_db)
):
    """Quick approve endpoint"""
    repo = HITLRequestRepository(db)
    hitl = repo.get(hitl_id)
    
    if not hitl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HITL request not found"
        )
    
    hitl.response = response
    hitl.status = "approved"
    hitl.responded_at = datetime.utcnow()
    repo.update(hitl)
    
    # Continue workflow
    ralph = Ralph(db)
    ralph.handle_hitl_response(hitl_id, response, approved=True)
    
    return {"status": "approved", "hitl_id": str(hitl_id)}


@router.post("/{hitl_id}/reject")
def reject_hitl(
    hitl_id: UUID,
    response: str = "Rejected",
    db: Session = Depends(get_db)
):
    """Quick reject endpoint"""
    repo = HITLRequestRepository(db)
    hitl = repo.get(hitl_id)
    
    if not hitl:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HITL request not found"
        )
    
    hitl.response = response
    hitl.status = "rejected"
    hitl.responded_at = datetime.utcnow()
    repo.update(hitl)
    
    return {"status": "rejected", "hitl_id": str(hitl_id)}
