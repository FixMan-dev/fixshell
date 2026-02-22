import click
import sys
from .ui.renderer import Renderer
from .modes.git.git_mode import GitMode
from .modes.github.github_mode import GitHubMode
from .modes.docker.docker_mode import DockerMode
from .modes.linux.linux_mode import LinuxMode
from .config import VERSION

@click.group()
@click.version_option(version=VERSION)
@click.option('--dry-run', is_flag=True, help="Simulate execution without making changes.")
@click.pass_context
def cli(ctx, dry_run):
    """
    FixShell AI - The Deterministic, State-Aware DevOps Engine.
    """
    ctx.ensure_object(dict)
    ctx.obj['dry_run'] = dry_run

@cli.command()
@click.pass_context
def git(ctx):
    """Git Guided Workflow Mode."""
    mode = GitMode(dry_run=ctx.obj['dry_run'])
    mode.run_guided_workflow()

@cli.command()
@click.pass_context
def github(ctx):
    """GitHub Management Mode."""
    mode = GitHubMode(dry_run=ctx.obj['dry_run'])
    mode.run_menu()

@cli.command()
@click.pass_context
def docker(ctx):
    """Docker Workflow Mode."""
    mode = DockerMode(dry_run=ctx.obj['dry_run'])
    mode.run_guided_workflow()

@cli.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('args', nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def diagnosis(ctx, args):
    """AI Diagnosis Mode for arbitrary commands."""
    mode = LinuxMode(dry_run=ctx.obj['dry_run'])
    mode.diagnose_and_fix(list(args))

def main():
    Renderer.print_banner("FixShell AI Engine")
    try:
        cli(obj={})
    except Exception as e:
        Renderer.print_error(f"Internal Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
