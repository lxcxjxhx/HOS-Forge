"""
HOS-Forge Security Tools Unit Tests

测试所有安全工具的实现：
- NmapTool: 网络扫描
- SemgrepTool: SAST 代码分析
- NucleiTool: 漏洞扫描
- TrivyTool: 容器/文件系统扫描
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hosforge.security_tools import (
    BaseSecurityTool,
    NmapTool,
    NucleiTool,
    SecurityToolResult,
    SemgrepTool,
    TrivyTool,
)


# ============================================================================
# BaseSecurityTool Tests
# ============================================================================


class TestBaseSecurityTool:
    """测试安全工具基类"""

    def test_security_tool_result_dataclass(self):
        """测试 SecurityToolResult 数据结构"""
        result = SecurityToolResult(
            tool_name="test_tool",
            success=True,
            output="test output",
            error="",
            raw_data={"key": "value"},
            execution_time_ms=100.5,
        )

        assert result.tool_name == "test_tool"
        assert result.success is True
        assert result.output == "test output"
        assert result.error == ""
        assert result.raw_data == {"key": "value"}
        assert result.execution_time_ms == 100.5

    def test_security_tool_result_to_dict(self):
        """测试 SecurityToolResult.to_dict() 方法"""
        result = SecurityToolResult(
            tool_name="test_tool",
            success=True,
            output="output",
            error="error",
            execution_time_ms=50.0,
        )

        result_dict = result.to_dict()
        assert result_dict["tool_name"] == "test_tool"
        assert result_dict["success"] is True
        assert result_dict["output"] == "output"
        assert result_dict["error"] == "error"
        assert result_dict["execution_time_ms"] == 50.0


# ============================================================================
# NmapTool Tests
# ============================================================================


class TestNmapTool:
    """测试 Nmap 网络扫描工具"""

    @pytest.fixture
    def nmap_tool(self):
        """创建 NmapTool 实例"""
        return NmapTool()

    def test_nmap_tool_name(self, nmap_tool):
        """测试工具名称"""
        assert nmap_tool.name == "nmap"

    @pytest.mark.asyncio
    async def test_nmap_validate_not_found(self, nmap_tool):
        """测试 Nmap 不可用时的验证"""
        with patch("shutil.which", return_value=None):
            result = await nmap_tool.validate()
            assert result is False

    @pytest.mark.asyncio
    async def test_nmap_validate_found(self, nmap_tool):
        """测试 Nmap 可用时的验证"""
        with patch("shutil.which", return_value="/usr/bin/nmap"):
            result = await nmap_tool.validate()
            assert result is True

    @pytest.mark.asyncio
    async def test_nmap_run_not_installed(self, nmap_tool):
        """测试 Nmap 未安装时的执行"""
        with patch("shutil.which", return_value=None):
            result = await nmap_tool.run("192.168.1.1")
            assert result.success is False
            assert "not installed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_nmap_run_success(self, nmap_tool):
        """测试 Nmap 成功执行"""
        mock_xml_output = b"""<?xml version="1.0"?>
