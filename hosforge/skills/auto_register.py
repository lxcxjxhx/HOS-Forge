"""Skill 自动注册模块，支持自动发现和注册 skills。"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from hosforge.skills.loader import SkillLoader
from hosforge.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)


class AutoSkillRegistrar:
    """自动 Skill 注册器，负责自动发现和注册 skills。"""

    def __init__(self, registry: Optional[SkillRegistry] = None) -> None:
        """初始化自动注册器。

        Args:
            registry: Skill 注册表实例，如果为 None 则创建新的
        """
        self.registry = registry or SkillRegistry()
        self.loader = SkillLoader()

    def auto_discover_and_register(
        self,
        paths: List[str],
        registry: Optional[SkillRegistry] = None,
    ) -> int:
        """自动发现并注册 skills。

        Args:
            paths: 要扫描的路径列表（目录或模块路径）
            registry: 可选的注册表实例，如果为 None 则使用实例的 registry

        Returns:
            成功注册的 skill 数量
        """
        target_registry = registry or self.registry
        skills = self.loader.discover_skills(paths)

        registered_count = 0
        for skill in skills:
            try:
                target_registry.register(skill)
                registered_count += 1
                logger.info(f"已注册 skill: {skill.name}")
            except Exception as e:
                logger.error(f"注册 skill {skill.name} 时出错: {e}")

        logger.info(f"共注册 {registered_count} 个 skills")
        return registered_count

    def load_from_config(self, config_path: str) -> int:
        """从配置文件加载并注册 skills。

        配置文件格式示例：
        ```yaml
        skill_paths:
          - ./skills
          - hosforge.skills.security
        enabled_skills:
          - github_integration
          - semgrep_scan
        skill_defaults:
          timeout: 60
          retry_count: 3
        ```

        Args:
            config_path: 配置文件路径（YAML 格式）

        Returns:
            成功注册的 skill 数量
        """
        config = self._load_config(config_path)
        if config is None:
            return 0

        skill_paths = config.get("skill_paths", [])
        enabled_skills = config.get("enabled_skills", [])

        # 发现并加载所有 skills
        all_skills = self.loader.discover_skills(skill_paths)

        # 过滤出启用的 skills
        registered_count = 0
        for skill in all_skills:
            if enabled_skills and skill.name not in enabled_skills:
                logger.debug(f"跳过未启用的 skill: {skill.name}")
                continue

            try:
                self.registry.register(skill)
                registered_count += 1
                logger.info(f"已注册 skill: {skill.name}")
            except Exception as e:
                logger.error(f"注册 skill {skill.name} 时出错: {e}")

        logger.info(f"从配置 {config_path} 注册了 {registered_count} 个 skills")
        return registered_count

    def _load_config(self, config_path: str) -> Optional[Dict[str, Any]]:
        """加载 YAML 配置文件。

        Args:
            config_path: 配置文件路径

        Returns:
            配置字典，如果加载失败返回 None
        """
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"配置文件不存在: {config_path}")
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            logger.info(f"已加载配置文件: {config_path}")
            return config or {}
        except Exception as e:
            logger.error(f"加载配置文件 {config_path} 时出错: {e}")
            return None
