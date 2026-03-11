"""Planner Agent - Generates executable plans from objectives"""
from uuid import UUID
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from dsagent.db.models import Project, Plan, Item, Dataset
from dsagent.db.repositories import ProjectRepository, PlanRepository, ItemRepository, DatasetRepository
from dsagent.config import get_settings


class PlannerAgent:
    """
    Planner Agent generates granular, executable plans from user objectives.
    It analyzes the task and creates a list of items (PRD) with skills.
    """
    
    SKILL_MAPPING = {
        "load_data": "inspect-data",
        "profile_columns": "inspect-data",
        "eda": "generate-eda",
        "clean_data": "data-cleaning",
        "feature_engineering": "feature-engineering",
        "train_model": "train-baselines",
        "evaluate_model": "evaluate-models",
        "report": "write-report",
        "analyze_statistical": "analyze-statistical",
    }
    
    PHASES = ["EDA", "MODELING", "EVALUATION", "REPORTING"]
    
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.plan_repo = PlanRepository(db)
        self.item_repo = ItemRepository(db)
        self.dataset_repo = DatasetRepository(db)
        self.settings = get_settings()
    
    async def generate_plan(
        self, 
        project_id: UUID,
        user_objective: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate a plan based on user objective.
        
        This uses the LLM to analyze the objective and create items.
        """
        project = self.project_repo.get(project_id)
        if not project:
            return {"status": "error", "message": "Project not found"}
        
        # Get available datasets
        datasets = self.dataset_repo.get_by_project(project_id)
        
        # Generate plan using LLM
        items = await self._llm_generate_items(
            objective=user_objective,
            project=project,
            datasets=datasets,
            context=context
        )
        
        # Create plan in DB
        plan = Plan(
            project_id=project_id,
            items=[item.dict() for item in items],
            status="draft"
        )
        plan = self.plan_repo.create(plan)
        
        # Create items in DB
        for item_data in items:
            item = Item(
                project_id=project_id,
                plan_id=plan.id,
                skill_name=item_data.skill_name,
                skill_params=item_data.skill_params or {},
                phase=item_data.phase,
                title=item_data.title,
                description=item_data.description,
                status="pending"
            )
            self.item_repo.create(item)
        
        return {
            "status": "success",
            "plan_id": str(plan.id),
            "items_count": len(items),
            "items": [item.dict() for item in items]
        }
    
    async def _llm_generate_items(
        self,
        objective: str,
        project: Project,
        datasets: List[Dataset],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to generate items based on objective.
        
        This is a simplified version - in production, call actual LLM.
        """
        # Simplified template-based generation
        # In production, this would call Claude/OpenAI
        
        items = []
        item_id = 1
        
        # EDA items
        if any(kw in objective.lower() for kw in ["eda", "exploratory", "analyze", "explorar"]):
            items.extend([
                {"id": str(item_id := item_id + 1), "phase": "EDA", "skill_name": "inspect-data", "skill_params": {}, "title": "Load and inspect data", "description": "Load dataset and inspect schema"},
                {"id": str(item_id := item_id + 1), "phase": "EDA", "skill_name": "inspect-data", "skill_params": {"profile": "numeric"}, "title": "Profile numeric columns", "description": "Analyze numeric column distributions"},
                {"id": str(item_id := item_id + 1), "phase": "EDA", "skill_name": "inspect-data", "skill_params": {"profile": "categorical"}, "title": "Profile categorical columns", "description": "Analyze categorical column distributions"},
                {"id": str(item_id := item_id + 1), "phase": "EDA", "skill_name": "generate-eda", "skill_params": {}, "title": "Generate EDA visualizations", "description": "Create EDA report with visualizations"},
            ])
        
        # Modeling items
        if any(kw in objective.lower() for kw in ["predict", "model", "train", "classification", "regression"]):
            if not items:  # If no EDA, add data loading first
                items.append({"id": "1", "phase": "EDA", "skill_name": "inspect-data", "skill_params": {}, "title": "Load data", "description": "Load dataset"})
            
            items.extend([
                {"id": str(item_id := item_id + 1), "phase": "MODELING", "skill_name": "data-cleaning", "skill_params": {}, "title": "Clean and preprocess data", "description": "Handle missing values, encoding"},
                {"id": str(item_id := item_id + 1), "phase": "MODELING", "skill_name": "feature-engineering", "skill_params": {}, "title": "Feature engineering", "description": "Create new features"},
                {"id": str(item_id := item_id + 1), "phase": "MODELING", "skill_name": "train-baselines", "skill_params": {"models": ["LogisticRegression"]}, "title": "Train baseline model", "description": "Train LogisticRegression"},
                {"id": str(item_id := item_id + 1), "phase": "MODELING", "skill_name": "train-baselines", "skill_params": {"models": ["RandomForest"]}, "title": "Train RandomForest", "description": "Train RandomForest model"},
                {"id": str(item_id := item_id + 1), "phase": "MODELING", "skill_name": "train-baselines", "skill_params": {"models": ["XGBoost"]}, "title": "Train XGBoost", "description": "Train XGBoost model"},
            ])
        
        # Evaluation items
        if any(kw in objective.lower() for kw in ["evaluate", "compare", "metric"]):
            items.append({"id": str(item_id := item_id + 1), "phase": "EVALUATION", "skill_name": "evaluate-models", "skill_params": {}, "title": "Compare models", "description": "Compare all model metrics"})
        
        # Reporting items
        if any(kw in objective.lower() for kw in ["report", "summary", "final"]):
            items.append({"id": str(item_id := item_id + 1), "phase": "REPORTING", "skill_name": "write-report", "skill_params": {}, "title": "Generate final report", "description": "Create final report"})
        
        # Default: basic EDA if nothing matched
        if not items:
            items = [
                {"id": "1", "phase": "EDA", "skill_name": "inspect-data", "skill_params": {}, "title": "Load and inspect data", "description": "Load dataset and explore"},
                {"id": "2", "phase": "REPORTING", "skill_name": "write-report", "skill_params": {}, "title": "Generate report", "description": "Create summary report"},
            ]
        
        return items
    
    async def refine_plan(
        self, 
        plan_id: UUID, 
        feedback: str
    ) -> Dict[str, Any]:
        """
        Refine plan based on human feedback.
        """
        plan = self.plan_repo.get(plan_id)
        if not plan:
            return {"status": "error", "message": "Plan not found"}
        
        # In production, use LLM to refine based on feedback
        # For now, just return current plan
        return {
            "status": "success",
            "plan_id": str(plan_id),
            "message": "Plan refinement would be handled by LLM"
        }
    
    def get_plan(self, plan_id: UUID) -> Optional[Dict[str, Any]]:
        """Get plan details."""
        plan = self.plan_repo.get(plan_id)
        if not plan:
            return None
        
        items = self.item_repo.get_by_plan(plan_id)
        
        return {
            "id": str(plan.id),
            "project_id": str(plan.project_id),
            "status": plan.status,
            "items": [
                {
                    "id": str(item.id),
                    "skill_name": item.skill_name,
                    "phase": item.phase,
                    "title": item.title,
                    "description": item.description,
                    "status": item.status
                }
                for item in items
            ],
            "created_at": plan.created_at.isoformat()
        }
