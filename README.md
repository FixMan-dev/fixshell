# FixShell AI (System-Aware Diagnostic Engine)

![PyPI - Version](https://img.shields.io/pypi/v/fixshell)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fixshell)
![License](https://img.shields.io/badge/license-MIT-green)

**Stop Googling error codes. Start fixing them.**

FixShell is a command-line companion that intercepts shell errors, understands your specific Linux environment, and uses a local AI to suggest safe, instant fixes. It runs entirely on your machine—no data is ever sent to the cloud.

---

## ❓ Why use FixShell?

Linux is powerful, but its error messages can be cryptic.
- **The Problem**: A command fails. You get "exit code 127" or "permission denied." You copy the error, paste it into Google, scroll through StackOverflow, and blindly try commands that might break your system.
- **The FixShell Solution**:
    - **Context-Aware**: It knows you're on Fedora (so it suggests `dnf`, not `apt`). It knows if SELinux is blocking you.
    - **Privacy-First**: It uses a local LLM (Ollama). Your server logs and sensitive paths never leave your localhost.
    - **Safety-Guarded**: It actively blocks dangerous commands (like `rm -rf /` or reckless `chmod 777`).

## ⚙️ How It Works

FixShell acts as a smart wrapper around your terminal commands:

1.  **Execution**: You run `fixshell -- <command>`. FixShell runs the command for you.
2.  **Detection**: If the command succeeds, you see the output as normal. If it **fails**, FixShell wakes up.
3.  **Context Collection**: It gathers:
    - The raw error output (stderr).
    - Your Distribution (Ubuntu, Arch, Fedora, etc.).
    - Active Package Manager (`apt`, `pacman`, `dnf`, `zypper`).
    - System State (Disk usage, open ports, SELinux status).
4.  **AI Analysis**: It sends this structured blueprint to your local AI model (via Ollama).
5.  **Solution**: It presents a ranked list of solutions with confidence scores and specific commands to run.

---

## 📦 Installation

FixShell is a Python-based tool and works on any Linux distribution (Ubuntu, Fedora, Arch, Kali, Debian, etc.).

### Option 1: Install via pip (Universal)
The easiest way to install for your user:
```bash
pip install fixshell
```

### Option 2: Install via pipx (Recommended)
If you use `pipx` to manage CLI tools (keeps your system environment clean):
```bash
pipx install fixshell
```

### � Prerequisites: The AI Brain (Ollama)
FixShell provides the *logic*, but **Ollama** provides the *intelligence*. You must have Ollama running locally.

1.  **Install Ollama**: [Download from ollama.com](https://ollama.com)
2.  **Pull the Model**: We recommend `qwen2.5:3b` for the best balance of speed and accuracy.
    ```bash
    ollama pull qwen2.5:3b
    ```
3.  **Start the Server**:
    ```bash
    ollama serve
    ```

---

## 💻 Usage & Examples

Using FixShell is simple. Just put `fixshell --` before any command you are unsure about.

### 1. The "Missing Command" Scenario
You try to run `docker`, but it's not installed. FixShell detects your distro and gives the specific install command.
```bash
$ fixshell -- docker ps

> Command 'docker' not found.
> ...
> [1] Install Docker (Confidence: 0.98)
> Suggestion: sudo dnf install docker  [For Fedora users]
> Suggestion: sudo apt install docker.io [For Ubuntu users]
```

### 2. The "Permission Denied" Scenario
You try to edit a system file but forgot `sudo`.
```bash
$ fixshell -- cat /etc/shadow

> Permission denied.
> ...
> [1] Insufficient Privileges (Confidence: 0.95)
> Explanation: /etc/shadow is a critical system file readable only by root.
> Suggestion: sudo cat /etc/shadow
```

### 3. The "Port Conflict" Scenario
You try to start a server, but the port is taken. FixShell checks `ss` (socket stats) to confirm.
```bash
$ fixshell -- python3 server.py

> Address already in use.
> ...
> [1] Port 8080 Conflict (Confidence: 1.0)
> Explanation: Process 'nginx' is already listening on port 8080.
> Suggestion: sudo systemctl stop nginx
> Suggestion: Kill process 1234
```

---

## 🛡️ Safety Features
FixShell is designed to help, not harm. It includes a regex-based **Safety Layer** that scans every suggestion before showing it to you.

- **BLOCKED**: `rm -rf /` or recursive deletions.
- **BLOCKED**: `chmod 777` on root directories.
- **BLOCKED**: Modifying system-critical files (`/etc/passwd`) without valid reason.
- **BLOCKED**: Disabling SELinux (`setenforce 0`).

*Disclaimer: Always review the commands before executing them. AI can hallucinate, though our safety layer minimizes catastrophic risks.*

---

## 🏗️ Architecture

- **Core**: Python 3.10+
- **CLI Framework**: Click
- **LLM Engine**: Ollama (Local API)
- **Package Manager**: Poetry (for development)

## 📄 License

MIT License. Open source and free to use.
