"""Verification Pipeline - 安全发现验证流水线编排。"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from hosforge.memory.store import SecurityMemoryStore

from .agents import (
    ExploitAgent,
    PatchAgent,
    PRGeneratorAgent,
    ReviewAgent,
    VerificationAgent,
)
from .state_machine import FindingState, FindingStateMachine

logger = logging.getLogger(__name__)

# PatchAgent 最大重试次数（ReviewAgent 未批准时）
MAX_PATCH_RETRIES = 3


class VerificationPipeline:
    """安全发现验证流水线。

    按以下阶段顺序执行：
    1. VerificationAgent  - 误报检查
    2. ExploitAgent       - 漏洞复现
    3. PatchAgent         - 生成修复代码
    4. ReviewAgent        - 审查修复（未通过则回到 PatchAgent，最多重试 3 次）
    5. PRGeneratorAgent   - 生成 PR 元数据
    """

    def __init__(self, memory_store: Optional[SecurityMemoryStore] = None):
        """初始化流水线。

        Args:
            memory_store: 可选的安全记忆存储
        """
        self._memory_store = memory_store

        self._verification_agent = VerificationAgent(memory_store)
        self._exploit_agent = ExploitAgent(memory_store)
        self._patch_agent = PatchAgent(memory_store)
        self._review_agent = ReviewAgent(memory_store)
        self._pr_agent = PRGeneratorAgent(memory_store)

        # 运行时状态
        self._state_machine: Optional[FindingStateMachine] = None
        self._stage_results: Dict[str, Any] = {}

    async def run(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整验证流水线。

        Args:
            finding: 安全发现信息字典，至少包含 id 字段

        Returns:
            Dict 包含流水线各阶段的输出结果及最终状态
        """
        finding_id = finding.get("id", "unknown")
        self._state_machine = FindingStateMachine(finding_id)
        self._stage_results = {}

        logger.info("开始验证流水线: %s", finding_id)

        # FINDING → CANDIDATE（进入候选池后开始验证）
        self._state_machine.transition(FindingState.CANDIDATE)

        # ── 阶段 1: 误报检查 ──────────────────────────────────────────
        logger.info("[阶段 1/5] VerificationAgent - 误报检查")
        verification_result = await self._verification_agent.execute(finding)
        self._stage_results["verification"] = verification_result

        if not verification_result.get("verified", False):
            self._state_machine.transition(FindingState.REJECTED)
            logger.info("发现被判定为误报，流水线终止")
            return self._build_result(finding, rejected_at="verification")

        # ── 阶段 2: 漏洞复现 ──────────────────────────────────────────
        logger.info("[阶段 2/5] ExploitAgent - 漏洞复现")
        exploit_result = await self._exploit_agent.execute(finding)
        self._stage_results["exploit"] = exploit_result

        if not exploit_result.get("reproducible", False):
            self._state_machine.transition(FindingState.REJECTED)
            logger.info("漏洞无法复现，流水线终止")
            return self._build_result(finding, rejected_at="exploit")

        # CANDIDATE → VERIFIED
        self._state_machine.transition(FindingState.VERIFIED)

        # ── 阶段 3 & 4: 补丁生成 + 审查（最多重试 3 次）────────────────
        patch_result: Dict[str, Any] = {}
        review_result: Dict[str, Any] = {}

        for attempt in range(1, MAX_PATCH_RETRIES + 1):
            logger.info("[阶段 3/5] PatchAgent - 生成修复 (尝试 %d/%d)", attempt, MAX_PATCH_RETRIES)
            patch_result = await self._patch_agent.execute(finding)
            self._stage_results["patch"] = patch_result
            self._stage_results[f"patch_attempt_{attempt}"] = patch_result

            logger.info("[阶段 4/5] ReviewAgent - 审查修复")
            review_input = {**finding, **patch_result}
            review_result = await self._review_agent.execute(review_input)
            self._stage_results["review"] = review_result
            self._stage_results[f"review_attempt_{attempt}"] = review_result

            if review_result.get("approved", False):
                break

            logger.info(
                "审查未通过 (评分: %d)，重试 (%d/%d)",
                review_result.get("score", 0),
                attempt,
                MAX_PATCH_RETRIES,
            )
        else:
            # 3 次重试后仍未通过
            logger.warning("补丁审查 %d 次后仍未通过，流水线终止", MAX_PATCH_RETRIES)
            self._state_machine.transition(FindingState.REJECTED)
            return self._build_result(finding, rejected_at="review")

        # VERIFIED → FIXED
        self._state_machine.transition(FindingState.FIXED)

        # ── 阶段 5: 生成 PR 元数据 ────────────────────────────────────
        logger.info("[阶段 5/5] PRGeneratorAgent - 生成 PR 元数据")
        pr_input = {**finding, **patch_result, "patch_description": patch_result.get("description", "")}
        pr_result = await self._pr_agent.execute(pr_input)
        self._stage_results["pr"] = pr_result

        # FIXED → CLOSED
        self._state_machine.transition(FindingState.CLOSED)

        logger.info("验证流水线完成: %s", finding_id)
        return self._build_result(finding)

    def get_pipeline_status(self) -> Dict[str, Any]:
        """获取流水线当前状态及各阶段结果。

        Returns:
            Dict 包含当前状态和所有已完成阶段的结果
        """
        return {
            "state": self._state_machine.current_state.value if self._state_machine else None,
            "finding_id": self._state_machine.finding_id if self._state_machine else None,
            "stage_results": dict(self._stage_results),
        }

    def _build_result(
        self,
        finding: Dict[str, Any],
        rejected_at: Optional[str] = None,
    ) -> Dict[str, Any]:
        """构建流水线最终结果字典。"""
        state = self._state_machine.current_state if self._state_machine else None
        return {
            "finding_id": finding.get("id", "unknown"),
            "final_state": state.value if state else None,
            "rejected_at": rejected_at,
            "stages": dict(self._stage_results),
        }
