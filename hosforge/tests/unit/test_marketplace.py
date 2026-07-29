"""Skill 市场功能单元测试。"""

import shutil
import tempfile
from pathlib import Path

from hosforge.skills.marketplace import (
    InstallStatus,
    MarketplaceClient,
    RemoteSkill,
    RemoteSkillRegistry,
    SkillVersion,
)


class TestSkillVersion:
    """测试 SkillVersion 数据模型。"""

    def test_skill_version_creation(self):
        """测试 SkillVersion 实例化。"""
        version = SkillVersion(
            version="1.0.0", release_date="2024-01-15", changelog="Initial release", min_hos_version="0.1.0"
        )
        assert version.version == "1.0.0"
        assert version.release_date == "2024-01-15"
        assert str(version) == "1.0.0"

    def test_skill_version_to_dict(self):
        """测试 SkillVersion 转换为字典。"""
        version = SkillVersion(version="1.0.0", release_date="2024-01-15")
        data = version.to_dict()
        assert data["version"] == "1.0.0"
        assert data["release_date"] == "2024-01-15"

    def test_skill_version_from_dict(self):
        """测试从字典创建 SkillVersion。"""
        data = {"version": "2.0.0", "release_date": "2024-02-01", "changelog": "Major update"}
        version = SkillVersion.from_dict(data)
        assert version.version == "2.0.0"
        assert version.release_date == "2024-02-01"


class TestRemoteSkill:
    """测试 RemoteSkill 数据模型。"""

    def test_remote_skill_creation(self):
        """测试 RemoteSkill 实例化。"""
        skill = RemoteSkill(name="test-skill", description="A test skill", author="Test Author", tags=["test", "demo"])
        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert skill.author == "Test Author"
        assert skill.tags == ["test", "demo"]
        assert skill.install_status == InstallStatus.NOT_INSTALLED

    def test_remote_skill_to_dict(self):
        """测试 RemoteSkill 转换为字典。"""
        skill = RemoteSkill(name="test-skill", description="Test", latest_version=SkillVersion(version="1.0.0"))
        data = skill.to_dict()
        assert data["name"] == "test-skill"
        assert data["latest_version"]["version"] == "1.0.0"

    def test_remote_skill_from_dict(self):
        """测试从字典创建 RemoteSkill。"""
        data = {
            "name": "test-skill",
            "description": "Test skill",
            "author": "Author",
            "versions": [{"version": "1.0.0"}],
            "tags": ["test"],
            "download_count": 100,
        }
        skill = RemoteSkill.from_dict(data)
        assert skill.name == "test-skill"
        assert skill.author == "Author"
        assert len(skill.versions) == 1
        assert skill.download_count == 100

    def test_remote_skill_matches_query(self):
        """测试 RemoteSkill 搜索匹配。"""
        skill = RemoteSkill(
            name="code-review", description="Automated code review", author="HOS Team", tags=["python", "quality"]
        )
        assert skill.matches_query("code") is True
        assert skill.matches_query("review") is True
        assert skill.matches_query("python") is True
        assert skill.matches_query("nonexistent") is False

    def test_remote_skill_has_update(self):
        """测试 RemoteSkill 更新检查。"""
        skill = RemoteSkill(
            name="test-skill",
            description="Test",
            install_status=InstallStatus.INSTALLED,
            installed_version="1.0.0",
            latest_version=SkillVersion(version="1.1.0"),
        )
        assert skill.has_update() is True

        skill.installed_version = "1.1.0"
        assert skill.has_update() is False


