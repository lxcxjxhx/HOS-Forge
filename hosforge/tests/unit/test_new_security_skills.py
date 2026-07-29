"""Trivy 和 CodeQL 安全 Skill 单元测试。"""

import json
from unittest.mock import MagicMock, patch

import pytest

from hosforge.skills.security.codeql_skill import CodeQLScanSkill
from hosforge.skills.security.trivy_skill import TrivyScanSkill


class TestTrivyScanSkill:
    """测试 TrivyScanSkill。"""

    def test_skill_initialization(self):
        """测试 TrivyScanSkill 初始化。"""
        skill = TrivyScanSkill()
        assert skill.name == "trivy_scan"
        assert "target" in skill.parameters["required"]
        assert "scan_type" in skill.parameters["properties"]
        assert "severity" in skill.parameters["properties"]

    def test_execute_success(self):
        """测试 trivy 扫描成功执行。"""
        trivy_output = {
            "Results": [
                {
                    "Target": "alpine:3.14",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-12345",
                            "PkgName": "libssl",
                            "Severity": "HIGH",
                        },
                        {
                            "VulnerabilityID": "CVE-2021-67890",
                            "PkgName": "zlib",
                            "Severity": "MEDIUM",
                        },
                    ],
                }
            ]
        }

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps(trivy_output)
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            skill = TrivyScanSkill()
            result = skill.execute(target="alpine:3.14")

            assert result["total"] == 2
            assert result["target"] == "alpine:3.14"
            assert result["scan_type"] == "image"
            assert len(result["vulnerabilities"]) == 2
            assert result["vulnerabilities"][0]["VulnerabilityID"] == "CVE-2021-12345"

            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "trivy" in cmd
            assert "image" in cmd
            assert "--format" in cmd
            assert "json" in cmd

    def test_execute_with_scan_type(self):
        """测试指定扫描类型。"""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"Results": []})
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            skill = TrivyScanSkill()
            result = skill.execute(target="./src", scan_type="fs")

            assert result["scan_type"] == "fs"
            cmd = mock_run.call_args[0][0]
            assert "fs" in cmd

    def test_execute_with_severity(self):
        """测试按严重级别过滤。"""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"Results": []})
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            skill = TrivyScanSkill()
            skill.execute(target="nginx:latest", severity="HIGH,CRITICAL")

            cmd = mock_run.call_args[0][0]
            assert "--severity" in cmd
            assert "HIGH,CRITICAL" in cmd

    def test_execute_command_not_found(self):
        """测试 trivy 命令不存在。"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            skill = TrivyScanSkill()
            with pytest.raises(FileNotFoundError, match="trivy 命令未找到"):
                skill.execute(target="test:latest")

    def test_execute_invalid_json(self):
        """测试无效 JSON 输出。"""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "not valid json"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc):
            skill = TrivyScanSkill()
            with pytest.raises(ValueError, match="无法解析 trivy JSON 输出"):
                skill.execute(target="test:latest")

    def test_execute_empty_results(self):
        """测试无漏洞结果。"""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"Results": []})
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc):
            skill = TrivyScanSkill()
            result = skill.execute(target="clean-image:latest")

            assert result["total"] == 0
            assert result["vulnerabilities"] == []


class TestCodeQLScanSkill:
    """测试 CodeQLScanSkill。"""

    def test_skill_initialization(self):
        """测试 CodeQLScanSkill 初始化。"""
        skill = CodeQLScanSkill()
        assert skill.name == "codeql_scan"
        assert "database" in skill.parameters["required"]
        assert "query_suite" in skill.parameters["properties"]
        assert "language" in skill.parameters["properties"]

    def test_execute_success(self):
        """测试 codeql 分析成功执行。"""
        sarif_output = {
            "runs": [
                {
                    "tool": {"driver": {"name": "CodeQL"}},
                    "results": [
                        {
                            "ruleId": "js/sql-injection",
                            "message": {"text": "SQL injection vulnerability"},
                            "level": "error",
                            "locations": [
                                {
                                    "physicalLocation": {
                                        "artifactLocation": {"uri": "src/app.js"},
                                        "region": {"startLine": 42},
                                    }
                                }
                            ],
                        },
                        {
                            "ruleId": "js/xss",
                            "message": {"text": "Cross-site scripting vulnerability"},
                            "level": "warning",
                            "locations": [],
                        },
                    ],
                }
            ]
        }

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps(sarif_output)
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            skill = CodeQLScanSkill()
            result = skill.execute(database="/path/to/db")

            assert result["total"] == 2
            assert result["database"] == "/path/to/db"
            assert len(result["alerts"]) == 2
            assert result["alerts"][0]["rule_id"] == "js/sql-injection"
            assert result["alerts"][0]["level"] == "error"
            assert result["alerts"][1]["rule_id"] == "js/xss"

            mock_run.assert_called_once()
            cmd = mock_run.call_args[0][0]
            assert "codeql" in cmd
            assert "database" in cmd
            assert "analyze" in cmd

    def test_execute_with_query_suite(self):
        """测试指定查询套件。"""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"runs": [{"results": []}]})
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            skill = CodeQLScanSkill()
            skill.execute(database="/path/to/db", query_suite="security-and-quality")

            cmd = mock_run.call_args[0][0]
            assert "security-and-quality" in cmd

    def test_execute_with_language(self):
        """测试指定语言。"""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = json.dumps({"runs": [{"results": []}]})
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            skill = CodeQLScanSkill()
            skill.execute(database="/path/to/db", language="python")

            cmd = mock_run.call_args[0][0]
            assert "python-security-extended" in cmd

    def test_execute_command_not_found(self):
        """测试 codeql 命令不存在。"""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            skill = CodeQLScanSkill()
            with pytest.raises(FileNotFoundError, match="codeql 命令未找到"):
                skill.execute(database="/path/to/db")

    def test_execute_invalid_sarif(self):
        """测试无效 SARIF 输出。"""
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "not valid sarif"
        mock_proc.stderr = ""

        with patch("subprocess.run", return_value=mock_proc):
            skill = CodeQLScanSkill()
            with pytest.raises(ValueError, match="无法解析 CodeQL SARIF 输出"):
                skill.execute(database="/path/to/db")
