from typing import List, Dict, Any, Optional

def check_deterministic(cmd_list: List[str], stderr: str, smart_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Checks for 100% clear deterministic failures to skip LLM latency.
    """
    stderr_lower = stderr.lower()
    
    # 1. Port Conflict with verified process
    if "address already in use" in stderr_lower:
        ss_out = smart_context.get("ss_output", "")
        if "LISTEN" in ss_out:
            return {
                "possible_causes": [{
                    "cause": "DeterministicPortConflict",
                    "explanation": "A process is already listening on this port (verified via ss).",
                    "suggested_commands": [
                        {"cmd": "sudo ss -tulpn | grep LISTEN", "risk": "low", "rationale": "Identify the process."},
                        {"cmd": "sudo systemctl stop <service>", "risk": "medium", "rationale": "Stop the conflicting service."}
                    ],
                    "initial_confidence": 1.0
                }]
            }

    # 2. Disk Full with verified 100% usage
    if "no space left" in stderr_lower:
        df_out = smart_context.get("df_output", "")
        if "100%" in df_out:
            return {
                "possible_causes": [{
                    "cause": "DeterministicDiskFull",
                    "explanation": "The disk is completely full (verified via df).",
                    "suggested_commands": [
                        {"cmd": "df -h", "risk": "low", "rationale": "Check mount point usage."},
                        {"cmd": "sudo du -sh /* | sort -hr | head -n 5", "risk": "low", "rationale": "Find space hogs."}
                    ],
                    "initial_confidence": 1.0
                }]
            }
            
    # 3. Command Missing
    if "not found" in stderr_lower and len(cmd_list) > 0:
        import shutil
        if not shutil.which(cmd_list[0]):
             return {
                "possible_causes": [{
                    "cause": "DeterministicCommandMissing",
                    "explanation": f"The binary '{cmd_list[0]}' is not in your current $PATH.",
                    "suggested_commands": [
                        {"cmd": f"sudo apt install {cmd_list[0]}", "risk": "medium", "rationale": "Attempt installation."},
                        {"cmd": "echo $PATH", "risk": "low", "rationale": "Check path configuration."}
                    ],
                    "initial_confidence": 1.0
                }]
            }

    return None
