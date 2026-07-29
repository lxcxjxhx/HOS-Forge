"""远程 Skill 注册表，管理远程 skill 源和缓存。"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from hosforge.skills.marketplace.models import RemoteSkill, SkillVersion


class RemoteSkillRegistry:
    """远程 Skill 注册表。

    管理远程 skill 源，缓存远程 skill 列表，提供 skill 查询功能。

    Attributes:
        sources: 远程 skill 源列表
        cache_file: 缓存文件路径
        cache_ttl: 缓存有效期（秒）
        _skills: 缓存的 skill 字典
        _last_refresh: 上次刷新时间
    """

    def __init__(
        self,
        sources: Optional[List[str]] = None,
        cache_file: Optional[Path] = None,
        cache_ttl: int = 3600,
    ) -> None:
        """初始化 RemoteSkillRegistry。

        Args:
            sources: 远程 skill 源 URL 列表，如果为 None 则使用默认源
            cache_file: 缓存文件路径，如果为 None 则使用默认路径
            cache_ttl: 缓存有效期（秒），默认 3600 秒（1 小时）
        """
        self.sources = sources or ["https://marketplace.hos-forge.dev/api/skills"]
        self.cache_file = cache_file or Path.home() / ".hos" / "cache" / "remote_skills.json"
        self.cache_ttl = cache_ttl
        self._skills: Dict[str, RemoteSkill] = {}
        self._last_refresh: Optional[float] = None

        # 确保缓存目录存在
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)

        # 尝试从缓存加载
        self._load_from_cache()

    def list_skills(self, force_refresh: bool = False) -> List[RemoteSkill]:
        """列出所有远程 skills。

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            RemoteSkill 实例列表
        """
        # 检查是否需要刷新
        if force_refresh or self._needs_refresh():
            self._refresh_from_sources()

        return list(self._skills.values())

    def get_skill(self, skill_name: str) -> Optional[RemoteSkill]:
        """获取指定的远程 skill。

        Args:
            skill_name: skill 名称

        Returns:
            RemoteSkill 实例，如果不存在则返回 None
        """
        # 确保已加载
        if not self._skills:
            self.list_skills()

        return self._skills.get(skill_name)

    def search_skills(self, query: str) -> List[RemoteSkill]:
        """搜索 skills。

        Args:
            query: 搜索查询字符串

        Returns:
            匹配的 RemoteSkill 实例列表
        """
        all_skills = self.list_skills()
        return [skill for skill in all_skills if skill.matches_query(query)]

    def add_source(self, source_url: str) -> None:
        """添加远程 skill 源。

        Args:
            source_url: 源 URL
        """
        if source_url not in self.sources:
            self.sources.append(source_url)

    def remove_source(self, source_url: str) -> bool:
        """移除远程 skill 源。

        Args:
            source_url: 源 URL

        Returns:
            是否成功移除
        """
        if source_url in self.sources:
            self.sources.remove(source_url)
            return True
        return False

    def clear_cache(self) -> None:
        """清除缓存。"""
        if self.cache_file.exists():
            self.cache_file.unlink()
        self._skills = {}
        self._last_refresh = None

    def _needs_refresh(self) -> bool:
        """检查是否需要刷新缓存。

        Returns:
            是否需要刷新
        """
        if self._last_refresh is None:
            return True

        elapsed = time.time() - self._last_refresh
        return elapsed > self.cache_ttl

    def _refresh_from_sources(self) -> None:
        """从远程源刷新 skill 列表。

        这是一个模拟实现，实际使用时需要从真实的远程 API 获取数据。
        """
        # 模拟从远程源获取数据
        # 实际实现中，这里应该调用 HTTP API 获取 skill 列表
        mock_skills = self._get_mock_skills()

        # 更新缓存
        self._skills = {skill.name: skill for skill in mock_skills}
        self._last_refresh = time.time()

        # 保存到缓存文件
        self._save_to_cache()

    def _load_from_cache(self) -> None:
        """从缓存文件加载 skill 列表。"""
        if not self.cache_file.exists():
            return

        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            skills_data = data.get("skills", [])
            self._skills = {skill_data["name"]: RemoteSkill.from_dict(skill_data) for skill_data in skills_data}
            self._last_refresh = data.get("timestamp")

        except Exception:
            # 缓存损坏，忽略
            self._skills = {}
            self._last_refresh = None

    def _save_to_cache(self) -> None:
        """保存 skill 列表到缓存文件。"""
        try:
            data = {
                "timestamp": self._last_refresh,
                "skills": [skill.to_dict() for skill in self._skills.values()],
            }

            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception:
            # 保存失败，忽略
            pass

    def _get_mock_skills(self) -> List[RemoteSkill]:
        """获取模拟的 skill 列表（用于演示和测试）。

        Returns:
            RemoteSkill 实例列表
        """
        return [
            RemoteSkill(
                name="code-review",
                description="Automated code review skill for Python projects",
                author="HOS Team",
                versions=[
                    SkillVersion(version="1.2.0", release_date="2024-01-15"),
                    SkillVersion(version="1.1.0", release_date="2023-12-01"),
                    SkillVersion(version="1.0.0", release_date="2023-10-15"),
                ],
                latest_version=SkillVersion(version="1.2.0", release_date="2024-01-15"),
                tags=["code-quality", "python", "review"],
                repository="https://github.com/hos-forge/code-review-skill",
                download_count=1520,
                rating=4.7,
            ),
            RemoteSkill(
                name="security-scanner",
                description="Comprehensive security scanning for multiple languages",
                author="Security Team",
                versions=[
                    SkillVersion(version="2.0.0", release_date="2024-01-20"),
                    SkillVersion(version="1.5.0", release_date="2023-11-10"),
                ],
                latest_version=SkillVersion(version="2.0.0", release_date="2024-01-20"),
                tags=["security", "scanning", "vulnerability"],
                repository="https://github.com/hos-forge/security-scanner",
                download_count=3200,
                rating=4.9,
            ),
            RemoteSkill(
                name="test-generator",
                description="AI-powered test case generation for Python projects",
                author="QA Team",
                versions=[
                    SkillVersion(version="0.9.0", release_date="2024-01-10"),
                ],
                latest_version=SkillVersion(version="0.9.0", release_date="2024-01-10"),
                tags=["testing", "ai", "automation"],
                repository="https://github.com/hos-forge/test-generator",
                download_count=890,
                rating=4.5,
            ),
            RemoteSkill(
                name="doc-generator",
                description="Automatic documentation generation from code",
                author="Docs Team",
                versions=[
                    SkillVersion(version="1.0.0", release_date="2023-12-20"),
                ],
                latest_version=SkillVersion(version="1.0.0", release_date="2023-12-20"),
                tags=["documentation", "automation"],
                repository="https://github.com/hos-forge/doc-generator",
                download_count=650,
                rating=4.3,
            ),
            RemoteSkill(
                name="performance-profiler",
                description="Performance profiling and optimization suggestions",
                author="Performance Team",
                versions=[
                    SkillVersion(version="1.1.0", release_date="2024-01-18"),
                    SkillVersion(version="1.0.0", release_date="2023-11-25"),
                ],
                latest_version=SkillVersion(version="1.1.0", release_date="2024-01-18"),
                tags=["performance", "profiling", "optimization"],
                repository="https://github.com/hos-forge/performance-profiler",
                download_count=1100,
                rating=4.6,
            ),
        ]
