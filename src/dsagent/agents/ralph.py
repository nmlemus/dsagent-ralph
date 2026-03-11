"""Ralph - Orchestrator Agent for DSAgent"""
from uuid import UUID
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from dsagent.db.models import Project, Item, Experiment, Plan, HITLRequest, Learning
from dsagent.db.repositories import (
    ProjectRepository, ItemRepository, ExperimentRepository,
    PlanRepository, HITLRequestRepository, LearningRepository
)


class Ralph:
    """
    Ralph is the central orchestrator for DSAgent.
    He coordinates all other agents and maintains workflow state.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.item_repo = ItemRepository(db)
        self.experiment_repo = ExperimentRepository(db)
        self.plan_repo = PlanRepository(db)
        self.hitl_repo = HITLRequestRepository(db)
        self.learning_repo = LearningRepository(db)
    
    async def run_workflow(self, project_id: UUID) -> Dict[str, Any]:
        """
        Main workflow loop - runs until all items complete or ESCALATE.
        """
        project = self.project_repo.get(project_id)
        if not project:
            return {"status": "error", "message": "Project not found"}
        
        # Get or create current experiment
        experiment = self.experiment_repo.get_latest(project_id)
        if not experiment or experiment.status == "completed":
            # Create new experiment
            iteration = (experiment.iteration + 1) if experiment else 1
            experiment = Experiment(
                project_id=project_id,
                iteration=iteration,
                status="running"
            )
            self.experiment_repo.create(experiment)
        
        while True:
            # Get next pending item
            item = self.item_repo.get_pending(project_id)
            
            if not item:
                # No more items - workflow complete
                experiment.status = "completed"
                experiment.completed_at = datetime.utcnow()
                self.experiment_repo.update(experiment)
                
                project.status = "completed"
                self.project_repo.update(project)
                
                return {
                    "status": "completed",
                    "experiment_id": str(experiment.id),
                    "iteration": experiment.iteration
                }
            
            # Execute item (delegate to Executor Agent)
            item = await self._execute_item(item)
            
            # Check if we need HITL
            if item.status == "waiting_approval":
                hitl = self.hitl_repo.get_pending(project_id)
                if hitl:
                    return {
                        "status": "waiting_human",
                        "hitl_request_id": str(hitl.id),
                        "question": hitl.question
                    }
            
            # Evaluate if we should continue or iterate
            if item.status == "completed":
                evaluation = await self._evaluate_progress(project_id, experiment)
                
                if evaluation["decision"] == "ITERATE":
                    # Create new experiment iteration
                    experiment = Experiment(
                        project_id=project_id,
                        iteration=experiment.iteration + 1,
                        status="running"
                    )
                    self.experiment_repo.create(experiment)
                    
                elif evaluation["decision"] == "ESCALATE":
                    return {
                        "status": "escalated",
                        "reason": evaluation["reason"]
                    }
    
    async def _execute_item(self, item: Item) -> Item:
        """Execute a single item - delegates to Executor Agent."""
        from dsagent.agents.executor import ExecutorAgent
        
        # Mark as running
        item.status = "running"
        item.started_at = datetime.utcnow()
        self.item_repo.update(item)
        
        try:
            executor = ExecutorAgent(self.db)
            result = await executor.execute(item)
            
            item.status = "completed"
            item.result = result
            item.completed_at = datetime.utcnow()
            
            if item.started_at:
                item.duration_seconds = int(
                    (item.completed_at - item.started_at).total_seconds()
                )
            
        except Exception as e:
            item.status = "failed"
            item.error = str(e)
        
        return self.item_repo.update(item)
    
    async def _evaluate_progress(
        self, 
        project_id: UUID, 
        experiment: Experiment
    ) -> Dict[str, Any]:
        """Evaluate if we should continue or iterate - delegates to Evaluator Agent."""
        from dsagent.agents.evaluator import EvaluatorAgent
        
        evaluator = EvaluatorAgent(self.db)
        return await evaluator.evaluate(project_id, experiment)
    
    async def handle_hitl_response(
        self, 
        hitl_id: UUID, 
        response: str,
        approved: bool
    ) -> Dict[str, Any]:
        """Handle human response to HITL request."""
        hitl = self.hitl_repo.get(hitl_id)
        if not hitl:
            return {"status": "error", "message": "HITL request not found"}
        
        hitl.response = response
        hitl.status = "approved" if approved else "rejected"
        hitl.responded_at = datetime.utcnow()
        self.hitl_repo.update(hitl)
        
        if approved:
            # Continue workflow
            return await self.run_workflow(hitl.project_id)
        else:
            # Stop workflow
            return {
                "status": "rejected",
                "message": "Human rejected the plan"
            }
    
    def add_learning(self, project_id: UUID, experiment_id: UUID, content: str):
        """Add a learning to the project."""
        learning = Learning(
            project_id=project_id,
            experiment_id=experiment_id,
            content=content
        )
        self.learning_repo.create(learning)
    
    def get_status(self, project_id: UUID) -> Dict[str, Any]:
        """Get current workflow status."""
        project = self.project_repo.get(project_id)
        if not project:
            return {"status": "error", "message": "Project not found"}
        
        items = self.item_repo.get_by_project(project_id)
        pending = [i for i in items if i.status == "pending"]
        completed = [i for i in items if i.status == "completed"]
        failed = [i for i in items if i.status == "failed"]
        
        experiment = self.experiment_repo.get_latest(project_id)
        
        return {
            "project_id": str(project_id),
            "project_status": project.status,
            "experiment_iteration": experiment.iteration if experiment else 0,
            "experiment_status": experiment.status if experiment else None,
            "items_total": len(items),
            "items_pending": len(pending),
            "items_completed": len(completed),
            "items_failed": len(failed)
        }
