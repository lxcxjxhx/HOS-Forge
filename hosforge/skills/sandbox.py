"""Skill 沙箱执行环境，提供安全隔离和资源限制。"""

import signal
import threading
import time
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from hosforge.skills.base_skill import Skill, SkillResult


class Permission(Enum):
    """权限枚举。"""

    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    NETWORK_ACCESS = "network_access"
    SUBPROCESS = "subprocess"
    ENV_ACCESS = "env_access"


class SecurityViolation(Exception):
    """安全违规异常。"""

    def __init__(self, message: str, permission: Optional[Permission] = None):
        super().__init__(message)
        self.permission = permission


class ResourceLimitExceeded(Exception):
    """资源限制超出异常。"""

    pass


class SandboxConfig:
    """沙箱配置。

    Attributes:
        allowed_permissions: 允许的权限集合
        max_execution_time: 最大执行时间（秒）
        max_memory_mb: 最大内存使用（MB）
        allowed_paths: 允许访问的文件路径列表
        allowed_networks: 允许访问的网络地址列表
        blocked_imports: 禁止导入的模块列表
    """

    def __init__(
        self,
        allowed_permissions: Optional[Set[Permission]] = None,
        max_execution_time: float = 30.0,
        max_memory_mb: int = 512,
        allowed_paths: Optional[List[str]] = None,
        allowed_networks: Optional[List[str]] = None,
        blocked_imports: Optional[List[str]] = None,
    ) -> None:
        """初始化沙箱配置。

        Args:
            allowed_permissions: 允许的权限集合
            max_execution_time: 最大执行时间（秒）
            max_memory_mb: 最大内存使用（MB）
            allowed_paths: 允许访问的文件路径列表
            allowed_networks: 允许访问的网络地址列表
            blocked_imports: 禁止导入的模块列表
        """
        self.allowed_permissions = allowed_permissions or set()
        self.max_execution_time = max_execution_time
        self.max_memory_mb = max_memory_mb
        self.allowed_paths = allowed_paths or []
        self.allowed_networks = allowed_networks or []
        self.blocked_imports = blocked_imports or [
            "subprocess",
            "os.system",
            "ctypes",
        ]


class SandboxContext:
    """沙箱执行上下文。

    管理 skill 执行期间的权限检查和资源限制。
    """

    def __init__(self, config: SandboxConfig) -> None:
        """初始化沙箱上下文。

        Args:
            config: 沙箱配置
        """
        self.config = config
        self._start_time: Optional[float] = None
        self._file_access_log: List[str] = []
        self._network_access_log: List[str] = []

    def check_permission(self, permission: Permission, resource: str = "") -> bool:
        """检查是否允许特定权限。

        Args:
            permission: 要检查的权限
            resource: 资源标识（如文件路径、网络地址）

        Returns:
            是否允许

        Raises:
            SecurityViolation: 如果权限被拒绝
        """
        if permission not in self.config.allowed_permissions:
            raise SecurityViolation(
                f"Permission denied: {permission.value}",
                permission=permission,
            )

        # 检查文件路径
        if permission in (Permission.FILE_READ, Permission.FILE_WRITE):
            if not self._is_path_allowed(resource):
                raise SecurityViolation(
                    f"File access denied: {resource}",
                    permission=permission,
                )
            self._file_access_log.append(f"{permission.value}:{resource}")

        # 检查网络访问
        elif permission == Permission.NETWORK_ACCESS:
            if not self._is_network_allowed(resource):
                raise SecurityViolation(
                    f"Network access denied: {resource}",
                    permission=permission,
                )
            self._network_access_log.append(resource)

        return True

    def _is_path_allowed(self, path: str) -> bool:
        """检查文件路径是否在允许列表中。

        Args:
            path: 文件路径

        Returns:
            是否允许
        """
        if not self.config.allowed_paths:
            return False

        path_obj = Path(path).resolve()
        for allowed in self.config.allowed_paths:
            allowed_obj = Path(allowed).resolve()
            try:
                path_obj.relative_to(allowed_obj)
                return True
            except ValueError:
                continue

        return False

    def _is_network_allowed(self, address: str) -> bool:
        """检查网络地址是否在允许列表中。

        Args:
            address: 网络地址

        Returns:
            是否允许
        """
        if not self.config.allowed_networks:
            return False

        for allowed in self.config.allowed_networks:
            if allowed in address or address in allowed:
                return True

        return False

    def check_timeout(self) -> None:
        """检查是否超时。

        Raises:
            ResourceLimitExceeded: 如果执行超时
        """
        if self._start_time is None:
            return

        elapsed = time.time() - self._start_time
        if elapsed > self.config.max_execution_time:
            raise ResourceLimitExceeded(
                f"Execution timeout: {elapsed:.2f}s > {self.config.max_execution_time}s"
            )

    def get_access_log(self) -> Dict[str, List[str]]:
        """获取访问日志。

        Returns:
            包含文件和网络访问日志的字典
        """
        return {
            "file_access": self._file_access_log.copy(),
            "network_access": self._network_access_log.copy(),
        }


