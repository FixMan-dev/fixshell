# FixShell v0.1.2 - Deterministic DevOps Orchestration Engine

FixShell is a state-aware orchestration engine that transforms cryptic terminal failures into guided, self-healing workflows. It prioritizes deterministic logic (regex/rules) to ensure speed and reliability, with an optional LLM layer for complex edge cases.

## 🌟 Key Features

### 🐳 Docker Lifecycle Management
- **Smart Installation**: Automatically detects missing Docker environments and provides tailored installation guides for:
  - **Ubuntu/Debian** (APT repository setup)
  - **Fedora** (DNF repository setup)
  - **Arch Linux** (Pacman)
  - **CentOS/RHEL** (Yum)
  - **Windows (WSL)** (Docker Desktop integration)
- **Auto-Healing**: Intercepts `permission denied`, `daemon not running`, `port conflicts`, and `name collisions`.

### 🐙 Git & GitHub Workflow
- **State-Aware Sync**: Deterministic Pull → Commit → Push pipeline.
- **Auto-Upstream**: Detects and fixes missing tracking information or upstream branches automatically.
- **GitHub CLI Integration**: Unified authentication and repository management.

### 🔍 Proactive Linux Diagnosis
- **Evidence Scoring**: Probes system metrics (`df`, `ss`, `ls`) to identify root causes like disk exhaustion or port conflicts before they crash your session.
- **AI Toggle**: Run with `--ai` to activate local LLM diagnosis (Ollama) when deterministic rules aren't enough.

## 🛠️ Installation

```bash
pip install fixshell
```

## 📖 Usage

### Entrypoints
FixShell provides the `fixshell` command.

### 1. Docker Guided Mode
```bash
fixshell docker
```
*Follow the on-screen menu to install Docker, build images, or manage containers safely.*

### 2. Git/GitHub Mode
```bash
fixshell git
fixshell github
```

### 3. Diagnosis Mode
```bash
# Deterministic (default)
fixshell diagnosis apt install git

# AI-Powered
fixshell diagnosis --ai python app.py
```

## 🏗️ Architecture
- **Classifier**: Multi-layered regex engine with priority metadata.
- **Retry Engine**: Implements the recursive recovery loop (Execute → Classify → Resolve → Retry).
- **StateMachine**: Tracks global system state (`OS_STATE`, `DISTRO_STATE`, `AUTH_STATE`).
- **Renderer**: Professional TUI using `rich`.

## 📦 Publishing (DevOps)
FixShell uses **Trusted Publishing** via GitHub Actions.
1. Bump version in `src/fixshell/config.py`.
2. Push a tag: `git tag v0.1.2 && git push --tags`.
3. GitHub Actions builds the wheel/sdist and publishes to PyPI via OIDC.

## 🛡️ Security
- Every command is previewed in a **PLAN** block before execution.
- Destructive operations require explicit confirmation.
- Safe-by-default environment variables (e.g., `GIT_TERMINAL_PROMPT=0`).

---
Maintainer: **FIXMAN_404** (Thilak Divyadharshan)
License: **MIT**
