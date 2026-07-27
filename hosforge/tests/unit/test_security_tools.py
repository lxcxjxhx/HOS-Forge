"""
HOS-Forge Security Tools Tests — 安全工具单元测试。

测试所有安全工具的真实调用实现。
"""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hosforge.security_tools import (
    BaseSecurityTool,
    BurpTool,
    NmapTool,
    NucleiTool,
    SecurityToolResult,
    SemgrepTool,
    TrivyTool,
)


class TestNmapTool:
    """NmapTool 测试套件"""

    def test_nmap_tool_initialization(self):
        """测试 NmapTool 初始化"""
        tool = NmapTool()
        assert tool.name == "nmap"
        assert tool._nmap_path == "nmap"

    def test_nmap_tool_custom_path(self):
        """测试自定义 Nmap 路径"""
        tool = NmapTool(nmap_path="/usr/local/bin/nmap")
        assert tool._nmap_path == "/usr/local/bin/nmap"

    @pytest.mark.asyncio
    async def test_nmap_validate_not_found(self):
        """测试 Nmap 不可用时的验证"""
        tool = NmapTool()
        with patch("shutil.which", return_value=None):
            result = await tool.validate()
            assert result is False

    @pytest.mark.asyncio
    async def test_nmap_validate_found(self):
        """测试 Nmap 可用时的验证"""
        tool = NmapTool()
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            result = await tool.validate()
            assert result is True

    @pytest.mark.asyncio
    async def test_nmap_run_not_installed(self):
        """测试 Nmap 未安装时的运行"""
        tool = NmapTool()
        with patch("shutil.which", return_value=None):
            result = await tool.run("example.com")
            assert result.success is False
            assert "not installed" in result.error

    @pytest.mark.asyncio
    async def test_nmap_parse_output(self):
        """测试 Nmap XML 输出解析"""
        tool = NmapTool()
        xml_output = """<?xml version="1.0"?>
<nmaprun>
  <host>
    <status state="up"/>
    <ports>
      <port protocol="tcp" portid="22">
        <state state="open"/>
        <service name="ssh"/>
      </port>
      <port protocol="tcp" portid="80">
        <state state="open"/>
        <service name="http"/>
      </port>
    </ports>
    <os>
      <osmatch name="Linux 4.15" accuracy="95"/>
    </os>
  </host>
</nmaprun>"""
        result = tool._parse_nmap_output(xml_output)
        assert result["host_status"] == "up"
        assert 22 in result["open_ports"]
        assert 80 in result["open_ports"]
        assert result["services"][22] == "ssh"
        assert result["services"][80] == "http"
        assert "Linux" in result["os_guess"]


class TestSemgrepTool:
    """SemgrepTool 测试套件"""

    def test_semgrep_tool_initialization(self):
        """测试 SemgrepTool 初始化"""
        tool = SemgrepTool()
        assert tool.name == "semgrep"
        assert tool._semgrep_path == "semgrep"

    @pytest.mark.asyncio
    async def test_semgrep_validate_not_found(self):
        """测试 Semgrep 不可用时的验证"""
        tool = SemgrepTool()
        with patch("shutil.which", return_value=None):
            result = await tool.validate()
            assert result is False

    @pytest.mark.asyncio
    async def test_semgrep_run_not_installed(self):
        """测试 Semgrep 未安装时的运行"""
        tool = SemgrepTool()
        with patch("shutil.which", return_value=None):
            result = await tool.run("/path/to/project")
            assert result.success is False
            assert "not installed" in result.error

    def test_semgrep_parse_results(self):
        """测试 Semgrep JSON 输出解析"""
        tool = SemgrepTool()
        json_data = {
            "results": [
                {
                    "check_id": "python.lang.security.audit.eval-use",
                    "path": "test.py",
                    "start": {"line": 10, "col": 5},
                    "end": {"line": 10, "col": 20},
                    "extra": {
                        "message": "eval() is unsafe",
                        "severity": "ERROR",
                        "metadata": {
                            "cwe": ["CWE-95"],
                            "owasp": "A03:2021",
                        },
                    },
                }
            ],
            "errors": [],
        }
        findings = tool._parse_semgrep_results(json_data)
        assert len(findings) == 1
        assert findings[0]["check_id"] == "python.lang.security.audit.eval-use"
        assert findings[0]["path"] == "test.py"
        assert findings[0]["severity"] == "ERROR"
        assert "CWE-95" in findings[0]["metadata"]["cwe"]


