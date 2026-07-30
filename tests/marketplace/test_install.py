"""Marketplace 安装功能测试。

测试 skill 包解压、安装、验证和回滚功能，包括：
- tar.gz 和 zip 解压
- 文件完整性验证
- 安装失败回滚机制
- 完整安装流程
"""

import io
import json
import tarfile
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hosforge.skills.marketplace.client import MarketplaceClient
from hosforge.skills.marketplace.models import (
    InstallStatus,
    RemoteSkill,
    SkillVersion,
)


def _create_tar_gz_package(content_files: dict, top_dir: str = None) -> bytes:
    """创建 tar.gz 测试包。

    Args:
        content_files: 文件内容字典 {文件名: 内容}
        top_dir: 顶层目录名，如果为 None 则不创建顶层目录

    Returns:
        tar.gz 文件的字节内容
    """
    bio = io.BytesIO()
    with tarfile.open(fileobj=bio, mode="w:gz") as tar:
        for filename, content in content_files.items():
            if top_dir:
                arcname = f"{top_dir}/{filename}"
            else:
                arcname = filename
            data = content.encode("utf-8")
            info = tarfile.TarInfo(name=arcname)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return bio.getvalue()


def _create_zip_package(content_files: dict, top_dir: str = None) -> bytes:
    """创建 zip 测试包。

    Args:
        content_files: 文件内容字典 {文件名: 内容}
        top_dir: 顶层目录名，如果为 None 则不创建顶层目录

    Returns:
        zip 文件的字节内容
    """
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, content in content_files.items():
            if top_dir:
                arcname = f"{top_dir}/{filename}"
            else:
                arcname = filename
            zf.writestr(arcname, content)
    return bio.getvalue()


