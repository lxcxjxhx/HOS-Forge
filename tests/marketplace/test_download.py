"""Marketplace 下载功能测试。

测试 GitHub releases 下载功能，包括：
- GitHub URL 解析
- 下载成功场景
- 下载失败重试机制
- 网络错误处理
"""

import io
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

import pytest

from hosforge.skills.marketplace.client import MarketplaceClient
from hosforge.skills.marketplace.models import RemoteSkill, SkillVersion


def _make_mock_response(content: bytes = b"test content") -> MagicMock:
    """创建一个模拟的 HTTP 响应对象，支持 shutil.copyfileobj。"""
    # 使用 BytesIO 来模拟文件-like 对象，它正确实现了 read() 方法
    bio = io.BytesIO(content)
    mock_response = MagicMock()
    mock_response.__enter__ = MagicMock(return_value=bio)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestParseGithubUrl:
    """测试 GitHub URL 解析功能。"""

    def test_parse_standard_github_url(self):
        """测试标准 GitHub URL 解析。"""
        client = MarketplaceClient()
        url = "https://github.com/owner/repo"
        owner, repo = client._parse_github_url(url)
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_with_trailing_slash(self):
        """测试带末尾斜杠的 GitHub URL。"""
        client = MarketplaceClient()
        url = "https://github.com/owner/repo/"
        owner, repo = client._parse_github_url(url)
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_with_git_suffix(self):
        """测试带 .git 后缀的 GitHub URL。"""
        client = MarketplaceClient()
        url = "https://github.com/owner/repo.git"
        owner, repo = client._parse_github_url(url)
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_github_url_with_releases_path(self):
        """测试带 releases 路径的 GitHub URL。"""
        client = MarketplaceClient()
        url = "https://github.com/owner/repo/releases/tag/v1.0.0"
        owner, repo = client._parse_github_url(url)
        assert owner == "owner"
        assert repo == "repo"

    def test_parse_invalid_github_url_no_github(self):
        """测试无效 URL（不包含 github.com）。"""
        client = MarketplaceClient()
        url = "https://gitlab.com/owner/repo"
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            client._parse_github_url(url)

    def test_parse_invalid_github_url_too_short(self):
        """测试无效 URL（路径太短）。"""
        client = MarketplaceClient()
        url = "https://github.com/owner"
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            client._parse_github_url(url)


class TestGetReleaseAssetUrl:
    """测试 release asset URL 构造。"""

    def test_get_release_asset_url(self):
        """测试构造 release asset URL。"""
        client = MarketplaceClient()
        url = client._get_release_asset_url("owner", "repo", "v1.0.0")
        expected = "https://github.com/owner/repo/releases/download/v1.0.0/repo-v1.0.0"
        assert url == expected


class TestDownloadWithRetry:
    """测试带重试的下载功能。"""

    def test_download_success_first_attempt(self):
        """测试第一次尝试就成功下载。"""
        client = MarketplaceClient()

        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "test.tar.gz"

            with patch("urllib.request.urlopen", return_value=_make_mock_response()):
                result = client._download_with_retry(
                    "https://example.com/test.tar.gz", dest, max_retries=3, retry_delay=0.01
                )

            assert result is True
            assert dest.exists()

    def test_download_retry_on_http_error(self):
        """测试 HTTP 错误时的重试机制。"""
        client = MarketplaceClient()

        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "test.tar.gz"

            # 模拟前两次失败，第三次成功
            call_count = [0]

            def mock_urlopen(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] < 3:
                    raise HTTPError(
                        url="https://example.com/test.tar.gz",
                        code=500,
                        msg="Internal Server Error",
                        hdrs=MagicMock(),
                        fp=None,
                    )
                return _make_mock_response()

            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                result = client._download_with_retry(
                    "https://example.com/test.tar.gz", dest, max_retries=3, retry_delay=0.01
                )

            assert result is True
            assert call_count[0] == 3

    def test_download_fail_after_max_retries(self):
        """测试达到最大重试次数后失败。"""
        client = MarketplaceClient()

        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "test.tar.gz"

            # 模拟所有尝试都失败
            with patch("urllib.request.urlopen") as mock_urlopen:
                mock_urlopen.side_effect = HTTPError(
                    url="https://example.com/test.tar.gz",
                    code=500,
                    msg="Internal Server Error",
                    hdrs=MagicMock(),
                    fp=None,
                )

                result = client._download_with_retry(
                    "https://example.com/test.tar.gz", dest, max_retries=3, retry_delay=0.01
                )

            assert result is False
            assert not dest.exists()  # 应该清理临时文件

    def test_download_retry_on_network_error(self):
        """测试网络错误时的重试机制。"""
        client = MarketplaceClient()

        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "test.tar.gz"

            call_count = [0]

            def mock_urlopen(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] < 2:
                    raise URLError("Network unreachable")
                return _make_mock_response()

            with patch("urllib.request.urlopen", side_effect=mock_urlopen):
                result = client._download_with_retry(
                    "https://example.com/test.tar.gz", dest, max_retries=3, retry_delay=0.01
                )

            assert result is True
            assert call_count[0] == 2


