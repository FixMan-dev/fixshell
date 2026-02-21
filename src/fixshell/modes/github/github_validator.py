import subprocess
import shutil

def is_git_installed() -> bool:
    return shutil.which("git") is not None

def is_gh_installed() -> bool:
    return shutil.which("gh") is not None

def has_remote() -> bool:
    try:
        res = subprocess.run(["git", "remote"], capture_output=True, text=True)
        return "origin" in res.stdout
    except Exception:
        return False

def is_dirty() -> bool:
    try:
        res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        return bool(res.stdout.strip())
    except Exception:
        return False

def current_branch() -> str:
    try:
        res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
        return res.stdout.strip()
    except Exception:
        return ""
