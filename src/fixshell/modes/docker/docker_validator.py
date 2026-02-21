import subprocess
import socket
import shutil
from typing import Optional

def is_docker_installed() -> bool:
    """Check if docker binary exists in PATH."""
    return shutil.which("docker") is not None

def is_docker_running() -> bool:
    """Check if docker daemon is responsive."""
    try:
        subprocess.run(["docker", "info"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_port_free(port: int) -> bool:
    """Check if a local port is available."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def container_exists(name: str) -> bool:
    """Check if a container with this name already exists."""
    try:
        res = subprocess.run(["docker", "ps", "-a", "--filter", f"name=^/{name}$", "--format", "{{.Names}}"], capture_output=True, text=True)
        return name in res.stdout
    except Exception:
        return False
