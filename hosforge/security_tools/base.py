"""
HOS-Forge Security Tool Base — 安全工具基类。

所有外部安全工具集成需要继承 BaseSecurityTool。
"""

from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SecurityToolResult:
    """安全工具执行结果"""
    tool_name: str = ''
    success: bool = True
    output: str = ''
    error: str = ''
    raw_data: dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            'tool_name': self.tool_name,
            'success': self.success,
            'output': self.output,
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
        }


class BaseSecurityTool(abc.ABC):
    """
    安全工具抽象基类。

    子类必须实现:
        - name: 工具名称
        - run(target, **kwargs): 执行工具
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """工具唯一标识"""
        ...

    @abc.abstractmethod
    async def run(self, target: str, **kwargs: Any) -> SecurityToolResult:
        """
        在目标上执行安全工具。

        Args:
            target: 目标路径/URL/IP
            **kwargs: 工具特定参数

        Returns:
            SecurityToolResult: 执行结果
        """
        ...

    async def validate(self) -> bool:
        """
        验证工具是否可用（路径/二进制/API密钥等）
        """
        return False
