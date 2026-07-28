"""Skill 与 MCP tool 之间的桥接层。

提供两个核心类：
- SkillToMCPTool: 将 Skill 实例转换为 MCP tool 定义
- MCPToolExecutor: 将 MCP tool 调用路由到对应的 Skill 执行
"""

import json
from typing import Any, Dict, List

from hosforge.skills.base_skill import Skill, SkillResult
from hosforge.skills.registry import SkillRegistry


class SkillToMCPTool:
    """将 Skill 转换为 MCP tool 定义。

    MCP tool 定义遵循 Model Context Protocol 规范，包含
    name、description 和 inputSchema 三个字段。
    """

    @staticmethod
    def convert(skill: Skill) -> Dict[str, Any]:
        """将一个 Skill 转换为 MCP tool 定义。

        Args:
            skill: 要转换的 Skill 实例

        Returns:
            符合 MCP tool 规范的字典，包含 name、description、inputSchema
        """
        input_schema = skill.parameters if skill.parameters else {
            "type": "object",
            "properties": {},
        }

        return {
            "name": skill.name,
            "description": skill.description,
            "inputSchema": input_schema,
        }

    @staticmethod
    def convert_all(skills: List[Skill]) -> List[Dict[str, Any]]:
        """批量将 Skill 列表转换为 MCP tool 定义列表。

        Args:
            skills: Skill 实例列表

        Returns:
            MCP tool 定义列表
        """
        return [SkillToMCPTool.convert(s) for s in skills]


class MCPToolExecutor:
    """执行 MCP tool 调用并路由到对应的 Skill。

    通过 SkillRegistry 查找目标 Skill，执行后将结果
    封装为 MCP tool 调用结果格式。
    """

    def __init__(self, registry: SkillRegistry) -> None:
        """初始化执行器。

        Args:
            registry: 已注册 Skill 的注册表
        """
        self._registry = registry

    @property
    def registry(self) -> SkillRegistry:
        """获取底层的 SkillRegistry。"""
        return self._registry

    def execute(
        self, tool_name: str, arguments: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """执行指定 tool 的调用。

        Args:
            tool_name: MCP tool 名称（对应 Skill.name）
            arguments: 传递给 Skill 的参数

        Returns:
            MCP tool 调用结果，格式为
            ``{"content": [{"type": "text", "text": "..."}], "isError": bool}``
        """
        args = arguments or {}
        result: SkillResult = self._registry.execute_skill(tool_name, **args)
        return self._format_result(result)

    def _format_result(self, result: SkillResult) -> Dict[str, Any]:
        """将 SkillResult 格式化为 MCP tool 返回结构。

        Args:
            result: Skill 执行产生的 SkillResult

        Returns:
            MCP 标准返回结构
        """
        if result.success:
            payload = result.data if result.data is not None else {}
            text = (
                json.dumps(payload, ensure_ascii=False, default=str)
                if not isinstance(payload, str)
                else payload
            )
            return {"content": [{"type": "text", "text": text}], "isError": False}

        error_text = result.error or "Unknown error"
        return {"content": [{"type": "text", "text": error_text}], "isError": True}
