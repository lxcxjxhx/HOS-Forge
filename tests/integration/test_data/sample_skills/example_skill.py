"""Example skill used as test data for integration tests."""

from typing import Any, Dict

from hosforge.skills.base_skill import Skill


class ExampleIntegrationSkill(Skill):
    """Example skill for testing dynamic loading."""

    def __init__(self) -> None:
        super().__init__(
            name="example_integration",
            description="Example skill for integration testing",
            parameters={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "A message to echo back",
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of times to repeat",
                    },
                },
                "required": ["message"],
            },
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Echo the message back."""
        message = kwargs.get("message", "")
        count = kwargs.get("count", 1)
        return {"echo": message * count, "length": len(message) * count}
