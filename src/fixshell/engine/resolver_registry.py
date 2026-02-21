
import os
import shutil
import subprocess
import click
from typing import Callable, Dict, Any, Optional

class ResolverRegistry:
    def __init__(self):
        self._resolvers: Dict[str, Callable] = {}

    def register(self, category: str, func: Callable):
        self._resolvers[category] = func

    def get_resolver(self, category: str) -> Optional[Callable]:
        return self._resolvers.get(category)

# --- Resolvers ---

def handle_directory_exists(matches, dry_run: bool = False) -> bool:
    path = matches[0] if matches else "unknown"
    click.secho(f"\n⚠ Path conflict: '{path}' already exists.", fg="yellow")
    click.echo("1. Use existing contents\n2. Wipe and clean\n3. Rename automatically\n4. Cancel")
    choice = click.prompt("Resolution", type=int, default=3)
    if choice == 1: return True
    if choice == 2:
        if click.confirm(f"Permanently delete {path}?", default=False):
            if not dry_run: 
                shutil.rmtree(path)
                os.makedirs(path)
            return True
    if choice == 3:
        i = 1
        while os.path.exists(f"{path}-{i}"): i += 1
        new_path = f"{path}-{i}"
        click.secho(f"✔ Auto-renamed to {new_path}", fg="green")
        if not dry_run: os.makedirs(new_path)
        return True
    return False

def handle_git_no_upstream(matches, dry_run: bool = False) -> bool:
    branch = matches[0] if matches else "main"
    cmd = ["git", "push", "--set-upstream", "origin", branch]
    click.secho(f"🔧 Applying Fix: Setting upstream for {branch}", fg="cyan")
    if not dry_run:
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0
    return True

def handle_git_no_tracking(matches, dry_run: bool = False) -> bool:
    click.secho("\n⚠ No tracking info for pull.", fg="yellow")
    click.echo("1. Pull from origin/main and SET as upstream")
    click.echo("2. Pull from origin/main once")
    click.echo("3. Cancel")
    choice = click.prompt("Resolution", type=int, default=1)
    if choice == 1:
        if not dry_run:
            subprocess.run(["git", "branch", "--set-upstream-to=origin/main"])
            return subprocess.run(["git", "pull"]).returncode == 0
    elif choice == 2:
        if not dry_run:
            return subprocess.run(["git", "pull", "origin", "main"]).returncode == 0
    return False

def handle_git_upstream_mismatch(matches, dry_run: bool = False) -> bool:
    # Git usually suggests the right command in the error output
    # If the user is seeing this, we should offer to push to HEAD:main or HEAD:danger etc.
    click.secho("\n⚠ Upstream branch name mismatch.", fg="yellow")
    click.echo("1. Push to origin/main (Default behavior)")
    click.echo("2. Push to same name on remote (Create remote branch)")
    click.echo("3. Cancel")
    choice = click.prompt("Choice", type=int, default=1)
    if choice == 1:
        if not dry_run:
            # Note: We use -u to make it permanent so the retry works
            return subprocess.run(["git", "push", "-u", "origin", "HEAD:main"]).returncode == 0
        return True
    elif choice == 2:
        if not dry_run:
            res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
            branch = res.stdout.strip()
            return subprocess.run(["git", "push", "-u", "origin", branch]).returncode == 0
        return True
    return False

def handle_git_delete_current_branch(matches, dry_run: bool = False) -> bool:
    branch = matches[0] if matches else "unknown"
    click.secho(f"\n⚠ Cannot delete active branch '{branch}'.", fg="yellow")
    
    # Try to find a safe branch to switch to
    target = "main"
    res = subprocess.run(["git", "branch", "--list", "main"], capture_output=True, text=True)
    if "main" not in res.stdout:
        res = subprocess.run(["git", "branch", "--list", "master"], capture_output=True, text=True)
        if "master" in res.stdout: target = "master"
        else:
            # Last resort: just find any branch that isn't the current one
            res = subprocess.run(["git", "branch", "--format=%(refname:short)"], capture_output=True, text=True)
            branches = [b.strip() for b in res.stdout.split('\n') if b.strip() and b.strip() != branch]
            if branches: target = branches[0]
            else: 
                click.secho("❌ No other branches to switch to!", fg="red")
                return False

    click.echo(f"1. Switch to '{target}' and then delete (Safe)")
    click.echo("2. Cancel")
    if click.prompt("Choice", type=int, default=1) == 1:
        if not dry_run:
            if subprocess.run(["git", "checkout", target]).returncode == 0:
                return subprocess.run(["git", "branch", "-D", branch]).returncode == 0
        return True
    return False

def handle_gh_auth_login(matches, dry_run: bool = False) -> bool:
    click.secho("\n💊 Needs Authentication: GitHub CLI is not logged in.", fg="yellow", bold=True)
    if click.confirm("   Would you like to authenticate now?", default=True):
        if not dry_run: subprocess.run(["gh", "auth", "login"])
        return True
    return False
