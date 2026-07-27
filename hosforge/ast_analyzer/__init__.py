"""Lightweight AST-based code security analysis engine.

Provides language parsers, pattern matching, taint analysis,
and report generation without external tool dependencies.
"""

from hosforge.ast_analyzer.python_parser import PythonASTParser
from hosforge.ast_analyzer.javascript_parser import JavaScriptParser
from hosforge.ast_analyzer.pattern_matcher import PatternMatcher
from hosforge.ast_analyzer.taint_analyzer import TaintAnalyzer
from hosforge.ast_analyzer.report_generator import ReportGenerator

__all__ = [
    "PythonASTParser",
    "JavaScriptParser",
    "PatternMatcher",
    "TaintAnalyzer",
    "ReportGenerator",
]