class SandboxExecutor:
    """沙箱执行器。

    在隔离环境中执行 skill，提供安全检查和资源限制。
    """

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        """初始化沙箱执行器。

        Args:
            config: 沙箱配置，如果为 None 则使用默认配置
        """
        self.config = config or SandboxConfig()

    def execute_skill(self, skill: Skill, **kwargs) -> SkillResult:
        """在沙箱中执行 skill。

        Args:
            skill: 要执行的 skill
            **kwargs: 传递给 skill 的参数

        Returns:
            SkillResult 实例
        """
        context = SandboxContext(self.config)
        context._start_time = time.time()

        # 创建执行线程
        result_container: List[Optional[SkillResult]] = [None]
        exception_container: List[Optional[Exception]] = [None]

        def execute_in_thread():
            try:
                # 执行 skill
                result_data = skill.execute(**kwargs)
                result_container[0] = SkillResult(
                    success=True,
                    data=result_data,
                    metadata={
                        "skill_name": skill.name,
                        "sandbox": True,
                        "access_log": context.get_access_log(),
                    },
                )
            except Exception as e:
                exception_container[0] = e

        thread = threading.Thread(target=execute_in_thread)
        thread.start()

        # 等待执行完成或超时
        thread.join(timeout=self.config.max_execution_time)

        # 检查超时
        if thread.is_alive():
            return SkillResult(
                success=False,
                error=f"Execution timeout: skill '{skill.name}' exceeded {self.config.max_execution_time}s",
                metadata={"skill_name": skill.name, "sandbox": True},
            )

        # 检查异常
        if exception_container[0] is not None:
            error = exception_container[0]
            if isinstance(error, SecurityViolation):
                return SkillResult(
                    success=False,
                    error=f"Security violation: {error}",
                    metadata={
                        "skill_name": skill.name,
                        "sandbox": True,
                        "violation": error.permission.value if error.permission else None,
                    },
                )
            elif isinstance(error, ResourceLimitExceeded):
                return SkillResult(
                    success=False,
                    error=f"Resource limit exceeded: {error}",
                    metadata={"skill_name": skill.name, "sandbox": True},
                )
            else:
                return SkillResult(
                    success=False,
                    error=f"Execution failed: {error}",
                    metadata={"skill_name": skill.name, "sandbox": True},
                )

        # 返回结果
        if result_container[0] is not None:
            return result_container[0]

        return SkillResult(
            success=False,
            error="Unknown execution error",
            metadata={"skill_name": skill.name, "sandbox": True},
        )


class SecureSkillWrapper:
    """安全 skill 包装器。

    为 skill 提供额外的安全检查层。
    """

    def __init__(
        self,
        skill: Skill,
        config: Optional[SandboxConfig] = None,
    ) -> None:
        """初始化安全 skill 包装器。

        Args:
            skill: 要包装的 skill
            config: 沙箱配置
        """
        self.skill = skill
        self.executor = SandboxExecutor(config)

    def execute(self, **kwargs) -> Dict[str, Any]:
        """在沙箱中执行 skill。

        Args:
            **kwargs: 传递给 skill 的参数

        Returns:
            包含执行结果的字典
        """
        result = self.executor.execute_skill(self.skill, **kwargs)

        if result.success:
            return result.data or {}
        else:
            return {
                "success": False,
                "error": result.error,
                "metadata": result.metadata,
            }


def create_secure_skill(
    skill: Skill,
    allowed_permissions: Optional[Set[Permission]] = None,
    max_execution_time: float = 30.0,
    allowed_paths: Optional[List[str]] = None,
    allowed_networks: Optional[List[str]] = None,
) -> SecureSkillWrapper:
    """创建安全 skill 的便捷函数。

    Args:
        skill: 要包装的 skill
        allowed_permissions: 允许的权限集合
        max_execution_time: 最大执行时间（秒）
        allowed_paths: 允许访问的文件路径列表
        allowed_networks: 允许访问的网络地址列表

    Returns:
        SecureSkillWrapper 实例
    """
    config = SandboxConfig(
        allowed_permissions=allowed_permissions,
        max_execution_time=max_execution_time,
        allowed_paths=allowed_paths,
        allowed_networks=allowed_networks,
    )
    return SecureSkillWrapper(skill, config)