class TestExtractSkillPackage:
    """测试 _extract_skill_package 方法。"""

    def test_extract_tar_gz_with_top_directory(self):
        """测试解压带顶层目录的 tar.gz 包。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            # 创建带顶层目录的 tar.gz 包
            content_files = {
                "__init__.py": "# skill init",
                "main.py": "def run(): pass",
                "README.md": "# Test Skill",
            }
            package_data = _create_tar_gz_package(content_files, top_dir="test-skill-1.0.0")

            # 写入临时文件
            package_path = Path(temp_dir) / "test-skill-1.0.0.tar.gz"
            package_path.write_bytes(package_data)

            # 解压
            target_dir = install_dir / "test-skill"
            result = client._extract_skill_package(package_path, target_dir, "test-skill")

            assert result["success"] is True
            assert (target_dir / "__init__.py").exists()
            assert (target_dir / "main.py").exists()
            assert (target_dir / "README.md").exists()

            # 验证内容
            assert (target_dir / "__init__.py").read_text() == "# skill init"
            assert (target_dir / "main.py").read_text() == "def run(): pass"

    def test_extract_tar_gz_without_top_directory(self):
        """测试解压不带顶层目录的 tar.gz 包（多个文件）。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            # 创建不带顶层目录的 tar.gz 包
            content_files = {
                "__init__.py": "# init",
                "skill.py": "class Skill: pass",
            }
            package_data = _create_tar_gz_package(content_files, top_dir=None)

            package_path = Path(temp_dir) / "test.tar.gz"
            package_path.write_bytes(package_data)

            target_dir = install_dir / "test-skill"
            result = client._extract_skill_package(package_path, target_dir, "test-skill")

            assert result["success"] is True
            assert (target_dir / "__init__.py").exists()
            assert (target_dir / "skill.py").exists()

    def test_extract_zip_with_top_directory(self):
        """测试解压带顶层目录的 zip 包。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            content_files = {
                "__init__.py": "# zip skill",
                "handler.py": "def handle(): return True",
            }
            package_data = _create_zip_package(content_files, top_dir="my-skill-2.0.0")

            package_path = Path(temp_dir) / "my-skill-2.0.0.zip"
            package_path.write_bytes(package_data)

            target_dir = install_dir / "my-skill"
            result = client._extract_skill_package(package_path, target_dir, "my-skill")

            assert result["success"] is True
            assert (target_dir / "__init__.py").exists()
            assert (target_dir / "handler.py").exists()
            assert (target_dir / "__init__.py").read_text() == "# zip skill"

    def test_extract_zip_without_top_directory(self):
        """测试解压不带顶层目录的 zip 包。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            content_files = {
                "__init__.py": "# init",
                "utils.py": "def helper(): pass",
            }
            package_data = _create_zip_package(content_files, top_dir=None)

            package_path = Path(temp_dir) / "test.zip"
            package_path.write_bytes(package_data)

            target_dir = install_dir / "test-skill"
            result = client._extract_skill_package(package_path, target_dir, "test-skill")

            assert result["success"] is True
            assert (target_dir / "__init__.py").exists()
            assert (target_dir / "utils.py").exists()

    def test_extract_unsupported_format(self):
        """测试解压不支持的格式。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            # 创建 .rar 文件
            package_path = Path(temp_dir) / "test.rar"
            package_path.write_bytes(b"fake rar content")

            target_dir = install_dir / "test-skill"
            result = client._extract_skill_package(package_path, target_dir, "test-skill")

            assert result["success"] is False
            assert "unsupported" in result["error"].lower()

    def test_extract_corrupted_tar_gz(self):
        """测试解压损坏的 tar.gz 文件。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            # 写入损坏的 tar.gz 数据
            package_path = Path(temp_dir) / "corrupted.tar.gz"
            package_path.write_bytes(b"this is not a valid tar.gz file")

            target_dir = install_dir / "test-skill"
            result = client._extract_skill_package(package_path, target_dir, "test-skill")

            assert result["success"] is False
            assert "failed to extract" in result["error"].lower() or "extraction failed" in result["error"].lower()

    def test_extract_corrupted_zip(self):
        """测试解压损坏的 zip 文件。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            # 写入损坏的 zip 数据
            package_path = Path(temp_dir) / "corrupted.zip"
            package_path.write_bytes(b"this is not a valid zip file")

            target_dir = install_dir / "test-skill"
            result = client._extract_skill_package(package_path, target_dir, "test-skill")

            assert result["success"] is False
            assert "failed to extract" in result["error"].lower() or "extraction failed" in result["error"].lower()

    def test_extract_creates_target_directory(self):
        """测试解压时自动创建目标目录。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            content_files = {"__init__.py": "# init"}
            package_data = _create_tar_gz_package(content_files, top_dir=None)

            package_path = Path(temp_dir) / "test.tar.gz"
            package_path.write_bytes(package_data)

            # 目标目录不存在
            target_dir = install_dir / "new-skill"
            assert not target_dir.exists()

            result = client._extract_skill_package(package_path, target_dir, "new-skill")

            assert result["success"] is True
            assert target_dir.exists()
            assert (target_dir / "__init__.py").exists()


