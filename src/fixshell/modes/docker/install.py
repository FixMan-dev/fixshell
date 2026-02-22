
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
            "cmd": ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y", "ca-certificates", "curl"],
            "purpose": "Ensure APT can handle HTTPS repositories and verify GPG signatures.",
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
            "desc": "Update and Install Docker",
            "cmd": ["sudo", "apt-get", "update", "&&", "sudo", "apt-get", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"],
            "purpose": "Synchronize repositories and install the complete Docker Engine suite.",
            "risk": "high"
        }
    ]
    return steps, is_supported

def get_windows_guide(build: str, arch: str):
    """
    Generates a high-security guide for Windows 2026.
    """
    major_ver = 11 if int(build) >= 22000 else 10
    min_build = WIN11_MIN_BUILD if major_ver == 11 else WIN10_MIN_BUILD
    
    is_supported = int(build) >= min_build
    download_url = f"https://desktop.docker.com/win/main/{arch}/Docker%20Desktop%20Installer.exe"
    
    guide = {
        "status": "✅ VERIFIED" if is_supported else "🚨 LEGACY BUILD",
        "description": "2026 Docker Desktop Lifecycle for Windows",
        "steps": [
            f"1. Obtain official installer ({arch}): {download_url}",
            "2. Run Installer.exe and verify 'Use WSL 2 instead of Hyper-V' is CHECKED.",
            "3. Restart Windows (Build {build}) to finish kernel integration.",
            "4. Launch Docker Desktop and sign the 2026 Service Agreement.",
            "5. Open PowerShell and verify: 'docker --version'"
        ],
        "risk_notice": "Manual installation required on Windows. No auto-execution for safety.",
        "support": SUPPORT_EMAIL
    }
    return guide, is_supported

def get_generic_linux_fallback():
    """Safety conversion for non-Ubuntu/Debian systems."""
    return [
        {
            "desc": "Convenience Script Deployment",
            "cmd": ["curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"],
            "purpose": "Download the official Docker automated installation script.",
            "risk": "medium"
        },
        {
            "desc": "Run Official Installer",
            "cmd": ["sudo", "sh", "get-docker.sh"],
            "purpose": "Execute the Docker convenience script (Caution: Bypasses manual step inspection).",
            "risk": "high"
        }
    ]