<nmaprun>
<host>
<status state="up"/>
<ports>
<port protocol="tcp" portid="22">
<state state="open"/>
<service name="ssh"/>
</port>
</ports>
</host>
</nmaprun>"""

        with (
            patch("shutil.which", return_value="/usr/bin/nmap"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_xml_output, b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await nmap_tool.run("192.168.1.1", ports="22")

            assert result.success is True
            assert result.tool_name == "nmap"
            assert "open_ports" in result.raw_data
            assert 22 in result.raw_data["open_ports"]

    @pytest.mark.asyncio
    async def test_nmap_run_timeout(self, nmap_tool):
        """测试 Nmap 执行超时"""
        with (
            patch("shutil.which", return_value="/usr/bin/nmap"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.side_effect = asyncio.TimeoutError()
            mock_process.kill = MagicMock()
            mock_exec.return_value = mock_process

            result = await nmap_tool.run("192.168.1.1", timeout=1)

            assert result.success is False
            assert "timed out" in result.error.lower()


# ============================================================================
# SemgrepTool Tests
# ============================================================================


class TestSemgrepTool:
    """测试 Semgrep SAST 工具"""

    @pytest.fixture
    def semgrep_tool(self):
        """创建 SemgrepTool 实例"""
        return SemgrepTool()

    def test_semgrep_tool_name(self, semgrep_tool):
        """测试工具名称"""
        assert semgrep_tool.name == "semgrep"

    @pytest.mark.asyncio
    async def test_semgrep_validate_not_found(self, semgrep_tool):
        """测试 Semgrep 不可用时的验证"""
        with patch("shutil.which", return_value=None):
            result = await semgrep_tool.validate()
            assert result is False

    @pytest.mark.asyncio
    async def test_semgrep_validate_found(self, semgrep_tool):
        """测试 Semgrep 可用时的验证"""
        with patch("shutil.which", return_value="/usr/bin/semgrep"):
            result = await semgrep_tool.validate()
            assert result is True

    @pytest.mark.asyncio
    async def test_semgrep_run_not_installed(self, semgrep_tool):
        """测试 Semgrep 未安装时的执行"""
        with patch("shutil.which", return_value=None):
            result = await semgrep_tool.run("/path/to/code")
            assert result.success is False
            assert "not installed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_semgrep_run_success(self, semgrep_tool):
        """测试 Semgrep 成功执行"""
        mock_json_output = b"""{
            "results": [
                {
                    "check_id": "python.lang.security.audit.eval",
                    "path": "test.py",
                    "start": {"line": 10, "col": 5},
                    "end": {"line": 10, "col": 20},
                    "extra": {
                        "message": "Use of eval detected",
                        "severity": "WARNING",
                        "metadata": {
                            "cwe": ["CWE-95"],
                            "owasp": "A03:2021"
                        }
                    }
                }
            ],
            "errors": []
        }"""

        with (
            patch("shutil.which", return_value="/usr/bin/semgrep"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_json_output, b"")
            mock_process.returncode = 1  # Semgrep 返回 1 表示发现漏洞
            mock_exec.return_value = mock_process

            result = await semgrep_tool.run("/path/to/code")

            assert result.success is True
            assert result.tool_name == "semgrep"
            assert "findings" in result.raw_data
            assert len(result.raw_data["findings"]) == 1
            assert result.raw_data["findings"][0]["check_id"] == "python.lang.security.audit.eval"

    @pytest.mark.asyncio
    async def test_semgrep_run_with_rules(self, semgrep_tool):
        """测试 Semgrep 使用自定义规则"""
        mock_json_output = b'{"results": [], "errors": []}'

        with (
            patch("shutil.which", return_value="/usr/bin/semgrep"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_json_output, b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await semgrep_tool.run(
                "/path/to/code",
                rules=["p/security-audit"],
                languages=["python", "javascript"],
            )

            assert result.success is True
            # 验证命令构建
            call_args = mock_exec.call_args[0]
            assert "--config" in call_args
            assert "p/security-audit" in call_args


# ============================================================================
# NucleiTool Tests
# ============================================================================


class TestNucleiTool:
    """测试 Nuclei 漏洞扫描工具"""

    @pytest.fixture
    def nuclei_tool(self):
        """创建 NucleiTool 实例"""
        return NucleiTool()

    def test_nuclei_tool_name(self, nuclei_tool):
        """测试工具名称"""
        assert nuclei_tool.name == "nuclei"

    @pytest.mark.asyncio
    async def test_nuclei_validate_not_found(self, nuclei_tool):
        """测试 Nuclei 不可用时的验证"""
        with patch("shutil.which", return_value=None):
            result = await nuclei_tool.validate()
            assert result is False

    @pytest.mark.asyncio
    async def test_nuclei_validate_found(self, nuclei_tool):
        """测试 Nuclei 可用时的验证"""
        with patch("shutil.which", return_value="/usr/bin/nuclei"):
            result = await nuclei_tool.validate()
            assert result is True

    @pytest.mark.asyncio
    async def test_nuclei_run_not_installed(self, nuclei_tool):
        """测试 Nuclei 未安装时的执行"""
        with patch("shutil.which", return_value=None):
            result = await nuclei_tool.run("https://example.com")
            assert result.success is False
            assert "not installed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_nuclei_run_success(self, nuclei_tool):
        """测试 Nuclei 成功执行"""
        mock_jsonl_output = b"""{"template-id":"cve-2021-44228","info":{"name":"Log4Shell","severity":"critical","classification":{"cve-id":["CVE-2021-44228"]}},"host":"https://example.com","type":"http"}
