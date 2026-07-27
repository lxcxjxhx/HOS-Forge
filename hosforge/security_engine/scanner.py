"""Advanced code scanner with project-level scanning capabilities."""

import os
from pathlib import Path
from typing import List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from hosforge.security_engine.engine import SecurityEngine
from hosforge.security_engine.report import SecurityReport


class CodeScanner:
    """
    Advanced code scanner for project-level security analysis.
    
    Features:
    - Multi-file concurrent scanning
    - Directory traversal with filtering
    - Exclude patterns support
    - Progress tracking
    """
    
    def __init__(
        self,
        rules_dir: Optional[str] = None,
        max_workers: int = 4,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """
        Initialize the code scanner.
        
        Args:
            rules_dir: Directory containing YAML rule files
            max_workers: Maximum number of concurrent scan workers
            exclude_patterns: List of glob patterns to exclude (e.g., ["*.test.py", "node_modules/*"])
        """
        self.engine = SecurityEngine(rules_dir)
        self.max_workers = max_workers
        self.exclude_patterns = exclude_patterns or []
    
    def scan_project(
        self,
        project_path: str,
        language: Optional[str] = None,
        progress_callback: Optional[callable] = None,
    ) -> SecurityReport:
        """
        Scan an entire project for security vulnerabilities.
        
        Args:
            project_path: Root directory of the project
            language: Filter by language (scans all if None)
            progress_callback: Optional callback(current, total, file_path) for progress tracking
            
        Returns:
            SecurityReport with all findings
        """
        project_path = Path(project_path)
        if not project_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {project_path}")
        
        # Collect files to scan
        files_to_scan = self._collect_files(project_path, language)
        
        if not files_to_scan:
            return SecurityReport(
                file_path=str(project_path),
                language=language or "mixed",
                findings=[],
            )
        
        # Scan files concurrently
        all_findings = []
        total_files = len(files_to_scan)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self._scan_file_safe, str(file_path)): file_path
                for file_path in files_to_scan
            }
            
            completed = 0
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                completed += 1
                
                if progress_callback:
                    progress_callback(completed, total_files, str(file_path))
                
                try:
                    report = future.result()
                    all_findings.extend(report.findings)
                except Exception as e:
                    # Log error but continue scanning
                    print(f"Error scanning {file_path}: {e}")
        
        return SecurityReport(
            file_path=str(project_path),
            language=language or "mixed",
            findings=all_findings,
        )
    
    def _collect_files(
        self,
        project_path: Path,
        language: Optional[str] = None,
    ) -> List[Path]:
        """Collect all code files to scan, respecting exclude patterns."""
        files = []
        
        for file_path in project_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Check if file should be excluded
            if self._should_exclude(file_path, project_path):
                continue
            
            # Check if it's a code file
            if not self.engine._is_code_file(file_path):
                continue
            
            # Filter by language if specified
            if language:
                detected_lang = self.engine._detect_language(file_path)
                if detected_lang != language:
                    continue
            
            files.append(file_path)
        
        return files
    
    def _should_exclude(self, file_path: Path, project_root: Path) -> bool:
        """Check if file matches any exclude pattern."""
        # Get relative path for pattern matching
        try:
            rel_path = file_path.relative_to(project_root)
            rel_path_str = str(rel_path)
        except ValueError:
            rel_path_str = str(file_path)
        
        # Check against exclude patterns
        import fnmatch
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern):
                return True
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
        
        # Common exclusions
        common_excludes = [
            "node_modules",
            ".git",
            "__pycache__",
            ".venv",
            "venv",
            "env",
            ".env",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
        ]
        
        for exclude_dir in common_excludes:
            if exclude_dir in rel_path.parts:
                return True
        
        return False
    
    def _scan_file_safe(self, file_path: str) -> SecurityReport:
        """Safely scan a file, catching exceptions."""
        try:
            return self.engine.scan_file(file_path)
        except Exception as e:
            # Return empty report on error
            return SecurityReport(
                file_path=file_path,
                language="unknown",
                findings=[],
            )
    
    def scan_with_git_diff(
        self,
        project_path: str,
        base_branch: str = "main",
    ) -> SecurityReport:
        """
        Scan only files changed in git diff against base branch.
        
        Args:
            project_path: Root directory of the project
            base_branch: Base branch to compare against
            
        Returns:
            SecurityReport with findings from changed files
        """
        import subprocess
        
        project_path = Path(project_path)
        
        # Get list of changed files
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", base_branch],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True,
            )
            changed_files = [
                project_path / f
                for f in result.stdout.strip().split("\n")
                if f
            ]
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git diff failed: {e}")
        
        # Filter to code files only
        code_files = [
            f for f in changed_files
            if f.exists() and self.engine._is_code_file(f)
        ]
        
        # Scan changed files
        all_findings = []
        for file_path in code_files:
            try:
                report = self.engine.scan_file(str(file_path))
                all_findings.extend(report.findings)
            except Exception as e:
                print(f"Error scanning {file_path}: {e}")
        
        return SecurityReport(
            file_path=str(project_path),
            language="mixed",
            findings=all_findings,
        )
