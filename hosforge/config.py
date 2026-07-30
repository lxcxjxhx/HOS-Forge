"""配置管理系统，支持多环境配置加载和环境变量覆盖。"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """配置管理器，支持多环境配置和环境变量覆盖。"""

    def __init__(self, config_dir: Optional[str] = None, env: Optional[str] = None):
        """初始化配置管理器。

        Args:
            config_dir: 配置目录路径，默认为项目根目录下的 config/
            env: 环境名称（dev/staging/prod），默认从环境变量 HOS_ENV 读取，否则为 dev
        """
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config"
        self.env = env or os.getenv("HOS_ENV", "dev")
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self):
        """加载配置文件和环境变量。"""
        # 1. 加载基础配置 config/base.yaml
        base_config = self._load_yaml_file(self.config_dir / "base.yaml")

        # 2. 加载环境配置 config/{env}.yaml
        env_config = self._load_yaml_file(self.config_dir / f"{self.env}.yaml")

        # 3. 合并配置（环境配置覆盖基础配置）
        self._config = self._merge_configs(base_config, env_config)

        # 4. 应用环境变量覆盖
        self._apply_env_overrides()

    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """加载 YAML 配置文件。

        Args:
            path: YAML 文件路径

        Returns:
            配置字典，如果文件不存在则返回空字典
        """
        if not path.exists():
            return {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except (yaml.YAMLError, OSError):
            return {}

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并两个配置字典。

        Args:
            base: 基础配置
            override: 覆盖配置

        Returns:
            合并后的配置
        """
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self):
        """应用环境变量覆盖。

        环境变量格式：HOS_{SECTION}_{KEY}（大写，下划线分隔）
        例如：HOS_MARKETPLACE_CACHE_DIR=/custom/path 覆盖 marketplace.cache_dir
        """
        prefix = "HOS_"
        for env_key, env_value in os.environ.items():
            if not env_key.startswith(prefix):
                continue

            # 移除前缀并转换为小写
            config_path = env_key[len(prefix):].lower()

            # 将下划线转换为点号路径（除了第一个下划线，它分隔 section 和 key）
            parts = config_path.split("_", 1)
            if len(parts) == 2:
                section, key = parts
                full_key = f"{section}.{key}"
            else:
                full_key = config_path

            # 设置配置值
            self.set(full_key, env_value)

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项，支持点号路径。

        Args:
            key: 配置键，支持点号路径如 "marketplace.cache_dir"
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置项（运行时）。

        Args:
            key: 配置键，支持点号路径
            value: 配置值
        """
        keys = key.split(".")
        config = self._config

        # 导航到倒数第二层
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]

        # 设置最后一层的值
        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置。

        Returns:
            完整的配置字典
        """
        return self._config.copy()
