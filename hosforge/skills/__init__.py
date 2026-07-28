"""Skill 抽象层模块，提供 Skill 基类、结果数据类、注册表和加载器。"""

from hosforge.skills.auto_register import AutoSkillRegistrar
from hosforge.skills.base_skill import Skill, SkillResult
from hosforge.skills.loader import SkillLoader
from hosforge.skills.metadata import (
    SkillMetadata,
    SkillMetadataExtractor,
    generate_skill_doc,
)
from hosforge.skills.registry import SkillRegistry

__all__ = [
    "Skill",
    "SkillResult",
    "SkillRegistry",
    "SkillLoader",
    "SkillMetadata",
    "SkillMetadataExtractor",
    "generate_skill_doc",
    "AutoSkillRegistrar",
]
