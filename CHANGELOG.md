# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-02-22

### Added
- **Docker Lifecycle Enhancements**:
    - State-aware installation detection (detects missing binary or stopped daemon).
    - Distro-specific installation guides for Ubuntu/Debian, Fedora, Arch, and CentOS.
    - Windows/WSL installation assistance.
    - Port and Container name conflict resolution.
- **Improved UI/UX**:
    - High-fidelity `rich`-based context panel showing OS, Distro, and system health.
    - Command preview blocks ("PLAN") for transparency before execution.
    - Professional banners and status indicators.
- **Universal Linux Diagnosis**:
    - Evidence-based scoring system to identify root causes like `DISK_FULL` or `PORT_CONFLICT`.
- **Modern Packaging**:
    - Migrated to Hatch backend (PEP 621 compliant).
    - Added GitHub Actions for Trusted Publishing (OIDC).

### Changed
- Refactored core engine into decoupled modules: `Classifier`, `Executor`, `RetryEngine`, and `WorkflowStateMachine`.
- Consolidated error datasets into deterministic JSON files.
- Renamed project CLI to `fixshell` (with `fx` alias).

## [0.1.1] - 2026-02-19
- Initial release with early Git and AI diagnosis features.