class TestNucleiTool:
    """NucleiTool 测试套件"""

    def test_nuclei_tool_initialization(self):
        """测试 NucleiTool 初始化"""
        tool = NucleiTool()
        assert tool.name == "nuclei"
        assert tool._nuclei_path == "nuclei"

    @pytest.mark.asyncio
    async def test_nuclei_validate_not_found(self):
        """测试 Nuclei 不可用时的验证"""
        tool = NucleiTool()
        with patch("shutil.which", return_value=None):
            result = await tool.validate()
            assert result is False

    @pytest.mark.asyncio
    async def test_nuclei_run_not_installed(self):
        """测试 Nuclei 未安装时的运行"""
        tool = NucleiTool()
        with patch("shutil.which", return_value=None):
            result = await tool.run("https://example.com")
            assert result.success is False
            assert "not installed" in result.error

    def test_nuclei_parse_results(self):
        """测试 Nuclei JSONL 输出解析"""
        tool = NucleiTool()
        jsonl_output = """{"template-id": "cve-2021-44228", "info": {"name": "Log4Shell", "severity": "CRITICAL"}, "host": "https://example.com", "matched-at": "https://example.com/api"}
{"template-id": "misconfig", "info": {"name": "Directory Listing", "severity": "MEDIUM"}, "host": "https://example.com", "matched-at": "https://example.com/admin/"}"""
        findings = tool._parse_nuclei_output(jsonl_output)
        assert len(findings) == 2
        assert findings[0]["template_id"] == "cve-2021-44228"
        assert findings[0]["severity"] == "CRITICAL"
        assert findings[1]["template_id"] == "misconfig"
        assert findings[1]["severity"] == "MEDIUM"


class TestTrivyTool:
    """TrivyTool 测试套件"""

    def test_trivy_tool_initialization(self):
        """测试 TrivyTool 初始化"""
        tool = TrivyTool()
        assert tool.name == "trivy"
        assert tool._trivy_path == "trivy"

    @pytest.mark.asyncio
    async def test_trivy_validate_not_found(self):
        """测试 Trivy 不可用时的验证"""
        tool = TrivyTool()
        with patch("shutil.which", return_value=None):
            result = await tool.validate()
            assert result is False

    @pytest.mark.asyncio
    async def test_trivy_run_not_installed(self):
        """测试 Trivy 未安装时的运行"""
        tool = TrivyTool()
        with patch("shutil.which", return_value=None):
            result = await tool.run("alpine:3.14")
            assert result.success is False
            assert "not installed" in result.error

    def test_trivy_parse_results(self):
        """测试 Trivy JSON 输出解析"""
        tool = TrivyTool()
        json_data = {
            "Results": [
                {
                    "Target": "alpine:3.14",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-44228",
                            "PkgName": "log4j",
                            "InstalledVersion": "2.14.0",
                            "FixedVersion": "2.15.0",
                            "Severity": "CRITICAL",
                            "Title": "Log4Shell",
                        }
                    ],
                }
            ]
        }
        vulnerabilities = tool._parse_trivy_results(json_data)
        assert len(vulnerabilities) == 1
        assert vulnerabilities[0]["vuln_id"] == "CVE-2021-44228"
        assert vulnerabilities[0]["pkg_name"] == "log4j"
        assert vulnerabilities[0]["severity"] == "CRITICAL"


class TestBurpTool:
    """BurpTool 测试套件"""

    def test_burp_tool_initialization(self):
        """测试 BurpTool 初始化"""
        tool = BurpTool()
        assert tool.name == "burpsuite"
        assert tool._base_url == "http://127.0.0.1:1337"

    def test_burp_tool_custom_config(self):
        """测试自定义 Burp 配置"""
        tool = BurpTool(base_url="http://localhost:8080", api_key="test-key")
        assert tool._base_url == "http://localhost:8080"
        assert tool._api_key == "test-key"

    @pytest.mark.asyncio
    async def test_burp_validate_not_available(self):
        """测试 Burp API 不可用时的验证"""
        tool = BurpTool()
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            result = await tool.validate()
            assert result is False

    @pytest.mark.asyncio
    async def test_burp_run_not_available(self):
        """测试 Burp API 不可用时的运行"""
        tool = BurpTool()
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            result = await tool.run("https://example.com")
            assert result.success is False
            assert "not available" in result.error


class TestSecurityToolResult:
    """SecurityToolResult 测试套件"""

    def test_result_to_dict(self):
        """测试结果转换为字典"""
        result = SecurityToolResult(
            tool_name="test",
            success=True,
            output="test output",
            error="",
            execution_time_ms=100.5,
        )
        result_dict = result.to_dict()
        assert result_dict["tool_name"] == "test"
        assert result_dict["success"] is True
        assert result_dict["output"] == "test output"
        assert result_dict["execution_time_ms"] == 100.5


class TestBaseSecurityTool:
    """BaseSecurityTool 测试套件"""

    def test_base_tool_is_abstract(self):
        """测试基类是抽象类"""
        with pytest.raises(TypeError):
            BaseSecurityTool()

    def test_concrete_tool_implementation(self):
        """测试具体工具实现"""

        class ConcreteTool(BaseSecurityTool):
            @property
            def name(self) -> str:
                return "concrete"

            async def run(self, target: str, **kwargs) -> SecurityToolResult:
                return SecurityToolResult(tool_name=self.name, success=True)

        tool = ConcreteTool()
        assert tool.name == "concrete"
        result = asyncio.run(tool.run("test"))
        assert result.success is True
