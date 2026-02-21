import sys
import subprocess
import click
from .context import collect_basic_context, collect_smart_context
from .prompt import build_prompt, SYSTEM_PROMPT, calculate_evidence_score, auto_correct_pkg_command
from .llm import get_diagnosis
from .safety import validate_commands
from .history import find_similar, add_entry, track_outcome
from .metrics import track_call
from .rules import check_deterministic
from .classifier import ErrorClassifier

# Import new modes
from .modes.docker.docker_mode import DockerMode
from .modes.git.git_mode import GitMode

@click.command(context_settings=dict(ignore_unknown_options=True))
@click.option('--dry-run', is_flag=True, help="Simulate execution without making changes.")
@click.argument('command_args', nargs=-1, type=click.UNPROCESSED)
def main(command_args, dry_run):
    """
    FixShell AI - The Intelligent Linux Companion
    
    Usage:
      fixshell docker         - Docker workflow mode
      fixshell git            - Git / GitHub workflow mode
      fixshell -- <command>   - AI Diagnosis mode
    """
    cmd_list = list(command_args)
    if not cmd_list:
        with click.Context(main) as ctx:
            click.echo(ctx.get_help())
        return

    # Subcommand Routing (Deterministic)
    if cmd_list[0] == 'docker':
        mode = DockerMode(dry_run=dry_run)
        mode.run_guided_workflow()
    elif cmd_list[0] == 'git':
        mode = GitMode(dry_run=dry_run)
        mode.run_guided_workflow()
    elif cmd_list[0] == 'github': # Compatibility alias
        mode = GitMode(dry_run=dry_run)
        mode.run_guided_workflow()
    else:
        # Pass to AI Loop
        run_ai_loop(cmd_list)

def run_ai_loop(command_args):
    """The original logic for intercepting and diagnosing failed commands."""
    cmd_list = list(command_args)
    if cmd_list and cmd_list[0] == '--':
        cmd_list = cmd_list[1:]
        
    if not cmd_list:
        click.echo("Usage: fixshell -- <command>")
        return

    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        
        if result.returncode == 0:
            track_call(failed=False)
            track_outcome(" ".join(cmd_list), success=True)
            print(result.stdout, end='')
        else:
            context = collect_basic_context(cmd_list, result)
            smart_context = collect_smart_context(cmd_list, result.stderr)
            context["smart_context"] = smart_context
            
            similar = find_similar(" ".join(cmd_list), result.stderr)
            if similar:
                click.echo(click.style(f"💡 Similar issue found in history (Top Fix: {similar.get('top_fix')})", fg="cyan", italic=True))
            
            scope_result = ErrorClassifier.classify(" ".join(cmd_list), result.returncode, result.stderr, result.stdout)
            if scope_result["confidence"] > 0.6:
                click.echo(click.style(f"Scope Detected: {scope_result['error_scope'].upper()} (Confidence: {scope_result['confidence']})", fg="cyan", dim=True))
                context["error_scope"] = scope_result

            diagnosis = check_deterministic(cmd_list, result.stderr, smart_context)
            if diagnosis:
                click.echo(click.style("\nResolved via Deterministic Engine (Skipping LLM)", fg="green", italic=True))
            else:
                click.echo(click.style("\nAnalyzing failure with FixShell AI...", fg="cyan"))
                prompt = build_prompt(context)
                diagnosis = get_diagnosis(SYSTEM_PROMPT, prompt)
            
            if diagnosis and "possible_causes" in diagnosis:
                render_diagnosis(diagnosis, context)
                add_entry(" ".join(cmd_list), result.stderr, diagnosis)
            else:
                render_fallback(cmd_list)
            
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        click.echo(f"FixShell: Command '{cmd_list[0]}' not found.", err=True)
        sys.exit(127)
    except Exception as e:
        click.echo(f"FixShell Internal Error: {e}", err=True)
        sys.exit(1)

def render_diagnosis(diagnosis, context):
    """Extracted rendering logic from original main."""
    env = context.get("env", {})
    depth_str = f"Distro: {env.get('distro')} | Pkg: {env.get('pkg_manager')} | SELinux: {env.get('selinux')} | systemd: {'yes' if env.get('has_systemd') else 'no'}"
    click.echo(click.style(depth_str, fg="white", dim=True))
    click.echo(click.style("\n--- FIXSHELL AI DIAGNOSIS ---", fg="yellow", bold=True))
    
    causes = diagnosis.get("possible_causes", [])
    
    # Calculate total weight for normalization
    total_raw_score = 0.0
    for cause_data in causes:
        cause_name = cause_data.get("cause", "")
        base_conf = cause_data.get("initial_confidence", 0.5)
        evidence = calculate_evidence_score(context, cause_name)
        total_raw_score += (base_conf + evidence["score_modifier"])
    
    norm_factor = 1.0 / total_raw_score if total_raw_score > 1.0 else 1.0

    for i, cause_data in enumerate(causes[:3]):
        cause_name = cause_data.get("cause", "")
        evidence = calculate_evidence_score(context, cause_name)
        final_conf = (cause_data.get("initial_confidence", 0.5) + evidence["score_modifier"]) * norm_factor
        
        conf_color = "green" if final_conf > 0.8 else "yellow" if final_conf > 0.5 else "red"
        click.echo(click.style(f"\n[{i+1}] {cause_name}", fg="magenta", bold=True) + click.style(f" (Confidence: {final_conf:.2f})", fg=conf_color))
        
        for link in evidence["evidence_links"]:
            click.echo(click.style(f"    🔗 Evidence: {link}", fg="cyan", dim=True))
        
        click.echo(click.style(f"    Explanation: ", fg="green") + cause_data.get("explanation", "N/A"))
        click.echo(click.style("    Suggested Fixes:", fg="blue"))
        
        raw_cmds = cause_data.get("suggested_commands", [])
        cmd_objs = [c if isinstance(c, dict) else {"cmd": c, "risk": "low"} for c in raw_cmds]
        cmd_strs = [auto_correct_pkg_command(c.get("cmd"), env) for c in cmd_objs]
        
        validated = validate_commands(cmd_strs)
        for j, (cmd, is_safe, warning) in enumerate(validated):
            risk = cmd_objs[j].get("risk", "low")
            if is_safe:
                click.echo(f"      $ {cmd} [{risk.upper()}]")
            else:
                click.echo(click.style(f"      [BLOCKED] {cmd}", fg="red"))
                click.echo(click.style(f"        ↳ {warning}", fg="red", italic=True))
    
    click.echo(click.style("\n-----------------------------\n", fg="yellow", bold=True))

def render_fallback(cmd_list):
    click.echo(click.style("LLM diagnosis failed. Falling back to debug mode.", fg="red"))
    click.echo(click.style("\n--- FALLBACK DEBUG SUGGESTIONS ---", fg="yellow", bold=True))
    click.echo(f"  $ strace {' '.join(cmd_list)}")
    click.echo(f"  $ journalctl -xe")
    click.echo(click.style("----------------------------------\n", fg="yellow", bold=True))

if __name__ == "__main__":
    main()
