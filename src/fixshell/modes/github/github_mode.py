
import click
import os
import json
import subprocess
from ...engine.error_classifier import ErrorClassifierEngine
from ...engine.resolver_registry import (
    ResolverRegistry, handle_gh_auth_login, handle_directory_exists,
    handle_git_no_upstream, handle_git_no_tracking, handle_git_upstream_mismatch,
    handle_git_delete_current_branch
)
from ...engine.state_machine import WorkflowStateMachine
from .github_context import GitHubContext
from .github_templates import GH_MAIN_MENU

class GitHubMode:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
        # 1. Initialize Engine
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dataset_dir = os.path.join(base_path, "dataset")
        self.classifier = ErrorClassifierEngine(dataset_dir)
        
        # 2. Setup Registries
        self.registry = ResolverRegistry()
        self.registry.register("GH_AUTH_REQUIRED", handle_gh_auth_login)
        self.registry.register("GIT_NO_UPSTREAM", handle_git_no_upstream)
        self.registry.register("GIT_NO_TRACKING_INFO", handle_git_no_tracking)
        self.registry.register("GIT_UPSTREAM_MISMATCH", handle_git_upstream_mismatch)
        self.registry.register("GIT_DELETE_CURRENT_BRANCH", handle_git_delete_current_branch)
        self.registry.register("FS_DIRECTORY_EXISTS", handle_directory_exists)
        
        # 3. Instantiate core components
        self.context = GitHubContext(dry_run)
        self.sm = WorkflowStateMachine(self.classifier, self.registry, dry_run, mode="github")

    def run_menu(self):
        while True:
            click.clear()
            self.context.refresh()
            self.context.display(click)
            
            click.echo(GH_MAIN_MENU)
            choice = click.prompt("Select an option", type=int, default=12)
            
            if choice == 12: break
            elif choice == 1: self.auth_menu()
            elif choice == 2: self.sm.execute_step(["gh", "repo", "list", "--limit", "20"], "Listing Repositories", context_manager=self.context)
            elif choice == 3: self.select_repo()
            elif choice == 4: self.create_repo()
            elif choice == 5: self.link_repo()
            elif choice == 6: self.manage_branches()
            elif choice == 7: self.manage_pr()
            elif choice == 8: self.manage_issues()
            elif choice == 9: self.manage_ci()
            elif choice == 10: self.manage_releases()
            elif choice == 11: self.sm.execute_step(["gh", "repo", "view"], "Showing Repo Details", context_manager=self.context)
            else: click.secho("Invalid option.", fg="red")
            
            if choice != 12:
                input("\nPress Enter to continue...")

    def auth_menu(self):
        click.clear()
        self.context.refresh()
        click.echo("\n--- GitHub Authentication ---")
        click.echo("1. Login\n2. Logout\n3. Refresh Token\n4. Status\n5. Cancel")
        c = click.prompt("Choice", type=int)
        if c == 1: self.sm.execute_step(["gh", "auth", "login"], "Login", context_manager=self.context, interactive=True)
        elif c == 2: self.sm.execute_step(["gh", "auth", "logout"], "Logout", context_manager=self.context)
        elif c == 3: self.sm.execute_step(["gh", "auth", "refresh", "--hostname", "github.com"], "Refresh", context_manager=self.context)
        elif c == 4: self.sm.execute_step(["gh", "auth", "status"], "Status", context_manager=self.context, interactive=True)

    def create_repo(self):
        name = click.prompt("Repository Name")
        private = click.confirm("Private?", default=True)
        vis = "--private" if private else "--public"
        self.sm.execute_step(["gh", "repo", "create", name, vis, "--source=.", "--remote=origin"], "Creating Repo", context_manager=self.context)
        self.sm.execute_step(["git", "push", "-u", "origin", "HEAD"], "Pushing initial code", context_manager=self.context)

    def select_repo(self):
        name = click.prompt("Enter Repository (owner/repo)")
        self.sm.execute_step(["gh", "repo", "view", name], f"Viewing {name}", context_manager=self.context)

    def link_repo(self):
        url = click.prompt("Repository URL or Name")
        self.sm.execute_step(["git", "remote", "add", "origin", url], "Linking Remote", context_manager=self.context)

    def manage_branches(self):
        self.sm.execute_step(["git", "branch", "-a"], "Listing all branches", context_manager=self.context)

    def manage_pr(self):
        title = click.prompt("Title")
        self.sm.execute_step(["gh", "pr", "create", "--title", title, "--body", "Automated PR"], "Creating PR", context_manager=self.context)

    def manage_issues(self):
        self.sm.execute_step(["gh", "issue", "list"], "Listing Issues", context_manager=self.context)

    def manage_ci(self):
        self.sm.execute_step(["gh", "workflow", "list"], "Listing Workflows", context_manager=self.context)

    def manage_releases(self):
        self.sm.execute_step(["gh", "release", "list"], "Listing Releases", context_manager=self.context)
