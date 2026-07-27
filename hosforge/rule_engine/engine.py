"""Rule engine for evaluating security rules against code."""
import ast
import re
from typing import List

from hosforge.rule_engine.schema import (
    LogicOperator,
    MatchLocation,
    PatternType,
    RuleMatchResult,
    SecurityRule,
)


class RuleEngine:
    """Engine for evaluating security rules against code."""

    def __init__(self, rules: List[SecurityRule]):
        """Initialize with a list of security rules."""
        self.rules = rules

    def evaluate(self, code: str, language: str) -> List[RuleMatchResult]:
        """Evaluate all rules against the given code."""
        results = []
        for rule in self.rules:
            result = self._evaluate_rule(rule, code, language)
            results.append(result)
        return results

    def _evaluate_rule(self, rule: SecurityRule, code: str, language: str) -> RuleMatchResult:
        """Evaluate a single rule against code."""
        pattern_results = []

        for pattern in rule.patterns:
            if pattern.language != language:
                continue

            matched = False
            location = None

            if pattern.type == PatternType.REGEX:
                matched, location = self._match_regex(pattern.pattern, code)
            elif pattern.type == PatternType.AST_MATCH:
                matched, location = self._match_ast(pattern.pattern, code, language)
            elif pattern.type == PatternType.TAINT_FLOW:
                matched, location = self._match_taint_flow(pattern, code, language)
            elif pattern.type == PatternType.SEMANTIC:
                matched, location = self._match_semantic(pattern.pattern, code, language)

            pattern_results.append((matched, location, pattern.pattern))

        # Apply logic operator
        if rule.logic_operator == LogicOperator.AND:
            matched = all(r[0] for r in pattern_results) if pattern_results else False
        elif rule.logic_operator == LogicOperator.OR:
            matched = any(r[0] for r in pattern_results) if pattern_results else False
        elif rule.logic_operator == LogicOperator.NOT:
            matched = not any(r[0] for r in pattern_results) if pattern_results else False
        else:
            matched = any(r[0] for r in pattern_results) if pattern_results else False

        # Find first matched location
        location = None
        matched_pattern = None
        for m, loc, pat in pattern_results:
            if m:
                location = loc
                matched_pattern = pat
                break

        # Extract CWE IDs and OWASP category from metadata
        cwe_ids = []
        owasp_category = None
        if rule.metadata:
            cwe = rule.metadata.get("cwe")
            if cwe:
                cwe_ids = [cwe] if isinstance(cwe, str) else cwe
            owasp_category = rule.metadata.get("owasp")

        return RuleMatchResult(
            rule_name=rule.name,
            matched=matched,
            location=location,
            severity=rule.severity if matched else None,
            description=rule.metadata.get("description", ""),
            remediation=rule.remediation if matched else None,
            matched_pattern=matched_pattern,
            cwe_ids=cwe_ids,
            owasp_category=owasp_category,
        )

    def _match_regex(self, pattern: str, code: str) -> tuple[bool, str | None]:
        """Match code against regex pattern."""
        try:
            match = re.search(pattern, code, re.MULTILINE)
            if match:
                line_num = code[:match.start()].count('\n') + 1
                return True, f"line {line_num}"
        except re.error:
            pass
        return False, None

    def _match_ast(self, pattern: str, code: str, language: str) -> tuple[bool, str | None]:
        """Match code against AST pattern (Python only for now)."""
        if language != "python":
            return False, None

        try:
            tree = ast.parse(code)
            # Simple AST matching - check for specific patterns
            # This is a simplified implementation
            if "exec(" in pattern or "eval(" in pattern:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if node.func.id in pattern:
                                return True, f"line {node.lineno}"
        except SyntaxError:
            pass
        return False, None

    def _match_taint_flow(self, pattern, code: str, language: str) -> tuple[bool, str | None]:
        """Match taint flow pattern - detect data flow from source to sink."""
        if language != "python":
            return False, None

        try:
            tree = ast.parse(code)
            
            # Find taint sources (user input)
            sources = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for common input sources
                    if isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['get', 'post', 'form', 'args', 'data']:
                            sources.append(node.lineno)
                    elif isinstance(node.func, ast.Name):
                        if node.func.id in ['input', 'request']:
                            sources.append(node.lineno)
            
            # Find taint sinks (dangerous operations)
            sinks = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['exec', 'eval']:
                            sinks.append(node.lineno)
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in ['system', 'popen', 'execute', 'query', 'run']:
                            sinks.append(node.lineno)
            
            # Check if there's a path from source to sink
            if sources and sinks:
                # Simple check: if any source comes before any sink
                for source_line in sources:
                    for sink_line in sinks:
                        if source_line < sink_line:
                            return True, f"line {sink_line}"
            
        except SyntaxError:
            pass
        return False, None

    def _match_semantic(self, pattern: str, code: str, language: str) -> tuple[bool, str | None]:
        """Match semantic pattern - higher-level code patterns."""
        if language != "python":
            return False, None

        try:
            tree = ast.parse(code)
            
            # Check for dangerous function calls
            if "dangerous_function" in pattern:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if node.func.id in ['exec', 'eval', 'compile', '__import__']:
                                return True, f"line {node.lineno}"
            
            # Check for hardcoded credentials
            if "hardcoded_credential" in pattern:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                if target.id.lower() in ['password', 'secret', 'api_key', 'token']:
                                    if isinstance(node.value, ast.Constant):
                                        return True, f"line {node.lineno}"
            
            # Check for weak cryptography
            if "weak_crypto" in pattern:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Attribute):
                            if node.func.attr in ['md5', 'sha1']:
                                return True, f"line {node.lineno}"
            
        except SyntaxError:
            pass
        return False, None
