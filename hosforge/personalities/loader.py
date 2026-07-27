"""Personality loader for YAML personality files."""

import yaml
from pathlib import Path
from typing import Dict, List, Union
from .schema import Personality, PersonalitySchema


class PersonalityLoader:
    """Loader for personality YAML files."""
    
    def __init__(self, personalities_dir: Union[str, Path, None] = None):
        """Initialize personality loader.
        
        Args:
            personalities_dir: Directory containing personality YAML files
        """
        if personalities_dir is None:
            # Default to examples/personalities
            personalities_dir = Path(__file__).parent.parent.parent / "examples" / "personalities"
        
        self._personalities_dir = Path(personalities_dir)
        self._personalities: Dict[str, Personality] = {}
        
        # Load all personalities
        self._load_all()
    
    def _load_all(self) -> None:
        """Load all personality YAML files from directory."""
        if not self._personalities_dir.exists():
            return
        
        for yaml_file in self._personalities_dir.glob("*.yaml"):
            try:
                personality = self._load_file(yaml_file)
                self._personalities[personality.name] = personality
            except Exception:
                # Skip invalid files
                pass
    
    def _load_file(self, file_path: Path) -> Personality:
        """Load a single personality YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Personality object
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        schema = PersonalitySchema.from_yaml_dict(data)
        return schema.personality
    
    def get_personality(self, name: str) -> Personality:
        """Get personality by name.
        
        Args:
            name: Personality name
            
        Returns:
            Personality object
            
        Raises:
            KeyError: If personality not found
        """
        if name not in self._personalities:
            raise KeyError(f"Personality '{name}' not found")
        return self._personalities[name]
    
    def list_personalities(self) -> List[str]:
        """List all available personality names.
        
        Returns:
            List of personality names
        """
        return list(self._personalities.keys())