
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

def handle_directory_exists(matches, dry_run: bool = False, **kwargs) -> bool:
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

def handle_git_no_upstream(matches, dry_run: bool = False, **kwargs) -> bool:
    branch = matches[0] if matches else "main"
    cmd = ["git", "push", "--set-upstream", "origin", branch]
    click.secho(f"🔧 Applying Fix: Setting upstream for {branch}", fg="cyan")
    if not dry_run:
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0
    return True

def handle_git_no_tracking(matches, dry_run: bool = False, **kwargs) -> bool:
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

def handle_git_upstream_mismatch(matches, dry_run: bool = False, **kwargs) -> bool:
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

def handle_git_delete_current_branch(matches, dry_run: bool = False, **kwargs) -> bool:
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

def handle_gh_auth_login(matches, dry_run: bool = False, **kwargs) -> bool:
    click.secho("\n💊 Needs Authentication: GitHub CLI is not logged in.", fg="yellow", bold=True)
    if click.confirm("   Would you like to authenticate now?", default=True):
        if not dry_run: subprocess.run(["gh", "auth", "login"])
        return True
    return False

# --- Docker Resolvers ---

def handle_docker_name_conflict(matches, dry_run: bool = False, **kwargs) -> bool:
    name = matches[0] if matches else "unknown"
    click.secho(f"\n⚠ Docker container name conflict: '{name}' already exists.", fg="yellow")
    click.echo("1. Stop and remove existing container\n2. Rename new container automatically\n3. Cancel")
    choice = click.prompt("Resolution", type=int, default=1)
    if choice == 1:
        if not dry_run:
            subprocess.run(["docker", "rm", "-f", name])
        return True
    if choice == 2:
        return True # The SM handles retry, but if we rename we might need to modify the command. 
                    # For now, let's just support removal.
    return False

def handle_docker_daemon_service(matches, dry_run: bool = False, **kwargs) -> bool:
    click.secho("\n💊 Docker daemon is not running.", fg="yellow", bold=True)
    if click.confirm("   Would you like to start the Docker service now?", default=True):
        if not dry_run:
            subprocess.run(["sudo", "systemctl", "start", "docker"])
        return True
    return False

def handle_docker_not_installed(matches, dry_run: bool = False, state: Dict[str, Any] = None) -> bool:
    from ..modes.docker.install import get_ubuntu_installer, get_windows_guide, get_generic_linux_fallback, SUPPORT_EMAIL
    from .executor import Executor
    
    executor = Executor(dry_run=dry_run)
    os_name = state.get("OS_STATE", "Linux")
    distro_info = state.get("DISTRO_STATE", {})
    arch = state.get("ARCH_STATE", "amd64")
    
    click.secho(f"\n🧩 FixShell Safe-Install Protocol: Docker Engine (v0.2.0)", fg="white", bold=True)
    click.echo(f"   Context: {os_name} {distro_info.get('id', '')} ({distro_info.get('codename', '')}) on {arch}")
    
    if os_name == "Linux":
        distro_id = distro_info.get("id", "").lower()
        codename = distro_info.get("codename", "noble").lower()
        
        if distro_id in ["ubuntu", "debian"]:
            steps, supported = get_ubuntu_installer(codename, arch)
            
            if not supported:
                click.secho(f"\n🚨 ERROR_UNSUPPORTED_DISTRO: '{codename}' is not on the official Feb 2026 support list.", fg="red", bold=True)
                click.echo(f"   Official Support: Questing 25.10, Noble 24.04 LTS, Jammy 22.04 LTS")
                click.echo(f"   For issues: {SUPPORT_EMAIL}")
                
                if not click.confirm(f"\n   Attempt fallback using 'noble' (Ubuntu 24.04) repository?", default=False):
                    click.secho("   ❌ Aborted by user.", fg="yellow")
                    return False
            
            click.secho("\n🛡️  Preparation Complete. Manual step-by-step approval required.", fg="cyan")
            
            for step in steps:
                res = executor.run(
                    step["cmd"], 
                    desc=step["desc"], 
                    purpose=step["purpose"], 
                    risk=step["risk"],
                    capture=False # Stream output live
                )
                if res.returncode != 0 and res.returncode != 130:
                    click.secho(f"\n❌ STEP FAILED: {step['desc']}", fg="red", bold=True)
                    click.echo(f"   Diagnostic: Exit {res.returncode}")
                    click.echo(f"   Need help? {SUPPORT_EMAIL}")
                    return False
            
            click.secho("\n✅ Docker installation sequence finalized.", fg="green", bold=True)
            click.secho(f"   Note: Run 'sudo usermod -aG docker $USER' to enable non-root access.", fg="white", dim=True)
            return True

        else:
            # Generic Linux
            click.secho("\n⚠️  Generic Linux detected. Using Docker convenience script.", fg="yellow")
            if click.confirm("   Proceed with convenience script? (Limited step-by-step visibility)", default=True):
                for step in get_generic_linux_fallback():
                    executor.run(step["cmd"], desc=step["desc"], purpose=step["purpose"], risk=step["risk"], capture=False)
                return True

    elif os_name == "Windows":
        guide, supported = get_windows_guide(distro_info.get("build", "0"), arch)
        click.secho(f"\n🖥️  Windows 2026 Support Status: {guide['status']}", fg="cyan", bold=True)
        click.echo("-" * 50)
        for s in guide["steps"]: click.echo(f"   {s}")
        click.echo("-" * 50)
        click.secho(f"   ⚠️  {guide['risk_notice']}", fg="yellow")
        click.secho(f"   📧 Support: {SUPPORT_EMAIL}", fg="white", dim=True)
        return True

    return False