class TestValidateSkillFiles:
    """测试 _validate_skill_files 方法。"""

    def test_validate_skill_with_init_py(self):
        """测试包含 __init__.py 的 skill 验证通过。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "__init__.py").write_text("# init")
            (skill_dir / "main.py").write_text("def run(): pass")

            result = client._validate_skill_files(skill_dir, "test-skill")

            assert result["valid"] is True
            assert len(result["errors"]) == 0

    def test_validate_skill_with_skill_name_py(self):
        """测试包含 <skill_name>.py 的 skill 验证通过。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "my-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "my-skill.py").write_text("class MySkill: pass")

            result = client._validate_skill_files(skill_dir, "my-skill")

            assert result["valid"] is True
            assert len(result["errors"]) == 0

    def test_validate_skill_missing_required_files(self):
        """测试缺少必要文件时验证失败。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            # 只创建无关文件
            (skill_dir / "utils.py").write_text("def helper(): pass")

            result = client._validate_skill_files(skill_dir, "test-skill")

            assert result["valid"] is False
            assert any("missing required files" in e.lower() for e in result["errors"])

    def test_validate_skill_directory_not_exist(self):
        """测试目录不存在时验证失败。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "nonexistent-skill"

            result = client._validate_skill_files(skill_dir, "nonexistent-skill")

            assert result["valid"] is False
            assert any("does not exist" in e for e in result["errors"])

    def test_validate_skill_with_valid_metadata(self):
        """测试包含有效 metadata.json 的 skill 验证通过。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "__init__.py").write_text("# init")

            metadata = {"name": "test-skill", "version": "1.0.0"}
            (skill_dir / "metadata.json").write_text(json.dumps(metadata))

            result = client._validate_skill_files(skill_dir, "test-skill")

            assert result["valid"] is True
            assert len(result["errors"]) == 0

    def test_validate_skill_metadata_missing_name(self):
        """测试 metadata.json 缺少 name 字段时验证失败。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "__init__.py").write_text("# init")

            metadata = {"version": "1.0.0"}  # 缺少 name
            (skill_dir / "metadata.json").write_text(json.dumps(metadata))

            result = client._validate_skill_files(skill_dir, "test-skill")

            assert result["valid"] is False
            assert any("name" in e.lower() for e in result["errors"])

    def test_validate_skill_metadata_missing_version(self):
        """测试 metadata.json 缺少 version 字段时验证失败。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "__init__.py").write_text("# init")

            metadata = {"name": "test-skill"}  # 缺少 version
            (skill_dir / "metadata.json").write_text(json.dumps(metadata))

            result = client._validate_skill_files(skill_dir, "test-skill")

            assert result["valid"] is False
            assert any("version" in e.lower() for e in result["errors"])

    def test_validate_skill_invalid_metadata_json(self):
        """测试 metadata.json 格式无效时验证失败。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "__init__.py").write_text("# init")

            # 写入无效的 JSON
            (skill_dir / "metadata.json").write_text("{invalid json content")

            result = client._validate_skill_files(skill_dir, "test-skill")

            assert result["valid"] is False
            assert any("invalid metadata.json" in e.lower() for e in result["errors"])

    def test_validate_skill_metadata_name_mismatch_warning(self):
        """测试 metadata.json name 不匹配时产生警告。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "__init__.py").write_text("# init")

            metadata = {"name": "different-name", "version": "1.0.0"}
            (skill_dir / "metadata.json").write_text(json.dumps(metadata))

            result = client._validate_skill_files(skill_dir, "test-skill")

            # 验证仍然通过（只是警告）
            assert result["valid"] is True
            assert any("does not match" in w for w in result["warnings"])

    def test_validate_skill_missing_optional_files_warning(self):
        """测试缺少可选文件时产生警告但不影响验证。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "__init__.py").write_text("# init")
            # 不创建 README.md 和 metadata.json

            result = client._validate_skill_files(skill_dir, "test-skill")

            assert result["valid"] is True
            # 应该有可选文件缺失的警告
            assert any("readme.md" in w.lower() or "metadata.json" in w.lower() for w in result["warnings"])


class TestRollbackInstallation:
    """测试 _rollback_installation 方法。"""

    def test_rollback_removes_skill_directory(self):
        """测试回滚时删除 skill 目录。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "__init__.py").write_text("# init")
            (skill_dir / "main.py").write_text("def run(): pass")

            result = client._rollback_installation("test-skill", skill_dir)

            assert result["success"] is True
            assert not skill_dir.exists()

    def test_rollback_cleans_temp_files(self):
        """测试回滚时清理临时文件。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            # 创建临时文件
            temp_file1 = Path(temp_dir) / "temp1.tar.gz"
            temp_file1.write_bytes(b"temp content 1")
            temp_file2 = Path(temp_dir) / "temp2.zip"
            temp_file2.write_bytes(b"temp content 2")

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)

            result = client._rollback_installation(
                "test-skill", skill_dir, temp_files=[temp_file1, temp_file2]
            )

            assert result["success"] is True
            assert not temp_file1.exists()
            assert not temp_file2.exists()
            assert not skill_dir.exists()

    def test_rollback_when_directory_not_exist(self):
        """测试回滚时目录不存在的情况。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "nonexistent-skill"

            result = client._rollback_installation("nonexistent-skill", skill_dir)

            assert result["success"] is True

    def test_rollback_with_empty_temp_files_list(self):
        """测试回滚时空临时文件列表的情况。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)

            result = client._rollback_installation("test-skill", skill_dir, temp_files=[])

            assert result["success"] is True
            assert not skill_dir.exists()


