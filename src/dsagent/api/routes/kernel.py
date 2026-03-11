"""Kernel API routes"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any

from dsagent.services.kernel_manager import kernel_manager

router = APIRouter(prefix="/api/v1/kernel", tags=["kernel"])


class ExecuteCodeRequest(BaseModel):
    code: str
    timeout: Optional[int] = 300


@router.post("/{project_id}/execute")
async def execute_code(
    project_id: str,
    request: ExecuteCodeRequest
):
    """Execute code in project's kernel"""
    result = await kernel_manager.execute_code(
        project_id=project_id,
        code=request.code,
        timeout=request.timeout
    )
    return result


@router.get("/{project_id}/state")
async def get_kernel_state(project_id: str):
    """Get kernel state for project"""
    state = await kernel_manager.get_kernel_state(project_id)
    return state


@router.post("/{project_id}/reset")
async def reset_kernel(project_id: str):
    """Reset kernel for project"""
    success = await kernel_manager.reset_kernel(project_id)
    return {"success": success}


@router.post("/{project_id}/release")
async def release_kernel(project_id: str):
    """Release kernel back to pool"""
    await kernel_manager.release_kernel(project_id)
    return {"status": "released"}


@router.get("/stats")
async def get_kernel_stats():
    """Get kernel manager statistics"""
    return kernel_manager.get_stats()