class TestRemoteSkillRegistry:
    """测试 RemoteSkillRegistry。"""

    def test_registry_initialization(self):
        """测试 RemoteSkillRegistry 初始化。"""
        registry = RemoteSkillRegistry()
        assert registry.sources is not None
        assert len(registry.sources) > 0

    def test_registry_list_skills(self):
        """测试列出远程 skills。"""
        registry = RemoteSkillRegistry()
        skills = registry.list_skills(force_refresh=True)
        assert len(skills) > 0
        assert all(isinstance(s, RemoteSkill) for s in skills)

    def test_registry_get_skill(self):
        """测试获取指定 skill。"""
        registry = RemoteSkillRegistry()
        skill = registry.get_skill("code-review")
        assert skill is not None
        assert skill.name == "code-review"

    def test_registry_get_nonexistent_skill(self):
        """测试获取不存在的 skill。"""
        registry = RemoteSkillRegistry()
        skill = registry.get_skill("nonexistent-skill")
        assert skill is None

    def test_registry_search_skills(self):
        """测试搜索 skills。"""
        registry = RemoteSkillRegistry()
        results = registry.search_skills("security")
        assert len(results) > 0
        assert any("security" in s.name.lower() or "security" in s.description.lower() for s in results)

    def test_registry_add_source(self):
        """测试添加远程源。"""
        registry = RemoteSkillRegistry()
        initial_count = len(registry.sources)
        registry.add_source("https://new-source.example.com/api")
        assert len(registry.sources) == initial_count + 1

    def test_registry_remove_source(self):
        """测试移除远程源。"""
        registry = RemoteSkillRegistry()
        source = registry.sources[0]
        result = registry.remove_source(source)
        assert result is True
        assert source not in registry.sources


class TestMarketplaceClient:
    """测试 MarketplaceClient。"""

    def setup_method(self):
        """每个测试方法前的设置。"""
        self.temp_dir = tempfile.mkdtemp()
        self.install_dir = Path(self.temp_dir) / "skills"
        self.cache_dir = Path(self.temp_dir) / "cache"
        self.client = MarketplaceClient(install_dir=self.install_dir, cache_dir=self.cache_dir)

    def teardown_method(self):
        """每个测试方法后的清理。"""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)

    def test_client_initialization(self):
        """测试 MarketplaceClient 初始化。"""
        assert self.client.install_dir.exists()
        assert self.client.cache_dir.exists()

    def test_client_list_remote_skills(self):
        """测试列出远程 skills。"""
        skills = self.client.list_remote_skills()
        assert len(skills) > 0

    def test_client_install_skill(self):
        """测试安装 skill。"""
        result = self.client.install_skill("code-review")
        assert result["success"] is True
        assert "Successfully installed" in result["message"]
        assert (self.install_dir / "code-review").exists()

    def test_client_install_already_installed(self):
        """测试重复安装 skill。"""
        self.client.install_skill("code-review")
        result = self.client.install_skill("code-review")
        assert result["success"] is False
        assert "already installed" in result["error"]

    def test_client_install_nonexistent_skill(self):
        """测试安装不存在的 skill。"""
        result = self.client.install_skill("nonexistent-skill")
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_client_uninstall_skill(self):
        """测试卸载 skill。"""
        self.client.install_skill("code-review")
        result = self.client.uninstall_skill("code-review")
        assert result["success"] is True
        assert "Successfully uninstalled" in result["message"]
        assert not (self.install_dir / "code-review").exists()

    def test_client_uninstall_not_installed(self):
        """测试卸载未安装的 skill。"""
        result = self.client.uninstall_skill("code-review")
        assert result["success"] is False
        assert "not installed" in result["error"]

    def test_client_update_skill(self):
        """测试更新 skill。"""
        # 先安装
        self.client.install_skill("code-review")
        # 模拟旧版本
        metadata_file = self.install_dir / "code-review" / "metadata.json"
        import json

        with open(metadata_file, "w") as f:
            json.dump({"name": "code-review", "version": "1.0.0"}, f)

        # 更新
        result = self.client.update_skill("code-review")
        assert result["success"] is True
        assert "Successfully updated" in result["message"]

    def test_client_update_not_installed(self):
        """测试更新未安装的 skill。"""
        result = self.client.update_skill("code-review")
        assert result["success"] is False
        assert "not installed" in result["error"]

    def test_client_search_skills(self):
        """测试搜索 skills。"""
        results = self.client.search_skills("security")
        assert len(results) > 0

    def test_client_get_installed_skills(self):
        """测试获取已安装的 skills。"""
        # 初始为空
        installed = self.client.get_installed_skills()
        assert len(installed) == 0

        # 安装一个 skill
        self.client.install_skill("code-review")

        # 再次检查
        installed = self.client.get_installed_skills()
        assert len(installed) == 1
        assert installed[0]["name"] == "code-review"
