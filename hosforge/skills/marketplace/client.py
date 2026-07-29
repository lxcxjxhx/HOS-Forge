"""Skill 市场客户端，提供远程 skill 的列表、安装、卸载、更新和搜索功能。"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from hosforge.skills.marketplace.models import (
    InstallStatus,
    RemoteSkill,
)
from hosforge.skills.marketplace.registry import RemoteSkillRegistry


class MarketplaceClient:
    """Skill 市场客户端。

    提供与远程 skill 市场交互的功能，包括列出、安装、卸载、更新和搜索 skills。

    Attributes:
        registry: 远程 skill 注册表
        install_dir: skill 安装目录
        cache_dir: 缓存目录
    """

    def __init__(
        self,
        registry: Optional[RemoteSkillRegistry] = None,
        install_dir: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
    ) -> None:
        """初始化 MarketplaceClient。

        Args:
            registry: 远程 skill 注册表，如果为 None 则使用默认注册表
            install_dir: skill 安装目录，如果为 None 则使用默认目录
            cache_dir: 缓存目录，如果为 None 则使用默认目录
        """
        self.registry = registry or RemoteSkillRegistry()
        self.install_dir = install_dir or Path.home() / ".hos" / "skills"
        self.cache_dir = cache_dir or Path.home() / ".hos" / "cache"

        # 确保目录存在
        self.install_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def list_remote_skills(self, force_refresh: bool = False) -> List[RemoteSkill]:
        """列出所有可用的远程 skills。

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            RemoteSkill 实例列表
        """
        return self.registry.list_skills(force_refresh=force_refresh)

    def install_skill(self, skill_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """安装指定的 skill。

        Args:
            skill_name: skill 名称
            version: 指定版本，如果为 None 则安装最新版本

        Returns:
            包含安装结果的字典
        """
        # 查找 skill
        skill = self.registry.get_skill(skill_name)
        if skill is None:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found in marketplace",
            }

        # 确定要安装的版本
        target_version = version
        if target_version is None:
            if skill.latest_version:
                target_version = skill.latest_version.version
            elif skill.versions:
                target_version = skill.versions[0].version
            else:
                return {
                    "success": False,
                    "error": f"No versions available for skill '{skill_name}'",
                }

        # 检查是否已安装
        skill_install_dir = self.install_dir / skill_name
        if skill_install_dir.exists():
            return {
                "success": False,
                "error": f"Skill '{skill_name}' is already installed. Use update to upgrade.",
            }

        try:
            # 更新状态为安装中
            skill.install_status = InstallStatus.INSTALLING

            # 下载 skill（模拟下载过程）
            download_result = self._download_skill(skill_name, target_version)

            if not download_result["success"]:
                skill.install_status = InstallStatus.ERROR
                return download_result

            # 创建安装目录
            skill_install_dir.mkdir(parents=True, exist_ok=True)

            # 保存 skill 元数据
            metadata = {
                "name": skill_name,
                "version": target_version,
                "source": skill.repository or "marketplace",
            }
            metadata_file = skill_install_dir / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 更新状态
            skill.install_status = InstallStatus.INSTALLED
            skill.installed_version = target_version

            return {
                "success": True,
                "message": f"Successfully installed {skill_name} v{target_version}",
                "skill_name": skill_name,
                "version": target_version,
            }

        except Exception as e:
            skill.install_status = InstallStatus.ERROR
            return {
                "success": False,
                "error": f"Failed to install {skill_name}: {str(e)}",
            }

    def uninstall_skill(self, skill_name: str) -> Dict[str, Any]:
        """卸载指定的 skill。

        Args:
            skill_name: skill 名称

        Returns:
            包含卸载结果的字典
        """
        skill_install_dir = self.install_dir / skill_name

        if not skill_install_dir.exists():
            return {
                "success": False,
                "error": f"Skill '{skill_name}' is not installed",
            }

        try:
            # 更新状态
            skill = self.registry.get_skill(skill_name)
            if skill:
                skill.install_status = InstallStatus.UNINSTALLING

            # 删除安装目录
            shutil.rmtree(skill_install_dir)

            # 更新状态
            if skill:
                skill.install_status = InstallStatus.NOT_INSTALLED
                skill.installed_version = None

            return {
                "success": True,
                "message": f"Successfully uninstalled {skill_name}",
                "skill_name": skill_name,
            }

        except Exception as e:
            if skill:
                skill.install_status = InstallStatus.ERROR
            return {
                "success": False,
                "error": f"Failed to uninstall {skill_name}: {str(e)}",
            }

    def update_skill(self, skill_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """更新指定的 skill。

        Args:
            skill_name: skill 名称
            version: 目标版本，如果为 None 则更新到最新版本

        Returns:
            包含更新结果的字典
        """
        skill_install_dir = self.install_dir / skill_name

        if not skill_install_dir.exists():
            return {
                "success": False,
                "error": f"Skill '{skill_name}' is not installed. Use install first.",
            }

        # 查找 skill
        skill = self.registry.get_skill(skill_name)
        if skill is None:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found in marketplace",
            }

        # 确定目标版本
        target_version = version
        if target_version is None:
            if skill.latest_version:
                target_version = skill.latest_version.version
            elif skill.versions:
                target_version = skill.versions[0].version
            else:
                return {
                    "success": False,
                    "error": f"No versions available for skill '{skill_name}'",
                }

        # 检查当前版本
        current_version = self._get_installed_version(skill_name)
        if current_version == target_version:
            return {
                "success": True,
                "message": f"Skill '{skill_name}' is already at version {target_version}",
                "skill_name": skill_name,
                "version": target_version,
            }

        try:
            # 更新状态
            skill.install_status = InstallStatus.INSTALLING

            # 下载新版本
            download_result = self._download_skill(skill_name, target_version)

            if not download_result["success"]:
                skill.install_status = InstallStatus.ERROR
                return download_result

            # 更新元数据
            metadata = {
                "name": skill_name,
                "version": target_version,
                "source": skill.repository or "marketplace",
            }
            metadata_file = skill_install_dir / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 更新状态
            skill.install_status = InstallStatus.INSTALLED
            skill.installed_version = target_version

            return {
                "success": True,
                "message": f"Successfully updated {skill_name} from v{current_version} to v{target_version}",
                "skill_name": skill_name,
                "old_version": current_version,
                "new_version": target_version,
            }

        except Exception as e:
            skill.install_status = InstallStatus.ERROR
            return {
                "success": False,
                "error": f"Failed to update {skill_name}: {str(e)}",
            }

    def search_skills(self, query: str) -> List[RemoteSkill]:
        """搜索 skills。

        Args:
            query: 搜索查询字符串

        Returns:
            匹配的 RemoteSkill 实例列表
        """
        all_skills = self.list_remote_skills()
        return [skill for skill in all_skills if skill.matches_query(query)]

    def _download_skill(self, skill_name: str, version: str) -> Dict[str, Any]:
        """下载 skill（内部方法）。

        这是一个模拟实现，实际使用时需要连接到真实的 skill 仓库。

        Args:
            skill_name: skill 名称
            version: 版本号

        Returns:
            包含下载结果的字典
        """
        # 模拟下载过程
        # 实际实现中，这里应该从远程仓库下载 skill 文件
        return {
            "success": True,
            "message": f"Downloaded {skill_name} v{version}",
        }

    def _get_installed_version(self, skill_name: str) -> Optional[str]:
        """获取已安装 skill 的版本。

        Args:
            skill_name: skill 名称

        Returns:
            版本号字符串，如果未安装则返回 None
        """
        metadata_file = self.install_dir / skill_name / "metadata.json"

        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            return metadata.get("version")
        except Exception:
            return None

    def get_installed_skills(self) -> List[Dict[str, Any]]:
        """获取所有已安装的 skills。

        Returns:
            已安装 skill 的信息列表
        """
        installed = []

        if not self.install_dir.exists():
            return installed

        for skill_dir in self.install_dir.iterdir():
            if skill_dir.is_dir():
                metadata_file = skill_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        installed.append(metadata)
                    except Exception:
                        pass

        return installed
