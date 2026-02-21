
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

    def _handle_directory_conflict(self, path):
        """Recovery Decision Tree for directory conflicts."""
        while True:
            click.secho(f"\n⚠ Directory '{os.path.basename(path)}' already exists.", fg="yellow")
            click.echo("Choose how to proceed:")
            click.echo("1. Use this existing directory (as-is)")
            click.echo("2. Clear directory contents and continue (Destructive)")
            click.echo("3. Choose a different directory name")
            click.echo("4. Rename automatically (append -1, -2, etc.)")
            click.echo("5. Cancel")
            
            choice = click.prompt("Select an option", type=int, default=3)
            
            if choice == 1:
                return path
            elif choice == 2:
                if click.confirm(click.style("Are you sure you want to DELETE all files in this directory?", fg="red", bold=True)):
                    if not self.dry_run:
                        import shutil
                        for filename in os.listdir(path):
                            file_path = os.path.join(path, filename)
                            try:
                                if os.path.isfile(file_path) or os.path.islink(file_path):
                                    os.unlink(file_path)
                                elif os.path.isdir(file_path) and not filename == ".git":
                                    shutil.rmtree(file_path)
                            except Exception as e:
                                click.secho(f"  Error clearing {filename}: {e}", fg="red")
                    click.secho("✔ Directory cleared.", fg="green")
                    return path
            elif choice == 3:
                new_name = click.prompt("Enter new directory name")
                new_path = os.path.join(os.path.dirname(path), new_name)
                if not os.path.exists(new_path):
                    if not self.dry_run: os.makedirs(new_path)
                    return new_path
                path = new_path # Loop again
            elif choice == 4:
                counter = 1
                base = path
                while os.path.exists(f"{base}-{counter}"):
                    counter += 1
                new_path = f"{base}-{counter}"
                if not self.dry_run: os.makedirs(new_path)
                click.secho(f"✔ Created automatic directory: {os.path.basename(new_path)}", fg="green")
                return new_path
            else:
                return None

    def start_new_project(self):
        if not self._validate_env(): return
        
        target_dir = os.getcwd()
        if GitValidator.is_git_repo():
            click.secho("\n❌ Current directory is already a Git repository!", fg="red")
            if click.confirm(click.style("Would you like to setup this project in a DIFFERENT directory?", fg="cyan"), default=True):
                target_dir = os.path.join(os.getcwd(), click.prompt("Enter directory name"))
                if os.path.exists(target_dir) and os.listdir(target_dir):
                    target_dir = self._handle_directory_conflict(target_dir)
                    if not target_dir: return # Cancelled
                elif not os.path.exists(target_dir):
                    if not self.dry_run: os.makedirs(target_dir)
            else:
                # User wants to stay here even if it is a repo? 
                # This is usually a bad idea for "start new project"
                if not click.confirm(click.style("Proceed anyway in this existing Git repo?", fg="yellow")):
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

    def _handle_detached_head(self):
        """Recovery decision tree for Detached HEAD."""
        while True:
            click.secho("\n⚠ Detached HEAD detected. You are not on a branch!", fg="yellow")
            click.echo("Choose how to proceed:")
            click.echo("1. Create a new branch at this point (Save your work)")
            click.echo("2. Switch back to 'main' (WARNING: You may lose uncommitted work)")
            click.echo("3. Cancel")
            
            choice = click.prompt("Select an option", type=int, default=1)
            if choice == 1:
                new_branch = click.prompt("Enter new branch name")
                if not self.dry_run:
                    subprocess.run(["git", "checkout", "-b", new_branch])
                return True
            elif choice == 2:
                if click.confirm(click.style("Switch to 'main' and potentially discard progress?", fg="red")):
                    if not self.dry_run:
                        subprocess.run(["git", "checkout", "main"])
                    return True
            else:
                return False

    def daily_work(self):
        if not GitValidator.is_git_repo():
            click.secho("\n❌ Not a git repository.", fg="red")
            if click.confirm(click.style("Would you like to INITIALIZE this directory as a Git repository now?", fg="cyan"), default=True):
                self.start_new_project()
                return
            return
        
        if GitValidator.is_detached_head():
            if not self._handle_detached_head(): return

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

    def _handle_branch_conflict(self, branch):
        """Recovery Decision Tree for branch conflicts."""
        while True:
            click.secho(f"\n⚠ Branch '{branch}' already exists.", fg="yellow")
            click.echo("Choose how to proceed:")
            click.echo("1. Switch to the existing branch")
            click.echo("2. Reset branch (Delete and recreate - Destructive)")
            click.echo("3. Choose a different branch name")
            click.echo("4. Cancel")
            
            choice = click.prompt("Select an option", type=int, default=3)
            if choice == 1: return ("switch", branch)
            if choice == 2:
                if click.confirm(click.style(f"Permanently delete branch '{branch}'?", fg="red")):
                    if not self.dry_run: subprocess.run(["git", "branch", "-D", branch])
                    return ("create", branch)
            if choice == 3:
                branch = click.prompt("Enter new branch name")
                if not GitValidator.branch_exists(branch): return ("create", branch)
            if choice == 4: return (None, None)

    def create_feature_branch(self):
        branch = click.prompt("New feature branch name")
        if not GitValidator.validate_branch_name(branch):
            click.secho("❌ Invalid branch name.", fg="red")
            return
        
        target_action = "create"
        if GitValidator.branch_exists(branch):
            target_action, branch = self._handle_branch_conflict(branch)
            if not target_action: return

        if not GitValidator.is_working_dir_clean():
            click.secho("❌ Working directory not clean. Commit or stash changes first.", fg="red")
            return

        if target_action == "create":
            steps = [
                {"desc": f"Creating branch {branch}", "cmd": ["git", "checkout", "-b", branch]},
                {"desc": "Setting upstream", "cmd": ["git", "push", "-u", "origin", branch]}
            ]
        else: # switch
            steps = [
                {"desc": f"Switching to existing branch {branch}", "cmd": ["git", "checkout", branch]},
                {"desc": "Syncing with origin", "cmd": ["git", "pull", "origin", branch]}
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
