"""安全相关 Skill 集合，提供漏洞扫描、代码分析和 GitHub 集成能力。"""

from hosforge.skills.security.codeql_skill import CodeQLScanSkill
from hosforge.skills.security.github_skill import GitHubIntegrationSkill
from hosforge.skills.security.nuclei_skill import NucleiScanSkill
from hosforge.skills.security.semgrep_skill import SemgrepScanSkill
from hosforge.skills.security.trivy_skill import TrivyScanSkill

__all__ = [
    "NucleiScanSkill",
    "SemgrepScanSkill",
    "GitHubIntegrationSkill",
    "TrivyScanSkill",
    "CodeQLScanSkill",
]
