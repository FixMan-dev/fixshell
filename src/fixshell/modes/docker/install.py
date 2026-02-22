
from typing import List, Dict, Any
import click
import subprocess
import os

SUPPORT_EMAIL = "📧 fixman.services24hrs@gmail.com"

# 2026 Standards
SUPPORTED_CODENAMES = ["jammy", "noble", "questing"]
WIN10_MIN_BUILD = 19045
WIN11_MIN_BUILD = 22631

def get_ubuntu_installer(codename, arch):
    """Generates the 2026-standard Ubuntu/Debian installer logic using deb822."""
    is_supported = codename in SUPPORTED_CODENAMES
    target_codename = codename if is_supported else "noble"
    
    steps = [
        {"desc": "📁 Creating keyrings directory", "cmd": ["sudo", "install", "-m", "0755", "-d", "/etc/apt/keyrings"]},
        {"desc": "🔑 Downloading Docker GPG key", "cmd": ["sudo", "curl", "-fsSL", f"https://download.docker.com/linux/ubuntu/gpg", "-o", "/etc/apt/keyrings/docker.asc"]},
        {"desc": "🔓 Setting GPG permissions", "cmd": ["sudo", "chmod", "a+r", "/etc/apt/keyrings/docker.asc"]},
        {
            "desc": "📄 Configuring deb822 repository", 
            "cmd": f"""sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: {target_codename}
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF"""
        },
        {"desc": "🔄 Updating package index", "cmd": ["sudo", "apt-get", "update"]},
        {"desc": "🚀 Installing Docker Engine", "cmd": ["sudo", "apt-get", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"]},
        {"desc": "🎉 Enabling Docker service", "cmd": ["sudo", "systemctl", "enable", "--now", "docker"]}
    ]
    return steps, is_supported

def get_windows_guide(build, arch):
    """Generates a guide for Windows with 2026 version checks."""
    major_ver = 11 if int(build) >= 22000 else 10
    min_build = WIN11_MIN_BUILD if major_ver == 11 else WIN10_MIN_BUILD
    
    is_supported = int(build) >= min_build
    download_url = f"https://desktop.docker.com/win/main/{arch}/Docker%20Desktop%20Installer.exe"
    
    guide = {
        "status": "✅ COMPATIBLE" if is_supported else "🚨 NOT FULLY SUPPORTED",
        "steps": [
            f"1. Download Docker Desktop ({arch}): {download_url}",
            "2. Run the installer and ensure 'WSL 2' is checked.",
            "3. Restart if prompted by Windows.",
            "4. Open Docker Desktop and accept the service agreement.",
            "5. Run 'docker version' in PowerShell to verify."
        ],
        "prerequisites": "Requires Windows Pro/Ent/Edu (WSL 2.1.5+ recommended)."
    }
    return guide, is_supported

def get_generic_install():
    """Generic fallback script using the official convenience script."""
    return [
        {"desc": "📥 Downloading official install script", "cmd": ["curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"]},
        {"desc": "🛠️ Running standard installation", "cmd": ["sudo", "sh", "get-docker.sh"]},
        {"desc": "📧 For help, contact", "cmd": ["echo", SUPPORT_EMAIL]}
    ]
