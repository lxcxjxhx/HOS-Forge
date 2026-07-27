"""Finding State Machine - 安全发现状态机管理。"""

from enum import Enum
from typing import List


class FindingState(Enum):
    """安全发现状态枚举"""
    FINDING = "finding"
    CANDIDATE = "candidate"
    VERIFIED = "verified"
    FIXED = "fixed"
    CLOSED = "closed"
    REJECTED = "rejected"


class FindingStateMachine:
    """安全发现状态机 - 管理发现的生命周期状态转换。"""

    # 允许的状态转换规则
    # FINDING→CANDIDATE, CANDIDATE→VERIFIED/REJECTED, VERIFIED→FIXED, FIXED→CLOSED, any→FINDING (reset)
    ALLOWED_TRANSITIONS = {
        FindingState.FINDING: [FindingState.CANDIDATE, FindingState.FINDING],
        FindingState.CANDIDATE: [FindingState.VERIFIED, FindingState.REJECTED, FindingState.FINDING],
        FindingState.VERIFIED: [FindingState.FIXED, FindingState.FINDING],
        FindingState.FIXED: [FindingState.CLOSED, FindingState.FINDING],
        FindingState.CLOSED: [FindingState.FINDING],
        FindingState.REJECTED: [FindingState.FINDING],
    }

    def __init__(self, finding_id: str):
        """初始化状态机。

        Args:
            finding_id: 安全发现的唯一标识符
        """
        self._finding_id = finding_id
        self._current_state = FindingState.FINDING

    @property
    def finding_id(self) -> str:
        """获取发现 ID"""
        return self._finding_id

    @property
    def current_state(self) -> FindingState:
        """获取当前状态"""
        return self._current_state

    def transition(self, new_state: FindingState) -> bool:
        """尝试转换到新状态。

        Args:
            new_state: 目标状态

        Returns:
            bool: 转换是否成功

        Raises:
            ValueError: 当转换不被允许时
        """
        allowed = self.get_allowed_transitions()

        if new_state not in allowed:
            raise ValueError(
                f"不允许从 {self._current_state.value} 转换到 {new_state.value}。"
                f"允许的目标状态: {[s.value for s in allowed]}"
            )

        self._current_state = new_state
        return True

    def get_allowed_transitions(self) -> List[FindingState]:
        """获取当前状态允许的所有转换目标。

        Returns:
            List[FindingState]: 允许的目标状态列表
        """
        return self.ALLOWED_TRANSITIONS.get(self._current_state, [])

    def reset(self) -> None:
        """重置状态到 FINDING"""
        self._current_state = FindingState.FINDING

    def is_terminal(self) -> bool:
        """检查是否处于终止状态。

        Returns:
            bool: 是否处于终止状态（CLOSED 或 REJECTED）
        """
        return self._current_state in (FindingState.CLOSED, FindingState.REJECTED)

    def __str__(self) -> str:
        return f"FindingStateMachine({self._finding_id}: {self._current_state.value})"
