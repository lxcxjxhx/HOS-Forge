"""Personality loader for YAML personality files."""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Union

from .schema import Personality, PersonalitySchema


class PersonalityLoader:
    """Loader for YAML personality files."""
    
    def __init__(self):
        """Initialize personality loader."""
        self._cache: Dict[str, Personality] = {}
    
    def load(self, file_path: Union[str, Path]) -> Personality:
        """Load personality from YAML file.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Personality object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            yaml.YAMLError: If YAML is invalid
            ValueError: If schema is invalid
        """
        path = Path(file_path)
        
        # Check cache
        cache_key = str(path.absolute())
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        if not path.exists():
            raise FileNotFoundError(f"Personality file not found: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        schema = self.parse_dict(data)
        self._cache[cache_key] = schema.personality
        
        return schema.personality
    
    def load_string(self, yaml_content: str) -> Personality:
        """Load personality from YAML string.
        
        Args:
            yaml_content: YAML content as string
            
        Returns:
            Personality object
        """
        data = yaml.safe_load(yaml_content)
        schema = self.parse_dict(data)
        return schema.personality
    
    def parse_dict(self, data: Dict[str, Any]) -> PersonalitySchema:
        """Parse personality from dictionary.
        
        Args:
            data: Dictionary containing personality definition
            
        Returns:
            PersonalitySchema object
        """
        if not isinstance(data, dict):
            raise ValueError("Personality must be a dictionary")
        
        schema = PersonalitySchema.from_yaml_dict(data)
        self._validate_personality(schema.personality)
        
        return schema
    
    def _validate_personality(self, personality: Personality) -> None:
        """Validate personality structure.
        
        Args:
            personality: Personality to validate
            
        Raises:
            ValueError: If personality is invalid
        """
        if not personality.name:
            raise ValueError("Personality must have a name")
        
        if not personality.role:
            raise ValueError("Personality must have a role")
    
    def load_directory(self, directory: Union[str, Path]) -> List[Personality]:
        """Load all personalities from a directory.
        
        Args:
            directory: Path to directory containing YAML files
            
        Returns:
            List of Personality objects
        """
        path = Path(directory)
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        personalities = []
        for yaml_file in path.glob("*.yaml"):
            try:
                personality = self.load(yaml_file)
                personalities.append(personality)
            except Exception as e:
                # Log error but continue loading other files
                import logging
                logging.getLogger(__name__).warning(
                    f"Failed to load {yaml_file}: {e}"
                )
        
        return personalities
