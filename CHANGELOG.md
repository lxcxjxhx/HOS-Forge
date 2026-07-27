# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### HOS Taskflow Engine
- YAML-based security workflow orchestration engine
- Workflow parser with dependency graph resolution
- Multi-agent scheduling with sequential, parallel, and conditional branching
- Checkpoint/resume mechanism for long-running workflows
- Example workflows: security-audit, cve-research, dependency-scan, container-security, code-review, incident-response, api-security-test

#### Security Personality System
- YAML-based personality definition system
- Personality loader with validation
- Pre-defined personalities: cve_researcher, red_team, blue_team, code_reviewer, senior_security_engineer, exploit_validator
- Personality-to-agent binding mechanism

#### HOS MCP Hub
- Unified security tool ecosystem framework
- MCP server registration and discovery mechanism
- Unified MCP client interface
- Dynamic loading and configuration management
- Core MCP servers: hos-ls-server, semgrep-server, nuclei-server, codeql-server, github-server

#### Security Memory
- Security knowledge base with CVE, vulnerability patterns, patch history, false positive records
- Vector database integration for semantic search
- False positive rate statistics and pattern matching
- Historical task learning mechanism

#### Agent Verification Loop
- State machine for vulnerability lifecycle: Finding → Candidate → Verified → Fixed → Closed
- Verification agent for false positive checking
- Exploit agent for vulnerability reproduction
- Patch agent for fix code generation
- Review agent for fix validation
- Automatic PR generation

#### Documentation
- Taskflow Engine usage guide
- Personality definition guide
- MCP server development guide
- Security Memory usage guide
- Example workflow library

### Changed
- Project repositioned from "OpenHands + security enhancement plugin" to "AI Native Cybersecurity Engineering Platform"
- Core positioning updated to "Security Agent Orchestration Framework"
- Architecture upgraded to support multi-agent collaboration and workflow orchestration

## [1.0.0] - 2025-01-15

### Added
- Initial release based on OpenHands
- AI Security Coding Agent with vulnerability detection
- Security Code Review Agent for CWE/CVE/OWASP Top 10 analysis
- Security Knowledge Base (RAG + CVE/CWE) with SQLite + vector search
- MCP Security Tool Ecosystem with Nmap, Semgrep, Nuclei, Burp Suite integration
- Local Model Optimizer with QLoRA/LoRA fine-tuning
- Security Report Engine with HTML generation

[Unreleased]: https://github.com/lxcxjxhx/HOS-Forge/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/lxcxjxhx/HOS-Forge/releases/tag/v1.0.0
