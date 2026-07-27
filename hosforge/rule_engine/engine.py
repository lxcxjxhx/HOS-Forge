"""Rule engine for evaluating security rules against code."""
import ast
import re
from typing import List

from hosforge.rule_engine.schema import (
    LogicOperator,
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

        return RuleMatchResult(
            rule_name=rule.name,
            matched=matched,
            location=location,
            severity=rule.severity if matched else None,
            description=rule.metadata.get("description", ""),
            remediation=rule.remediation if matched else None,
            matched_pattern=matched_pattern,
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
