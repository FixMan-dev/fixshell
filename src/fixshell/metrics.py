import os
import json
import time

METRICS_FILE = os.path.expanduser("~/.fixshell_metrics.json")

def load_metrics():
    if not os.path.exists(METRICS_FILE):
        return {"total_calls": 0, "failures_captured": 0, "llm_calls": 0, "blocked_commands": 0, "confidence_avg": 0.0}
    try:
        with open(METRICS_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {"total_calls": 0, "failures_captured": 0, "llm_calls": 0, "blocked_commands": 0, "confidence_avg": 0.0}

def save_metrics(metrics):
    try:
        with open(METRICS_FILE, 'w') as f:
            json.dump(metrics, f, indent=2)
    except Exception:
        pass

def track_call(failed=False, llm_used=False, confidence=None, blocked_count=0):
    metrics = load_metrics()
    metrics["total_calls"] += 1
    if failed:
        metrics["failures_captured"] += 1
    if llm_used:
        metrics["llm_calls"] += 1
    if blocked_count > 0:
        metrics["blocked_commands"] += blocked_count
    if confidence is not None:
        # Running average
        n = metrics["llm_calls"]
        current_avg = metrics["confidence_avg"]
        metrics["confidence_avg"] = ((current_avg * (n-1)) + confidence) / n if n > 0 else confidence
        
    save_metrics(metrics)
