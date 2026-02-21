
import subprocess
import os
import click
from typing import Dict, Any, Optional, List

class GitExecutor:
    """
    Executes Git commands safely and handles errors via the deterministic engine.
    Supports showing planned commands and dry-runs.
    """
    
    def __init__(self, classifier, dry_run: bool = False):
        self.classifier = classifier
        self.dry_run = dry_run

    def execute_workflow(self, steps: List[Dict[str, Any]], title: str):
        """
        Executes a sequence of steps. Each step can have 'cmd', 'desc', 'action', 'interactive'.
        """
        click.secho(f"\n--- {title} ---", fg="cyan", bold=True)
        
        # 1. Show planned commands
        click.secho("\nPlanned Commands:", fg="yellow")
        for step in steps:
            if 'cmd' in step:
                cmd_str = " ".join(step['cmd']) if isinstance(step['cmd'], list) else step['cmd']
                click.echo(f"  $ {cmd_str}  # {step.get('desc', '')}")
        
        if not self.dry_run:
            if not click.confirm("\nProceed with execution?", default=True):
                click.secho("Aborted.", fg="red")
                return

        # 2. Execution
        click.echo("")
        for i, step in enumerate(steps, 1):
            desc = step.get('desc', 'Executing...')
            click.echo(f"Step {i}: {desc} ", nl=False)
            
            if 'cmd' in step:
                success = self.run_command(step['cmd'], interactive=step.get('interactive', False))
                if not success:
                    return False
            elif 'action' in step:
                # For custom logic between commands
                success = step['action']()
                if not success:
                    click.secho("❌ Failed", fg="red")
                    return False
                click.secho("✔", fg="green")
        
        click.secho("\n✔ Workflow Completed Successfully!", fg="green", bold=True)
        return True

    def run_command(self, cmd: Any, interactive: bool = False) -> bool:
        if isinstance(cmd, str):
            cmd_list = cmd.split()
        else:
            cmd_list = cmd
            
        if self.dry_run:
            click.secho(f"[DRY-RUN] Success", fg="blue")
            return True

        # Special handling for interactive commands (like gh auth login)
        if interactive:
            click.echo("(Switching to Interactive Mode)...")
            try:
                result = subprocess.run(cmd_list)
                if result.returncode == 0:
                    click.secho("✔", fg="green")
                    return True
                else:
                    click.secho("❌", fg="red")
                    return False
            except Exception as e:
                click.secho(f"❌ (Internal Error: {str(e)})", fg="red")
                return False

        while True:
            try:
                # Set environment to prevent hanging on prompts
                env = os.environ.copy()
                env["GIT_TERMINAL_PROMPT"] = "0"
                env["GIT_ASKPASS"] = "true" # Forces fail if askpass needed
                
                result = subprocess.run(cmd_list, capture_output=True, text=True, env=env)
                if result.returncode == 0:
                    click.secho("✔", fg="green")
                    return True
                else:
                    click.secho("❌", fg="red")
                    handle_res = self._handle_error(result.stderr or result.stdout)
                    if handle_res == "RETRY":
                        click.secho(f"Retrying: {' '.join(cmd_list)}...", fg="yellow")
                        continue
                    return False
            except Exception as e:
                click.secho(f"❌ (Internal Error: {str(e)})", fg="red")
                return False

    def _handle_error(self, stderr: str):
        error_info = self.classifier.classify(stderr, mode="git")
        click.secho("\n" + "="*60, fg="red")
        click.secho(f"GIT ERROR DETECTED: {error_info.get('category', 'unknown').upper()}", bold=True)
        click.secho(f"SCOPE: {error_info.get('scope', 'UNKNOWN')}")
        click.secho(f"SEVERITY: {error_info.get('severity', 'medium')}")
        click.echo("-" * 60)
        click.secho("RECOMMENDED CHECKS:", fg="yellow")
        for check in error_info.get("recommended_checks", []):
            click.echo(f"  - {check}")
        click.secho("\nSUGGESTED FIX:", fg="green")
        for fix in error_info.get("suggested_fix", []):
            click.echo(f"  - {fix}")
        click.secho("="*60 + "\n", fg="red")

        # Proactive Fix Offering
        fix_cmds = error_info.get("fix_commands")
        if fix_cmds:
            if click.confirm(click.style("Would you like FixShell to apply this fix for you?", fg="cyan", bold=True), default=True):
                for cmd in fix_cmds:
                    click.secho(f"  Applying: {' '.join(cmd)}...", fg="yellow")
                    if not self.dry_run:
                        res = subprocess.run(cmd, capture_output=True, text=True)
                        if res.returncode == 0:
                            click.secho("    ✔ Fix applied successfully.", fg="green")
                        else:
                            click.secho(f"    ❌ Fix failed: {res.stderr}", fg="red")
                            return False
                    else:
                        click.secho("    [DRY-RUN] Fix simulated.", fg="blue")
                
                if click.confirm(click.style("Fix applied. Would you like to RETRY the original command?", fg="cyan"), default=True):
                    return "RETRY"
        return False
