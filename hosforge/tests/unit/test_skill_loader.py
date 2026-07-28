"""Skill 加载器和元数据提取器单元测试。"""

import pytest
from typing import Any, Dict

from hosforge.skills import Skill
from hosforge.skills.loader import SkillLoader
from hosforge.skills.metadata import SkillMetadata, SkillMetadataExtractor, generate_skill_doc


class SampleSkill(Skill):
    """用于测试的示例 Skill。"""

    def __init__(self) -> None:
        super().__init__(
            name="sample_skill",
            description="A sample skill for testing",
            parameters={
                "type": "object",
                "properties": {
                    "input": {"type": "string", "description": "Input string"},
                    "count": {"type": "integer", "description": "Repeat count"},
                },
                "required": ["input"],
            },
        )
        self.version = "1.0.0"
        self.author = "Test Author"
        self.tags = ["test", "sample"]

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行示例操作。"""
        input_str = kwargs.get("input", "")
        count = kwargs.get("count", 1)
        return {"result": input_str * count}


class AnotherSkill(Skill):
    """另一个测试 Skill。"""

    def __init__(self) -> None:
        super().__init__(
            name="another_skill",
            description="Another test skill",
        )

    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行另一个操作。"""
        return {"status": "ok"}


class TestSkillLoader:
    """测试 SkillLoader。"""

    def test_load_from_directory_nonexistent(self):
        """测试从不存在的目录加载。"""
        loader = SkillLoader()
        skills = loader.load_from_directory("/nonexistent/path")
        assert skills == []

    def test_load_from_module_nonexistent(self):
        """测试从不存在的模块加载。"""
        loader = SkillLoader()
        skills = loader.load_from_module("nonexistent.module")
        assert skills == []

    def test_discover_skills_empty_paths(self):
        """测试空路径列表。"""
        loader = SkillLoader()
        skills = loader.discover_skills([])
        assert skills == []

    def test_extract_skills_from_module(self):
        """测试从模块提取 skills。"""
        import hosforge.tests.unit.test_skill_loader as test_module

        loader = SkillLoader()
        skills = loader._extract_skills_from_module(test_module)

        # 应该找到 SampleSkill 和 AnotherSkill
        skill_names = [s.name for s in skills]
        assert "sample_skill" in skill_names
        assert "another_skill" in skill_names

    def test_is_skill_subclass_valid(self):
        """测试检查有效的 Skill 子类。"""
        loader = SkillLoader()
        assert loader._is_skill_subclass(SampleSkill) is True
        assert loader._is_skill_subclass(AnotherSkill) is True

    def test_is_skill_subclass_invalid(self):
        """测试检查无效的 Skill 子类。"""
        loader = SkillLoader()
        assert loader._is_skill_subclass(Skill) is False
        assert loader._is_skill_subclass(str) is False
        assert loader._is_skill_subclass(int) is False


class TestSkillMetadata:
    """测试 SkillMetadata。"""

    def test_metadata_creation(self):
        """测试元数据创建。"""
        metadata = SkillMetadata(
            name="test",
            description="Test skill",
            version="1.0.0",
            author="Author",
            tags=["tag1", "tag2"],
        )
        assert metadata.name == "test"
        assert metadata.description == "Test skill"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Author"
        assert metadata.tags == ["tag1", "tag2"]

    def test_metadata_defaults(self):
        """测试元数据默认值。"""
        metadata = SkillMetadata(name="test", description="Test")
        assert metadata.version == "0.1.0"
        assert metadata.author == ""
        assert metadata.tags == []
        assert metadata.parameters == {}


class TestSkillMetadataExtractor:
    """测试 SkillMetadataExtractor。"""

    def test_extract_metadata(self):
        """测试提取元数据。"""
        skill = SampleSkill()
        extractor = SkillMetadataExtractor()
        metadata = extractor.extract(skill)

        assert metadata.name == "sample_skill"
        assert metadata.description == "A sample skill for testing"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.tags == ["test", "sample"]
        assert "input" in metadata.parameters["properties"]

    def test_extract_metadata_defaults(self):
        """测试提取元数据默认值。"""
        skill = AnotherSkill()
        extractor = SkillMetadataExtractor()
        metadata = extractor.extract(skill)

        assert metadata.name == "another_skill"
        assert metadata.version == "0.1.0"
        assert metadata.author == ""
        assert metadata.tags == []


class TestGenerateSkillDoc:
    """测试文档生成。"""

    def test_generate_doc_with_parameters(self):
        """测试生成带参数的文档。"""
        skill = SampleSkill()
        doc = generate_skill_doc(skill)

        assert "# sample_skill" in doc
        assert "A sample skill for testing" in doc
        assert "1.0.0" in doc
        assert "Test Author" in doc
        assert "test, sample" in doc
        assert "input" in doc
        assert "count" in doc
        assert "Input string" in doc

    def test_generate_doc_without_parameters(self):
        """测试生成无参数的文档。"""
        skill = AnotherSkill()
        doc = generate_skill_doc(skill)

        assert "# another_skill" in doc
        assert "Another test skill" in doc
        assert "无参数定义" in doc or "参数" not in doc
