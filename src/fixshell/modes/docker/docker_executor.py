
import subprocess
import os
import click
from typing import Dict, Any, Optional

class DockerExecutor:
    """
    Executes Docker commands safely and handles errors via the deterministic engine.
    """
    
    def __init__(self, classifier, dry_run: bool = False):
        self.classifier = classifier
        self.dry_run = dry_run

    def execute(self, cmd: list, description: str) -> bool:
        click.echo(f"  [STEP] {description}...")
        
        if self.dry_run:
            click.echo(f"    [DRY-RUN] Would execute: {' '.join(cmd)}")
            return True

        while True:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    click.secho(f"    ✔ Success", fg="green")
                    return True
                else:
                    click.secho(f"    ❌ Failed", fg="red")
                    handle_res = self._handle_error(result.stderr or result.stdout)
                    if handle_res == "RETRY":
                        click.secho(f"    Retrying: {' '.join(cmd)}...", fg="yellow")
                        continue
                    return False
            except Exception as e:
                click.secho(f"    ❌ Exception: {str(e)}", fg="red")
                return False

    def _handle_error(self, stderr: str):
        error_info = self.classifier.classify(stderr, mode="docker")
        click.echo("\n" + "="*50)
        click.secho(f"DOCKER ERROR DETECTED: {error_info.get('category', 'unknown').upper()}", bold=True)
        click.echo(f"SCOPE: {error_info.get('scope', 'UNKNOWN')}")
        click.echo(f"SEVERITY: {error_info.get('severity', 'medium')}")
        click.echo("-" * 50)
        click.secho("RECOMMENDED CHECKS:", fg="yellow")
        for check in error_info.get("recommended_checks", []):
            click.echo(f"  - {check}")
        click.secho("\nSUGGESTED FIX:", fg="green")
        for fix in error_info.get("suggested_fix", []):
            click.echo(f"  - {fix}")
        click.echo("="*50 + "\n")

        # Proactive Fix Offering
        fix_cmds = error_info.get("fix_commands")
        if fix_cmds:
            if click.confirm(click.style("Would you like FixShell to apply this fix for you?", fg="cyan", bold=True), default=True):
                for cmd_template in fix_cmds:
                    # Simple placeholder replacement for $USER
                    cmd = [c.replace("$USER", os.getenv("USER", "user")) if isinstance(c, str) else c for c in cmd_template]
                    
                    click.secho(f"    Applying: {' '.join(cmd)}...", fg="yellow")
                    if not self.dry_run:
                        res = subprocess.run(cmd, capture_output=True, text=True)
                        if res.returncode == 0:
                            click.secho("      ✔ Fix applied successfully.", fg="green")
                        else:
                            click.secho(f"      ❌ Fix failed: {res.stderr}", fg="red")
                            return False
                    else:
                        click.secho("      [DRY-RUN] Fix simulated.", fg="blue")
                
                if click.confirm(click.style("Fix applied. Would you like to RETRY the original command?", fg="cyan"), default=True):
                    return "RETRY"
        
        return False
