
import click
import os
import sys
import subprocess
from .git_templates import GIT_MENU, GITIGNORE_CONTENT, CI_TEMPLATES
from .git_validator import GitValidator
from .git_executor import GitExecutor
from ...engine.error_classifier import ErrorClassifierEngine

class GitMode:
    """
    Controller for the Guided Git Workflow Mode.
    Models real-world development steps deterministically.
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        dataset_dir = os.path.join(base_path, "dataset")
        self.classifier = ErrorClassifierEngine(dataset_dir)
        self.executor = GitExecutor(self.classifier, dry_run=dry_run)

    def run_guided_workflow(self):
        while True:
            click.clear()
            click.secho("🐙 Git Mode – Guided Workflow", fg="magenta", bold=True, underline=True)
            click.echo("")
            
            for key, val in GIT_MENU.items():
                click.echo(f"{key}. {val}")
            
            choice = click.prompt("\nSelect an option", type=str, default="11")
            
            if choice == "11":
                break
            elif choice == "1":
                self.start_new_project()
            elif choice == "2":
                self.clone_repository()
            elif choice == "3":
                self.daily_work()
            elif choice == "4":
                self.create_feature_branch()
            elif choice == "5":
                self.sync_with_main()
            elif choice == "6":
                self.resolve_merge_conflict()
            elif choice == "7":
                self.delete_branch_safely()
            elif choice == "8":
                self.add_ci_workflow()
            elif choice == "9":
                self.show_status()
            elif choice == "10":
                self.authenticate_gh()
            else:
                click.secho("Invalid option.", fg="red")
            
            if choice != "11":
                input("\nPress Enter to return to menu...")

    def _validate_env(self):
        click.secho("\nChecking Environment...", fg="yellow")
        checks = GitValidator.validate_environment()
        all_pass = True
        for ok, msg in checks:
            icon = "✔" if ok else "❌"
            color = "green" if ok else "red"
            click.secho(f"  {icon} {msg}", fg=color)
            if not ok: all_pass = False
        return all_pass

    def start_new_project(self):
        if not self._validate_env(): return
        
        target_dir = os.getcwd()
        if GitValidator.is_git_repo():
            click.secho("\n❌ Current directory is already a Git repository!", fg="red")
            if click.confirm(click.style("Would you like to create a NEW directory for this project?", fg="cyan"), default=True):
                new_name = click.prompt("Enter new directory name")
                target_dir = os.path.join(os.getcwd(), new_name)
                try:
                    if not self.dry_run:
                        os.makedirs(target_dir, exist_ok=False)
                    click.secho(f"✔ Created directory: {target_dir}", fg="green")
                except FileExistsError:
                    click.secho(f"❌ Directory '{new_name}' already exists and is not empty.", fg="red")
                    return
            else:
                return

        # Change to target directory for the execution
        original_dir = os.getcwd()
        if not self.dry_run:
            os.chdir(target_dir)

        try:
            name = click.prompt("Repository name", default=os.path.basename(target_dir))
            visibility = "--private" if click.confirm("Make it private?", default=True) else "--public"
            init_readme = click.confirm("Initialize README.md?", default=True)
            gitignore = click.prompt("Add .gitignore template?", type=click.Choice(['python', 'node', 'none']), default='none')
            ci = click.prompt("Add CI template?", type=click.Choice(['python', 'node', 'none']), default='none')

            steps = [
                {"desc": "Initializing local git", "cmd": ["git", "init"]},
            ]
            
            if init_readme:
                steps.append({"desc": "Creating README.md", "action": lambda: self._write_file("README.md", f"# {name}\n")})
            
            if gitignore != 'none':
                steps.append({"desc": f"Creating .gitignore ({gitignore})", "action": lambda: self._write_file(".gitignore", GITIGNORE_CONTENT[gitignore])})

            steps.extend([
                {"desc": "Adding files", "cmd": ["git", "add", "."]},
                {"desc": "Initial commit", "cmd": ["git", "commit", "-m", "Initial commit"]},
                {"desc": "Creating GitHub repo", "cmd": ["gh", "repo", "create", name, visibility, "--source=.", "--remote=origin"]},
                {"desc": "Setting main branch", "cmd": ["git", "branch", "-M", "main"]},
                {"desc": "Pushing to GitHub", "cmd": ["git", "push", "-u", "origin", "main"]}
            ])

            if ci != 'none':
                def add_ci():
                    os.makedirs(".github/workflows", exist_ok=True)
                    self._write_file(f".github/workflows/{ci}-ci.yml", CI_TEMPLATES[ci])
                    subprocess.run(["git", "add", ".github/workflows/"])
                    subprocess.run(["git", "commit", "-m", f"Add {ci} CI workflow"])
                    subprocess.run(["git", "push"])
                    return True
                steps.append({"desc": f"Adding CI template ({ci})", "action": add_ci})

            self.executor.execute_workflow(steps, "Start New Project")

        finally:
            if not self.dry_run:
                os.chdir(original_dir)

    def _write_file(self, path, content):
        if not self.dry_run:
            with open(path, "w") as f:
                f.write(content)
        return True

    def clone_repository(self):
        url = click.prompt("Repository URL (HTTPS or SSH)")
        if not GitValidator.validate_url(url):
            click.secho("❌ Invalid URL format.", fg="red")
            return
        
        self.executor.execute_workflow([
            {"desc": f"Cloning {url}", "cmd": ["git", "clone", url]}
        ], "Clone Repository")

    def daily_work(self):
        if not GitValidator.is_git_repo():
            click.secho("\n❌ Not a git repository.", fg="red")
            if click.confirm(click.style("Would you like to INITIALIZE this directory as a Git repository now?", fg="cyan"), default=True):
                self.start_new_project()
                return
            return
        
        if GitValidator.is_detached_head():
            click.secho("❌ Detached HEAD detected. Please switch to a branch.", fg="red")
            return

        if GitValidator.is_merge_in_progress():
            click.secho("❌ Merge in progress. Resolve conflicts first.", fg="red")
            return

        msg = click.prompt("Commit message")
        
        steps = [
            {"desc": "Syncing with remote (pull)", "cmd": ["git", "pull"]},
            {"desc": "Staging all changes", "cmd": ["git", "add", "."]},
            {"desc": "Committing changes", "cmd": ["git", "commit", "-m", msg]},
            {"desc": "Pushing to remote", "cmd": ["git", "push"]}
        ]
        
        self.executor.execute_workflow(steps, "Daily Work")

    def create_feature_branch(self):
        branch = click.prompt("New feature branch name")
        if not GitValidator.validate_branch_name(branch):
            click.secho("❌ Invalid branch name.", fg="red")
            return
        
        if GitValidator.branch_exists(branch):
            click.secho(f"❌ Branch '{branch}' already exists.", fg="red")
            return

        if not GitValidator.is_working_dir_clean():
            click.secho("❌ Working directory not clean. Commit or stash changes first.", fg="red")
            return

        steps = [
            {"desc": f"Creating branch {branch}", "cmd": ["git", "checkout", "-b", branch]},
            {"desc": "Setting upstream", "cmd": ["git", "push", "-u", "origin", branch]}
        ]
        self.executor.execute_workflow(steps, "Create Feature Branch")

    def sync_with_main(self):
        current = GitValidator.get_current_branch()
        if current == "main":
            click.secho("❌ Already on 'main' branch.", fg="red")
            return
        
        if GitValidator.is_rebase_in_progress() or GitValidator.is_merge_in_progress():
            click.secho("❌ Rebase or Merge already in progress.", fg="red")
            return

        steps = [
            {"desc": "Switching to main", "cmd": ["git", "checkout", "main"]},
            {"desc": "Updating main", "cmd": ["git", "pull", "origin", "main"]},
            {"desc": f"Switching back to {current}", "cmd": ["git", "checkout", current]},
            {"desc": "Merging main into feature", "cmd": ["git", "merge", "main"]}
        ]
        self.executor.execute_workflow(steps, f"Sync {current} with Main")

    def resolve_merge_conflict(self):
        if not GitValidator.is_merge_in_progress():
            click.secho("No active merge conflict detected.", fg="yellow")
            return

        click.secho("\n--- Merge Conflicts Detected ---", fg="red", bold=True)
        subprocess.run(["git", "status", "-s"])
        
        click.echo("\n1. Resolve conflicts in your editor.")
        click.echo("2. Save files.")
        
        if click.confirm("Have you resolved all conflicts?", default=False):
            steps = [
                {"desc": "Staging resolved files", "cmd": ["git", "add", "."]},
                {"desc": "Completing merge commit", "cmd": ["git", "commit", "--no-edit"]}
            ]
            self.executor.execute_workflow(steps, "Conflict Resolution")
        else:
            click.echo("Resolution aborted. Use your IDE to fix markers (<<<<<<<, =======, >>>>>>>).")

    def delete_branch_safely(self):
        branch = click.prompt("Branch name to delete")
        current = GitValidator.get_current_branch()
        
        if branch == "main" or branch == "master":
            click.secho("❌ Deletion of 'main/master' is restricted for safety.", fg="red", bold=True)
            return
        
        if branch == current:
            click.secho(f"❌ Cannot delete the current branch '{current}'. Switch to another branch first.", fg="red")
            return

        steps = [
            {"desc": f"Deleting local branch {branch}", "cmd": ["git", "branch", "-d", branch]},
            {"desc": f"Deleting remote branch origin/{branch}", "cmd": ["git", "push", "origin", "--delete", branch]}
        ]
        self.executor.execute_workflow(steps, f"Safe Delete Branch: {branch}")

    def add_ci_workflow(self):
        ci = click.prompt("Select CI template", type=click.Choice(['python', 'node']), default='python')
        
        def write_ci():
            os.makedirs(".github/workflows", exist_ok=True)
            path = f".github/workflows/{ci}-ci.yml"
            self._write_file(path, CI_TEMPLATES[ci])
            return True

        steps = [
            {"desc": f"Creating {ci} CI template", "action": write_ci},
            {"desc": "Staging workflow", "cmd": ["git", "add", ".github/workflows/"]},
            {"desc": "Committing workflow", "cmd": ["git", "commit", "-m", f"Add {ci} CI workflow"]},
            {"desc": "Pushing workflow", "cmd": ["git", "push"]}
        ]
        self.executor.execute_workflow(steps, "Add CI Workflow")

    def show_status(self):
        click.secho("\n--- Repository Status ---", fg="cyan", bold=True)
        subprocess.run(["git", "status"])
        click.secho("\n--- Recent Commits ---", fg="cyan")
        subprocess.run(["git", "log", "-n", "5", "--oneline", "--graph", "--decorate"])

    def authenticate_gh(self):
        click.secho("\n--- GitHub CLI Authentication ---", fg="magenta", bold=True)
        click.echo("1. Login with a web browser (Default)")
        click.echo("2. Login with an Auth Token (Paste token)")
        
        auth_choice = click.prompt("Select login method", type=int, default=1)
        
        if auth_choice == 1:
            self.executor.execute_workflow([
                {"desc": "Launching browser login", "cmd": ["gh", "auth", "login"], "interactive": True}
            ], "GitHub Web Auth")
        elif auth_choice == 2:
            token = click.prompt("Paste your Personal Access Token", hide_input=True)
            if token:
                # Use a temporary file or pipe to safely pass the token
                def apply_token():
                    try:
                        process = subprocess.Popen(["gh", "auth", "login", "--with-token"], stdin=subprocess.PIPE, text=True)
                        process.communicate(input=token)
                        return process.returncode == 0
                    except Exception:
                        return False
                
                self.executor.execute_workflow([
                    {"desc": "Authenticating with token", "action": apply_token},
                    {"desc": "Configuring git credentials", "cmd": ["gh", "auth", "setup-git"]}
                ], "GitHub Token Auth")
        
        # After auth, ensure git is configured
        subprocess.run(["gh", "auth", "setup-git"])
