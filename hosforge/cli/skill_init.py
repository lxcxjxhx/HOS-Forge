"""Skill 初始化工具，提供 skill 脚手架生成功能。"""

import os
import sys
from pathlib import Path
from typing import Optional


SKILL_TEMPLATE = '''"""{{ skill_name }} - {{ description }}"""

from typing import Any, Dict

from hosforge.skills.base_skill import Skill


class {{ class_name }}(Skill):
    """{{ description }}

    Attributes:
        name: Skill 名称
        description: Skill 描述
        parameters: 输入参数 schema
    """

    def __init__(self) -> None:
        """初始化 {{ class_name }}。"""
        super().__init__(
            name="{{ skill_name }}",
            description="{{ description }}",
            parameters={
                "type": "object",
                "properties": {
                    "input": {
                        "type": "string",
                        "description": "输入参数",
                    },
                },
                "required": ["input"],
            },
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行 skill 核心逻辑。

        Args:
            **kwargs: 传递给 skill 的参数

        Returns:
            包含执行结果的字典
        """
        input_value = kwargs.get("input", "")

        # TODO: 实现你的 skill 逻辑
        result = {
            "success": True,
            "data": {
                "processed": input_value,
                "message": "Skill executed successfully",
            },
        }

        return result
'''


TEST_TEMPLATE = '''"""Tests for {{ skill_name }} skill."""

import pytest

from {{ module_path }} import {{ class_name }}


class Test{{ class_name }}:
    """Test suite for {{ class_name }}."""

    def setup_method(self):
        """Set up test fixtures."""
        self.skill = {{ class_name }}()

    def test_skill_initialization(self):
        """Test skill initialization."""
        assert self.skill.name == "{{ skill_name }}"
        assert self.skill.description == "{{ description }}"
        assert "input" in self.skill.parameters.get("properties", {})

    def test_skill_validate_input_valid(self):
        """Test input validation with valid input."""
        assert self.skill.validate_input(input="test input")

    def test_skill_validate_input_missing_required(self):
        """Test input validation with missing required parameter."""
        assert not self.skill.validate_input()

    def test_skill_execute_success(self):
        """Test successful skill execution."""
        result = self.skill.execute(input="test input")
        assert result["success"] is True
        assert "data" in result
        assert result["data"]["processed"] == "test input"

    def test_skill_execute_with_empty_input(self):
        """Test skill execution with empty input."""
        result = self.skill.execute(input="")
        assert result["success"] is True
'''


