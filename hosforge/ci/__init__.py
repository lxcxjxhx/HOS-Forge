"""
HOS-Forge CI/CD — 安全质量门禁集成。

提供:
    - GitHub Actions 辅助脚本
    - 本地 pre-commit hook 生成
    - Reality Score CLI 检查
    - SAST 扫描编排
"""

from hosforge.ci.check import run_reality_check, run_sast_scan

__all__ = ['run_reality_check', 'run_sast_scan']
