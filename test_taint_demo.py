#!/usr/bin/env python3
"""Demo script to test taint analysis detection."""

import os
from hosforge.rule_engine import RuleEngine, SecurityRule, RulePattern, PatternType, Severity, RuleType, LogicOperator

# Create a taint flow rule for command injection
cmd_injection_rule = SecurityRule(
    name="command_injection_taint",
    type=RuleType.VULNERABILITY,
    severity=Severity.CRITICAL,
    patterns=[
        RulePattern(
            type=PatternType.TAINT_FLOW,
            language="python",
            pattern="taint_flow",
        )
    ],
    logic_operator=LogicOperator.OR,
)

# Test code with taint flow vulnerability
vulnerable_code = """
import os

user_input = input("Enter command: ")
os.system(user_input)
"""

# Test code without taint flow
safe_code = """
import os

# Static command, no user input
os.system("ls -la")
"""

# Create engine and test
engine = RuleEngine([cmd_injection_rule])

print("Testing vulnerable code...")
results = engine.evaluate(vulnerable_code, "python")
print(f"Matched: {results[0].matched}")
print(f"Location: {results[0].location}")
print(f"Severity: {results[0].severity}")
print()

print("Testing safe code...")
results = engine.evaluate(safe_code, "python")
print(f"Matched: {results[0].matched}")
print(f"Location: {results[0].location}")
print()

if results[0].matched:
    print("❌ False positive detected!")
else:
    print("✓ Correctly identified as safe")
