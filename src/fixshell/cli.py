import sys
import subprocess
import shutil
import click
import json
from .context import collect_basic_context, collect_smart_context
from .prompt import build_prompt, SYSTEM_PROMPT, calculate_evidence_score, auto_correct_pkg_command
from .llm import get_diagnosis
from .safety import validate_commands
from .history import find_similar, add_entry, track_outcome
from .metrics import track_call
from .rules import check_deterministic

@click.command(context_settings=dict(ignore_unknown_options=True))
@click.argument('command_args', nargs=-1, required=True, type=click.UNPROCESSED)
def main(command_args):
    """
    FixShell AI - Hybrid Loop
    
    Usage: fixshell -- <your command here>
    everything after -- is passed through.
    """
    
    # Check if user typed `fixshell command` or `fixshell -- command`
    # Click's ignore_unknown_options=True + nargs=-1 + UNPROCESSED should capture everything.
    
    # If the first arg is '--', skip it as per convention but usually click handles it.
    # However, if user types `fixshell ls -l`, `command_args` might be `('ls', '-l')`.
    # If user types `fixshell -- ls -l`, `command_args` might be `('--', 'ls', '-l')` depending on shell expansion?
    # No, typically Click swallows `--` if it's meant for options.
    # But let's handle the explicit `--` if present at index 0.
    
    cmd_list = list(command_args)
    if cmd_list and cmd_list[0] == '--':
        cmd_list = cmd_list[1:]
        
    if not cmd_list:
        click.echo("Usage: fixshell -- <command>")
        sys.exit(1)

    # 1. Executor (Week 1)
    # "Use subprocess.run(cmd_list, capture_output=True)"
    
    try:
        # We must capture output to analyze it later for failure detection.
        # But for valid commands, we want to print stdout.
        result = subprocess.run(cmd_list, capture_output=True, text=True)
        
        # 2. Failure Detection (Week 2 Preview)
        # "If exit_code == 0 → print original stdout only"
        if result.returncode == 0:
            track_call(failed=False)
            track_outcome(" ".join(cmd_list), success=True)
            print(result.stdout, end='') # stdout already contains newlines usually
        else:
            # Week 2: Failure Detection + Basic Context
            # Week 3: Smart Context Collection
            
            # Week 2 & 3: Context Collection
            context = collect_basic_context(cmd_list, result)
            smart_context = collect_smart_context(cmd_list, result.stderr)
            context["smart_context"] = smart_context
            
            # context memory check
            similar = find_similar(" ".join(cmd_list), result.stderr)
            if similar:
                click.echo(click.style(f"💡 Similar issue found in history (Top Fix: {similar.get('top_fix')})", fg="cyan", italic=True))
            
            # Deterministic check (Skip LLM if clear)
            diagnosis = check_deterministic(cmd_list, result.stderr, smart_context)
            if diagnosis:
                click.echo(click.style("\nResolved via Deterministic Engine (Skipping LLM)", fg="green", italic=True))
            else:
                # LLM Integration
                click.echo(click.style("\nAnalyzing failure with FixShell AI...", fg="cyan"))
                prompt = build_prompt(context)
                diagnosis = get_diagnosis(SYSTEM_PROMPT, prompt)
            
            if diagnosis and "possible_causes" in diagnosis:
                env = context.get("env", {})
                depth_str = f"Distro: {env.get('distro')} | Pkg: {env.get('pkg_manager')} | SELinux: {env.get('selinux')} | systemd: {'yes' if env.get('has_systemd') else 'no'}"
                click.echo(click.style(depth_str, fg="white", dim=True))
                
                click.echo(click.style("\n--- FIXSHELL AI DIAGNOSIS (v9.5) ---", fg="yellow", bold=True))
                
                causes = diagnosis.get("possible_causes", [])
                processed_causes = []
                seen_causes = set()

                # Pass 1: Calculate raw scores & Dedup
                total_raw_score = 0.0
                
                for cause_data in causes:
                    cause_name = cause_data.get("cause", "Unknown")
                    
                    # Semantic Deduplication
                    simple_id = cause_name.lower().replace("_", " ").strip()
                    if simple_id in seen_causes: continue
                    seen_causes.add(simple_id)

                    base_conf = cause_data.get("initial_confidence", 0.5)
                    
                    # Apply Structured Evidence Scoring
                    evidence_result = calculate_evidence_score(context, cause_name)
                    raw_score = base_conf + evidence_result["score_modifier"]
                    
                    processed_causes.append({
                        "data": cause_data,
                        "raw_score": raw_score,
                        "evidence": evidence_result,
                        "name": cause_name
                    })
                    total_raw_score += raw_score

                # Pass 2: Normalize (Week 10 Math Fix)
                # If total > 1.0, scale down. If < 1.0, keep as is (independent probabilities).
                norm_factor = 1.0 / total_raw_score if total_raw_score > 1.0 else 1.0
                
                # Sort by score
                processed_causes.sort(key=lambda x: x["raw_score"], reverse=True)
                
                top_conf = 0.0
                blocked_in_session = 0
                displayed_count = 0

                for item in processed_causes:
                    if displayed_count >= 3: break
                    
                    final_conf = item["raw_score"] * norm_factor
                    if displayed_count == 0: top_conf = final_conf
                    
                    cause_name = item["name"]
                    cause_data = item["data"]
                    evidence_result = item["evidence"]
                    
                    conf_color = "green" if final_conf > 0.8 else "yellow" if final_conf > 0.5 else "red"
                    
                    click.echo(click.style(f"\n[{displayed_count + 1}] {cause_name}", fg="magenta", bold=True) + 
                               click.style(f" (Confidence: {final_conf:.2f})", fg=conf_color))
                    
                    # Show Evidence Links
                    for link in evidence_result["evidence_links"]:
                        click.echo(click.style(f"    🔗 Evidence: {link}", fg="cyan", dim=True))

                    click.echo(click.style(f"    Explanation: ", fg="green") + cause_data.get("explanation", "N/A"))
                    
                    click.echo(click.style("    Suggested Fixes:", fg="blue"))
                    raw_cmds = cause_data.get("suggested_commands", [])
                    cmd_objs = [c if isinstance(c, dict) else {"cmd": c, "risk": "low"} for c in raw_cmds]
                    
                    # Extract command strings for safety validator & Auto-Correction
                    cmd_strs = []
                    for c in cmd_objs:
                        # NEW: Auto-Correction
                        corrected = auto_correct_pkg_command(c.get("cmd"), env)
                        cmd_strs.append(corrected)
                    
                    validated_results = validate_commands(cmd_strs)
                    
                    for j, (cmd, is_safe, warning) in enumerate(validated_results):
                        original_cmd = cmd_objs[j].get("cmd")
                        was_corrected = (cmd != original_cmd)
                        
                        llm_risk = cmd_objs[j].get("risk", "low")
                        risk_color = "red" if llm_risk == "high" or not is_safe else "yellow" if llm_risk == "medium" else "green"
                        
                        if is_safe:
                            msg = f"      $ {cmd} " 
                            if was_corrected:
                                msg += click.style("(Auto-Corrected) ", fg="yellow", italic=True)
                            msg += click.style(f"[{llm_risk.upper()}]", fg=risk_color)
                            click.echo(msg)
                        else:
                            blocked_in_session += 1
                            click.echo(click.style(f"      [BLOCKED] {cmd}", fg="red"))
                            click.echo(click.style(f"        ↳ {warning}", fg="red", italic=True))
                    
                    displayed_count += 1
                
                click.echo(click.style("\n-----------------------------\n", fg="yellow", bold=True))
                # Store in history
                add_entry(" ".join(cmd_list), result.stderr, diagnosis)
                
                # Metrics
                track_call(failed=True, llm_used=True, confidence=top_conf, blocked_count=blocked_in_session)
            else:
                track_call(failed=True, llm_used=False)
                click.echo(click.style("LLM diagnosis failed. Falling back to debug mode.", fg="red"))
                click.echo(click.style("\n--- FALLBACK DEBUG SUGGESTIONS ---", fg="yellow", bold=True))
                click.echo(f"  $ strace {' '.join(cmd_list)}")
                click.echo(f"  $ journalctl -xe")
                click.echo(f"  $ dmesg | tail -n 20")
                click.echo(click.style("----------------------------------\n", fg="yellow", bold=True))
            
            # We exit with the same code to be a transparent wrapper
            sys.exit(result.returncode)
            
    except FileNotFoundError:
        click.echo(f"FixShell: Command '{cmd_list[0]}' not found.", err=True)
        sys.exit(127)
    except Exception as e:
        click.echo(f"FixShell Internal Error: {e}", err=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
