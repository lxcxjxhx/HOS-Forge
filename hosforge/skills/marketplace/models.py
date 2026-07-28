"""Skill 市场数据模型，定义远程 Skill、版本和安装状态。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class InstallStatus(Enum):
    """Skill 安装状态枚举。"""
    
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    UPDATE_AVAILABLE = "update_available"
    INSTALLING = "installing"
    UNINSTALLING = "uninstalling"
    ERROR = "error"


@dataclass
class SkillVersion:
    """Skill 版本信息。
    
    Attributes:
        version: 版本号字符串（如 "1.0.0"）
        release_date: 发布日期
        changelog: 变更日志
        min_hos_version: 最低 HOS-Forge 版本要求
    """
    
    version: str
    release_date: Optional[str] = None
    changelog: Optional[str] = None
    min_hos_version: Optional[str] = None
    
    def __str__(self) -> str:
        """返回版本号的字符串表示。"""
        return self.version
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "version": self.version,
            "release_date": self.release_date,
            "changelog": self.changelog,
            "min_hos_version": self.min_hos_version,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillVersion":
        """从字典创建实例。"""
        return cls(
            version=data.get("version", "0.0.0"),
            release_date=data.get("release_date"),
            changelog=data.get("changelog"),
            min_hos_version=data.get("min_hos_version"),
        )


@dataclass
class RemoteSkill:
    """远程 Skill 信息。
    
    Attributes:
        name: Skill 名称
        description: Skill 描述
        author: 作者
        versions: 可用版本列表
        latest_version: 最新版本
        tags: 标签列表
        repository: 仓库地址
        install_status: 安装状态
        installed_version: 已安装版本
        download_count: 下载次数
        rating: 评分
    """
    
    name: str
    description: str
    author: str = ""
    versions: List[SkillVersion] = field(default_factory=list)
    latest_version: Optional[SkillVersion] = None
    tags: List[str] = field(default_factory=list)
    repository: Optional[str] = None
    install_status: InstallStatus = InstallStatus.NOT_INSTALLED
    installed_version: Optional[str] = None
    download_count: int = 0
    rating: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式。"""
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "versions": [v.to_dict() for v in self.versions],
            "latest_version": self.latest_version.to_dict() if self.latest_version else None,
            "tags": self.tags,
            "repository": self.repository,
            "install_status": self.install_status.value,
            "installed_version": self.installed_version,
            "download_count": self.download_count,
            "rating": self.rating,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RemoteSkill":
        """从字典创建实例。"""
        versions_data = data.get("versions", [])
        versions = [SkillVersion.from_dict(v) for v in versions_data]
        
        latest_version = None
        if data.get("latest_version"):
            latest_version = SkillVersion.from_dict(data["latest_version"])
        elif versions:
            latest_version = versions[0]
        
        install_status = InstallStatus.NOT_INSTALLED
        if data.get("install_status"):
            try:
                install_status = InstallStatus(data["install_status"])
            except ValueError:
                pass
        
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            author=data.get("author", ""),
            versions=versions,
            latest_version=latest_version,
            tags=data.get("tags", []),
            repository=data.get("repository"),
            install_status=install_status,
            installed_version=data.get("installed_version"),
            download_count=data.get("download_count", 0),
            rating=data.get("rating"),
        )
    
    def has_update(self) -> bool:
        """检查是否有可用更新。"""
        if self.install_status != InstallStatus.INSTALLED:
            return False
        if not self.installed_version or not self.latest_version:
            return False
        return self.installed_version != self.latest_version.version
    
    def matches_query(self, query: str) -> bool:
        """检查 Skill 是否匹配搜索查询。"""
        query_lower = query.lower()
        return (
            query_lower in self.name.lower()
            or query_lower in self.description.lower()
            or query_lower in self.author.lower()
            or any(query_lower in tag.lower() for tag in self.tags)
        )
