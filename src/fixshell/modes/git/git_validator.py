
import shutil
import subprocess
import os
import re
from typing import List, Tuple, Optional

class GitValidator:
    """
    Validates environment and state for Git operations.
    """

    @staticmethod
    def validate_environment() -> List[Tuple[bool, str]]:
        results = []
        
        # 1. Git Installed
        if shutil.which("git"):
            results.append((True, "Git is installed."))
        else:
            results.append((False, "Git is NOT installed. Please install it first."))

        # 2. GH CLI Installed
        if shutil.which("gh"):
            results.append((True, "GitHub CLI (gh) is installed."))
        else:
            results.append((False, "GitHub CLI (gh) is NOT installed. Recommended for repository creation."))

        # 3. GH Authenticated
        try:
            gh_auth = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
            if gh_auth.returncode == 0:
                results.append((True, "GitHub CLI is authenticated."))
            else:
                results.append((False, "GitHub CLI is NOT authenticated. Run 'gh auth login'."))
        except Exception:
            results.append((False, "Could not verify GitHub authentication."))

        return results

    @staticmethod
    def is_git_repo() -> bool:
        return os.path.isdir(".git") or subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True).returncode == 0

    @staticmethod
    def get_current_branch() -> str:
        try:
            return subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        except:
            return ""

    @staticmethod
    def is_working_dir_clean() -> bool:
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        return len(status.strip()) == 0

    @staticmethod
    def is_merge_in_progress() -> bool:
        return os.path.exists(".git/MERGE_HEAD")

    @staticmethod
    def is_rebase_in_progress() -> bool:
        return os.path.exists(".git/rebase-merge") or os.path.exists(".git/rebase-apply")

    @staticmethod
    def is_detached_head() -> bool:
        res = subprocess.run(["git", "symbolic-ref", "-q", "HEAD"], capture_output=True)
        return res.returncode != 0

    @staticmethod
    def validate_branch_name(name: str) -> bool:
        # Simple regex for valid git branch names
        if not name or " " in name: return False
        return re.match(r"^[a-zA-Z0-9._\-/]+$", name) is not None

    @staticmethod
    def branch_exists(name: str) -> bool:
        res = subprocess.run(["git", "show-ref", "--verify", f"refs/heads/{name}"], capture_output=True)
        return res.returncode == 0

    @staticmethod
    def validate_url(url: str) -> bool:
        # Basic URL validation for git remotes
        return url.startswith("http") or url.startswith("git@")

    @staticmethod
    def has_upstream() -> bool:
        res = subprocess.run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], capture_output=True)
        return res.returncode == 0
