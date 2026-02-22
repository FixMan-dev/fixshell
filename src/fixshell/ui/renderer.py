from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme
from rich.box import ROUNDED, DOUBLE_EDGE
from typing import List, Optional

# Custom theme for FixShell
fixshell_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green bold",
    "command": "bright_white on grey11 bold",
    "step": "magenta bold",
    "banner": "bright_blue bold",
})

console = Console(theme=fixshell_theme)

class Renderer:
    """
    Handles all visual output for FixShell using Rich.
    Ensures a premium, production-grade aesthetics.
    """

    @staticmethod
    def print_banner(text: str):
        console.print(Panel(
            Text(text.upper(), justify="center", style="banner"),
            box=DOUBLE_EDGE,
            padding=(1, 2)
        ))

    @staticmethod
    def print_step(desc: str):
        console.print(f"\n[step]🚀 {desc}[/step]")

    @staticmethod
    def print_command(cmd: str):
        # Premium command display box
        console.print(Panel(
            Text(f" $ {cmd} ", style="command"),
            box=ROUNDED,
            title="[dim]PLAN[/dim]",
            title_align="left",
            border_style="bright_black"
        ))

    @staticmethod
    def print_success(msg: str = "Success"):
        console.print(f"   [success]✔ {msg}[/success]")

    @staticmethod
    def print_error(msg: str):
        console.print(f"   [error]❌ {msg}[/error]")

    @staticmethod
    def print_info(msg: str):
        console.print(f"   [info]ℹ {msg}[/info]")

    @staticmethod
    def print_resolution(category: str):
        console.print(Panel(
            f"[warning]💊 Needs Resolution:[/warning] [bold]{category}[/bold]\n"
            f"[dim]Attempting to Shift State...[/dim]",
            border_style="yellow",
            box=ROUNDED
        ))

    @staticmethod
    def print_fatal(category: str, suggestion: str, raw_error: str):
        console.print("\n")
        console.print(Panel(
            Text.assemble(
                ("FATAL ERROR: UNRECOVERABLE\n", "error"),
                (f"Category: {category}\n\n", "white"),
                ("Suggestion: ", "cyan"), (f"{suggestion}\n\n", "white"),
                ("Raw Stderr:\n", "dim"), (raw_error, "red dim")
            ),
            title="[error]CRITICAL FAILURE[/error]",
            border_style="red",
            box=DOUBLE_EDGE
        ))
