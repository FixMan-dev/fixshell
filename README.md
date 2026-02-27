# FixShell v0.1.4 — Deterministic DevOps Orchestration Engine

FixShell is a modern, state-aware orchestration engine designed to transform cryptic terminal failures into guided, self-healing workflows. It prioritizes **Deterministic Safety** through a robust regex-based classification engine and provides optional **LLM-powered diagnosis** for complex edge cases.

Built for version-controlled environments and hybrid cloud/local development, FixShell ensures that your DevOps pipeline remains resilient, auditable, and secure.

---

## 🚀 Core Features

### 🛡️ Safety & Security (Safe-Install Protocol)
FixShell implements a **Zero Blind Execution** policy. No privileged command (sudo, apt, curl) ever runs without your explicit authorization.
- **Transparency**: Every step displays its **Purpose** and **Risk Level** (Low/Medium/High) before the prompt.
- **Auditable**: Real-time streaming of all command output directly to your terminal.
- **Dry-Run Mode**: Use `--dry-run` to simulate any workflow without modifying your system.

### 🐳 Docker Enterprise Management (Feb 2026 Standards)
- **Safe-Install Protocol**: Supports official Ubuntu releases (Questing 25.10, Noble 24.04 LTS, Jammy 22.04 LTS) using the modern `deb822` repository format.
- **Auto-Healing**:
    - Intercepts and resolves **Daemon Not Running** errors.
    - Automated **Container Name Conflict** resolution (Stop/Remove).
    - **Permission Management**: Detects missing user groups and guides through repair.
- **Lifecycle Ops**: Built-in templates for MySQL/PostgreSQL deployment and Node/Python containerization.

### 🐙 Git & GitHub Orchestration
- **Smart-Sync**: Automated `Pull -> Commit -> Push` pipeline with state-aware context.
- **Self-Healing Git**:
    - Detects and fixes **Missing Upstream** tracking.
    - Handles **Active Branch Deletion** conflicts by suggesting safe context switches.
- **GitHub CLI Integration**: Native support for `gh` authentication checks and repository lifecycle management.

### 🔍 Proactive Linux Diagnosis
- **Evidence-Based Scoring**: FixShell probes system metrics (`ss`, `df`, `ls`, `ps`) to identify the root cause of failures (e.g., Port occupied vs. Disk full).
- **Dual-Engine Logic**:
    - **Deterministic (Default)**: Lightning-fast regex classification for 99% of common errors.
    - **AI-Powered (Toggle)**: Run any command with `--ai` to activate local LLM diagnosis (Ollama) for intricate stack traces.

---

## �️ Technical Architecture

FixShell is built as a recursive recovery loop:

1.  **Executor**: Handles command execution with safety previews and live output streaming.
2.  **Classifier**: A multi-layered engine that maps stderr/stdout output to specific error categories.
3.  **Registry Resolvers**: A modular registry of deterministic healing logic.
4.  **Workflow StateMachine**: Tracks global environment state including OS, Distro, Arch, Auth status, and Repository context.

---

## 🛠️ Installation

Requirements: **Python 3.10+**

```bash
pip install fixshell
```

To enable AI features, ensure **Ollama** is installed and running locally.

---

## 📖 Usage

### 1. The Safe Docker Workflow
```bash
fixshell docker
```
*Follow the guided TUI to install the engine, manage containers, or debug services.*

### 2. Git Automation
```bash
fixshell git push
fixshell github repos
```

### 3. Self-Healing Linux Commands
Run any command through the diagnosis engine to catch failures before they exit.
```bash
# Deterministic mode
fixshell diagnosis apt install git

# AI-Powered mode (requires Ollama)
fixshell diagnosis --ai python main.py
```

### 4. Global Flags
- `--dry-run`: View the plan without executing.
- `--version`: Check current engine version.

---

## 🆘 Support & Community

For advanced troubleshooting, reporting bugs, or requesting support for specific Linux distributions:
📧 **fixman.services24hrs@gmail.com**

---
Maintainer: **FIXMAN_404** (Thilak Divyadharshan)  
License: **MIT**  
Copyright: **© 2026 FixShell Project**