"""

        with (
            patch("shutil.which", return_value="/usr/bin/nuclei"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_jsonl_output, b"")
            mock_process.returncode = 1  # Nuclei 返回 1 表示发现漏洞
            mock_exec.return_value = mock_process

            result = await nuclei_tool.run("https://example.com")

            assert result.success is True
            assert result.tool_name == "nuclei"
            assert "findings" in result.raw_data
            assert len(result.raw_data["findings"]) == 1
            assert result.raw_data["findings"][0]["template_id"] == "cve-2021-44228"

    @pytest.mark.asyncio
    async def test_nuclei_run_with_tags(self, nuclei_tool):
        """测试 Nuclei 使用标签过滤"""
        mock_jsonl_output = b'{"template-id":"test","info":{"name":"Test","severity":"info"},"host":"https://example.com"}\n'

        with (
            patch("shutil.which", return_value="/usr/bin/nuclei"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_jsonl_output, b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await nuclei_tool.run(
                "https://example.com",
                tags=["cve", "misconfig"],
                severity="high",
            )

            assert result.success is True
            # 验证命令构建
            call_args = mock_exec.call_args[0]
            assert "-tags" in call_args
            assert "-severity" in call_args


# ============================================================================
# TrivyTool Tests
# ============================================================================


class TestTrivyTool:
    """测试 Trivy 容器/文件系统扫描工具"""

    @pytest.fixture
    def trivy_tool(self):
        """创建 TrivyTool 实例"""
        return TrivyTool()

    def test_trivy_tool_name(self, trivy_tool):
        """测试工具名称"""
        assert trivy_tool.name == "trivy"

    @pytest.mark.asyncio
    async def test_trivy_validate_not_found(self, trivy_tool):
        """测试 Trivy 不可用时的验证"""
        with patch("shutil.which", return_value=None):
            result = await trivy_tool.validate()
            assert result is False

    @pytest.mark.asyncio
    async def test_trivy_validate_found(self, trivy_tool):
        """测试 Trivy 可用时的验证"""
        with patch("shutil.which", return_value="/usr/bin/trivy"):
            result = await trivy_tool.validate()
            assert result is True

    @pytest.mark.asyncio
    async def test_trivy_run_not_installed(self, trivy_tool):
        """测试 Trivy 未安装时的执行"""
        with patch("shutil.which", return_value=None):
            result = await trivy_tool.run("nginx:latest")
            assert result.success is False
            assert "not installed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_trivy_run_image_success(self, trivy_tool):
        """测试 Trivy 镜像扫描成功执行"""
        mock_json_output = b"""{
            "Results": [
                {
                    "Target": "nginx:latest (debian 11.2)",
                    "Class": "os-pkgs",
                    "Type": "debian",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2022-1234",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.1.1k-1",
                            "FixedVersion": "1.1.1l-1",
                            "Severity": "HIGH",
                            "Title": "OpenSSL vulnerability",
                            "Description": "Buffer overflow in OpenSSL",
                            "PrimaryURL": "https://avd.aquasec.com/nvd/cve-2022-1234"
                        }
                    ]
                }
            ]
        }"""

        with (
            patch("shutil.which", return_value="/usr/bin/trivy"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_json_output, b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await trivy_tool.run("nginx:latest", scan_type="image")

            assert result.success is True
            assert result.tool_name == "trivy"
            assert "findings" in result.raw_data
            assert len(result.raw_data["findings"]) == 1
            assert result.raw_data["findings"][0]["vuln_id"] == "CVE-2022-1234"
            assert result.raw_data["findings"][0]["pkg_name"] == "openssl"

    @pytest.mark.asyncio
    async def test_trivy_run_fs_success(self, trivy_tool):
        """测试 Trivy 文件系统扫描成功执行"""
        mock_json_output = b"""{
            "Results": [
                {
                    "Target": "package-lock.json",
                    "Class": "lang-pkgs",
                    "Type": "npm",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2022-5678",
                            "PkgName": "lodash",
                            "InstalledVersion": "4.17.20",
                            "FixedVersion": "4.17.21",
                            "Severity": "CRITICAL"
                        }
                    ]
                }
            ]
        }"""

        with (
            patch("shutil.which", return_value="/usr/bin/trivy"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_json_output, b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await trivy_tool.run("/path/to/project", scan_type="fs")

            assert result.success is True
            assert "findings" in result.raw_data
            assert len(result.raw_data["findings"]) == 1

    @pytest.mark.asyncio
    async def test_trivy_run_with_severity_filter(self, trivy_tool):
        """测试 Trivy 使用严重级别过滤"""
        mock_json_output = b'{"Results": []}'

        with (
            patch("shutil.which", return_value="/usr/bin/trivy"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_json_output, b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await trivy_tool.run(
                "nginx:latest",
                severity="HIGH,CRITICAL",
                ignore_unfixed=True,
            )

            assert result.success is True
            # 验证命令构建
            call_args = mock_exec.call_args[0]
            assert "--severity" in call_args
            assert "HIGH,CRITICAL" in call_args
            assert "--ignore-unfixed" in call_args

    @pytest.mark.asyncio
    async def test_trivy_parse_misconfigurations(self, trivy_tool):
        """测试 Trivy 解析配置问题"""
        mock_json_output = b"""{
            "Results": [
                {
                    "Target": "Dockerfile",
                    "Class": "config",
                    "Type": "dockerfile",
                    "Misconfigurations": [
                        {
                            "ID": "DS001",
                            "Title": "Missing HEALTHCHECK instruction",
                            "Description": "Add HEALTHCHECK to Dockerfile",
                            "Severity": "MEDIUM"
                        }
                    ]
                }
            ]
        }"""

        with (
            patch("shutil.which", return_value="/usr/bin/trivy"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_json_output, b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await trivy_tool.run(".", scan_type="config")

            assert result.success is True
            assert "findings" in result.raw_data
            assert len(result.raw_data["findings"]) == 1
            assert result.raw_data["findings"][0]["vuln_id"] == "DS001"

    @pytest.mark.asyncio
    async def test_trivy_parse_secrets(self, trivy_tool):
        """测试 Trivy 解析密钥泄露"""
        mock_json_output = b"""{
            "Results": [
                {
                    "Target": "config.py",
                    "Class": "secret",
                    "Secrets": [
                        {
                            "RuleID": "aws-access-key-id",
                            "Title": "AWS Access Key ID",
                            "Match": "AKIAIOSFODNN7EXAMPLE",
                            "Severity": "CRITICAL",
                            "StartLine": 10,
                            "EndLine": 10
                        }
                    ]
                }
            ]
        }"""

        with (
            patch("shutil.which", return_value="/usr/bin/trivy"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (mock_json_output, b"")
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await trivy_tool.run("/path/to/project", scan_type="fs")

            assert result.success is True
            assert "findings" in result.raw_data
            assert len(result.raw_data["findings"]) == 1
            assert result.raw_data["findings"][0]["vuln_id"] == "aws-access-key-id"


# ============================================================================
# Integration Tests
# ============================================================================


class TestSecurityToolsIntegration:
    """安全工具集成测试"""

    @pytest.mark.asyncio
    async def test_all_tools_have_consistent_interface(self):
        """测试所有工具具有一致的接口"""
        tools = [
            NmapTool(),
            SemgrepTool(),
            NucleiTool(),
            TrivyTool(),
        ]

        for tool in tools:
            # 验证工具名称
            assert isinstance(tool.name, str)
            assert len(tool.name) > 0

            # 验证 validate 方法存在
            assert hasattr(tool, "validate")
            assert callable(getattr(tool, "validate"))

            # 验证 run 方法存在
            assert hasattr(tool, "run")
            assert callable(getattr(tool, "run"))

    @pytest.mark.asyncio
    async def test_all_tools_return_security_tool_result(self):
        """测试所有工具返回 SecurityToolResult"""
        tools = [
            NmapTool(),
            SemgrepTool(),
            NucleiTool(),
            TrivyTool(),
        ]

        with patch("shutil.which", return_value=None):
            for tool in tools:
                result = await tool.run("test-target")
                assert isinstance(result, SecurityToolResult)
                assert result.tool_name == tool.name
                assert result.success is False  # 工具未安装时应返回失败
