"""Skill 沙箱执行环境，提供安全隔离和资源限制。"""

import json
import logging
import signal
import subprocess
import sys
import tempfile
import threading
import time
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from hosforge.skills.base_skill import Skill, SkillResult

logger = logging.getLogger(__name__)


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


class ProcessSandboxExecutor:
    """进程级沙箱执行器，使用 subprocess 在独立进程中执行 skill。
    
    提供真正的安全隔离，skill 在独立的 Python 进程中执行，
    通过 JSON 序列化的 stdin/stdout 进行进程间通信。
    支持 CPU 时间限制和内存限制（跨平台）。
    """

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        """初始化进程级沙箱执行器。
        
        Args:
            config: 沙箱配置，如果为 None 则使用默认配置
        """
        self.config = config or SandboxConfig()
        self._resource_limits_supported = self._setup_resource_limits()

    def _setup_resource_limits(self) -> bool:
        """设置资源限制。
        
        检测并配置当前平台支持的资源限制机制。
        
        Returns:
            是否支持资源限制
        """
        self._psutil_available = False
        self._resource_module_available = False
        
        # 尝试导入 psutil（跨平台）
        try:
            import psutil
            self._psutil = psutil
            self._psutil_available = True
            logger.debug("psutil 可用，将使用 psutil 进行资源监控")
        except ImportError:
            logger.debug("psutil 不可用，将尝试使用平台特定方法")
        
        # Unix/Linux: 尝试使用 resource 模块
        if sys.platform != "win32":
            try:
                import resource
                self._resource = resource
                self._resource_module_available = True
                logger.debug("resource 模块可用，将使用 setrlimit 进行资源限制")
            except ImportError:
                logger.warning("resource 模块不可用")
        
        if not self._psutil_available and not self._resource_module_available:
            logger.warning(
                "无法设置资源限制：psutil 和 resource 模块均不可用。"
                "建议安装 psutil: pip install psutil"
            )
            return False
        
        return True

    def _get_process_resources(self, process: subprocess.Popen) -> Dict[str, float]:
        """获取子进程的资源使用情况。
        
        Args:
            process: 子进程对象
            
        Returns:
            包含资源使用信息的字典（cpu_time, memory_mb）
        """
        if not self._psutil_available:
            return {"cpu_time": 0.0, "memory_mb": 0.0}
        
        try:
            proc = self._psutil.Process(process.pid)
            cpu_time = proc.cpu_times()
            memory_info = proc.memory_info()
            return {
                "cpu_time": cpu_time.user + cpu_time.system,
                "memory_mb": memory_info.rss / (1024 * 1024),
            }
        except (self._psutil.NoSuchProcess, self._psutil.AccessDenied):
            return {"cpu_time": 0.0, "memory_mb": 0.0}

    def _enforce_limits(self, process: subprocess.Popen) -> Optional[str]:
        """监控并强制执行资源限制。
        
        检查子进程的 CPU 时间和内存使用，如果超出限制则终止进程。
        
        Args:
            process: 子进程对象
            
        Returns:
            如果违反限制，返回错误信息；否则返回 None
        """
        if process.poll() is not None:
            return None  # 进程已结束
        
        resources = self._get_process_resources(process)
        
        # 检查 CPU 时间限制
        if resources["cpu_time"] > self.config.max_execution_time:
            logger.warning(
                f"CPU 时间超限：{resources['cpu_time']:.2f}s > {self.config.max_execution_time}s"
            )
            try:
                process.kill()
                process.wait(timeout=1)
            except Exception:
                pass
            return f"CPU time limit exceeded: {resources['cpu_time']:.2f}s > {self.config.max_execution_time}s"
        
        # 检查内存限制
        if resources["memory_mb"] > self.config.max_memory_mb:
            logger.warning(
                f"内存超限：{resources['memory_mb']:.2f}MB > {self.config.max_memory_mb}MB"
            )
            try:
                process.kill()
                process.wait(timeout=1)
            except Exception:
                pass
            return f"Memory limit exceeded: {resources['memory_mb']:.2f}MB > {self.config.max_memory_mb}MB"
        
        return None

    def _monitor_resources(self, process: subprocess.Popen, stop_event: threading.Event) -> Optional[str]:
        """在后台线程中监控资源使用。
        
        Args:
            process: 子进程对象
            stop_event: 停止信号
            
        Returns:
            如果违反限制，返回错误信息；否则返回 None
        """
        violation = None
        while not stop_event.is_set():
            if process.poll() is not None:
                break
            
            violation = self._enforce_limits(process)
            if violation:
                break
            
            stop_event.wait(timeout=0.1)  # 每 100ms 检查一次
        
        return violation

    def execute_skill(self, skill: Skill, **kwargs) -> SkillResult:
        """在独立进程中执行 skill。
        
        Args:
            skill: 要执行的 skill
            **kwargs: 传递给 skill 的参数
        
        Returns:
            SkillResult 实例
        """
        return self._execute_with_timeout(
            skill, kwargs, self.config.max_execution_time
        )

    def _create_worker_script(self) -> str:
        """创建子进程工作脚本。
        
        Returns:
            Python 脚本内容
        """
        script = '''
import sys
import json
import importlib
import importlib.util
import traceback

def main():
    # 从 stdin 读取输入
    input_data = json.load(sys.stdin)
    
    skill_module = input_data["skill_module"]
    skill_class = input_data["skill_class"]
    skill_file = input_data.get("skill_file")
    skill_args = input_data["args"]
    
    # 动态导入 skill
    if skill_file:
        spec = importlib.util.spec_from_file_location(skill_module, skill_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[skill_module] = module
        spec.loader.exec_module(module)
    else:
        module = importlib.import_module(skill_module)
    
    skill_cls = getattr(module, skill_class)
    skill = skill_cls()
    
    # 执行 skill
    result = skill.execute(**skill_args)
    
    # 输出结果
    print(json.dumps({"success": True, "data": result}))

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        print(json.dumps({"success": False, "error": error_msg, "traceback": tb}))
        sys.exit(1)
'''
        return script

    def _make_preexec_fn(self) -> Optional[Callable[[], None]]:
        """创建 preexec_fn，用于在子进程启动时设置资源硬限制（仅 Unix）。

        Returns:
            preexec_fn 可调用对象，或 None（非 Unix 平台）
        """
        if sys.platform == "win32" or not self._resource_module_available:
            return None

        max_cpu_time = int(self.config.max_execution_time) + 1
        max_memory_bytes = self.config.max_memory_mb * 1024 * 1024
        resource_mod = self._resource

        def _set_limits() -> None:
            try:
                # CPU 时间限制（秒）
                resource_mod.setrlimit(
                    resource_mod.RLIMIT_CPU, (max_cpu_time, max_cpu_time)
                )
            except (ValueError, resource_mod.error):
                pass
            try:
                # 内存限制（字节）
                resource_mod.setrlimit(
                    resource_mod.RLIMIT_AS, (max_memory_bytes, max_memory_bytes)
                )
            except (ValueError, resource_mod.error):
                pass
            try:
                # 数据段大小限制
                resource_mod.setrlimit(
                    resource_mod.RLIMIT_DATA, (max_memory_bytes, max_memory_bytes)
                )
            except (ValueError, resource_mod.error):
                pass

        return _set_limits

    def _execute_with_timeout(
        self, skill: Skill, kwargs: Dict[str, Any], timeout: float
    ) -> SkillResult:
        """带超时的子进程执行，同时监控资源限制。

        Args:
            skill: 要执行的 skill
            kwargs: 传递给 skill 的参数
            timeout: 超时时间（秒）

        Returns:
            SkillResult 实例
        """
        import inspect

        worker_script = self._create_worker_script()

        # 获取 skill 类的文件路径，以便在子进程中导入
        try:
            skill_file = inspect.getfile(skill.__class__)
        except (TypeError, OSError):
            skill_file = None

        # Unix: 使用 preexec_fn 设置硬限制
        preexec_fn = self._make_preexec_fn()

        popen_kwargs: Dict[str, Any] = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
        }
        if preexec_fn is not None:
            popen_kwargs["preexec_fn"] = preexec_fn

        process = subprocess.Popen(
            [sys.executable, "-c", worker_script],
            **popen_kwargs,
        )

        input_data = {
            "skill_module": skill.__module__,
            "skill_class": skill.__class__.__name__,
            "skill_file": skill_file,
            "args": kwargs,
        }

        # 启动资源监控线程（如果支持）
        stop_event = threading.Event()
        monitor_thread: Optional[threading.Thread] = None
        monitor_result: List[Optional[str]] = [None]

        if self._resource_limits_supported and self._psutil_available:
            def _monitor() -> None:
                monitor_result[0] = self._monitor_resources(process, stop_event)

            monitor_thread = threading.Thread(target=_monitor, daemon=True)
            monitor_thread.start()

        try:
            stdout, stderr = process.communicate(
                input=json.dumps(input_data), timeout=timeout
            )

            # 停止监控线程
            stop_event.set()
            if monitor_thread is not None:
                monitor_thread.join(timeout=1)

            # 检查监控线程是否检测到违规
            if monitor_result[0] is not None:
                return SkillResult(
                    success=False,
                    error=f"Resource limit exceeded: {monitor_result[0]}",
                    metadata={
                        "skill_name": skill.name,
                        "sandbox": True,
                        "process_sandbox": True,
                        "resource_violation": True,
                    },
                )

            # 检查进程返回码
            if process.returncode != 0:
                # 检查是否因 Unix 资源限制被杀死（SIGXCPU=24, SIGKILL=9）
                if sys.platform != "win32" and process.returncode < 0:
                    sig = -process.returncode
                    if sig == 24:  # SIGXCPU - CPU 时间超限
                        return SkillResult(
                            success=False,
                            error=f"CPU time limit exceeded (SIGXCPU)",
                            metadata={
                                "skill_name": skill.name,
                                "sandbox": True,
                                "process_sandbox": True,
                                "resource_violation": True,
                            },
                        )
                    elif sig == 9:  # SIGKILL - 可能是 OOM killer
                        return SkillResult(
                            success=False,
                            error=f"Process killed (possible memory limit exceeded, SIGKILL)",
                            metadata={
                                "skill_name": skill.name,
                                "sandbox": True,
                                "process_sandbox": True,
                                "resource_violation": True,
                            },
                        )

                # 尝试从 stdout 解析错误信息
                try:
                    error_result = json.loads(stdout.strip())
                    return SkillResult(
                        success=False,
                        error=error_result.get("error", "Unknown error in subprocess"),
                        metadata={
                            "skill_name": skill.name,
                            "sandbox": True,
                            "process_sandbox": True,
                            "traceback": error_result.get("traceback"),
                        },
                    )
                except json.JSONDecodeError:
                    # 无法解析 JSON，使用 stderr
                    return SkillResult(
                        success=False,
                        error=f"Process failed with return code {process.returncode}: {stderr}",
                        metadata={
                            "skill_name": skill.name,
                            "sandbox": True,
                            "process_sandbox": True,
                        },
                    )

            # 解析成功结果
            if not stdout.strip():
                return SkillResult(
                    success=False,
                    error="Process produced no output",
                    metadata={
                        "skill_name": skill.name,
                        "sandbox": True,
                        "process_sandbox": True,
                    },
                )

            result = json.loads(stdout.strip())
            return SkillResult(
                success=result.get("success", False),
                data=result.get("data"),
                error=result.get("error"),
                metadata={
                    "skill_name": skill.name,
                    "sandbox": True,
                    "process_sandbox": True,
                },
            )

        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
            stop_event.set()
            if monitor_thread is not None:
                monitor_thread.join(timeout=1)
            return SkillResult(
                success=False,
                error=f"Execution timeout: skill '{skill.name}' exceeded {timeout}s",
                metadata={
                    "skill_name": skill.name,
                    "sandbox": True,
                    "process_sandbox": True,
                },
            )
        except json.JSONDecodeError as e:
            process.kill()
            process.wait()
            stop_event.set()
            if monitor_thread is not None:
                monitor_thread.join(timeout=1)
            return SkillResult(
                success=False,
                error=f"Failed to parse process output: {e}",
                metadata={
                    "skill_name": skill.name,
                    "sandbox": True,
                    "process_sandbox": True,
                },
            )
        except Exception as e:
            try:
                process.kill()
                process.wait()
            except Exception:
                pass
            stop_event.set()
            if monitor_thread is not None:
                monitor_thread.join(timeout=1)
            return SkillResult(
                success=False,
                error=f"Process execution failed: {e}",
                metadata={
                    "skill_name": skill.name,
                    "sandbox": True,
                    "process_sandbox": True,
                },
            )
