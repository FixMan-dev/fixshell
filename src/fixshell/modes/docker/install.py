
from typing import List, Dict, Any

INSTALL_TEMPLATES = {
    "ubuntu": {
        "name": "Docker Engine (Ubuntu/Debian)",
        "prerequisites": ["sudo access", "Internet connection"],
        "steps": [
            {"desc": "Update apt index", "cmd": ["sudo", "apt-get", "update"]},
            {"desc": "Install dependencies", "cmd": ["sudo", "apt-get", "install", "-y", "ca-certificates", "curl", "gnupg"]},
            {"desc": "Add GPG key", "cmd": ["sudo", "install", "-m", "0755", "-d", "/etc/apt/keyrings"]},
            {"desc": "Download key", "cmd": ["curl", "-fsSL", "https://download.docker.com/linux/ubuntu/gpg", "-o", "/etc/apt/keyrings/docker.asc"]},
            {"desc": "Add Repo", "cmd": "echo \"deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu jammy stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null"},
            {"desc": "Install Docker", "cmd": "sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"},
            {"desc": "Finalize", "cmd": ["sudo", "systemctl", "enable", "--now", "docker"]}
        ]
    },
    "fedora": {
        "name": "Docker Engine (Fedora)",
        "steps": [
            {"desc": "Remove old versions", "cmd": ["sudo", "dnf", "remove", "docker", "docker-client", "docker-client-latest", "docker-common", "docker-latest", "docker-latest-logrotate", "docker-logrotate", "docker-selinux", "docker-engine-selinux", "docker-engine"]},
            {"desc": "Add repository", "cmd": ["sudo", "dnf", "-y", "install", "dnf-plugins-core"]},
            {"desc": "Setup repo", "cmd": ["sudo", "dnf", "config-manager", "--add-repo", "https://download.docker.com/linux/fedora/docker-ce.repo"]},
            {"desc": "Install Docker", "cmd": ["sudo", "dnf", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"]},
            {"desc": "Start Docker", "cmd": ["sudo", "systemctl", "enable", "--now", "docker"]}
        ]
    },
    "arch": {
        "name": "Docker Engine (Arch Linux)",
        "steps": [
            {"desc": "Install Docker", "cmd": ["sudo", "pacman", "-S", "--noconfirm", "docker"]},
            {"desc": "Start Docker", "cmd": ["sudo", "systemctl", "enable", "--now", "docker"]}
        ]
    },
    "centos": {
        "name": "Docker Engine (CentOS/RHEL)",
        "steps": [
            {"desc": "Install yum-utils", "cmd": ["sudo", "yum", "install", "-y", "yum-utils"]},
            {"desc": "Add repo", "cmd": ["sudo", "yum-config-manager", "--add-repo", "https://download.docker.com/linux/centos/docker-ce.repo"]},
            {"desc": "Install Docker", "cmd": ["sudo", "yum", "install", "-y", "docker-ce", "docker-ce-cli", "containerd.io", "docker-buildx-plugin", "docker-compose-plugin"]},
            {"desc": "Start Docker", "cmd": ["sudo", "systemctl", "enable", "--now", "docker"]}
        ]
    },
    "windows_wsl": {
        "name": "Docker Desktop Integration (WSL)",
        "steps": [
            {"desc": "Informational", "cmd": ["echo", "Please install Docker Desktop for Windows first from: https://www.docker.com/products/docker-desktop"]},
            {"desc": "Enable WSL Integration", "cmd": ["echo", "In Docker Desktop Settings -> Resources -> WSL Integration, enable for your distro."]}
        ]
    },
    "fallback": {
        "name": "Generic Docker Installation",
        "steps": [
            {"desc": "Install via official script", "cmd": ["curl", "-fsSL", "https://get.docker.com", "-o", "get-docker.sh"]},
            {"desc": "Run install script", "cmd": ["sudo", "sh", "get-docker.sh"]}
        ]
    }
}