README_TEMPLATE = '''# {{ skill_name }}

{{ description }}

## Installation

```bash
# Install from skill marketplace
hos skill market install {{ skill_name }}

# Or copy to your local skills directory
cp -r {{ skill_name }} ~/.hos/skills/
```

## Usage

### CLI

```bash
# Execute skill
hos skill run {{ skill_name }} input="your input here"
```

### Python API

```python
from {{ module_path }} import {{ class_name }}

skill = {{ class_name }}()
result = skill.execute(input="your input here")
print(result)
```

### MCP Server

```bash
# Start MCP server
python -m hosforge.mcp_server.server

# Call via HTTP
curl -X POST http://localhost:8000/tools/{{ skill_name }}/execute \\
  -H "Content-Type: application/json" \\
  -d '{"arguments": {"input": "your input here"}}'
```

## Parameters

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| input     | string | Yes      | Input parameter |

## Examples

### Example 1: Basic usage

```bash
hos skill run {{ skill_name }} input="hello world"
```

Output:
```json
{
  "success": true,
  "data": {
    "processed": "hello world",
    "message": "Skill executed successfully"
  }
}
```

## Development

### Running tests

```bash
pytest tests/test_{{ skill_name }}.py -v
```

### Code quality

```bash
# Format code
black {{ skill_name }}.py

# Check types
mypy {{ skill_name }}.py
```

## License

MIT
'''


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to CamelCase.

    Args:
        snake_str: Snake case string

    Returns:
        CamelCase string
    """
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def init_skill(
    skill_name: str,
    description: str = "A custom HOS-Forge skill",
    output_dir: Optional[str] = None,
    with_tests: bool = True,
    with_readme: bool = True,
) -> Dict[str, Any]:
    """Initialize a new skill with template files.

    Args:
        skill_name: Skill name (snake_case)
        description: Skill description
        output_dir: Output directory (default: current directory)
        with_tests: Whether to generate test file
        with_readme: Whether to generate README file

    Returns:
        Dictionary with creation results
    """
    # Validate skill name
    if not skill_name.isidentifier():
        return {
            "success": False,
            "error": f"Invalid skill name: {skill_name}. Must be a valid Python identifier.",
        }

    # Convert to snake_case if needed
    skill_name = skill_name.lower().replace("-", "_").replace(" ", "_")

    # Prepare variables
    class_name = to_camel_case(skill_name)
    module_name = f"{skill_name}_skill"
    module_path = f"hosforge.skills.custom.{module_name}"

    # Determine output directory
    if output_dir is None:
        output_dir = os.getcwd()
    output_path = Path(output_dir)

    # Create skill directory
    skill_dir = output_path / skill_name
    if skill_dir.exists():
        return {
            "success": False,
            "error": f"Directory already exists: {skill_dir}",
        }

    try:
        skill_dir.mkdir(parents=True, exist_ok=True)

        created_files = []

        # Generate main skill file
        skill_file = skill_dir / f"{module_name}.py"
        skill_content = (
            SKILL_TEMPLATE.replace("{{ skill_name }}", skill_name)
            .replace("{{ class_name }}", class_name)
            .replace("{{ description }}", description)
        )
        skill_file.write_text(skill_content, encoding="utf-8")
        created_files.append(str(skill_file))

        # Generate __init__.py
        init_file = skill_dir / "__init__.py"
        init_content = f'''"""Custom skill: {skill_name}"""

from .{module_name} import {class_name}

__all__ = ["{class_name}"]
'''
        init_file.write_text(init_content, encoding="utf-8")
        created_files.append(str(init_file))

        # Generate test file
        if with_tests:
            test_file = skill_dir / f"test_{module_name}.py"
            test_content = (
                TEST_TEMPLATE.replace("{{ skill_name }}", skill_name)
                .replace("{{ class_name }}", class_name)
                .replace("{{ description }}", description)
                .replace("{{ module_path }}", module_path)
            )
            test_file.write_text(test_content, encoding="utf-8")
            created_files.append(str(test_file))

        # Generate README
        if with_readme:
            readme_file = skill_dir / "README.md"
            readme_content = (
                README_TEMPLATE.replace("{{ skill_name }}", skill_name)
                .replace("{{ class_name }}", class_name)
                .replace("{{ description }}", description)
                .replace("{{ module_path }}", module_path)
            )
            readme_file.write_text(readme_content, encoding="utf-8")
            created_files.append(str(readme_file))

        return {
            "success": True,
            "skill_name": skill_name,
            "class_name": class_name,
            "output_dir": str(skill_dir),
            "created_files": created_files,
            "message": f"Skill '{skill_name}' initialized successfully at {skill_dir}",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to initialize skill: {str(e)}",
        }


def cmd_skill_init(args) -> int:
    """Execute skill init command.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success)
    """
    result = init_skill(
        skill_name=args.name,
        description=getattr(args, "description", "A custom HOS-Forge skill"),
        output_dir=getattr(args, "output", None),
        with_tests=getattr(args, "with_tests", True),
        with_readme=getattr(args, "with_readme", True),
    )

    if result["success"]:
        print(f"✓ {result['message']}")
        print(f"\nCreated files:")
        for file_path in result["created_files"]:
            print(f"  - {file_path}")
        print(f"\nNext steps:")
        print(f"  1. Edit {result['skill_name']}/{result['skill_name']}_skill.py to implement your logic")
        print(f"  2. Run tests: pytest {result['skill_name']}/test_*.py -v")
        print(f"  3. Install: hos skill market install {result['skill_name']}")
        return 0
    else:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1
