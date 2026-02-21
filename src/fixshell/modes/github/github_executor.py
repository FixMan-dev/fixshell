import subprocess
import click
from .github_validator import is_git_installed, is_gh_installed, is_dirty, has_remote, current_branch

def run_git_step(desc: str, cmd: str = None, action: str = None, dry_run: bool = False) -> bool:
    click.echo(f"Step: {desc} ... ", nl=False)
    
    if dry_run:
        click.echo(click.style("SKIPPED (DRY-RUN)", fg="yellow"))
        if cmd: click.echo(click.style(f"  > Suggest: {cmd}", fg="dim"))
        return True

    try:
        if action == "validate_git":
            if not is_git_installed():
                click.echo(click.style("❌ Git not found", fg="red"))
                return False
        
        elif action == "validate_gh":
            if not is_gh_installed():
                click.echo(click.style("❌ GH CLI not found", fg="red"))
                return False
        
        elif action == "safe_push":
            if is_dirty():
                click.echo(click.style("❌ Uncommitted changes", fg="red"))
                return False
            if not has_remote():
                click.echo(click.style("❌ No remote 'origin'", fg="red"))
                return False
            
            branch = current_branch()
            # Safety logic: Prevent force push via deterministic checks
            if not branch:
                click.echo(click.style("❌ Not on any branch", fg="red"))
                return False
            
            # Run simulation/check before final push if possible
            subprocess.run(["git", "push", "origin", branch], capture_output=True, check=True)

        elif cmd:
            # Safety filter: block hard resets or force pushes
            if "--force" in cmd or "--hard" in cmd:
                 click.echo(click.style("❌ BLOCKED (Dangerous flag)", fg="red"))
                 return False
            
            subprocess.run(cmd.split(), capture_output=True, check=True)

        click.echo(click.style("✔ SUCCESS", fg="green"))
        return True
    except subprocess.CalledProcessError as e:
        click.echo(click.style(f"❌ FAILED", fg="red"))
        return False

def execute_git_workflow(template: dict, dry_run: bool = False):
    click.echo(click.style(f"\n🐙 Starting Git Workflow: {template['name']}", bold=True))
    for step in template["steps"]:
        res = run_git_step(step["desc"], step.get("cmd"), step.get("action"), dry_run)
        if not res: return
    click.echo(click.style("\n✨ Summary:", bold=True))
    click.echo(f"  {template['summary']}")
