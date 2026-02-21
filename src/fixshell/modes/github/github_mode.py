import click
import sys
import subprocess
from .github_templates import GITHUB_TEMPLATES
from .github_executor import execute_git_workflow
from .github_validator import is_git_installed, is_gh_installed, current_branch

def show_github_menu(dry_run: bool):
    """Interactive GitHub Mode Menu."""
    click.clear()
    click.echo(click.style("🐙 GitHub Mode", fg="magenta", bold=True, underline=True))
    click.echo("")
    
    click.echo("1. Initialize Git Repository")
    click.echo("2. Create GitHub Repository (via gh CLI)")
    click.echo("3. Push Current Project Safely")
    click.echo("4. Create Feature Branch")
    click.echo("5. Sync With Main Branch")
    click.echo("6. Add CI for Node Project")
    click.echo("7. Add CI for Python Project")
    click.echo("8. Show Git Status")
    click.echo("9. Exit")
    click.echo("")
    
    choice = click.prompt("Select an option", type=int)
    
    if choice == 9:
        sys.exit(0)
    
    if choice == 1:
        execute_git_workflow(GITHUB_TEMPLATES["init_repo"], dry_run)
    
    elif choice == 2:
        # Create via gh CLI
        repo_name = click.prompt("Repository Name", default="my-new-repo")
        execute_git_workflow({
            "name": "Create GitHub Repo",
            "steps": [
                {"desc": "Check GH CLI", "action": "validate_gh"},
                {"desc": f"Creating repo '{repo_name}'", "cmd": f"gh repo create {repo_name} --public --source=. --remote=origin"}
            ],
            "summary": f"GitHub repository '{repo_name}' created and linked."
        }, dry_run)
        
    elif choice == 3:
        execute_git_workflow({
            "name": "Safe Push",
            "steps": [{"desc": "Pushing to origin", "action": "safe_push"}],
            "summary": f"Branch {current_branch()} pushed successfully."
        }, dry_run)
        
    elif choice == 4:
        branch_name = click.prompt("New Branch Name")
        execute_git_workflow({
            "name": "Create Feature Branch",
            "steps": [
                {"desc": f"Creating branch {branch_name}", "cmd": f"git checkout -b {branch_name}"}
            ],
            "summary": f"Switched to new branch: {branch_name}"
        }, dry_run)

    elif choice == 5:
        execute_git_workflow({
            "name": "Sync main",
            "steps": [
                {"desc": "Fetching", "cmd": "git fetch origin"},
                {"desc": "Merging main", "cmd": "git merge origin/main"}
            ],
            "summary": "Local branch synced with origin/main."
        }, dry_run)
        
    elif choice == 6:
        execute_git_workflow(GITHUB_TEMPLATES["ci_node"], dry_run)
        
    elif choice == 7:
        execute_git_workflow(GITHUB_TEMPLATES["ci_python"], dry_run)
        
    elif choice == 8:
        subprocess.run(["git", "status", "-s"])
        
    input("\nPress Enter to return to menu...")
    show_github_menu(dry_run)
