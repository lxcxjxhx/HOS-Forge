"""Skill 元数据模块，定义 Skill 元数据结构并提供元数据提取与文档生成能力。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from hosforge.skills.base_skill import Skill


@dataclass
class SkillMetadata:
    """Skill 元数据数据类。

    Attributes:
        name: Skill 名称
        description: Skill 描述
        version: Skill 版本
        author: Skill 作者
        tags: Skill 标签列表
        parameters: Skill 输入参数 schema
    """

    name: str
    description: str
    version: str = "0.1.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)


class SkillMetadataExtractor:
    """从 Skill 实例中提取元数据。"""

    def extract(self, skill: Skill) -> SkillMetadata:
        """从 Skill 实例提取元数据。

        提取策略：
        - 基础字段（name/description/parameters）直接读取 skill 属性
        - version/author/tags 优先读取 skill 实例上的同名属性，
          其次读取类属性，最后使用默认值

        Args:
            skill: Skill 实例

        Returns:
            提取到的 SkillMetadata 实例
        """
        version = self._get_attr(skill, "version", "0.1.0")
        author = self._get_attr(skill, "author", "")
        tags = self._get_attr(skill, "tags", [])
        if not isinstance(tags, list):
            tags = list(tags)

        return SkillMetadata(
            name=skill.name,
            description=skill.description,
            version=str(version),
            author=str(author),
            tags=tags,
            parameters=dict(skill.parameters) if skill.parameters else {},
        )

    @staticmethod
    def _get_attr(skill: Skill, name: str, default: Any) -> Any:
        """安全获取 skill 实例或类上的属性。"""
        if hasattr(skill, name):
            return getattr(skill, name)
        return default


def generate_skill_doc(skill: Skill) -> str:
    """生成 Markdown 格式的 Skill 文档。

    Args:
        skill: Skill 实例

    Returns:
        Markdown 格式的文档字符串
    """
    extractor = SkillMetadataExtractor()
    meta = extractor.extract(skill)

    lines: List[str] = [
        f"# {meta.name}",
        "",
        meta.description,
        "",
        "| 字段 | 值 |",
        "| --- | --- |",
        f"| 版本 | {meta.version} |",
        f"| 作者 | {meta.author or '-'} |",
        f"| 标签 | {', '.join(meta.tags) if meta.tags else '-'} |",
        "",
    ]

    if meta.parameters:
        lines.append("## 参数")
        lines.append("")
        properties = meta.parameters.get("properties", {})
        required = set(meta.parameters.get("required", []))
        if properties:
            lines.append("| 参数 | 类型 | 必填 | 描述 |")
            lines.append("| --- | --- | --- | --- |")
            for param_name, param_schema in properties.items():
                p_type = param_schema.get("type", "any")
                p_desc = param_schema.get("description", "")
                p_req = "是" if param_name in required else "否"
                lines.append(f"| {param_name} | {p_type} | {p_req} | {p_desc} |")
            lines.append("")
        else:
            lines.append("无参数定义。")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"
