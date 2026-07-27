"""Personality schema definitions for security expert roles."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Personality:
    """Security personality definition."""
    name: str
    role: str
    description: str
    skills: List[str] = field(default_factory=list)
    rules: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalitySchema:
    """Complete personality schema."""
    personality: Personality
    version: str = "1.0"
    
    @classmethod
    def from_yaml_dict(cls, data: Dict[str, Any]) -> 'PersonalitySchema':
        """Create PersonalitySchema from YAML dictionary.
        
        Args:
            data: Dictionary from YAML file
            
        Returns:
            PersonalitySchema object
        """
        personality_data = data.get('personality', data)
        
        personality = Personality(
            name=personality_data.get('name', 'unnamed'),
            role=personality_data.get('role', ''),
            description=personality_data.get('description', ''),
            skills=personality_data.get('skills', []),
            rules=personality_data.get('rules', []),
            tools=personality_data.get('tools', []),
            config=personality_data.get('config', {}),
        )
        
        return cls(
            personality=personality,
            version=data.get('version', '1.0'),
        )