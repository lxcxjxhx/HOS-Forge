"""Python AST parser using the standard library ``ast`` module."""
from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ASTNode:
    """Normalized representation of an AST node across languages."""

    node_type: str
    name: str = ""
    line: int = 0
    col: int = 0
    value: str = ""
    children: list["ASTNode"] = field(default_factory=list)
    attributes: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    """Result of parsing a source file."""

    source: str
    language: str
    nodes: List[ASTNode] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class PythonASTParser:
    """Parse Python source code into normalized AST nodes."""

    DANGEROUS_FUNCTIONS = {
        "eval", "exec", "os.system", "os.popen", "subprocess.call",
        "subprocess.run", "subprocess.Popen", "subprocess.check_output",
        "compile", "__import__", "input",
    }

    DANGEROUS_IMPORTS = {"os", "subprocess", "shutil", "pickle", "shelve"}

    SECRET_KEYWORDS = {
        "password", "passwd", "secret", "api_key", "apikey", "token",
        "private_key", "auth",
    }

    def parse(self, source: str) -> ParseResult:
        """Parse Python source code and return normalized AST nodes."""
        result = ParseResult(source=source, language="python")
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            result.errors.append(f"SyntaxError: {exc}")
            return result

        for node in ast.walk(tree):
            normalized = self._normalize_node(node)
            if normalized is not None:
                result.nodes.append(normalized)
        return result

    def find_dangerous_calls(self, source: str) -> List[ASTNode]:
        """Find calls to dangerous functions."""
        result = self.parse(source)
        return [
            n for n in result.nodes
            if n.node_type == "call" and n.name in self.DANGEROUS_FUNCTIONS
        ]

    def find_hardcoded_strings(self, source: str) -> List[ASTNode]:
        """Find assignments that look like hardcoded secrets."""
        result = self.parse(source)
        findings: List[ASTNode] = []
        for node in result.nodes:
            if node.node_type != "assignment":
                continue
            name_lower = node.name.lower()
            if any(kw in name_lower for kw in self.SECRET_KEYWORDS):
                findings.append(node)
        return findings

    def find_imports(self, source: str) -> List[ASTNode]:
        """Find all import statements."""
        result = self.parse(source)
        return [n for n in result.nodes if n.node_type == "import"]

    def find_dangerous_imports(self, source: str) -> List[ASTNode]:
        """Find imports of potentially dangerous modules."""
        return [
            n for n in self.find_imports(source)
            if n.name in self.DANGEROUS_IMPORTS
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalize_node(self, node: ast.AST) -> Optional[ASTNode]:
        """Convert a Python AST node to a normalized ASTNode."""
        if isinstance(node, ast.Call):
            return self._normalize_call(node)
        if isinstance(node, ast.Assign):
            return self._normalize_assign(node)
        if isinstance(node, ast.Import):
            return self._normalize_import(node)
        if isinstance(node, ast.ImportFrom):
            return self._normalize_import_from(node)
        if isinstance(node, ast.FunctionDef):
            return ASTNode(
                node_type="function_def",
                name=node.name,
                line=node.lineno,
                col=node.col_offset,
            )
        if isinstance(node, ast.ClassDef):
            return ASTNode(
                node_type="class_def",
                name=node.name,
                line=node.lineno,
                col=node.col_offset,
            )
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return ASTNode(
                node_type="string_literal",
                line=node.lineno,
                col=node.col_offset,
                value=node.value,
            )
        return None

    def _normalize_call(self, node: ast.Call) -> ASTNode:
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            cur = node.func
            while isinstance(cur, ast.Attribute):
                parts.append(cur.attr)
                cur = cur.value
            if isinstance(cur, ast.Name):
                parts.append(cur.id)
            name = ".".join(reversed(parts))

        args = []
        for arg in node.args:
            if isinstance(arg, ast.Constant):
                args.append(str(arg.value))
            elif isinstance(arg, ast.Name):
                args.append(arg.id)

        return ASTNode(
            node_type="call",
            name=name,
            line=node.lineno,
            col=node.col_offset,
            attributes={"args": args},
        )

    def _normalize_assign(self, node: ast.Assign) -> Optional[ASTNode]:
        if not node.targets:
            return None
        target = node.targets[0]
        name = ""
        if isinstance(target, ast.Name):
            name = target.id
        elif isinstance(target, ast.Attribute):
            name = target.attr

        value = ""
        if isinstance(node.value, ast.Constant):
            value = str(node.value.value)

        return ASTNode(
            node_type="assignment",
            name=name,
            line=node.lineno,
            col=node.col_offset,
            value=value,
        )

    def _normalize_import(self, node: ast.Import) -> ASTNode:
        names = [alias.name for alias in node.names]
        return ASTNode(
            node_type="import",
            name=names[0] if names else "",
            line=node.lineno,
            col=node.col_offset,
            attributes={"all_names": names},
        )

    def _normalize_import_from(self, node: ast.ImportFrom) -> ASTNode:
        module = node.module or ""
        names = [alias.name for alias in node.names]
        return ASTNode(
            node_type="import",
            name=module,
            line=node.lineno,
            col=node.col_offset,
            attributes={"all_names": names, "from_module": module},
        )
