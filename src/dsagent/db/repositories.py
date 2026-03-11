"""Database repositories for DSAgent"""
from uuid import UUID
from typing import Optional, List, TypeVar, Generic
from sqlalchemy.orm import Session

from dsagent.db.models import (
    Project, Dataset, Plan, Item, Experiment, Model,
    Conversation, HITLRequest, Learning
)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, model: type[T], db: Session):
        self.model = model
        self.db = db
    
    def get(self, id: UUID) -> Optional[T]:
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self) -> List[T]:
        return self.db.query(self.model).all()
    
    def create(self, obj: T) -> T:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def update(self, obj: T) -> T:
        self.db.commit()
        self.db.refresh(obj)
        return obj
    
    def delete(self, id: UUID) -> bool:
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: Session):
        super().__init__(Project, db)
    
    def get_by_name(self, name: str) -> Optional[Project]:
        return self.db.query(Project).filter(Project.name == name).first()
    
    def get_by_status(self, status: str) -> List[Project]:
        return self.db.query(Project).filter(Project.status == status).all()


class DatasetRepository(BaseRepository[Dataset]):
    def __init__(self, db: Session):
        super().__init__(Dataset, db)
    
    def get_by_project(self, project_id: UUID) -> List[Dataset]:
        return self.db.query(Dataset).filter(Dataset.project_id == project_id).all()


class PlanRepository(BaseRepository[Plan]):
    def __init__(self, db: Session):
        super().__init__(Plan, db)
    
    def get_by_project(self, project_id: UUID) -> List[Plan]:
        return self.db.query(Plan).filter(Plan.project_id == project_id).all()
    
    def get_approved(self, project_id: UUID) -> List[Plan]:
        return self.db.query(Plan).filter(
            Plan.project_id == project_id,
            Plan.status == "approved"
        ).all()


class ItemRepository(BaseRepository[Item]):
    def __init__(self, db: Session):
        super().__init__(Item, db)
    
    def get_by_project(self, project_id: UUID) -> List[Item]:
        return self.db.query(Item).filter(Item.project_id == project_id).all()
    
    def get_by_plan(self, plan_id: UUID) -> List[Item]:
        return self.db.query(Item).filter(Item.plan_id == plan_id).all()
    
    def get_pending(self, project_id: UUID) -> Optional[Item]:
        return self.db.query(Item).filter(
            Item.project_id == project_id,
            Item.status == "pending"
        ).order_by(Item.id).first()
    
    def get_by_phase(self, project_id: UUID, phase: str) -> List[Item]:
        return self.db.query(Item).filter(
            Item.project_id == project_id,
            Item.phase == phase
        ).all()


class ExperimentRepository(BaseRepository[Experiment]):
    def __init__(self, db: Session):
        super().__init__(Experiment, db)
    
    def get_by_project(self, project_id: UUID) -> List[Experiment]:
        return self.db.query(Experiment).filter(
            Experiment.project_id == project_id
        ).order_by(Experiment.iteration.desc()).all()
    
    def get_latest(self, project_id: UUID) -> Optional[Experiment]:
        return self.db.query(Experiment).filter(
            Experiment.project_id == project_id
        ).order_by(Experiment.iteration.desc()).first()
    
    def get_running(self, project_id: UUID) -> Optional[Experiment]:
        return self.db.query(Experiment).filter(
            Experiment.project_id == project_id,
            Experiment.status == "running"
        ).first()


class ModelRepository(BaseRepository[Model]):
    def __init__(self, db: Session):
        super().__init__(Model, db)
    
    def get_by_experiment(self, experiment_id: UUID) -> List[Model]:
        return self.db.query(Model).filter(
            Model.experiment_id == experiment_id
        ).all()


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self, db: Session):
        super().__init__(Conversation, db)
    
    def get_by_project(self, project_id: UUID) -> List[Conversation]:
        return self.db.query(Conversation).filter(
            Conversation.project_id == project_id
        ).order_by(Conversation.created_at.desc()).all()


class HITLRequestRepository(BaseRepository[HITLRequest]):
    def __init__(self, db: Session):
        super().__init__(HITLRequest, db)
    
    def get_pending(self, project_id: Optional[UUID] = None) -> List[HITLRequest]:
        query = self.db.query(HITLRequest).filter(HITLRequest.status == "pending")
        if project_id:
            query = query.filter(HITLRequest.project_id == project_id)
        return query.all()
    
    def get_by_project(self, project_id: UUID) -> List[HITLRequest]:
        return self.db.query(HITLRequest).filter(
            HITLRequest.project_id == project_id
        ).order_by(HITLRequest.created_at.desc()).all()


class LearningRepository(BaseRepository[Learning]):
    def __init__(self, db: Session):
        super().__init__(Learning, db)
    
    def get_by_project(self, project_id: UUID) -> List[Learning]:
        return self.db.query(Learning).filter(
            Learning.project_id == project_id
        ).order_by(Learning.created_at.desc()).all()
    
    def get_by_experiment(self, experiment_id: UUID) -> List[Learning]:
        return self.db.query(Learning).filter(
            Learning.experiment_id == experiment_id
        ).order_by(Learning.created_at.desc()).all()
