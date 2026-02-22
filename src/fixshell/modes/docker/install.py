
from typing import List, Dict, Any
import click
import subprocess
import os

SUPPORT_EMAIL = "📧 fixman.services24hrs@gmail.com"

# OFFICIAL DOCKER SUPPORT (Feb 2026)
SUPPORTED_CODENAMES = ["questing", "noble", "jammy"]
# Questing: 25.10, Noble: 24.04 LTS, Jammy: 22.04 LTS

WIN10_MIN_BUILD = 19045
WIN11_MIN_BUILD = 22631

def get_ubuntu_installer(codename: str, arch: str):
    """
    Generates 2026-standard Ubuntu/Debian installer with safety metadata.
    Ref: https://docs.docker.com/engine/install/ubuntu/
    """
    is_supported = codename in SUPPORTED_CODENAMES
    target_codename = codename if is_supported else "noble"
    
    steps = [
        {
            "desc": "Remove conflicting packages",
            "cmd": ["sudo", "apt-get", "remove", "-y", "docker.io", "docker-doc", "docker-compose", "docker-compose-v2", "podman-docker", "containerd", "runc"],
            "purpose": "Uninstall legacy or conflicting Docker-related packages to prevent binary overlaps.",
            "risk": "medium"
        },
        {
            "desc": "Install prerequisites",
            "cmd": ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y", "ca-certificates", "curl", "gnupg", "lsb-release"],
            "purpose": "Ensure APT can handle HTTPS repositories, verify GPG signatures, and track distro info.",
            "risk": "low"
        },
        {
            "desc": "Create keyrings directory",
            "cmd": ["sudo", "install", "-m", "0755", "-d", "/etc/apt/keyrings"],
            "purpose": "Securely host the Docker official GPG key file.",
            "risk": "low"
        },
        {
            "desc": "Download GPG key",
            "cmd": ["sudo", "curl", "-fsSL", "https://download.docker.com/linux/ubuntu/gpg", "-o", "/etc/apt/keyrings/docker.asc"],
            "purpose": "Fetch the public key used to verify the authenticity of Docker packages.",
            "risk": "medium"
        },
        {
            "desc": "Set key permissions",
            "cmd": ["sudo", "chmod", "a+r", "/etc/apt/keyrings/docker.asc"],
            "purpose": "Grant read access to the GPG key for all users/processes.",
            "risk": "low"
        },
        {
            "desc": "Configure deb822 source",
            "cmd": f"""sudo tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: {target_codename}
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
EOF""",
            "purpose": "Add the Docker repository using the modern deb822 format (Mandatory in 2026).",
            "risk": "high"
        },
        {
            "desc": "Update repository index",
            "cmd": ["sudo", "apt-get", "update"],
            "purpose": "Synchronize package lists including the new Docker repository.",
            "risk": "medium"
        },
        {
            "desc": "Install Docker Engine suite",
            "cmd": ["sudo", "apt-get", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"],
            "purpose": "Install the complete Docker Engine suite from the verified repository.",
            "risk": "high"
        },
        {
            "desc": "Start and enable Docker service",
            "cmd": ["sudo", "systemctl", "enable", "--now", "docker"],
            "purpose": "Ensure Docker starts automatically on boot and is running now.",
            "risk": "medium"
        },
        {
            "desc": "Add user to docker group",
            "cmd": ["sudo", "usermod", "-aG", "docker", os.environ.get("USER", "$(whoami)")],
            "purpose": "Allow the current user to run Docker commands without sudo (requires re-login).",
            "risk": "medium"
        }
    ]
    return steps, is_supported

def get_windows_guide(build: str, arch: str):
    """
    Generates a high-security guide for Windows 2026.
    """
    try:
        b_int = int(build)
    except ValueError:
        b_int = 0

    major_ver = 11 if b_int >= 22000 else 10
    min_build = WIN11_MIN_BUILD if major_ver == 11 else WIN10_MIN_BUILD
    
    is_supported = b_int >= min_build
    download_url = f"https://desktop.docker.com/win/main/{arch}/Docker%20Desktop%20Installer.exe"
    
    guide = {
        "status": "✅ VERIFIED" if is_supported else "🚨 LEGACY BUILD",
        "description": "2026 Docker Desktop Lifecycle for Windows",
        "steps": [
            f"1. Obtain official installer ({arch}): {download_url}",
            "2. Run Installer.exe and verify 'Use WSL 2 instead of Hyper-V' is CHECKED.",
            "3. Windows Build {build} detected. Restart might be required.",
            "4. Launch Docker Desktop and sign the 2026 Service Agreement.",
            "5. Open PowerShell and verify: 'docker --version'"
        ],
        "risk_notice": "Manual installation required on Windows for safety. No auto-scripts allowed.",
        "support": SUPPORT_EMAIL
    }
    return guide, is_supported
