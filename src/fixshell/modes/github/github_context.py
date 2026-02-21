
import subprocess
import os

class GitHubContext:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.user = "Unknown"
        self.host = "github.com"
        self.repo = "None"
        self.branch = "None"
        self.remote_url = "None"
        self.is_repo = False
        self.default_branch = "main"

    def refresh(self):
        try:
            # 1. Check if Git repo
            res = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
            self.is_repo = res.returncode == 0
            
            if self.is_repo:
                # 2. Get Branch
                b_res = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True)
                self.branch = b_res.stdout.strip() or "DETACHED"
                
                # 3. Get Remote
                r_res = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)
                self.remote_url = r_res.stdout.strip() if r_res.returncode == 0 else "None"
            
            # 4. Get GH User
            u_res = subprocess.run(["gh", "api", "user", "--template", "{{.login}}"], capture_output=True, text=True)
            if u_res.returncode == 0:
                self.user = u_res.stdout.strip()
            else:
                self.user = "Not Logged In"

        except Exception:
            pass

    def display(self, click):
        click.secho("-" * 56, fg="bright_black")
        click.secho("🔎 CURRENT GITHUB CONTEXT", fg="cyan", bold=True)
        click.secho("-" * 56, fg="bright_black")
        
        user_color = "green" if self.user != "Not Logged In" else "red"
        click.echo(f"{'👤 User:':<18} " + click.style(self.user, fg=user_color))
        
        repo_status = "Yes" if self.is_repo else "No"
        repo_color = "green" if self.is_repo else "red"
        click.echo(f"{'📦 Is Git Repo:':<18} " + click.style(repo_status, fg=repo_color))
        
        if self.is_repo:
            click.echo(f"{'🌿 Branch:':<18} " + click.style(self.branch, fg="magenta"))
            click.echo(f"{'🔗 Remote:':<18} " + click.style(self.remote_url, fg="blue"))
            
        click.secho("-" * 56, fg="bright_black")
        click.echo("")