class TestDownloadSkill:
    """测试 _download_skill 方法。"""

    def test_download_skill_not_found(self):
        """测试下载不存在的 skill。"""
        client = MarketplaceClient()
        result = client._download_skill("nonexistent-skill", "1.0.0")
        assert result["success"] is False
        assert "not found" in result["error"].lower() or "no repository" in result["error"].lower()

    def test_download_skill_no_repository(self):
        """测试下载没有 repository 的 skill。"""
        client = MarketplaceClient()

        # Mock registry 返回没有 repository 的 skill
        mock_skill = RemoteSkill(
            name="test-skill",
            description="Test skill",
            repository=None,
        )
        client.registry.get_skill = MagicMock(return_value=mock_skill)

        result = client._download_skill("test-skill", "1.0.0")
        assert result["success"] is False
        assert "no repository" in result["error"].lower()

    def test_download_skill_invalid_repository_url(self):
        """测试下载 repository URL 无效的 skill。"""
        client = MarketplaceClient()

        mock_skill = RemoteSkill(
            name="test-skill",
            description="Test skill",
            repository="https://gitlab.com/owner/repo",  # 不是 GitHub
        )
        client.registry.get_skill = MagicMock(return_value=mock_skill)

        result = client._download_skill("test-skill", "1.0.0")
        assert result["success"] is False
        assert "invalid" in result["error"].lower()

    def test_download_skill_success_tar_gz(self):
        """测试成功下载 tar.gz 格式的 skill。"""
        client = MarketplaceClient()

        mock_skill = RemoteSkill(
            name="test-skill",
            description="Test skill",
            repository="https://github.com/owner/repo",
        )
        client.registry.get_skill = MagicMock(return_value=mock_skill)

        with patch.object(client, "_download_with_retry") as mock_download:
            # 第一次调用（tar.gz）成功
            mock_download.return_value = True

            result = client._download_skill("test-skill", "1.0.0")

            assert result["success"] is True
            assert "downloaded" in result["message"].lower()
            assert "file_path" in result
            assert result["file_path"].endswith(".tar.gz")

    def test_download_skill_success_zip_fallback(self):
        """测试 tar.gz 失败后回退到 zip 格式。"""
        client = MarketplaceClient()

        mock_skill = RemoteSkill(
            name="test-skill",
            description="Test skill",
            repository="https://github.com/owner/repo",
        )
        client.registry.get_skill = MagicMock(return_value=mock_skill)

        call_count = [0]

        def mock_download_with_retry(url, dest, *args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # 第一次（tar.gz）失败
                return False
            else:
                # 第二次（zip）成功
                return True

        with patch.object(client, "_download_with_retry", side_effect=mock_download_with_retry):
            result = client._download_skill("test-skill", "1.0.0")

            assert result["success"] is True
            assert "file_path" in result
            assert result["file_path"].endswith(".zip")

    def test_download_skill_both_formats_fail(self):
        """测试 tar.gz 和 zip 都失败的情况。"""
        client = MarketplaceClient()

        mock_skill = RemoteSkill(
            name="test-skill",
            description="Test skill",
            repository="https://github.com/owner/repo",
        )
        client.registry.get_skill = MagicMock(return_value=mock_skill)

        with patch.object(client, "_download_with_retry", return_value=False):
            result = client._download_skill("test-skill", "1.0.0")

            assert result["success"] is False
            assert "failed to download" in result["error"].lower()


class TestIntegration:
    """集成测试，测试完整的下载流程。"""

    def test_full_download_workflow(self):
        """测试完整的下载工作流。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            install_dir = Path(temp_dir) / "install"
            cache_dir = Path(temp_dir) / "cache"

            client = MarketplaceClient(install_dir=install_dir, cache_dir=cache_dir)

            # 创建一个真实的 skill 对象
            skill = RemoteSkill(
                name="test-skill",
                description="Test skill for integration",
                repository="https://github.com/test/test-skill",
                versions=[SkillVersion(version="1.0.0")],
                latest_version=SkillVersion(version="1.0.0"),
            )

            # Mock registry
            client.registry.get_skill = MagicMock(return_value=skill)

            # Mock _download_with_retry to create a dummy file
            def mock_download(url, dest, *args, **kwargs):
                dest.write_bytes(b"dummy content")
                return True

            with patch.object(client, "_download_with_retry", side_effect=mock_download):
                result = client._download_skill("test-skill", "1.0.0")

                assert result["success"] is True
                assert "file_path" in result
                assert Path(result["file_path"]).exists()
