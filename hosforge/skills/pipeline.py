"""Skill 编排管线，支持将多个 skill 串联为管线执行。"""

import operator
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from hosforge.skills.base_skill import Skill


class ErrorStrategy(Enum):
    """错误处理策略枚举。"""

    STOP = "stop"  # 遇到错误立即停止（默认）
    RETRY = "retry"  # 重试失败步骤
    SKIP = "skip"  # 跳过失败步骤继续执行


@dataclass
class RetryConfig:
    """重试配置。

    Attributes:
        max_attempts: 最大尝试次数（包括首次执行）
        delay_seconds: 重试间隔秒数
        backoff_multiplier: 退避乘数（指数退避）
    """

    max_attempts: int = 3
    delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0


# ---------------------------------------------------------------------------
# 条件分支 DSL
# ---------------------------------------------------------------------------

class ConditionEvaluator:
    """条件评估器，支持多种条件类型。

    支持的条件类型：
        - callable: 直接调用，返回 bool
        - dict: 条件表达式，如 {"field": "status", "operator": "==", "value": "success"}
        - str: 简单表达式字符串，如 "output.status == 'success'"

    支持的操作符：
        - 比较: ==, !=, >, <, >=, <=
        - 集合: in, not in
        - 字符串: contains, startswith, endswith
        - 逻辑: and, or, not
    """

    # 操作符映射
    OPERATORS: Dict[str, Callable] = {
        "==": operator.eq,
        "!=": operator.ne,
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "in": lambda a, b: a in b,
        "not in": lambda a, b: a not in b,
        "contains": lambda a, b: b in a if isinstance(a, (str, list, tuple, set)) else False,
        "startswith": lambda a, b: a.startswith(b) if isinstance(a, str) else False,
        "endswith": lambda a, b: a.endswith(b) if isinstance(a, str) else False,
    }

    # 正则表达式模式（预编译）
    _COMPARISON_PATTERN = re.compile(
        r"^([\w.]+)\s*(==|!=|>=|<=|>|<|not in|in|contains|startswith|endswith)\s+(.+)$"
    )

    def evaluate(self, condition: Any, context: Dict[str, Any]) -> bool:
        """评估条件。

        Args:
            condition: 条件定义，可以是：
                - callable: 直接调用
                - dict: 条件表达式
                - str: 简单表达式字符串
            context: 上下文数据，用于解析条件表达式

        Returns:
            bool: 条件是否满足
        """
        if condition is None:
            return True

        if callable(condition):
            return bool(condition(context))

        if isinstance(condition, dict):
            return self._evaluate_dict(condition, context)

        if isinstance(condition, str):
            return self._evaluate_string(condition, context)

        # 默认行为：将条件视为真值
        return bool(condition)

    def _evaluate_dict(
        self, condition: Dict[str, Any], context: Dict[str, Any]
    ) -> bool:
        """评估字典形式的条件表达式。

        支持两种格式：
        1. 简单条件: {"field": "status", "operator": "==", "value": "success"}
        2. 逻辑组合: {"and": [cond1, cond2]} 或 {"or": [cond1, cond2]} 或 {"not": cond}
        """
        # 逻辑组合
        if "and" in condition:
            return all(self.evaluate(c, context) for c in condition["and"])
        if "or" in condition:
            return any(self.evaluate(c, context) for c in condition["or"])
        if "not" in condition:
            return not self.evaluate(condition["not"], context)

        # 简单条件
        field_path = condition.get("field", "")
        op_name = condition.get("operator", "==")
        expected = condition.get("value")

        actual = self._resolve_field(field_path, context)
        op_func = self.OPERATORS.get(op_name)
        if op_func is None:
            raise ValueError(f"Unsupported operator: {op_name}")

        return op_func(actual, expected)

    def _evaluate_string(self, expr: str, context: Dict[str, Any]) -> bool:
        """评估字符串形式的简单表达式。

        支持格式：
        - "field == value"
        - "field != value"
        - "field > value"
        - 等等
        """
        expr = expr.strip()

        # 解析逻辑操作符（引号感知）
        # 处理 and
        parts = self._split_logical_op(expr, " and ")
        if len(parts) > 1:
            return all(self._evaluate_string(p.strip(), context) for p in parts)

        # 处理 or
        parts = self._split_logical_op(expr, " or ")
        if len(parts) > 1:
            return any(self._evaluate_string(p.strip(), context) for p in parts)

        # 处理 not（确保后续是合法表达式，避免误匹配 "note" 等字段名）
        if expr.startswith("not "):
            remainder = expr[4:].strip()
            if self._COMPARISON_PATTERN.match(remainder) or remainder.startswith("not "):
                return not self._evaluate_string(remainder, context)

        # 解析比较表达式（使用预编译正则）
        match = self._COMPARISON_PATTERN.match(expr)
        if not match:
            raise ValueError(f"Cannot parse condition expression: {expr}")

        field_path, op_name, value_str = match.groups()
        value_str = value_str.strip()

        # 解析值
        expected = self._parse_value(value_str)
        actual = self._resolve_field(field_path, context)

        op_func = self.OPERATORS.get(op_name)
        if op_func is None:
            raise ValueError(f"Unsupported operator: {op_name}")

        return op_func(actual, expected)

    def _split_logical_op(self, expr: str, operator: str) -> List[str]:
        """引号感知的逻辑操作符分割。

        Args:
            expr: 表达式字符串
            operator: 逻辑操作符（如 " and " 或 " or "）

        Returns:
            分割后的部分列表
        """
        parts = []
        current = []
        in_single_quote = False
        in_double_quote = False
        i = 0

        while i < len(expr):
            char = expr[i]

            # 处理引号状态
            if char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                current.append(char)
            elif char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                current.append(char)
            # 检查操作符（仅在引号外）
            elif (
                not in_single_quote
                and not in_double_quote
                and expr[i : i + len(operator)] == operator
            ):
                parts.append("".join(current))
                current = []
                i += len(operator)
                continue
            else:
                current.append(char)

            i += 1

        if current:
            parts.append("".join(current))

        return parts

    def _resolve_field(self, field_path: str, context: Dict[str, Any]) -> Any:
        """解析字段路径，支持嵌套访问（如 'output.status'）。"""
        if not field_path:
            return context

        parts = field_path.split(".")
        current = context
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _parse_value(self, value_str: str) -> Any:
        """解析值字符串为 Python 对象。"""
        # 去除引号
        if (value_str.startswith('"') and value_str.endswith('"')) or (
            value_str.startswith("'") and value_str.endswith("'")
        ):
            return value_str[1:-1]

        # 布尔值
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # None
        if value_str.lower() == "none":
            return None

        # 数字
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # 列表（简单解析）
        if value_str.startswith("[") and value_str.endswith("]"):
            inner = value_str[1:-1]
            if not inner.strip():
                return []
            items = [self._parse_value(item.strip()) for item in inner.split(",")]
            return items

        # 默认作为字符串返回
        return value_str


