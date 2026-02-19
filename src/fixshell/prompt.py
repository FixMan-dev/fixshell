import json
from typing import Dict, Any, List

SYSTEM_PROMPT = """You are a senior Linux system diagnostic engineer.
Analyze the provided structured failure context from a failed command.
Provide a ranked list of multiple possible root causes.

You MUST return your response in valid JSON format with the following keys:
- possible_causes: A list of objects, each containing:
    - cause: A short string identifying the technical reason.
    - explanation: A clear description of why this might be the cause.
    - suggested_commands: A list of objects, each with:
        - cmd: The command string.
        - risk: 'low', 'medium', or 'high'.
        - rationale: Why this command is suggested.
    - initial_confidence: A value from 0.0 to 1.0 (internal LLM estimate).

Guidelines:
- If evidence is clear (e.g., ss shows port bound), assign high confidence.
- Distinguish between safe "probes" (low risk) and "fixes" (medium/high risk).
- STRATEGIC ALIGNMENT: Use the detected 'environment' metadata.
- CONFIDENCE: Ensure your initial_confidences sum to <= 1.0 (or slightly more if independent). Do NOT return multiple 1.0 confidences.
- AUTO-CORRECTION NOTICE: If you fail to use the correct pkg_manager, the system will attempt to rewrite your command. Try to get it right."""

def auto_correct_pkg_command(cmd: str, env: Dict[str, Any]) -> str:
    """Auto-rewrites package manager commands to match the environment (Week 9.5)."""
    target_pkg = env.get("pkg_manager")
    if not target_pkg or target_pkg == "unknown":
        return cmd
        
    corrections = {
        "apt": ["apt-get", "apt"],
        "dnf": ["dnf", "yum"],
        "pacman": ["pacman"],
        "zypper": ["zypper"]
    }
    
    # If the command starts with sudo, handle it
    prefix = ""
    work_cmd = cmd
    if cmd.startswith("sudo "):
        prefix = "sudo "
        work_cmd = cmd[5:]
        
    parts = work_cmd.split()
    if not parts:
        return cmd
        
    current_pkg = parts[0]
    
    # Check if current command uses a package manager NOT matching the target
    mismatched = False
    for pkg, aliases in corrections.items():
        if pkg != target_pkg and current_pkg in aliases:
            mismatched = True
            break
            
    if mismatched:
        # Simple rewrite: replace first word with target_pkg
        return f"{prefix}{target_pkg} {' '.join(parts[1:])}"
        
    return cmd

def calculate_evidence_score(context: Dict[str, Any], cause_text: str) -> Dict[str, Any]:
    """
    Calculates a structured evidence score (Week 9.5).
    Returns {final_confidence, evidence_found: []}
    """
    # Formula: Baseline + Sum(Weights) clamped at 1.0
    weights = []
    smart_context = context.get("smart_context", {})
    stderr = context.get("stderr", "").lower()
    cause_lower = cause_text.lower()
    
    # Define weight mappings
    if "address already in use" in stderr or "port" in cause_lower:
        if "ss_output" in smart_context and "LISTEN" in smart_context["ss_output"]:
            weights.append(("Verified port occupation via 'ss'", 0.4))
            
    if "permission denied" in stderr or "permission" in cause_lower:
        if "ls_l_target" in smart_context and ("-" in smart_context["ls_l_target"] or "root" in smart_context["ls_l_target"]):
            weights.append(("Strict permissions detected on target", 0.3))
            
    if "no space left" in stderr or "disk" in cause_lower:
        if "df_output" in smart_context and ("100%" in smart_context["df_output"] or "9" in smart_context["df_output"]):
            weights.append(("Mount point depletion verified via 'df'", 0.5))
            
    if "connection refused" in stderr:
        if "ss_output" in smart_context and "LISTEN" not in smart_context["ss_output"]:
            weights.append(("Probed port has no listener", 0.4))
            
    # SELinux Context (Week 10: Strict Evidence)
    if "avc_denials" in smart_context:
        weights.append(("AVC Denial detected (SELinux blocking)", 0.6))

    return {
        "score_modifier": sum(w[1] for w in weights),
        "evidence_links": [w[0] for w in weights]
    }

def build_prompt(context: Dict[str, Any]) -> str:
    """
    Builds the structured user message for the LLM.
    """
    user_data = {
        "command": context.get("command"),
        "exit_code": context.get("exit_code"),
        "error_output": context.get("stderr"),
        "environment": context.get("env", {}),
        "system_state": {
            "user": context.get("user"),
            "cwd": context.get("cwd"),
            "os": context.get("uname")
        },
        "probes_output": context.get("smart_context", {})
    }
    
    full_json = json.dumps(user_data, indent=2)
    
    if len(full_json) > 6000:
        user_data["probes_output"] = {k: "Context too large, truncated." for k in user_data["probes_output"]}
        full_json = json.dumps(user_data, indent=2)

    user_message = f"I executed a command and it failed. Here is the context:\n\n{full_json}\n\nPlease diagnose this."
    return user_message
