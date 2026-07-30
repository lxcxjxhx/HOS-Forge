"""ConfigManager 单元测试。"""

import os
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import yaml

from hosforge.config import ConfigManager


@pytest.fixture
def config_dir(tmp_path):
    """创建临时配置目录和文件。"""
    config_path = tmp_path / "config"
    config_path.mkdir()

    base_config = {
        "marketplace": {
            "cache_dir": "~/.hos/cache",
            "install_dir": "~/.hos/skills",
            "github_api_timeout": 30,
        },
        "sandbox": {
            "max_execution_time": 30,
            "max_memory_mb": 512,
            "allowed_permissions": ["file_read", "network_access"],
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    }

    dev_config = {
        "logging": {"level": "DEBUG"},
        "marketplace": {"github_api_timeout": 60},
    }

    prod_config = {
        "logging": {"level": "WARNING"},
        "sandbox": {"max_execution_time": 60, "max_memory_mb": 1024},
    }

    for name, data in [("base.yaml", base_config), ("dev.yaml", dev_config), ("prod.yaml", prod_config)]:
        with open(config_path / name, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

    return str(config_path)


class TestConfigManagerBasicLoad:
    """测试基础配置加载。"""

    def test_load_base_config(self, config_dir):
        """测试加载基础配置文件。"""
        # 使用不存在的 env 来避免环境配置覆盖
        manager = ConfigManager(config_dir=config_dir, env="nonexistent")
        assert manager.get("marketplace.cache_dir") == "~/.hos/cache"
        assert manager.get("marketplace.install_dir") == "~/.hos/skills"
        assert manager.get("marketplace.github_api_timeout") == 30
        assert manager.get("sandbox.max_execution_time") == 30
        assert manager.get("sandbox.max_memory_mb") == 512
        assert manager.get("logging.level") == "INFO"

    def test_load_list_config(self, config_dir):
        """测试加载列表类型的配置。"""
        manager = ConfigManager(config_dir=config_dir, env="nonexistent")
        permissions = manager.get("sandbox.allowed_permissions")
        assert permissions == ["file_read", "network_access"]

    def test_missing_config_dir(self, tmp_path):
        """测试配置文件不存在时返回空配置。"""
        manager = ConfigManager(config_dir=str(tmp_path / "missing"), env="dev")
        assert manager.get("marketplace.cache_dir") is None
        assert manager.get_all() == {}


class TestEnvironmentConfigOverride:
    """测试环境配置覆盖。"""

    def test_dev_env_override(self, config_dir):
        """测试开发环境配置覆盖基础配置。"""
        manager = ConfigManager(config_dir=config_dir, env="dev")
        # dev 覆盖 logging.level
        assert manager.get("logging.level") == "DEBUG"
        # dev 覆盖 marketplace.github_api_timeout
        assert manager.get("marketplace.github_api_timeout") == 60
        # 基础配置保持不变
        assert manager.get("marketplace.cache_dir") == "~/.hos/cache"
        assert manager.get("sandbox.max_execution_time") == 30

    def test_prod_env_override(self, config_dir):
        """测试生产环境配置覆盖基础配置。"""
        manager = ConfigManager(config_dir=config_dir, env="prod")
        # prod 覆盖 logging.level
        assert manager.get("logging.level") == "WARNING"
        # prod 覆盖 sandbox 配置
        assert manager.get("sandbox.max_execution_time") == 60
        assert manager.get("sandbox.max_memory_mb") == 1024
        # 基础配置保持不变
        assert manager.get("marketplace.cache_dir") == "~/.hos/cache"
        assert manager.get("marketplace.github_api_timeout") == 30

    def test_default_env_is_dev(self, config_dir):
        """测试默认环境为 dev。"""
        with mock.patch.dict(os.environ, {}, clear=True):
            manager = ConfigManager(config_dir=config_dir)
            assert manager.env == "dev"
            assert manager.get("logging.level") == "DEBUG"

    def test_env_from_env_variable(self, config_dir):
        """测试从环境变量 HOS_ENV 读取环境。"""
        with mock.patch.dict(os.environ, {"HOS_ENV": "prod"}, clear=True):
            manager = ConfigManager(config_dir=config_dir)
            assert manager.env == "prod"
            assert manager.get("logging.level") == "WARNING"


class TestEnvironmentVariableOverride:
    """测试环境变量覆盖。"""

    def test_env_var_override(self, config_dir):
        """测试环境变量覆盖配置文件。"""
        env_vars = {"HOS_MARKETPLACE_CACHE_DIR": "/custom/cache"}
        with mock.patch.dict(os.environ, env_vars, clear=False):
            manager = ConfigManager(config_dir=config_dir, env="dev")
            assert manager.get("marketplace.cache_dir") == "/custom/cache"

    def test_env_var_override_nested(self, config_dir):
        """测试环境变量覆盖嵌套配置。"""
        env_vars = {"HOS_SANDBOX_MAX_EXECUTION_TIME": "120"}
        with mock.patch.dict(os.environ, env_vars, clear=False):
            manager = ConfigManager(config_dir=config_dir, env="dev")
            assert manager.get("sandbox.max_execution_time") == "120"

    def test_env_var_new_key(self, config_dir):
        """测试环境变量添加新配置项。"""
        env_vars = {"HOS_CUSTOM_NEW_KEY": "custom_value"}
        with mock.patch.dict(os.environ, env_vars, clear=False):
            manager = ConfigManager(config_dir=config_dir, env="dev")
            assert manager.get("custom.new_key") == "custom_value"

    def test_non_hos_env_var_ignored(self, config_dir):
        """测试非 HOS_ 前缀的环境变量被忽略。"""
        env_vars = {"OTHER_MARKETPLACE_CACHE_DIR": "/other/path"}
        with mock.patch.dict(os.environ, env_vars, clear=False):
            manager = ConfigManager(config_dir=config_dir, env="dev")
            assert manager.get("marketplace.cache_dir") == "~/.hos/cache"


class TestDotPathAccess:
    """测试点号路径访问。"""

    def test_single_key(self, config_dir):
        """测试单级键访问。"""
        manager = ConfigManager(config_dir=config_dir, env="nonexistent")
        # 单级键返回整个 section
        result = manager.get("marketplace")
        assert isinstance(result, dict)
        assert result["cache_dir"] == "~/.hos/cache"

    def test_nested_key(self, config_dir):
        """测试多级嵌套键访问。"""
        manager = ConfigManager(config_dir=config_dir, env="nonexistent")
        assert manager.get("marketplace.cache_dir") == "~/.hos/cache"
        assert manager.get("logging.format") == "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def test_missing_key_returns_default(self, config_dir):
        """测试不存在的键返回默认值。"""
        manager = ConfigManager(config_dir=config_dir, env="nonexistent")
        assert manager.get("nonexistent.key") is None
        assert manager.get("nonexistent.key", "default") == "default"
        assert manager.get("marketplace.nonexistent", 42) == 42

    def test_partial_path_not_dict(self, config_dir):
        """测试路径中间节点不是字典时返回默认值。"""
        manager = ConfigManager(config_dir=config_dir, env="nonexistent")
        # marketplace.cache_dir 是字符串，不能再访问子键
        assert manager.get("marketplace.cache_dir.subkey", "default") == "default"


class TestConfigMerge:
    """测试配置合并逻辑。"""

    def test_deep_merge(self, config_dir):
        """测试深度合并保留未覆盖的键。"""
        manager = ConfigManager(config_dir=config_dir, env="dev")
        # marketplace 中 cache_dir 和 install_dir 来自 base，github_api_timeout 来自 dev
        marketplace = manager.get("marketplace")
        assert marketplace["cache_dir"] == "~/.hos/cache"
        assert marketplace["install_dir"] == "~/.hos/skills"
        assert marketplace["github_api_timeout"] == 60

    def test_merge_does_not_mutate_base(self):
        """测试合并不会修改原始字典。"""
        manager = ConfigManager(config_dir="/tmp/nonexistent", env="nonexistent")
        base = {"a": {"b": 1, "c": 2}, "d": 3}
        override = {"a": {"b": 10}}
        result = manager._merge_configs(base, override)
        assert result["a"]["b"] == 10
        assert result["a"]["c"] == 2
        assert base["a"]["b"] == 1  # 原始不变

    def test_override_non_dict_with_dict(self):
        """测试非字典值被字典值覆盖。"""
        manager = ConfigManager(config_dir="/tmp/nonexistent", env="nonexistent")
        base = {"a": "string"}
        override = {"a": {"nested": "value"}}
        result = manager._merge_configs(base, override)
        assert result["a"] == {"nested": "value"}

    def test_override_dict_with_non_dict(self):
        """测试字典值被非字典值覆盖。"""
        manager = ConfigManager(config_dir="/tmp/nonexistent", env="nonexistent")
        base = {"a": {"nested": "value"}}
        override = {"a": "string"}
        result = manager._merge_configs(base, override)
        assert result["a"] == "string"


class TestSetAndGet:
    """测试运行时设置和获取。"""

    def test_set_and_get(self, config_dir):
        """测试运行时设置和获取配置。"""
        manager = ConfigManager(config_dir=config_dir, env="nonexistent")
        manager.set("custom.key", "value")
        assert manager.get("custom.key") == "value"

    def test_set_overwrites(self, config_dir):
        """测试设置覆盖已有值。"""
        manager = ConfigManager(config_dir=config_dir, env="nonexistent")
        manager.set("marketplace.cache_dir", "/new/path")
        assert manager.get("marketplace.cache_dir") == "/new/path"

    def test_set_creates_nested(self, config_dir):
        """测试设置创建嵌套路径。"""
        manager = ConfigManager(config_dir=config_dir, env="nonexistent")
        manager.set("new.section.deep.key", "deep_value")
        assert manager.get("new.section.deep.key") == "deep_value"

    def test_get_all(self, config_dir):
        """测试获取所有配置。"""
        manager = ConfigManager(config_dir=config_dir, env="dev")
        all_config = manager.get_all()
        assert isinstance(all_config, dict)
        assert "marketplace" in all_config
        assert "logging" in all_config
        # 确保返回的是副本
        all_config["new_key"] = "new_value"
        assert manager.get("new_key") is None


class TestProjectConfigFiles:
    """测试项目实际的配置文件。"""

    def test_project_base_config(self):
        """测试项目基础配置文件存在且可加载。"""
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config"
        if not config_path.exists():
            pytest.skip("config directory not found in project root")

        manager = ConfigManager(config_dir=str(config_path), env="nonexistent")
        assert manager.get("marketplace.cache_dir") == "~/.hos/cache"
        assert manager.get("sandbox.max_execution_time") == 30
        assert manager.get("logging.level") == "INFO"

    def test_project_dev_config(self):
        """测试项目开发环境配置。"""
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config"
        if not config_path.exists():
            pytest.skip("config directory not found in project root")

        manager = ConfigManager(config_dir=str(config_path), env="dev")
        assert manager.get("logging.level") == "DEBUG"
        assert manager.get("marketplace.github_api_timeout") == 60

    def test_project_prod_config(self):
        """测试项目生产环境配置。"""
        project_root = Path(__file__).parent.parent
        config_path = project_root / "config"
        if not config_path.exists():
            pytest.skip("config directory not found in project root")

        manager = ConfigManager(config_dir=str(config_path), env="prod")
        assert manager.get("logging.level") == "WARNING"
        assert manager.get("sandbox.max_execution_time") == 60
        assert manager.get("sandbox.max_memory_mb") == 1024
