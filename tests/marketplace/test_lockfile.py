"""版本锁定机制测试。"""

import json
import tempfile
from pathlib import Path

from hosforge.skills.marketplace.lockfile import (
    LockEntry,
    LockfileManager,
    SkillLockfile,
)


class TestLockEntry:
    """测试 LockEntry 数据类。"""

    def test_lock_entry_creation(self):
        """测试创建锁定条目。"""
        entry = LockEntry(
            name="test-skill",
            version="1.0.0",
            locked_at="2024-01-01T00:00:00",
            source="marketplace",
        )
        assert entry.name == "test-skill"
        assert entry.version == "1.0.0"
        assert entry.locked_at == "2024-01-01T00:00:00"
        assert entry.source == "marketplace"

    def test_lock_entry_to_dict(self):
        """测试转换为字典。"""
        entry = LockEntry(
            name="test-skill",
            version="1.0.0",
            locked_at="2024-01-01T00:00:00",
            source="marketplace",
        )
        data = entry.to_dict()
        assert data["name"] == "test-skill"
        assert data["version"] == "1.0.0"
        assert data["locked_at"] == "2024-01-01T00:00:00"
        assert data["source"] == "marketplace"

    def test_lock_entry_from_dict(self):
        """测试从字典创建。"""
        data = {
            "name": "test-skill",
            "version": "1.0.0",
            "locked_at": "2024-01-01T00:00:00",
            "source": "marketplace",
        }
        entry = LockEntry.from_dict(data)
        assert entry.name == "test-skill"
        assert entry.version == "1.0.0"
        assert entry.locked_at == "2024-01-01T00:00:00"
        assert entry.source == "marketplace"


class TestSkillLockfile:
    """测试 SkillLockfile 数据类。"""

    def test_lockfile_is_locked(self):
        """测试检查是否锁定。"""
        lockfile = SkillLockfile()
        lockfile.lock("test-skill", "1.0.0")
        assert lockfile.is_locked("test-skill") is True
        assert lockfile.is_locked("other-skill") is False

    def test_lockfile_get_locked_version(self):
        """测试获取锁定版本。"""
        lockfile = SkillLockfile()
        lockfile.lock("test-skill", "1.0.0")
        assert lockfile.get_locked_version("test-skill") == "1.0.0"
        assert lockfile.get_locked_version("other-skill") is None

    def test_lockfile_lock(self):
        """测试锁定 skill。"""
        lockfile = SkillLockfile()
        lockfile.lock("test-skill", "1.0.0", "marketplace")
        assert lockfile.is_locked("test-skill")
        assert lockfile.get_locked_version("test-skill") == "1.0.0"

    def test_lockfile_unlock(self):
        """测试解锁 skill。"""
        lockfile = SkillLockfile()
        lockfile.lock("test-skill", "1.0.0")
        assert lockfile.is_locked("test-skill") is True
        
        result = lockfile.unlock("test-skill")
        assert result is True
        assert lockfile.is_locked("test-skill") is False

    def test_lockfile_unlock_nonexistent(self):
        """测试解锁不存在的 skill。"""
        lockfile = SkillLockfile()
        result = lockfile.unlock("nonexistent-skill")
        assert result is False

    def test_lockfile_to_dict(self):
        """测试转换为字典。"""
        lockfile = SkillLockfile()
        lockfile.lock("test-skill", "1.0.0", "marketplace")
        data = lockfile.to_dict()
        
        assert data["version"] == 1
        assert "locked" in data
        assert "test-skill" in data["locked"]
        assert data["locked"]["test-skill"]["version"] == "1.0.0"

    def test_lockfile_from_dict(self):
        """测试从字典创建。"""
        data = {
            "version": 1,
            "locked": {
                "test-skill": {
                    "name": "test-skill",
                    "version": "1.0.0",
                    "locked_at": "2024-01-01T00:00:00",
                    "source": "marketplace",
                }
            },
        }
        lockfile = SkillLockfile.from_dict(data)
        assert lockfile.is_locked("test-skill")
        assert lockfile.get_locked_version("test-skill") == "1.0.0"


class TestLockfileManager:
    """测试 LockfileManager。"""

    def test_manager_load_empty(self):
        """测试加载不存在的 lockfile。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile_path = Path(temp_dir) / "skill-lock.json"
            manager = LockfileManager(lockfile_path)
            
            lockfile = manager.load()
            assert isinstance(lockfile, SkillLockfile)
            assert len(lockfile.entries) == 0

    def test_manager_save_and_load(self):
        """测试保存和加载 lockfile。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile_path = Path(temp_dir) / "skill-lock.json"
            manager = LockfileManager(lockfile_path)
            
            # 保存
            lockfile = SkillLockfile()
            lockfile.lock("test-skill", "1.0.0")
            manager.save(lockfile)
            
            # 加载
            loaded = manager.load()
            assert loaded.is_locked("test-skill")
            assert loaded.get_locked_version("test-skill") == "1.0.0"

    def test_manager_lock_skill(self):
        """测试锁定 skill。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile_path = Path(temp_dir) / "skill-lock.json"
            manager = LockfileManager(lockfile_path)
            
            manager.lock_skill("test-skill", "1.0.0")
            
            assert manager.is_locked("test-skill")
            assert manager.get_locked_version("test-skill") == "1.0.0"
            
            # 验证文件已写入
            assert lockfile_path.exists()

    def test_manager_unlock_skill(self):
        """测试解锁 skill。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile_path = Path(temp_dir) / "skill-lock.json"
            manager = LockfileManager(lockfile_path)
            
            manager.lock_skill("test-skill", "1.0.0")
            assert manager.is_locked("test-skill") is True
            
            result = manager.unlock_skill("test-skill")
            assert result is True
            assert manager.is_locked("test-skill") is False

    def test_manager_unlock_nonexistent(self):
        """测试解锁不存在的 skill。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile_path = Path(temp_dir) / "skill-lock.json"
            manager = LockfileManager(lockfile_path)
            
            result = manager.unlock_skill("nonexistent-skill")
            assert result is False

    def test_manager_list_locked(self):
        """测试列出所有锁定的 skill。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile_path = Path(temp_dir) / "skill-lock.json"
            manager = LockfileManager(lockfile_path)
            
            manager.lock_skill("skill-1", "1.0.0")
            manager.lock_skill("skill-2", "2.0.0")
            
            locked = manager.list_locked()
            assert len(locked) == 2
            names = {entry.name for entry in locked}
            assert names == {"skill-1", "skill-2"}

    def test_manager_load_corrupted_file(self):
        """测试加载损坏的 lockfile。"""
        with tempfile.TemporaryDirectory() as temp_dir:
            lockfile_path = Path(temp_dir) / "skill-lock.json"
            lockfile_path.write_text("{invalid json")
            
            manager = LockfileManager(lockfile_path)
            lockfile = manager.load()
            
            # 应该返回空的 lockfile
            assert isinstance(lockfile, SkillLockfile)
            assert len(lockfile.entries) == 0
