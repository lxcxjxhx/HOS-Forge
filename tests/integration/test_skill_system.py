"""Skill 系统集成测试。

测试 Skill 系统的核心功能，包括注册、发现、执行和错误处理。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from hosforge.skills.base_skill import Skill, SkillResult
from hosforge.skills.registry import SkillRegistry
from hosforge.skills.loader import SkillLoader
from hosforge.skills.metadata import SkillMetadataExtractor


class TestSkillRegistryIntegration:
    """测试 SkillRegistry 的集成场景。"""

    def test_register_multiple_skills(self):
        """测试注册多个 Skills。"""
        registry = SkillRegistry()
        
        # 创建多个 mock skills
        skill1 = Mock(spec=Skill)
        skill1.name = "skill1"
        skill1.description = "Test skill 1"
        
        skill2 = Mock(spec=Skill)
        skill2.name = "skill2"
        skill2.description = "Test skill 2"
        
        # 注册
        registry.register(skill1)
        registry.register(skill2)
        
        # 验证
        assert len(registry.list_skills()) == 2
        assert registry.get("skill1") == skill1
        assert registry.get("skill2") == skill2

    def test_unregister_skill(self):
        """测试取消注册 Skill。"""
        registry = SkillRegistry()
        
        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        
        registry.register(skill)
        assert registry.get("test_skill") is not None
        
        registry.unregister("test_skill")
        assert registry.get("test_skill") is None

    def test_execute_skill_success(self):
        """测试成功执行 Skill。"""
        registry = SkillRegistry()
        
        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.validate_input.return_value = True
        skill.execute.return_value = {"result": "success"}
        
        registry.register(skill)
        result = registry.execute_skill("test_skill", param1="value1")
        
        assert result.success is True
        assert result.data == {"result": "success"}
        skill.execute.assert_called_once_with(param1="value1")

    def test_execute_skill_not_found(self):
        """测试执行不存在的 Skill。"""
        registry = SkillRegistry()
        
        result = registry.execute_skill("nonexistent_skill")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_execute_skill_with_error(self):
        """测试执行 Skill 时发生错误。"""
        registry = SkillRegistry()
        
        skill = Mock(spec=Skill)
        skill.name = "error_skill"
        skill.validate_input.return_value = True
        skill.execute.side_effect = RuntimeError("Execution failed")
        
        registry.register(skill)
        
        result = registry.execute_skill("error_skill")
        assert result.success is False
        assert "Execution failed" in result.error

    def test_list_skills_empty_registry(self):
        """测试空注册表。"""
        registry = SkillRegistry()
        skills = registry.list_skills()
        assert len(skills) == 0

    def test_list_skills_with_multiple_skills(self):
        """测试列出多个 Skills。"""
        registry = SkillRegistry()
        
        for i in range(5):
            skill = Mock(spec=Skill)
            skill.name = f"skill_{i}"
            registry.register(skill)
        
        skills = registry.list_skills()
        assert len(skills) == 5
        skill_names = [s.name for s in skills]
        assert "skill_0" in skill_names
        assert "skill_4" in skill_names


class TestSkillLoaderIntegration:
    """测试 SkillLoader 的集成场景。"""

    def test_load_skills_from_directory(self, tmp_path):
        """测试从目录加载 Skills。"""
        # 创建一个测试 skill 文件
        skill_file = tmp_path / "test_skill.py"
        skill_file.write_text("""
from hosforge.skills.base_skill import Skill

class TestSkill(Skill):
    def __init__(self):
        super().__init__(
            name="loaded_skill",
            description="Loaded from directory",
            parameters={"type": "object", "properties": {}},
        )
    
    def execute(self, **kwargs):
        return {"status": "success"}
""")
        
        loader = SkillLoader()
        skills = loader.load_from_directory(str(tmp_path))
        
        assert len(skills) > 0
        assert any(s.name == "loaded_skill" for s in skills)

    def test_load_skills_from_nonexistent_directory(self):
        """测试从不存在的目录加载。"""
        loader = SkillLoader()
        skills = loader.load_from_directory("/nonexistent/path")
        assert len(skills) == 0

    def test_load_skills_from_invalid_module(self, tmp_path):
        """测试从无效模块加载。"""
        invalid_file = tmp_path / "invalid.py"
        invalid_file.write_text("invalid python syntax {{{")
        
        loader = SkillLoader()
        skills = loader.load_from_directory(str(tmp_path))
        # 应该跳过无效文件
        assert isinstance(skills, list)


class TestSkillMetadataExtractor:
    """测试 Skill 元数据提取。"""

    def test_extract_metadata_from_skill(self):
        """测试从 Skill 提取元数据。"""
        skill = Mock(spec=Skill)
        skill.name = "test_skill"
        skill.description = "Test skill description"
        skill.parameters = {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "Parameter 1"},
            },
            "required": ["param1"],
        }
        
        extractor = SkillMetadataExtractor()
        metadata = extractor.extract(skill)
        
        assert metadata.name == "test_skill"
        assert metadata.description == "Test skill description"
        assert "param1" in metadata.parameters["properties"]

    def test_extract_metadata_with_empty_parameters(self):
        """测试提取无参数的 Skill 元数据。"""
        skill = Mock(spec=Skill)
        skill.name = "no_param_skill"
        skill.description = "Skill without parameters"
        skill.parameters = {"type": "object", "properties": {}}
        
        extractor = SkillMetadataExtractor()
        metadata = extractor.extract(skill)
        
        assert metadata.name == "no_param_skill"
        assert len(metadata.parameters["properties"]) == 0


class TestSkillResultHandling:
    """测试 SkillResult 的处理。"""

    def test_skill_result_success(self):
        """测试成功的 SkillResult。"""
        result = SkillResult(
            success=True,
            data={"key": "value"},
            metadata={"duration": 1.5},
        )
        
        assert result.success is True
        assert result.data["key"] == "value"
        assert result.metadata["duration"] == 1.5
        assert result.error is None

    def test_skill_result_failure(self):
        """测试失败的 SkillResult。"""
        result = SkillResult(
            success=False,
            error="Something went wrong",
        )
        
        assert result.success is False
        assert result.error == "Something went wrong"
        assert result.data is None

    def test_skill_result_with_complex_data(self):
        """测试包含复杂数据的 SkillResult。"""
        complex_data = {
            "findings": [
                {"id": 1, "severity": "high"},
                {"id": 2, "severity": "medium"},
            ],
            "statistics": {
                "total": 2,
                "high": 1,
                "medium": 1,
            },
        }
        
        result = SkillResult(
            success=True,
            data=complex_data,
        )
        
        assert result.success is True
        assert len(result.data["findings"]) == 2
        assert result.data["statistics"]["total"] == 2
