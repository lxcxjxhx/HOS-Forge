"""JavaScript parser using regular expressions (no external dependencies)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from hosforge.ast_analyzer.python_parser import ASTNode, ParseResult


class JavaScriptParser:
    """Parse JavaScript source code into normalized AST nodes via regex."""

    DANGEROUS_FUNCTIONS = {
        "eval", "Function", "setTimeout", "setInterval",
        "document.write", "document.writeln", "innerHTML",
    }

    SECRET_KEYWORDS = {
        "password", "passwd", "secret", "api_key", "apikey", "token",
        "private_key", "auth",
    }

    # Pre-compiled patterns
    _RE_FUNCTION_CALL = re.compile(
        r'(?P<name>[a-zA-Z_$][\w$.]*)\s*\((?P<args>[^)]*)\)',
    )
    _RE_VAR_DECL = re.compile(
        r'(?:var|let|const)\s+(?P<name>\w+)\s*=\s*(?P<value>.+?)[\s;]*$',
        re.MULTILINE,
    )
    _RE_ASSIGNMENT = re.compile(
        r'(?P<name>[\w.]+)\s*=\s*(?P<value>.+?)[\s;]*$',
        re.MULTILINE,
    )
    _RE_IMPORT = re.compile(
        r'''(?:import\s+(?P<name>[\w{},\s*]+)\s+from\s+['"](?P<module>[^'"]+)['"])'''
        r'''|(?:require\s*\(\s*['"](?P<req_module>[^'"]+)['"]\s*\))''',
    )
    _RE_INNERHTML = re.compile(
        r'(?P<target>[\w.]+)\.innerHTML\s*=\s*(?P<value>.+?)[\s;]*$',
        re.MULTILINE,
    )
    _RE_STRING_LITERAL = re.compile(
        r"""(?:"""
        r"""'(?P<single>[^'\\]*(?:\\.[^'\\]*)*)'"""
        r"""|"(?P<double>[^"\\]*(?:\\.[^"\\]*)*)" """
        r""")""",
    )

    def parse(self, source: str) -> ParseResult:
        """Parse JavaScript source and return normalized AST nodes."""
        result = ParseResult(source=source, language="javascript")
        lines = source.split("\n")

        for line_no, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//"):
                continue

            self._extract_function_calls(stripped, line_no, result)
            self._extract_var_declarations(stripped, line_no, result)
            self._extract_innerHTML(stripped, line_no, result)
            self._extract_imports(stripped, line_no, result)

        return result

    def find_dangerous_calls(self, source: str) -> List[ASTNode]:
        """Find calls to dangerous JavaScript functions."""
        result = self.parse(source)
        return [
            n for n in result.nodes
            if n.node_type == "call" and n.name in self.DANGEROUS_FUNCTIONS
        ]

    def find_xss_patterns(self, source: str) -> List[ASTNode]:
        """Find innerHTML assignments and similar XSS patterns."""
        result = self.parse(source)
        return [
            n for n in result.nodes
            if n.node_type == "innerHTML_assignment"
            or (n.node_type == "call" and n.name in {"document.write", "document.writeln"})
        ]

    def find_hardcoded_strings(self, source: str) -> List[ASTNode]:
        """Find variable assignments that look like hardcoded secrets."""
        result = self.parse(source)
        findings: List[ASTNode] = []
        for node in result.nodes:
            if node.node_type != "assignment":
                continue
            name_lower = node.name.lower()
            if any(kw in name_lower for kw in self.SECRET_KEYWORDS):
                findings.append(node)
        return findings

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_function_calls(
        self, line: str, line_no: int, result: ParseResult
    ) -> None:
        for m in self._RE_FUNCTION_CALL.finditer(line):
            name = m.group("name")
            args_raw = m.group("args").strip()
            args = [a.strip().strip("'\"") for a in args_raw.split(",") if a.strip()] if args_raw else []
            result.nodes.append(ASTNode(
                node_type="call",
                name=name,
                line=line_no,
                attributes={"args": args},
            ))

    def _extract_var_declarations(
        self, line: str, line_no: int, result: ParseResult
    ) -> None:
        for m in self._RE_VAR_DECL.finditer(line):
            name = m.group("name")
            value = m.group("value").strip().strip("'\"")
            result.nodes.append(ASTNode(
                node_type="assignment",
                name=name,
                line=line_no,
                value=value,
                attributes={"declaration": True},
            ))

    def _extract_innerHTML(
        self, line: str, line_no: int, result: ParseResult
    ) -> None:
        for m in self._RE_INNERHTML.finditer(line):
            result.nodes.append(ASTNode(
                node_type="innerHTML_assignment",
                name=m.group("target"),
                line=line_no,
                value=m.group("value").strip(),
            ))

    def _extract_imports(
        self, line: str, line_no: int, result: ParseResult
    ) -> None:
        for m in self._RE_IMPORT.finditer(line):
            module = m.group("module") or m.group("req_module") or ""
            result.nodes.append(ASTNode(
                node_type="import",
                name=module,
                line=line_no,
                attributes={"module": module},
            ))
