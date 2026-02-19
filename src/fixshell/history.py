import os
import json
import time
from typing import Dict, Any, List, Optional

HISTORY_FILE = os.path.expanduser("~/.fixshell_history.json")

def load_history() -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history: List[Dict[str, Any]]):
    try:
        # Keep only last 50 entries
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history[-50:], f, indent=2)
    except Exception:
        pass

def add_entry(command: str, stderr: str, diagnosis: Dict[str, Any]):
    history = load_history()
    entry = {
        "timestamp": time.time(),
        "command": command,
        "stderr_summary": stderr[:200], # Store summary to save space
        "causes": [c.get("cause") for c in diagnosis.get("possible_causes", [])],
        "top_fix": diagnosis.get("possible_causes", [{}])[0].get("suggested_commands", [{}])[0].get("cmd")
    }
    history.append(entry)
    save_history(history)

def find_similar(command: str, stderr: str) -> Optional[Dict[str, Any]]:
    """Simple similarity check based on command name and stderr snippets."""
    history = load_history()
    cmd_name = command.split()[0] if command else ""
    
    # Priority 1: Reinforced (previously successful) fixes
    for entry in reversed(history):
        if entry.get("reinforced") and entry["command"].startswith(cmd_name):
             entry_stderr = entry.get("stderr_summary", "").lower()
             if any(word in entry_stderr for word in stderr.lower().split()[:3]):
                return entry

    # Priority 2: General history
    for entry in reversed(history):
        if entry["command"].startswith(cmd_name):
            entry_stderr = entry.get("stderr_summary", "").lower()
            if any(word in entry_stderr for word in stderr.lower().split()[:3]):
                return entry
    return None

def track_outcome(command: str, success: bool):
    """Reinforces the last failure if it succeeded this time (Week 9.5)."""
    history = load_history()
    if not history: return
    
    # If a command succeeds, check if the previous entry in history was a failure of the same command
    # and mark it as 'reinforced'
    for i in range(len(history)-1, -1, -1):
        if history[i]["command"] == command:
            history[i]["reinforced"] = success
            save_history(history)
            break
