"""Evaluator Agent - Evaluates results and decides next actions"""
from uuid import UUID
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
import json

from dsagent.db.models import Project, Experiment, Item, Model
from dsagent.db.repositories import (
    ProjectRepository, ExperimentRepository, ItemRepository, ModelRepository
)


class EvaluatorAgent:
    """
    Evaluator Agent evaluates model results and decides if the workflow
    should continue, iterate, or escalate.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.experiment_repo = ExperimentRepository(db)
        self.item_repo = ItemRepository(db)
        self.model_repo = ModelRepository(db)
    
    async def evaluate(
        self, 
        project_id: UUID, 
        experiment: Experiment
    ) -> Dict[str, Any]:
        """
        Evaluate experiment results and decide next action.
        
        Returns:
            - decision: PROCEED | ITERATE | ESCALATE
            - reason: explanation
            - details: additional info
        """
        project = self.project_repo.get(project_id)
        if not project:
            return {
                "decision": "ESCALATE",
                "reason": "Project not found"
            }
        
        # Get experiment metrics
        metrics = experiment.metrics or {}
        
        # Check if we have model results
        if not metrics:
            # Try to load from file
            metrics = self._load_metrics(project_id)
        
        if not metrics:
            return {
                "decision": "ITERATE",
                "reason": "No metrics available yet, need more items"
            }
        
        # Get threshold from project
        threshold = project.metric_threshold or 0.8
        metric_name = project.success_metric or "roc_auc"
        
        # Find best metric value
        best_value = self._get_best_metric(metrics, metric_name)
        
        if best_value is None:
            return {
                "decision": "ITERATE",
                "reason": f"No {metric_name} metric found in results"
            }
        
        # Decision logic
        if best_value >= threshold:
            return {
                "decision": "PROCEED",
                "reason": f"Target met: {metric_name} = {best_value:.4f} >= {threshold}",
                "details": {
                    "metric": metric_name,
                    "value": best_value,
                    "threshold": threshold,
                    "gap": best_value - threshold
                }
            }
        
        # Check iteration count
        if experiment.iteration >= 3:
            return {
                "decision": "PROCEED",
                "reason": f"Max iterations reached (3). Best {metric_name}: {best_value:.4f}",
                "details": {
                    "metric": metric_name,
                    "value": best_value,
                    "threshold": threshold,
                    "gap": threshold - best_value,
                    "iteration": experiment.iteration
                }
            }
        
        # Need more iterations
        return {
            "decision": "ITERATE",
            "reason": f"Target not met: {metric_name} = {best_value:.4f} < {threshold}. Need iteration {experiment.iteration + 1}",
            "details": {
                "metric": metric_name,
                "value": best_value,
                "threshold": threshold,
                "gap": threshold - best_value,
                "iteration": experiment.iteration,
                "suggestions": self._get_suggestions(metrics, metric_name)
            }
        }
    
    def _load_metrics(self, project_id: UUID) -> Dict[str, Any]:
        """Load metrics from file if available."""
        try:
            # Look for model results file
            # In production, use proper file handling
            pass
        except:
            pass
        return {}
    
    def _get_best_metric(
        self, 
        metrics: Dict[str, Any], 
        metric_name: str
    ) -> Optional[float]:
        """Extract best metric value from results."""
        best_value = None
        
        # Direct value
        if metric_name in metrics:
            return metrics[metric_name]
        
        # Per-model values
        if isinstance(metrics, dict):
            for model_name, model_metrics in metrics.items():
                if isinstance(model_metrics, dict) and metric_name in model_metrics:
                    value = model_metrics[metric_name]
                    if best_value is None or value > best_value:
                        best_value = value
        
        return best_value
    
    def _get_suggestions(
        self, 
        metrics: Dict[str, Any], 
        metric_name: str
    ) -> list[str]:
        """Generate suggestions for improvement."""
        suggestions = []
        
        # Analyze model comparison
        if isinstance(metrics, dict):
            model_values = {}
            for model_name, model_metrics in metrics.items():
                if isinstance(model_metrics, dict) and metric_name in model_metrics:
                    model_values[model_name] = model_metrics[metric_name]
            
            if model_values:
                worst = min(model_values.items(), key=lambda x: x[1])
                best = max(model_values.items(), key=lambda x: x[1])
                
                suggestions.append(f"Consider tuning {best[0]} (current best: {best[1]:.4f})")
                suggestions.append(f"Review why {worst[0]} performed poorly ({worst[1]:.4f})")
        
        # Generic suggestions
        suggestions.extend([
            "Try feature engineering",
            "Handle class imbalance",
            "Tune hyperparameters",
            "Add more data preprocessing"
        ])
        
        return suggestions[:3]
    
    async def evaluate_item(self, item: Item) -> Dict[str, Any]:
        """
        Evaluate a single item result.
        """
        if item.status == "failed":
            return {
                "valid": False,
                "reason": f"Item failed: {item.error}"
            }
        
        if item.status != "completed":
            return {
                "valid": False,
                "reason": f"Item not completed: {item.status}"
            }
        
        # Check result
        result = item.result or {}
        
        if result.get("status") == "error":
            return {
                "valid": False,
                "reason": f"Execution error: {result.get('error')}"
            }
        
        # Basic validation passed
        return {
            "valid": True,
            "output": result.get("output")
        }
    
    def check_for_issues(self, project_id: UUID) -> Dict[str, Any]:
        """
        Check for common issues in the workflow.
        """
        items = self.item_repo.get_by_project(project_id)
        failed_items = [i for i in items if i.status == "failed"]
        
        issues = []
        
        # Check for failures
        if len(failed_items) > 0:
            issues.append({
                "type": "failed_items",
                "count": len(failed_items),
                "items": [i.title for i in failed_items[:3]]
            })
        
        # Check for stuck items
        running_items = [i for i in items if i.status == "running"]
        if len(running_items) > 5:
            issues.append({
                "type": "stuck_items",
                "count": len(running_items)
            })
        
        return {
            "has_issues": len(issues) > 0,
            "issues": issues
        }
