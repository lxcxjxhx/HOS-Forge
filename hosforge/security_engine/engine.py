"""Security Engine - Core orchestration layer for vulnerability detection."""

import os
from pathlib import Path
from typing import List, Optional

from hosforge.rule_engine import RuleEngine, RuleParser, RuleMatchResult
from hosforge.security_engine.report import SecurityReport, Finding


class SecurityEngine:
    """
    Core security engine that orchestrates vulnerability detection and analysis.
    
    This engine coordinates:
    - Rule Engine: Pattern-based vulnerability detection
    - Knowledge Base: CVE/CWE information retrieval
    - Future: MCP tools, AST analysis, semantic analysis
    """
    
    def __init__(self, rules_dir: Optional[str] = None):
        """
        Initialize the security engine.
        
        Args:
            rules_dir: Directory containing YAML rule files. If None, uses default rules.
        """
        # Initialize Rule Engine
        if rules_dir is None:
            rules_dir = str(Path(__file__).parent.parent / "rule_engine" / "rules")
        
        parser = RuleParser()
        rules = parser.parse_dir(rules_dir)
        self.rule_engine = RuleEngine(rules)
        
        # Initialize Knowledge Base (optional)
        try:
            self.knowledge_base = KnowledgeBase()
        except Exception:
            # Knowledge base may not be fully initialized yet
            self.knowledge_base = None
    
    def scan_file(self, file_path: str, language: Optional[str] = None) -> SecurityReport:
        """
        Scan a single file for security vulnerabilities.
        
        Args:
            file_path: Path to the file to scan
            language: Programming language (auto-detected if None)
            
        Returns:
            SecurityReport with findings
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Auto-detect language from file extension
        if language is None:
            language = self._detect_language(file_path)
        
        # Read file content
        with file_path.open("r", encoding="utf-8") as f:
            code = f.read()
        
        # Run rule engine
        results = self.rule_engine.evaluate(code, language)
        
        # Convert to findings
        findings = []
        for result in results:
            if result.matched:
                finding = self._result_to_finding(result, file_path, code)
                findings.append(finding)
        
        return SecurityReport(
            file_path=str(file_path),
            language=language,
            findings=findings,
        )
    
    def scan_directory(
        self,
        dir_path: str,
        language: Optional[str] = None,
        recursive: bool = True,
    ) -> SecurityReport:
        """
        Scan a directory for security vulnerabilities.
        
        Args:
            dir_path: Directory to scan
            language: Filter by language (scans all if None)
            recursive: Scan subdirectories recursively
            
        Returns:
            SecurityReport with all findings
        """
        dir_path = Path(dir_path)
        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {dir_path}")
        
        all_findings = []
        
        # Collect files to scan
        pattern = "**/*" if recursive else "*"
        for file_path in dir_path.glob(pattern):
            if not file_path.is_file():
                continue
            
            # Skip non-code files
            if not self._is_code_file(file_path):
                continue
            
            # Filter by language if specified
            if language and self._detect_language(file_path) != language:
                continue
            
            # Scan file
            try:
                report = self.scan_file(str(file_path), language)
                all_findings.extend(report.findings)
            except Exception as e:
                # Log error but continue scanning
                print(f"Error scanning {file_path}: {e}")
        
        return SecurityReport(
            file_path=str(dir_path),
            language=language or "mixed",
            findings=all_findings,
        )
    
    def scan_code(self, code: str, language: str) -> SecurityReport:
        """
        Scan code string for security vulnerabilities.
        
        Args:
            code: Source code to scan
            language: Programming language
            
        Returns:
            SecurityReport with findings
        """
        results = self.rule_engine.evaluate(code, language)
        
        findings = []
        for result in results:
            if result.matched:
                finding = self._result_to_finding(result, None, code)
                findings.append(finding)
        
        return SecurityReport(
            file_path="<inline>",
            language=language,
            findings=findings,
        )
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".go": "go",
            ".rs": "rust",
            ".php": "php",
            ".rb": "ruby",
            ".cs": "csharp",
            ".cpp": "cpp",
            ".c": "cpp",
            ".h": "cpp",
        }
        return ext_map.get(file_path.suffix.lower(), "unknown")
    
    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file is a code file that should be scanned."""
        code_extensions = {
            ".py", ".js", ".ts", ".java", ".go", ".rs", ".php", ".rb",
            ".cs", ".cpp", ".c", ".h", ".jsx", ".tsx",
        }
        return file_path.suffix.lower() in code_extensions
    
    def _result_to_finding(
        self,
        result: RuleMatchResult,
        file_path: Optional[Path],
        code: str,
    ) -> Finding:
        """Convert a RuleMatchResult to a Finding."""
        # Extract code context (5 lines before and after)
        code_context = None
        if result.location and result.location.startswith("line "):
            try:
                line_num = int(result.location.split()[1])
                lines = code.split("\n")
                start = max(0, line_num - 6)
                end = min(len(lines), line_num + 5)
                code_context = "\n".join(lines[start:end])
            except (ValueError, IndexError):
                pass
        
        # Get CWE description from knowledge base
        cwe_description = None
        if self.knowledge_base and result.cwe_ids:
            try:
                # Try to get CWE info (may not be available)
                cwe_description = f"See {result.cwe_ids[0]} for details"
            except Exception:
                pass
        
        return Finding(
            rule_name=result.rule_name,
            severity=result.severity,
            location=result.location,
            description=result.description,
            remediation=result.remediation,
            cwe_ids=result.cwe_ids,
            owasp_category=result.owasp_category,
            code_context=code_context,
            file_path=str(file_path) if file_path else None,
        )
