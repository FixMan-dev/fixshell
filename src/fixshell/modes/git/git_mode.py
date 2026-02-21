
import click
import os
import json
import subprocess
from .git_templates import GIT_MENU, GITIGNORE_CONTENT, CI_TEMPLATES
from .git_validator import GitValidator
from ...engine.error_classifier import ErrorClassifierEngine
from ...engine.resolver_registry import (
    ResolverRegistry, handle_git_no_upstream, handle_git_no_tracking,
    handle_git_upstream_mismatch, handle_git_delete_current_branch,
    handle_directory_exists, handle_gh_auth_login
)
from ...engine.state_machine import WorkflowStateMachine
from ..github.github_context import GitHubContext

class GitMode:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
        # 1. Initialize Engine
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dataset_dir = os.path.join(base_path, "dataset")
        self.classifier = ErrorClassifierEngine(dataset_dir)
        
        # 2. Setup Registries
        self.registry = ResolverRegistry()
        self.registry.register("GIT_NO_UPSTREAM", handle_git_no_upstream)
        self.registry.register("GIT_NO_TRACKING_INFO", handle_git_no_tracking)
        self.registry.register("GIT_UPSTREAM_MISMATCH", handle_git_upstream_mismatch)
        self.registry.register("GIT_DELETE_CURRENT_BRANCH", handle_git_delete_current_branch)
        self.registry.register("FS_DIRECTORY_EXISTS", handle_directory_exists)
        self.registry.register("GH_AUTH_REQUIRED", handle_gh_auth_login)
        self.registry.register("AUTH_DENIED", handle_gh_auth_login)
        
        # 3. Instantiate core components
        self.context = GitHubContext(dry_run)
        self.sm = WorkflowStateMachine(self.classifier, self.registry, dry_run, mode="git")

    def run_guided_workflow(self):
        while True:
            click.clear()
            self.context.refresh()
            self.context.display(click)
            
            click.secho("🐙 Git Mode – Smart Workflow Engine", fg="magenta", bold=True)
            
            for key, val in GIT_MENU.items():
                click.echo(f"{key}. {val}")
            
            choice = click.prompt("\nSelect an option", type=str, default="11")
            
            if choice == "11": break
            elif choice == "1": self.start_new_project()
            elif choice == "2": self.sm.execute_step(["git", "clone", click.prompt("URL")], "Cloning Repo", context_manager=self.context)
            elif choice == "3": self.daily_work()
            elif choice == "4": self.create_feature_branch()
            elif choice == "5": self.sync_with_main()
            elif choice == "6": self.resolve_merge_conflict()
            elif choice == "7": self.delete_branch_safely()
            elif choice == "8": self.add_ci_workflow()
            elif choice == "9": self.show_status()
            elif choice == "10": self.sm.execute_step(["gh", "auth", "login"], "Login", context_manager=self.context, interactive=True)
            else: click.secho("Invalid option.", fg="red")
            
            if choice != "11":
                input("\nPress Enter to return to menu...")

    def start_new_project(self):
        name = click.prompt("Repository Name", default=os.path.basename(os.getcwd()))
        self.sm.execute_step(["git", "init"], "Initializing Git", context_manager=self.context)
        self.sm.execute_step(["git", "add", "."], "Staging files", context_manager=self.context)
        self.sm.execute_step(["git", "commit", "-m", "Initial commit"], "Committing files", context_manager=self.context)

    def daily_work(self):
        msg = click.prompt("Commit message", default="Update")
        self.sm.execute_step(["git", "pull"], "Syncing (Pulling)", context_manager=self.context)
        self.sm.execute_step(["git", "add", "."], "Staging changes", context_manager=self.context)
        self.sm.execute_step(["git", "commit", "-m", msg], "Committing", context_manager=self.context)
        self.sm.execute_step(["git", "push"], "Pushing to remote", context_manager=self.context)

    def create_feature_branch(self):
        branch = click.prompt("Feature branch name")
        self.sm.execute_step(["git", "checkout", "-b", branch], f"Creating branch '{branch}'", context_manager=self.context)

    def sync_with_main(self):
        self.sm.execute_step(["git", "fetch", "origin"], "Fetching updates", context_manager=self.context)
        self.sm.execute_step(["git", "merge", "origin/main"], "Merging main branch", context_manager=self.context)

    def resolve_merge_conflict(self):
        self.sm.execute_step(["git", "status"], "Checking status", context_manager=self.context)
        click.echo("Please resolve conflicts in your editor, then stage the files.")
        if click.confirm("Have you resolved the conflicts?", default=True):
            self.sm.execute_step(["git", "add", "."], "Staging resolved files", context_manager=self.context)
            self.sm.execute_step(["git", "commit", "--no-edit"], "Finalizing merge", context_manager=self.context)

    def delete_branch_safely(self):
        branch = click.prompt("Branch to delete")
        self.sm.execute_step(["git", "branch", "-d", branch], f"Deleting branch '{branch}'", context_manager=self.context)

    def add_ci_workflow(self):
        click.echo("1. Python CI\n2. Node CI")
        c = click.prompt("Choice", type=int)
        if c in [1, 2]:
            mode = "python" if c == 1 else "node"
            os.makedirs(".github/workflows", exist_ok=True)
            with open(f".github/workflows/{mode}-ci.yml", "w") as f:
                f.write(CI_TEMPLATES[mode])
            click.secho(f"✔ {mode.capitalize()} CI template added.", fg="green")

    def show_status(self):
        self.sm.execute_step(["git", "status", "-s"], "Showing short status", context_manager=self.context)
