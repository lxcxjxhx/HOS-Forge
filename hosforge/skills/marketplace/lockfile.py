"""Skill 版本锁定管理，提供 lockfile 的读写和锁定/解锁操作。"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class LockEntry:
    """单个 skill 的锁定条目。

    Attributes:
        name: skill 名称
        version: 锁定的版本号
        locked_at: 锁定时间戳
        source: skill 来源
    """

    name: str
    version: str
    locked_at: str = ""
    source: str = "marketplace"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "locked_at": self.locked_at,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LockEntry":
        return cls(
            name=data["name"],
            version=data["version"],
            locked_at=data.get("locked_at", ""),
            source=data.get("source", "marketplace"),
        )


@dataclass
class SkillLockfile:
    """Skill 版本锁定文件。

    格式: ~/.hos/skill-lock.json
    """

    version: int = 1
    entries: Dict[str, LockEntry] = field(default_factory=dict)

    def is_locked(self, skill_name: str) -> bool:
        """检查 skill 是否被锁定。"""
        return skill_name in self.entries

    def get_locked_version(self, skill_name: str) -> Optional[str]:
        """获取 skill 的锁定版本。"""
        entry = self.entries.get(skill_name)
        return entry.version if entry else None

    def lock(self, name: str, version: str, source: str = "marketplace") -> None:
        """锁定 skill 到指定版本。"""
        from datetime import datetime

        self.entries[name] = LockEntry(
            name=name,
            version=version,
            locked_at=datetime.now().isoformat(),
            source=source,
        )

    def unlock(self, name: str) -> bool:
        """解锁 skill。返回是否成功解锁。"""
        if name in self.entries:
            del self.entries[name]
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "locked": {name: entry.to_dict() for name, entry in self.entries.items()},
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillLockfile":
        lockfile = cls(version=data.get("version", 1))
        for name, entry_data in data.get("locked", {}).items():
            lockfile.entries[name] = LockEntry.from_dict(entry_data)
        return lockfile


class LockfileManager:
    """Lockfile 管理器，处理 lockfile 的持久化操作。"""

    def __init__(self, lockfile_path: Optional[Path] = None) -> None:
        self.lockfile_path = lockfile_path or Path.home() / ".hos" / "skill-lock.json"
        self._lockfile: Optional[SkillLockfile] = None

    def load(self) -> SkillLockfile:
        """加载 lockfile，如果不存在则返回空的 lockfile。"""
        if not self.lockfile_path.exists():
            self._lockfile = SkillLockfile()
            return self._lockfile

        try:
            with open(self.lockfile_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._lockfile = SkillLockfile.from_dict(data)
        except (json.JSONDecodeError, OSError, KeyError) as e:
            logger.warning(f"Failed to load lockfile: {e}, using empty lockfile")
            self._lockfile = SkillLockfile()

        return self._lockfile

    def save(self, lockfile: Optional[SkillLockfile] = None) -> None:
        """保存 lockfile 到磁盘。"""
        lf = lockfile or self._lockfile or SkillLockfile()
        self.lockfile_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.lockfile_path, "w", encoding="utf-8") as f:
            json.dump(lf.to_dict(), f, indent=2, ensure_ascii=False)

    def lock_skill(self, name: str, version: str, source: str = "marketplace") -> None:
        """锁定 skill 并持久化。"""
        lockfile = self.load()
        lockfile.lock(name, version, source)
        self.save(lockfile)

    def unlock_skill(self, name: str) -> bool:
        """解锁 skill 并持久化。返回是否成功。"""
        lockfile = self.load()
        result = lockfile.unlock(name)
        if result:
            self.save(lockfile)
        return result

    def is_locked(self, name: str) -> bool:
        """检查 skill 是否被锁定。"""
        lockfile = self.load()
        return lockfile.is_locked(name)

    def get_locked_version(self, name: str) -> Optional[str]:
        """获取锁定版本。"""
        lockfile = self.load()
        return lockfile.get_locked_version(name)

    def list_locked(self) -> List[LockEntry]:
        """列出所有锁定的 skill。"""
        lockfile = self.load()
        return list(lockfile.entries.values())
