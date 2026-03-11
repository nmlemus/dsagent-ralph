"""Chat API routes with SSE streaming"""
import asyncio
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from dsagent.api.deps import get_db
from dsagent.agents.conversational import ConversationalAgent
from dsagent.db.schemas import ChatMessage, ChatResponse
from dsagent.db.models import Project
from dsagent.db.repositories import ProjectRepository

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/{project_id}/stream")
async def chat_stream(
    project_id: UUID,
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """Chat with streaming response (SSE)"""
    
    # Verify project exists
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    async def generate():
        agent = ConversationalAgent(db)
        
        # Process message
        result = await agent.chat(project_id, message.message)
        
        # Yield response as SSE
        response_text = result.get("message", "")
        
        # First, send thinking
        yield f"event: thinking\ndata: {json.dumps({'thinking': 'Processing...'})}\n\n"
        
        # Then send response
        yield f"event: llm_response\ndata: {json.dumps({'content': response_text, 'type': result.get('type', 'text')})}\n\n"
        
        # Send done
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/{project_id}", response_model=ChatResponse)
async def chat_sync(
    project_id: UUID,
    message: ChatMessage,
    db: Session = Depends(get_db)
):
    """Chat without streaming (sync)"""
    
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    agent = ConversationalAgent(db)
    result = await agent.chat(project_id, message.message)
    
    return ChatResponse(
        response=result.get("message", ""),
        project_id=project_id,
        needs_hitl=result.get("needs_approval", False),
        hitl_request_id=result.get("hitl_request_id")
    )
