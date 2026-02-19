# FixShell AI (System-Aware Diagnostic Engine)

![PyPI - Version](https://img.shields.io/pypi/v/fixshell)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fixshell)
![License](https://img.shields.io/badge/license-MIT-green)

Refining Linux command-line error recovery with a hybrid, LLM-centered approach. FixShell intercepts failed commands, collects system context, and uses a local LLM (Ollama) to diagnose and suggest fixes.

## 🚀 Features

- **Context-Aware Diagnosis**: Analyzes command output, exit codes, and system state (distro, package manager, SELinux).
- **Hybrid Intelligence**: Combines deterministic rules (for instant fixes) with LLM reasoning (for complex errors).
- **Safety First**: Filters dangerous commands and utilizes a strict safety layer to prevent system damage.
- **Local Privacy**: Runs entirely on your machine using Ollama; no data leaves your system.

## 📦 Installation

```bash
pip install fixshell
```

## 🛠️ Prerequisites (Ollama)

FixShell requires **Ollama** to be installed and running locally to perform AI analysis.

1.  **Install Ollama**: [Download from ollama.com](https://ollama.com)
2.  **Pull the Model**:
    ```bash
    ollama pull qwen2.5:3b
    ```
3.  **Start Ollama Server**:
    Ensure the Ollama server is running (`ollama serve`).

## 💻 Usage

Prepend `fixshell --` to any command you want to run safely or debug.

```bash
fixshell -- <your_command>
```

**Examples:**

```bash
# Debug a failed docker command
fixshell -- docker run hello-world

# Analyze a missing package
fixshell -- python3 script.py

# Investigate permission errors
fixshell -- cat /etc/shadow
```

## ⚠️ Important Warning

FixShell uses a Large Language Model (LLM) for diagnosis. While we have implemented safety filters:
- **Always review suggested commands before execution.**
- **Do not run suggested commands blindly.**
- **The AI can make mistakes.**

## 🏗️ Architecture

- **Executor**: Runs your command and captures output.
- **Context Collector**: Gathers system metadata (OS, shell, history).
- **Log Filtering**: Extracts relevant error lines to reduce noise.
- **Safety Layer**: Scans for dangerous patterns (e.g., `rm -rf /`, `chmod 777`).
- **LLM Integration**: Queries the local Ollama instance for a diagnosis.

## 📄 License

MIT License
