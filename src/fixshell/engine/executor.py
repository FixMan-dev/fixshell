import subprocess
import os
import click
from ..ui.renderer import Renderer

class Executor:
    """
    Decoupled execution engine that handles shell interactions,
    previews, and dry-runs.
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def run(self, cmd_list: list, desc: str, interactive: bool = False, capture: bool = True, purpose: str = None, risk: str = "low") -> subprocess.CompletedProcess:
        """
        Executes a command with safety previews and live output options.
        """
        cmd_str = " ".join(cmd_list) if isinstance(cmd_list, list) else cmd_list
        
        # 1. Safety Preview (Mandatory for privileged/install steps)
        if purpose:
            Renderer.print_step(f"PLAN: {desc}")
            click.secho(f"   → Purpose: {purpose}", fg="white", dim=True)
            risk_color = "red" if risk == "high" else "yellow" if risk == "medium" else "green"
            click.secho(f"   → Risk: {risk.upper()}", fg=risk_color)
            Renderer.print_command(cmd_str)
            
            if not self.confirm("Authorize this command?", default=False):
                click.secho("   ❌ Step skipped by user.", fg="yellow")
                return subprocess.CompletedProcess(cmd_list, 130, stdout="", stderr="Skipped by user")

        else:
            Renderer.print_step(desc)
            Renderer.print_command(cmd_str)

        if self.dry_run:
            Renderer.print_info("[DRY-RUN] Execution simulated.")
            return subprocess.CompletedProcess(cmd_list, 0, stdout="", stderr="")

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        try:
            if not capture:
                # Live streaming mode (no capture)
                res = subprocess.run(cmd_list, env=env, shell=isinstance(cmd_list, str))
                return subprocess.CompletedProcess(cmd_list, res.returncode, stdout="", stderr="")
            else:
                return subprocess.run(cmd_list, capture_output=True, text=True, env=env, shell=isinstance(cmd_list, str))
        except Exception as e:
            return subprocess.CompletedProcess(cmd_list, 1, stdout="", stderr=str(e))

    @staticmethod
    def confirm(prompt_text: str = "Proceed?", default: bool = True) -> bool:
        return click.confirm(click.style(f"   {prompt_text}", fg="cyan", bold=True), default=default)
