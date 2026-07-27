"""Lightweight taint analysis for tracking user-controlled data flow."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from hosforge.ast_analyzer.python_parser import ASTNode, ParseResult


@dataclass
class TaintedVariable:
    """A variable that carries tainted (user-controlled) data."""

    name: str
    source: str  # e.g. "request.params", "input()"
    line: int = 0


@dataclass
class TaintFinding:
    """A finding where tainted data reaches a dangerous sink."""

    variable: str
    source: str
    sink: str
    line: int = 0
    file: str = ""
    severity: str = "high"
    description: str = ""


# ------------------------------------------------------------------
# Default configuration
# ------------------------------------------------------------------

DEFAULT_SOURCES = {
    # Python
    "request.args", "request.params", "request.form", "request.data",
    "request.values", "request.json", "request.query_string",
    "input(", "sys.argv", "sys.stdin",
    # JavaScript
    "location.search", "location.hash", "location.href",
    "document.URL", "document.referrer",
    "req.params", "req.query", "req.body", "req.headers",
}

DEFAULT_SINKS = {
    # Python
    "eval", "exec", "os.system", "os.popen",
    "subprocess.call", "subprocess.run", "subprocess.Popen",
    "cursor.execute", "execute",
    "open", "render_template_string",
    # JavaScript
    "innerHTML", "document.write", "document.writeln",
    "eval", "Function", "setTimeout", "setInterval",
}

DEFAULT_SANITIZERS = {
    # Python
    "escape", "html.escape", "markupsafe.escape",
    "shlex.quote", "urllib.parse.quote",
    "parameterize", "sanitize",
    # JavaScript
    "escapeHTML", "sanitize", "DOMPurify.sanitize",
    "encodeURIComponent", "encodeURI",
    "escape", "he.encode",
}


class TaintAnalyzer:
    """Track tainted data from sources through assignments to sinks."""

    def __init__(
        self,
        sources: Optional[Set[str]] = None,
        sinks: Optional[Set[str]] = None,
        sanitizers: Optional[Set[str]] = None,
    ) -> None:
        self.sources = sources or DEFAULT_SOURCES
        self.sinks = sinks or DEFAULT_SINKS
        self.sanitizers = sanitizers or DEFAULT_SANITIZERS

    def analyze(
        self, parse_result: ParseResult, file_path: str = ""
    ) -> List[TaintFinding]:
        """Run taint analysis on a parse result."""
        tainted: Dict[str, TaintedVariable] = {}
        findings: List[TaintFinding] = []

        for node in parse_result.nodes:
            # 1. Detect taint sources
            self._check_source(node, tainted)

            # 2. Propagate taint through assignments
            self._propagate(node, tainted)

            # 3. Check if tainted data reaches a sink
            new_findings = self._check_sink(node, tainted, file_path)
            findings.extend(new_findings)

        return findings

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_source(self, node: ASTNode, tainted: Dict[str, TaintedVariable]) -> None:
        """Mark variables as tainted if they originate from a source."""
        if node.node_type == "call":
            for src in self.sources:
                if src.endswith("("):
                    # Function-call style source like "input("
                    if node.name == src.rstrip("("):
                        # The return value is tainted but we don't know
                        # the variable name here; propagation handles it.
                        tainted.setdefault("__return__", TaintedVariable(
                            name="__return__", source=src, line=node.line,
                        ))
                elif node.name == src or node.name.startswith(src + "."):
                    tainted.setdefault("__return__", TaintedVariable(
                        name="__return__", source=src, line=node.line,
                    ))

        if node.node_type == "assignment":
            # Check if the RHS references a source
            value_lower = node.value.lower()
            for src in self.sources:
                src_clean = src.rstrip("(")
                if src_clean in value_lower:
                    tainted[node.name] = TaintedVariable(
                        name=node.name, source=src, line=node.line,
                    )

    def _propagate(self, node: ASTNode, tainted: Dict[str, TaintedVariable]) -> None:
        """Propagate taint through variable assignments."""
        if node.node_type != "assignment":
            return

        # If the assignment value references __return__ taint, capture it into
        # the named variable and clear the transient __return__ marker so it
        # doesn't trigger on every subsequent sink.
        if "__return__" in tainted and "__return__" in node.value:
            tv = tainted.pop("__return__")
            if not self._is_sanitized(node):
                tainted[node.name] = TaintedVariable(
                    name=node.name, source=tv.source, line=node.line,
                )
            return

        # If the value references a tainted variable, the target is tainted too
        for tname, tvar in list(tainted.items()):
            if tname == "__return__":
                continue
            if tname in node.value:
                # Check if sanitized
                if not self._is_sanitized(node):
                    tainted[node.name] = TaintedVariable(
                        name=node.name, source=tvar.source, line=node.line,
                    )

    def _check_sink(
        self,
        node: ASTNode,
        tainted: Dict[str, TaintedVariable],
        file_path: str,
    ) -> List[TaintFinding]:
        """Check if tainted data flows into a dangerous sink."""
        findings: List[TaintFinding] = []

        if node.node_type != "call":
            return findings

        # Check if the function itself is a sink
        is_sink = any(node.name == s or node.name.startswith(s + ".") for s in self.sinks)
        if not is_sink:
            return findings

        # Check if any argument is tainted
        args = node.attributes.get("args", [])
        for arg in args:
            if arg in tainted:
                tv = tainted[arg]
                findings.append(TaintFinding(
                    variable=arg,
                    source=tv.source,
                    sink=node.name,
                    line=node.line,
                    file=file_path,
                    description=(
                        f"Tainted variable '{arg}' (from {tv.source}) "
                        f"flows into dangerous function '{node.name}'"
                    ),
                ))

        return findings

    def _is_sanitized(self, node: ASTNode) -> bool:
        """Check if the assignment value passes through a sanitizer."""
        for san in self.sanitizers:
            if san in node.value:
                return True
        return False