class TestInstallSkillIntegration:
    """测试 install_skill 方法的完整安装流程。"""

    def _make_skill(self, name: str = "test-skill", version: str = "1.0.0") -> RemoteSkill:
        """创建测试用 RemoteSkill 对象。"""
        return RemoteSkill(
            name=name,
            description=f"Test skill: {name}",
            repository=f"https://github.com/test/{name}",
            versions=[SkillVersion(version=version)],
            latest_version=SkillVersion(version=version),
        )

    def test_install_skill_full_success(self):
        """测试完整安装流程成功。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            cache_dir = Path(temp_dir) / "cache"
            client = MarketplaceClient(install_dir=install_dir, cache_dir=cache_dir)

            skill = self._make_skill()
            client.registry.get_skill = MagicMock(return_value=skill)

            # 创建有效的 skill 包
            content_files = {
                "__init__.py": "# test skill",
                "main.py": "def run(): return 'hello'",
            }
            package_data = _create_tar_gz_package(content_files, top_dir="test-skill-1.0.0")

            # Mock 下载方法，创建真实的压缩包文件
            def mock_download(name, version):
                pkg_path = Path(temp_dir) / f"{name}-{version}.tar.gz"
                pkg_path.write_bytes(package_data)
                return {"success": True, "file_path": str(pkg_path)}

            with patch.object(client, "_download_skill", side_effect=mock_download):
                result = client.install_skill("test-skill", "1.0.0")

            assert result["success"] is True
            assert result["skill_name"] == "test-skill"
            assert result["version"] == "1.0.0"

            # 验证安装目录
            skill_dir = install_dir / "test-skill"
            assert skill_dir.exists()
            assert (skill_dir / "__init__.py").exists()
            assert (skill_dir / "main.py").exists()
            assert (skill_dir / "metadata.json").exists()

            # 验证 metadata
            with open(skill_dir / "metadata.json") as f:
                metadata = json.load(f)
            assert metadata["name"] == "test-skill"
            assert metadata["version"] == "1.0.0"

            # 验证状态更新
            assert skill.install_status == InstallStatus.INSTALLED
            assert skill.installed_version == "1.0.0"

    def test_install_skill_already_installed(self):
        """测试安装已存在的 skill。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill = self._make_skill()
            client.registry.get_skill = MagicMock(return_value=skill)

            # 创建已安装目录
            skill_dir = install_dir / "test-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "metadata.json").write_text("{}")

            result = client.install_skill("test-skill", "1.0.0")

            assert result["success"] is False
            assert "already installed" in result["error"].lower()

    def test_install_skill_not_found(self):
        """测试安装不存在的 skill。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            client.registry.get_skill = MagicMock(return_value=None)

            result = client.install_skill("nonexistent-skill", "1.0.0")

            assert result["success"] is False
            assert "not found" in result["error"].lower()

    def test_install_skill_download_failure(self):
        """测试下载失败时的处理。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill = self._make_skill()
            client.registry.get_skill = MagicMock(return_value=skill)

            with patch.object(
                client, "_download_skill",
                return_value={"success": False, "error": "Network error"},
            ):
                result = client.install_skill("test-skill", "1.0.0")

            assert result["success"] is False
            assert skill.install_status == InstallStatus.ERROR

    def test_install_skill_extraction_failure_triggers_rollback(self):
        """测试解压失败时触发回滚。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill = self._make_skill()
            client.registry.get_skill = MagicMock(return_value=skill)

            # 创建损坏的包文件
            def mock_download(name, version):
                pkg_path = Path(temp_dir) / f"{name}-{version}.tar.gz"
                pkg_path.write_bytes(b"corrupted data")
                return {"success": True, "file_path": str(pkg_path)}

            with patch.object(client, "_download_skill", side_effect=mock_download):
                result = client.install_skill("test-skill", "1.0.0")

            assert result["success"] is False
            assert skill.install_status == InstallStatus.ERROR

            # 验证回滚：安装目录应该被清理
            skill_dir = install_dir / "test-skill"
            assert not skill_dir.exists()

    def test_install_skill_validation_failure_triggers_rollback(self):
        """测试验证失败时触发回滚。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill = self._make_skill()
            client.registry.get_skill = MagicMock(return_value=skill)

            # 创建缺少必要文件的包
            content_files = {
                "utils.py": "def helper(): pass",  # 缺少 __init__.py 和 test-skill.py
            }
            package_data = _create_tar_gz_package(content_files, top_dir="test-skill-1.0.0")

            def mock_download(name, version):
                pkg_path = Path(temp_dir) / f"{name}-{version}.tar.gz"
                pkg_path.write_bytes(package_data)
                return {"success": True, "file_path": str(pkg_path)}

            with patch.object(client, "_download_skill", side_effect=mock_download):
                result = client.install_skill("test-skill", "1.0.0")

            assert result["success"] is False
            assert "validation failed" in result["error"].lower()
            assert skill.install_status == InstallStatus.ERROR

            # 验证回滚
            skill_dir = install_dir / "test-skill"
            assert not skill_dir.exists()

    def test_install_skill_zip_format(self):
        """测试安装 zip 格式的 skill 包。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill = self._make_skill()
            client.registry.get_skill = MagicMock(return_value=skill)

            content_files = {
                "__init__.py": "# zip skill",
                "core.py": "class Core: pass",
            }
            package_data = _create_zip_package(content_files, top_dir="test-skill-1.0.0")

            def mock_download(name, version):
                pkg_path = Path(temp_dir) / f"{name}-{version}.zip"
                pkg_path.write_bytes(package_data)
                return {"success": True, "file_path": str(pkg_path)}

            with patch.object(client, "_download_skill", side_effect=mock_download):
                result = client.install_skill("test-skill", "1.0.0")

            assert result["success"] is True
            skill_dir = install_dir / "test-skill"
            assert (skill_dir / "__init__.py").exists()
            assert (skill_dir / "core.py").exists()

    def test_install_skill_cleans_temp_package_after_success(self):
        """测试安装成功后清理临时包文件。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill = self._make_skill()
            client.registry.get_skill = MagicMock(return_value=skill)

            content_files = {"__init__.py": "# init"}
            package_data = _create_tar_gz_package(content_files, top_dir="test-skill-1.0.0")

            pkg_path = Path(temp_dir) / "test-skill-1.0.0.tar.gz"
            pkg_path.write_bytes(package_data)

            def mock_download(name, version):
                return {"success": True, "file_path": str(pkg_path)}

            with patch.object(client, "_download_skill", side_effect=mock_download):
                result = client.install_skill("test-skill", "1.0.0")

            assert result["success"] is True
            # 临时包文件应该被清理
            assert not pkg_path.exists()

    def test_install_skill_no_versions_available(self):
        """测试没有可用版本时安装失败。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            client = MarketplaceClient(install_dir=install_dir)

            skill = RemoteSkill(
                name="empty-skill",
                description="No versions",
                repository="https://github.com/test/empty-skill",
                versions=[],
                latest_version=None,
            )
            client.registry.get_skill = MagicMock(return_value=skill)

            result = client.install_skill("empty-skill")

            assert result["success"] is False
            assert "no versions" in result["error"].lower()
