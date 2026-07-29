"""Skill 基础模块，定义 Skill 基类和结果数据类。"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class SkillResult:
    """Skill 执行结果数据类。
    
    Attributes:
        success: 执行是否成功
        data: 执行返回的数据
        error: 错误信息（如果有）
        metadata: 额外的元数据
    """
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Skill(ABC):
    """Skill 抽象基类。
    
    所有具体的 Skill 实现都应该继承此类并实现 execute 方法。
    
    Attributes:
        name: Skill 的名称
        description: Skill 的描述
        parameters: 输入参数的 schema 定义
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化 Skill 实例。
        
        Args:
            name: Skill 的名称
            description: Skill 的描述
            parameters: 输入参数的 schema 定义
        """
        self.name = name
        self.description = description
        self.parameters = parameters or {}
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行 Skill 的核心逻辑。
        
        Args:
            **kwargs: 传递给 Skill 的参数
            
        Returns:
            包含执行结果的字典
        """
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """验证输入参数是否符合 schema 定义。
        
        Args:
            **kwargs: 待验证的参数
            
        Returns:
            参数验证是否通过
        """
        if not self.parameters:
            return True
        
        # 检查必填参数
        required = self.parameters.get("required", [])
        for param in required:
            if param not in kwargs:
                return False
        
        # 检查参数类型
        properties = self.parameters.get("properties", {})
        for key, value in kwargs.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type:
                    if not self._check_type(value, expected_type):
                        return False
        
        return True
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值是否符合预期类型。
        
        Args:
            value: 要检查的值
            expected_type: 预期的类型字符串
            
        Returns:
            类型是否匹配
        """
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected = type_map.get(expected_type)
        if expected is None:
            return True

        return isinstance(value, expected)
