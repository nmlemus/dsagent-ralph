"""Conversational Agent - Main interface with users"""
from uuid import UUID
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from dsagent.db.models import Project, Conversation, HITLRequest
from dsagent.db.repositories import (
    ProjectRepository, ConversationRepository, HITLRequestRepository
)
from dsagent.agents.ralph import Ralph
from dsagent.agents.planner import PlannerAgent


class ConversationalAgent:
    """
    Conversational Agent is the main interface for users.
    It handles chat messages, detects intent, and routes to other agents.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.conversation_repo = ConversationRepository(db)
        self.hitl_repo = HITLRequestRepository(db)
        self.ralph = Ralph(db)
        self.planner = PlannerAgent(db)
    
    async def chat(
        self, 
        project_id: UUID, 
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message and generate response.
        """
        # Save message to conversation
        conversation = self._get_or_create_conversation(project_id)
        self._add_message(conversation, "user", message)
        
        # Detect intent
        intent = self._detect_intent(message)
        
        # Route to appropriate handler
        if intent == "status":
            response = await self._handle_status(project_id)
        elif intent == "plan":
            response = await self._handle_plan(message, project_id, context)
        elif intent == "execute":
            response = await self._handle_execute(project_id)
        elif intent == "approve":
            response = await self._handle_approve(message, project_id)
        elif intent == "reject":
            response = await self._handle_reject(message, project_id)
        elif intent == "question":
            response = await self._handle_question(message, project_id)
        else:
            response = await self._handle_general(message, project_id)
        
        # Save response to conversation
        self._add_message(conversation, "assistant", response["message"])
        
        return response
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message."""
        message_lower = message.lower()
        
        # Status check
        if any(kw in message_lower for kw in ["status", "how is", "progress", "where"]):
            return "status"
        
        # Planning
        if any(kw in message_lower for kw in ["plan", "create", "generate", "make a"]):
            return "plan"
        
        # Execution
        if any(kw in message_lower for kw in ["run", "execute", "start", "go"]):
            return "execute"
        
        # Approval
        if any(kw in message_lower for kw in ["yes", "approve", "ok", "continue", "good"]):
            return "approve"
        
        # Rejection
        if any(kw in message_lower for kw in ["no", "reject", "stop", "cancel"]):
            return "reject"
        
        # Questions
        if "?" in message or any(kw in message_lower for kw in ["what", "how", "why", "can i"]):
            return "question"
        
        return "general"
    
    async def _handle_status(self, project_id: UUID) -> Dict[str, Any]:
        """Handle status request."""
        status = self.ralph.get_status(project_id)
        
        message = f"""## Project Status

- **Status**: {status.get('project_status', 'unknown')}
- **Iteration**: {status.get('experiment_iteration', 0)}
- **Items**: {status.get('items_completed', 0)}/{status.get('items_total', 0)} completed
- **Pending**: {status.get('items_pending', 0)}
- **Failed**: {status.get('items_failed', 0)}
"""
        
        return {
            "message": message,
            "type": "status",
            "data": status
        }
    
    async def _handle_plan(
        self, 
        message: str, 
        project_id: UUID,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle plan generation request."""
        # Extract objective from message
        # In production, use LLM to extract
        
        # Generate plan
        result = await self.planner.generate_plan(
            project_id=project_id,
            user_objective=message,
            context=context
        )
        
        if result["status"] == "success":
            # Create HITL for approval
            hitl = HITLRequest(
                project_id=project_id,
                type="plan_approval",
                question=f"¿Aprobar este plan con {result['items_count']} items?",
                context={"plan_id": result["plan_id"], "items": result["items"]},
                status="pending"
            )
            self.hitl_repo.create(hitl)
            
            # Build plan display
            items_text = "\n".join([
                f"- **{item['id']}**. {item['title']} ({item['phase']})"
                for item in result["items"]
            ])
            
            message = f"""## Plan Generado

{items_text}

¿Aprobar este plan para comenzar la ejecución?
"""
            
            return {
                "message": message,
                "type": "plan",
                "plan_id": result["plan_id"],
                "needs_approval": True,
                "hitl_request_id": str(hitl.id)
            }
        
        return {
            "message": f"Error generando plan: {result.get('message')}",
            "type": "error"
        }
    
    async def _handle_execute(self, project_id: UUID) -> Dict[str, Any]:
        """Handle execution request."""
        # Start Ralph workflow
        result = await self.ralph.run_workflow(project_id)
        
        if result["status"] == "completed":
            return {
                "message": f"✅ Workflow completado!\n\nExperiment ID: {result.get('experiment_id')}",
                "type": "complete"
            }
        elif result["status"] == "waiting_human":
            return {
                "message": f"⏳ Esperando aprobación humana:\n\n{result.get('question')}",
                "type": "waiting",
                "hitl_request_id": result.get("hitl_request_id")
            }
        else:
            return {
                "message": f"Status: {result.get('status')}\n{result.get('message', '')}",
                "type": result.get("status")
            }
    
    async def _handle_approve(self, message: str, project_id: UUID) -> Dict[str, Any]:
        """Handle approval response."""
        # Get pending HITL
        pending = self.hitl_repo.get_pending(project_id)
        if not pending:
            return {
                "message": "No hay nada pendiente de aprobación.",
                "type": "info"
            }
        
        hitl = pending[0]
        
        # Handle response
        result = await self.ralph.handle_hitl_response(
            hitl_id=hitl.id,
            response=message,
            approved=True
        )
        
        return {
            "message": "✅ Plan aprobado. Iniciando ejecución...",
            "type": "approved"
        }
    
    async def _handle_reject(self, message: str, project_id: UUID) -> Dict[str, Any]:
        """Handle rejection response."""
        pending = self.hitl_repo.get_pending(project_id)
        if not pending:
            return {
                "message": "No hay nada pendiente.",
                "type": "info"
            }
        
        hitl = pending[0]
        
        await self.ralph.handle_hitl_response(
            hitl_id=hitl.id,
            response=message,
            approved=False
        )
        
        return {
            "message": "❌ Plan rechazado. ¿Qué cambios necesitas?",
            "type": "rejected"
        }
    
    async def _handle_question(
        self, 
        message: str, 
        project_id: UUID
    ) -> Dict[str, Any]:
        """Handle general questions."""
        # In production, use LLM to answer
        return {
            "message": "Entiendo tu pregunta. Puedo ayudarte con:\n- Estado del proyecto\n- Crear nuevos planes\n- Ejecutar tareas\n\n¿Qué necesitas?",
            "type": "question"
        }
    
    async def _handle_general(
        self, 
        message: str, 
        project_id: UUID
    ) -> Dict[str, Any]:
        """Handle general messages."""
        return {
            "message": f"Entendido: '{message}'\n\n¿Necesitas algo específico? Puedo:\n- Ver el status\n- Crear un plan de análisis\n- Ejecutar el workflow",
            "type": "general"
        }
    
    def _get_or_create_conversation(self, project_id: UUID) -> Conversation:
        """Get or create conversation for project."""
        conversations = self.conversation_repo.get_by_project(project_id)
        if conversations:
            return conversations[0]
        
        conversation = Conversation(
            project_id=project_id,
            messages=[]
        )
        return self.conversation_repo.create(conversation)
    
    def _add_message(
        self, 
        conversation: Conversation, 
        role: str, 
        content: str
    ):
        """Add message to conversation."""
        messages = conversation.messages or []
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        conversation.messages = messages
        self.conversation_repo.update(conversation)
