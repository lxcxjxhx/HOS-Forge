"""Rule engine for evaluating security rules against code."""
import ast
import re
from typing import Any, List

from hosforge.rule_engine.schema import (
    LogicOperator,
    PatternType,
    RuleMatchResult,
    RulePattern,
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
                # Semantic matching not yet implemented
                matched, location = False, None

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

        # Extract CWE and OWASP from metadata
        cwe_ids = []
        cwe = rule.metadata.get("cwe", "")
        if cwe:
            cwe_ids.append(cwe)
        owasp_category = rule.metadata.get("owasp", "")

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

    def _match_taint_flow(
        self, pattern: RulePattern, code: str, language: str
    ) -> tuple[bool, str | None]:
        """
        Match code against taint flow pattern.
        
        Detects data flow from sources (user input) to sinks (dangerous operations)
        without proper sanitization.
        """
        if language != "python":
            return False, None

        try:
            tree = ast.parse(code)
            
            # Extract sources, sinks, and sanitizers from pattern constraints
            sources = pattern.constraints.get("sources", [])
            sinks = pattern.constraints.get("sinks", [])
            sanitizers = pattern.constraints.get("sanitizers", [])
            
            if not sources or not sinks:
                return False, None
            
            # Track tainted variables
            tainted_vars: set[str] = set()
            tainted_lines: dict[str, int] = {}
            
            # Find sources (user input)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    # Check if assignment comes from a source
                    if self._is_source(node.value, sources):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                tainted_vars.add(target.id)
                                tainted_lines[target.id] = target.lineno
                
                # Check function arguments
                elif isinstance(node, ast.FunctionDef):
                    for arg in node.args.args:
                        # Function parameters are potential sources
                        tainted_vars.add(arg.arg)
                        tainted_lines[arg.arg] = arg.lineno
            
            # Find sinks (dangerous operations)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if calling a sink function
                    if self._is_sink_call(node, sinks):
                        # Check if any argument is tainted
                        for arg in node.args:
                            if isinstance(arg, ast.Name) and arg.id in tainted_vars:
                                # Check if sanitized
                                if not self._is_sanitized(arg.id, sanitizers, tree):
                                    return True, f"line {node.lineno}"
                            
                            # Check attribute access on tainted vars
                            elif isinstance(arg, ast.Attribute):
                                if isinstance(arg.value, ast.Name):
                                    if arg.value.id in tainted_vars:
                                        if not self._is_sanitized(arg.value.id, sanitizers, tree):
                                            return True, f"line {node.lineno}"
                        
                        # Check keyword arguments
                        for kw in node.keywords:
                            if isinstance(kw.value, ast.Name) and kw.value.id in tainted_vars:
                                if not self._is_sanitized(kw.value.id, sanitizers, tree):
                                    return True, f"line {node.lineno}"
        
        except SyntaxError:
            pass
        
        return False, None
    
    def _is_source(self, node: ast.expr, sources: list[str]) -> bool:
        """Check if a node represents a taint source."""
        if isinstance(node, ast.Call):
            # Check for input(), request.args.get(), etc.
            if isinstance(node.func, ast.Name):
                if node.func.id in sources:
                    return True
            elif isinstance(node.func, ast.Attribute):
                # Check for request.args.get, request.form.get, etc.
                if isinstance(node.func.value, ast.Attribute):
                    full_name = f"{node.func.value.value}.{node.func.value.attr}.{node.func.attr}"
                    if full_name in sources:
                        return True
                elif isinstance(node.func.value, ast.Name):
                    full_name = f"{node.func.value.id}.{node.func.attr}"
                    if full_name in sources:
                        return True
        return False
    
    def _is_sink_call(self, node: ast.Call, sinks: list[str]) -> bool:
        """Check if a call node represents a taint sink."""
        if isinstance(node.func, ast.Name):
            if node.func.id in sinks:
                return True
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                full_name = f"{node.func.value.id}.{node.func.attr}"
                if full_name in sinks:
                    return True
            elif isinstance(node.func.value, ast.Attribute):
                full_name = f"{node.func.value.value}.{node.func.value.attr}.{node.func.attr}"
                if full_name in sinks:
                    return True
        return False
    
    def _is_sanitized(self, var_name: str, sanitizers: list[str], tree: ast.Module) -> bool:
        """Check if a variable has been sanitized."""
        if not sanitizers:
            return False
        
        # Look for sanitizer function calls on the variable
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                # Check if variable is reassigned through a sanitizer
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == var_name:
                        if isinstance(node.value, ast.Call):
                            if self._is_sanitizer_call(node.value, sanitizers):
                                return True
            
            # Check for sanitizer calls with the variable as argument
            elif isinstance(node, ast.Call):
                if self._is_sanitizer_call(node, sanitizers):
                    for arg in node.args:
                        if isinstance(arg, ast.Name) and arg.id == var_name:
                            return True
        
        return False
    
    def _is_sanitizer_call(self, node: ast.Call, sanitizers: list[str]) -> bool:
        """Check if a call is a sanitizer function."""
        if isinstance(node.func, ast.Name):
            if node.func.id in sanitizers:
                return True
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                full_name = f"{node.func.value.id}.{node.func.attr}"
                if full_name in sanitizers:
                    return True
        return False
