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

    def run(self, cmd_list: list, desc: str, interactive: bool = False, capture: bool = True) -> subprocess.CompletedProcess:
        """
        Executes a single command with full lifecycle reporting.
        """
        cmd_str = " ".join(cmd_list) if isinstance(cmd_list, list) else cmd_list
        
        Renderer.print_step(desc)
        Renderer.print_command(cmd_str)

        if self.dry_run:
            Renderer.print_info("[DRY-RUN] Command skipped.")
            # Return a mock successful result
            return subprocess.CompletedProcess(cmd_list, 0, stdout="", stderr="")

        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"

        if interactive:
            Renderer.print_info("Switching to Interactive Mode...")
            return subprocess.run(cmd_list, env=env)

        try:
            if capture:
                return subprocess.run(cmd_list, capture_output=True, text=True, env=env)
            else:
                return subprocess.run(cmd_list, env=env)
        except Exception as e:
            return subprocess.CompletedProcess(cmd_list, 1, stdout="", stderr=str(e))

    @staticmethod
    def confirm(prompt_text: str = "Proceed with execution?", default: bool = True) -> bool:
        return click.confirm(click.style(f"\n   {prompt_text}", fg="cyan", bold=True), default=default)
