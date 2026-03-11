"""Base Skill class for DSAgent"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class SkillInput(BaseModel):
    """Input schema for skills"""
    project_id: Optional[str] = None
    data_path: Optional[str] =: Optional[str] None
    target = None
    params: Dict[str, Any] = Field(default_factory=dict)


class SkillOutput(BaseModel):
    """Output schema for skills"""
    success: bool
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    charts: List[str] = Field(default_factory=list)
    artifacts: Dict[str, str] = Field(default_factory=dict)


class BaseSkill(ABC):
    """
    Base class for all skills in DSAgent.
    
    Each skill:
    - Has a unique name
    - Defines input/output schemas
    - Executes a specific data science task
    """
    
    name: str
    description: str
    category: str  # eda, modeling, evaluation, processing, reporting
    
    @abstractmethod
    async def execute(self, input_data: SkillInput) -> SkillOutput:
        """
        Execute the skill with given input.
        
        Args:
            input_data: SkillInput with parameters
            
        Returns:
            SkillOutput with results
        """
        pass
    
    def validate_input(self, input_data: SkillInput) -> Optional[str]:
        """
        Validate input data. Return error message if invalid.
        """
        return None
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get skill metadata"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category
        }


class SkillRegistry:
    """
    Registry for all available skills.
    """
    
    _skills: Dict[str, BaseSkill] = {}
    
    @classmethod
    def register(cls, skill: BaseSkill):
        """Register a skill"""
        cls._skills[skill.name] = skill
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseSkill]:
        """Get skill by name"""
        return cls._skills.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, BaseSkill]:
        """Get all registered skills"""
        return cls._skills.copy()
    
    @classmethod
    def get_by_category(cls, category: str) -> List[BaseSkill]:
        """Get skills by category"""
        return [
            s for s in cls._skills.values() 
            if s.category == category
        ]
    
    @classmethod
    def list_skills(cls) -> List[Dict[str, str]]:
        """List all skills"""
        return [
            {
                "name": s.name,
                "description": s.description,
                "category": s.category
            }
            for s in cls._skills.values()
        ]


# Decorator to register skills
def skill(name: str, description: str, category: str):
    """Decorator to register a skill class"""
    def decorator(cls):
        class WrappedSkill(cls, BaseSkill):
            _name = name
            _description = description
            _category = category
            
            @property
            def name(self):
                return self._name
            
            @property
            def description(self):
                return self._description
            
            @property
            def category(self):
                return self._category
        
        SkillRegistry.register(WrappedSkill())
        return cls
    return decorator
