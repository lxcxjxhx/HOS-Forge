"""Tests for AttackAgent."""
from unittest.mock import MagicMock

import pytest

from hosforge.security_agents.attack import AttackAgent
from hosforge.security_agents.base import SecurityAgentConfig, Severity


@pytest.fixture
def attack_agent():
    """Create AttackAgent instance."""
    return AttackAgent()


@pytest.fixture
def custom_config():
    """Create custom agent config."""
    return SecurityAgentConfig(
        name="CustomAttack",
        description="Custom attack agent",
        enabled=True,
        max_vulnerabilities=20,
    )


class TestAttackAgent:
    """Test cases for AttackAgent."""

    def test_init_default(self, attack_agent):
        """Test default initialization."""
        assert attack_agent.name == "AttackAgent"
        assert attack_agent.config.name == "AttackAgent"
        assert attack_agent.config.enabled is True
        assert attack_agent._current_report is None
        assert len(attack_agent._tool_adapters) == 0

    def test_init_custom_config(self, custom_config):
        """Test initialization with custom config."""
        agent = AttackAgent(config=custom_config)
        assert agent.config.name == "CustomAttack"
        assert agent.config.max_vulnerabilities == 20

    def test_register_tool(self, attack_agent):
        """Test tool registration."""
        mock_tool = MagicMock()
        attack_agent.register_tool("nmap", mock_tool)
        assert "nmap" in attack_agent._tool_adapters
        assert attack_agent._tool_adapters["nmap"] == mock_tool

    @pytest.mark.asyncio
    async def test_analyze_basic(self, attack_agent):
        """Test basic analyze method."""
        result = await attack_agent.analyze("example.com")
        assert result.target == "example.com"
        assert result.agent_name == "AttackAgent"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_analyze_with_options(self, attack_agent):
        """Test analyze with various options."""
        result = await attack_agent.analyze(
            "example.com",
            authorized=True,
            port_range="1-1024",
            fast_mode=True,
            skip_exploit=True,
        )
        assert result.target == "example.com"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_run_pentest_basic(self, attack_agent):
        """Test basic pentest execution."""
        from hosforge.security_agents.attack import PentestTarget

        target = PentestTarget(host="example.com")
        report = await attack_agent.run_pentest(target)

        assert report.target.host == "example.com"
        assert report.report_id.startswith("PT-")
        assert len(report.phases) > 0
        assert report.executive_summary is not None

    @pytest.mark.asyncio
    async def test_run_pentest_skip_exploit(self, attack_agent):
        """Test pentest with skip_exploit flag."""
        from hosforge.security_agents.attack import PentestTarget

        target = PentestTarget(host="example.com", scope_authorized=False)
        report = await attack_agent.run_pentest(target, skip_exploit=True)

        assert report.target.host == "example.com"
        # Check that exploitation phase was skipped
        exploit_phase = next(
            (p for p in report.phases if p.phase.value == "exploitation"),
            None
        )
        assert exploit_phase is not None
        assert exploit_phase.status == "skipped"

    @pytest.mark.asyncio
    async def test_phase_reconnaissance(self, attack_agent):
        """Test reconnaissance phase."""
        from hosforge.security_agents.attack import PentestTarget

        target = PentestTarget(host="example.com")
        result = await attack_agent._phase_reconnaissance(target)

        assert result.phase.value == "reconnaissance"
        assert result.status == "completed"
        assert "target" in result.data
        assert result.data["target"] == "example.com"

    @pytest.mark.asyncio
    async def test_phase_scanning(self, attack_agent):
        """Test scanning phase."""
        from hosforge.security_agents.attack import PentestPhase, PentestTarget, PhaseResult

        target = PentestTarget(host="example.com")
        recon_result = PhaseResult(
            phase=PentestPhase.RECON,
            status="completed",
            data={
                "open_ports": [80, 443],
                "services": {80: "http", 443: "https"},
            }
        )

        result = await attack_agent._phase_scanning(target, recon_result)

        assert result.phase.value == "scanning"
        assert result.status == "completed"
        assert "vulnerability_hints" in result.data

    @pytest.mark.asyncio
    async def test_phase_vuln_assessment(self, attack_agent):
        """Test vulnerability assessment phase."""
        from hosforge.security_agents.attack import PentestPhase, PentestTarget, PhaseResult

        target = PentestTarget(host="example.com")
        scan_result = PhaseResult(
            phase=PentestPhase.SCANNING,
            status="completed",
            data={
                "vulnerability_hints": [
                    {
                        "name": "Test Vuln",
                        "severity": "high",
                        "confidence": "high",
                        "cwe": "CWE-89",
                    }
                ]
            }
        )

        result = await attack_agent._phase_vuln_assessment(target, scan_result)

        assert result.phase.value == "vuln_assessment"
        assert result.status == "completed"
        assert "confirmed_vulns" in result.data

    @pytest.mark.asyncio
    async def test_phase_exploitation_unauthorized(self, attack_agent):
        """Test exploitation phase with unauthorized target."""
        from hosforge.security_agents.attack import PentestTarget

        target = PentestTarget(host="example.com", scope_authorized=False)
        result = await attack_agent._phase_exploitation(target, [])

        assert result.phase.value == "exploitation"
        assert result.status == "skipped"

    def test_hint_to_vulnerability(self, attack_agent):
        """Test converting hint to vulnerability."""
        hint = {
            "name": "SQL Injection",
            "severity": "critical",
            "cwe": "CWE-89",
            "description": "Test description",
        }

        vuln = attack_agent._hint_to_vulnerability(hint, "example.com")

        assert vuln is not None
        assert vuln.name == "SQL Injection"
        assert vuln.severity == Severity.CRITICAL
        assert vuln.cwe_id == "CWE-89"
        assert vuln.file_path == "example.com"

    def test_severity_to_score(self, attack_agent):
        """Test severity to score conversion."""
        assert attack_agent._severity_to_score(Severity.CRITICAL) == 95
        assert attack_agent._severity_to_score(Severity.HIGH) == 70
        assert attack_agent._severity_to_score(Severity.MEDIUM) == 40
        assert attack_agent._severity_to_score(Severity.LOW) == 15
        assert attack_agent._severity_to_score(Severity.INFO) == 5

    def test_calculate_risk_score_empty(self, attack_agent):
        """Test risk score calculation with empty list."""
        score = attack_agent._calculate_risk_score([])
        assert score == 0

    def test_calculate_risk_score_with_values(self, attack_agent):
        """Test risk score calculation with values."""
        scores = [95, 70, 40]
        score = attack_agent._calculate_risk_score(scores)
        assert 0 <= score <= 100
        # Max is 95, avg is ~68.3
        # Expected: 95 * 0.7 + 68.3 * 0.3 = 66.5 + 20.5 = 87
        assert score == 87

    def test_deduplicate_vulns(self, attack_agent):
        """Test vulnerability deduplication."""
        from hosforge.security_agents.base import SecurityVulnerability

        vulns = [
            SecurityVulnerability(name="SQL Injection", cwe_id="CWE-89"),
            SecurityVulnerability(name="SQL Injection", cwe_id="CWE-89"),  # Duplicate
            SecurityVulnerability(name="XSS", cwe_id="CWE-79"),
        ]

        deduped = attack_agent._deduplicate_vulns(vulns)
        assert len(deduped) == 2
        assert deduped[0].name == "SQL Injection"
        assert deduped[1].name == "XSS"

    def test_generate_recommendations_empty(self, attack_agent):
        """Test recommendations generation with no vulnerabilities."""
        recs = attack_agent._generate_recommendations([])
        assert len(recs) == 1
        assert "未发现严重安全风险" in recs[0]

    def test_generate_recommendations_with_vulns(self, attack_agent):
        """Test recommendations generation with vulnerabilities."""
        from hosforge.security_agents.base import SecurityVulnerability

        vulns = [
            SecurityVulnerability(
                name="SQL Injection",
                cwe_id="CWE-89",
                description="SQL injection vulnerability"
            ),
        ]

        recs = attack_agent._generate_recommendations(vulns)
        assert len(recs) == 1
        assert "CWE-89" in recs[0]
        assert "SQL Injection" in recs[0]

    @pytest.mark.asyncio
    async def test_generate_html_report(self, attack_agent):
        """Test HTML report generation."""
        from hosforge.security_agents.attack import PentestReport, PentestTarget

        report = PentestReport(
            report_id="PT-TEST123",
            target=PentestTarget(host="example.com"),
            risk_score=75,
            executive_summary="Test summary",
        )

        html = await attack_agent.generate_html_report(report)

        assert html is not None
        assert "<!DOCTYPE html>" in html
        assert "example.com" in html
        assert "PT-TEST123" in html
        assert "75" in html

    @pytest.mark.asyncio
    async def test_generate_markdown_report(self, attack_agent):
        """Test Markdown report generation."""
        from hosforge.security_agents.attack import PentestReport, PentestTarget

        report = PentestReport(
            report_id="PT-TEST123",
            target=PentestTarget(host="example.com"),
            risk_score=75,
            executive_summary="Test summary",
        )

        md = await attack_agent.generate_markdown_report(report)

        assert md is not None
        assert "# 🔐 HOS-Forge 渗透测试报告" in md
        assert "example.com" in md
        assert "PT-TEST123" in md
        assert "75" in md
