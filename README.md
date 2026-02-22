# FixShell v0.1.4 - Deterministic DevOps Orchestration Engine

FixShell is a secure, state-aware orchestration engine that transforms terminal failures into guided, self-healing workflows. In the 2026 edition (v0.1.4), we prioritize **Absolute Transparency** and **User Safety**.

## 🛡️ Safety & Security (v0.1.4 Edition)
- **Zero Blind Execution**: No privileged command (sudo, apt, curl) ever runs WITHOUT your explicit `[Y/n]` approval.
- **Deep Visibility**: Every installation step displays its **Purpose** and **Risk Level** before you authorize it.
- **Live Output**: Real-time streaming of command stdout/stderr directly to your terminal.

## 🐳 Docker Safe-Install Protocol (Feb 2026)
- **Official Support**: Questing (25.10), Noble (24.04 LTS), Jammy (22.04 LTS).
- **Bulletproof Detection**: Reliable OS/Codename parsing ensures you never get "Linux unknown" errors or signature mismatches.
- **Manual Method Only**: Uses the secure, official `deb822` repository mapping. No hidden scripts.

## 🆘 Support
For advanced troubleshooting or unsupported environments:
📧 **fixman.services24hrs@gmail.com**

## 📖 Usage
```bash
fixshell docker  # Choose 'Install Docker Engine' for the Safe-Install Protocol
```

## 🛠️ Installation
```bash
pip install fixshell
```

---
Maintainer: **FIXMAN_404** (Thilak Divyadharshan)
License: **MIT**