@dataclass
class StepResult:
    """单个步骤的执行结果。"""

    step_name: str
    success: bool
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    skipped: bool = False


@dataclass
class PipelineResult:
    """管线执行结果。"""

    success: bool
    step_results: List[StepResult] = field(default_factory=list)
    final_output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class PipelineStep:
    """管线步骤定义。"""

    skill: Skill
    input_mapping: Optional[Dict[str, str]] = None  # {"target_field": "source_field"}
    condition: Any = None  # 支持 callable, dict, str
    error_handler: Optional[Callable] = None
    error_strategy: ErrorStrategy = ErrorStrategy.STOP
    retry_config: Optional[RetryConfig] = None


class SkillPipeline:
    """Skill 编排管线，支持将多个 skill 串联执行。"""

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self.steps: List[PipelineStep] = []

    def add_step(
        self,
        skill: Skill,
        input_mapping: Optional[Dict[str, str]] = None,
        condition: Any = None,
        error_handler: Optional[Callable] = None,
        error_strategy: ErrorStrategy = ErrorStrategy.STOP,
        retry_config: Optional[RetryConfig] = None,
    ) -> "SkillPipeline":
        """添加管线步骤。

        Args:
            skill: 要执行的 skill
            input_mapping: 输入映射，用于将前一个 skill 的输出映射到当前 skill 的输入
            condition: 执行条件，支持 callable / dict / str，返回 False 则跳过该步骤
            error_handler: 错误处理器
            error_strategy: 错误处理策略（stop/retry/skip）
            retry_config: 重试配置，仅在 error_strategy=RETRY 时生效

        Returns:
            self（支持链式调用）
        """
        self.steps.append(
            PipelineStep(
                skill=skill,
                input_mapping=input_mapping,
                condition=condition,
                error_handler=error_handler,
                error_strategy=error_strategy,
                retry_config=retry_config,
            )
        )
        return self

    def execute(self, initial_input: Dict[str, Any]) -> PipelineResult:
        """执行管线。

        Args:
            initial_input: 初始输入数据

        Returns:
            PipelineResult 包含所有步骤的执行结果
        """
        step_results: List[StepResult] = []
        current_input = dict(initial_input)
        evaluator = ConditionEvaluator()

        for step in self.steps:
            step_name = step.skill.name

            # 检查执行条件
            if step.condition is not None:
                try:
                    should_run = evaluator.evaluate(step.condition, current_input)
                except Exception as e:
                    step_results.append(
                        StepResult(step_name=step_name, success=False, error=str(e))
                    )
                    return PipelineResult(
                        success=False,
                        step_results=step_results,
                        final_output=current_input,
                        error=f"Condition check failed for step '{step_name}': {e}",
                    )
                if not should_run:
                    step_results.append(
                        StepResult(
                            step_name=step_name,
                            success=True,
                            output=current_input,
                            skipped=True,
                        )
                    )
                    continue

            # 应用输入映射
            if step.input_mapping is not None:
                step_input = self._map_input(current_input, step.input_mapping)
            else:
                step_input = current_input

            # 执行 skill
            try:
                output = step.skill.execute(**step_input)
                if not isinstance(output, dict):
                    output = {"result": output}
                step_results.append(
                    StepResult(step_name=step_name, success=True, output=output)
                )
                current_input = output
            except Exception as e:
                # 先尝试自定义 error_handler
                if step.error_handler is not None:
                    try:
                        fallback = step.error_handler(e, current_input)
                        if isinstance(fallback, dict):
                            current_input = fallback
                        step_results.append(
                            StepResult(
                                step_name=step_name,
                                success=True,
                                output=current_input,
                                error=str(e),
                            )
                        )
                        continue
                    except Exception as handler_err:
                        step_results.append(
                            StepResult(
                                step_name=step_name,
                                success=False,
                                error=f"Handler failed: {handler_err}",
                            )
                        )
                        return PipelineResult(
                            success=False,
                            step_results=step_results,
                            final_output=current_input,
                            error=f"Step '{step_name}' failed and handler error: {handler_err}",
                        )

                # 根据错误策略处理
                if step.error_strategy == ErrorStrategy.STOP:
                    step_results.append(
                        StepResult(step_name=step_name, success=False, error=str(e))
                    )
                    return PipelineResult(
                        success=False,
                        step_results=step_results,
                        final_output=current_input,
                        error=f"Step '{step_name}' failed: {e}",
                    )
                elif step.error_strategy == ErrorStrategy.RETRY:
                    # 重试逻辑
                    retry_config = step.retry_config or RetryConfig()
                    retry_success = False
                    
                    for attempt in range(retry_config.max_attempts - 1):  # 已执行一次，所以 -1
                        time.sleep(retry_config.delay_seconds * (retry_config.backoff_multiplier ** attempt))
                        try:
                            output = step.skill.execute(**step_input)
                            if not isinstance(output, dict):
                                output = {"result": output}
                            step_results.append(
                                StepResult(
                                    step_name=step_name,
                                    success=True,
                                    output=output,
                                    error=f"Retried {attempt + 1} times after initial failure",
                                )
                            )
                            current_input = output
                            retry_success = True
                            break
                        except Exception as retry_e:
                            if attempt == retry_config.max_attempts - 2:  # 最后一次重试失败
                                step_results.append(
                                    StepResult(
                                        step_name=step_name,
                                        success=False,
                                        error=f"Failed after {retry_config.max_attempts} attempts: {retry_e}",
                                    )
                                )
                                return PipelineResult(
                                    success=False,
                                    step_results=step_results,
                                    final_output=current_input,
                                    error=f"Step '{step_name}' failed after {retry_config.max_attempts} attempts: {retry_e}",
                                )
                    
                    if retry_success:
                        continue
                elif step.error_strategy == ErrorStrategy.SKIP:
                    # 跳过失败步骤，继续使用当前输入
                    step_results.append(
                        StepResult(
                            step_name=step_name,
                            success=False,
                            output=current_input,
                            error=str(e),
                        )
                    )
                    continue

        return PipelineResult(
            success=True, step_results=step_results, final_output=current_input
        )

    def _map_input(
        self, output: Dict[str, Any], mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """将前一个 skill 的输出映射为当前 skill 的输入。

        Args:
            output: 前一个 skill 的输出
            mapping: 映射规则，如 {"target_field": "source_field"}

        Returns:
            映射后的输入数据
        """
        mapped: Dict[str, Any] = {}
        for target, source in mapping.items():
            if source in output:
                mapped[target] = output[source]
        return mapped
