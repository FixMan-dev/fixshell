from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from typing import Dict, Any

console = Console()

class ContextPanel:
    """
    Renders the state-aware dashboard showing the current health and 
    context of the dev environment.
    """

    @staticmethod
    def render(state: Dict[str, Any]):
        table = Table(show_header=False, box=None, padding=(0, 1))
        
        # CATEGORIES: AUTH, REPO, BRANCH, NETWORK, etc.
        rows = [
            ("👤 USER", state.get("AUTH_STATE", "Unknown"), "green" if state.get("AUTH_STATE") != "Unknown" else "red"),
            ("🌿 BRANCH", state.get("BRANCH_STATE", "N/A"), "magenta"),
            ("📦 REPO", state.get("REPO_STATE", "No"), "cyan"),
            ("🌐 NETWORK", state.get("NETWORK_STATE", "Online"), "blue"),
            ("🔒 PERMS", state.get("PERMISSION_STATE", "User"), "yellow"),
        ]

        for icon, val, color in rows:
            table.add_row(
                Text(icon, style="bold white"),
                Text(str(val), style=color)
            )

        console.print(Panel(
            table,
            title="[bold cyan]SYSTEM CONTEXT[/bold cyan]",
            border_style="bright_black",
            expand=False,
            padding=(1, 2)
        ))
        console.print("")
