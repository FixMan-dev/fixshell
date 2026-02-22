# Changelog

All notable changes to this project will be documented in this file.

## [0.1.4] – February 2026

### Fixed
- **OS Detection**: Resolved "Linux unknown" bug. Detection now correctly parses `/etc/os-release` and falls back to `lsb_release` for granularity.
- **Safety**: Removed unsafe `get.docker.com` convenience script fallback. All installations now follow the official manual protocol.

### Added
- **Strict Validation**: Mandatory check against supported codenames: **questing (25.10)**, **noble (24.04 LTS)**, and **jammy (22.04 LTS)**.
- **Noble Fallback**: Choice to fallback to the stable 'noble' repository if detection identifies a derivative or unsupported release.
- **Mandatory Authorizations**: Every privileged command (sudo, apt, curl) now requires explicit `[Y/n]` confirmation after a detailed Purpose/Risk preview.
- **Live Diagnostics**: Real-time output streaming during installation and detailed error classification for GPG/Signature issues.
- **Support Contact**: Official support 📧 **fixman.services24hrs@gmail.com** integrated into all recovery flows.

## [0.1.2] - 2026-02-22
- Refined branding and version consensus.
- Optimized Docker installers for shell-aware execution.

## [0.1.1] - 2026-02-19
- Initial release with early Git and AI diagnosis features.
