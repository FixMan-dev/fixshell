import re
import os
from typing import Dict, Any, Tuple

class ErrorClassifier:
    """
    Deterministic engine to classify error scope before LLM reasoning.
    Categorizes errors into: command_not_found, permission, network, resource, syntax, service.
    """
    
    # Pre-compiled patterns for efficiency
    # Format: (Regex Pattern, Confidence Score)
    PATTERNS = {
        "command_not_found": [
            (r"command not found", 0.9),
            (r"executable file not found", 0.9),
            (r"not recognized as an internal or external command", 0.9),
            (r"no such file or directory", 0.6) # Careful, this can be file I/O too
        ],
        "permission": [
            (r"permission denied", 0.95),
            (r"eacces", 0.8),
            (r"operation not permitted", 0.9),
            (r"access is denied", 0.9),
            (r"are you root", 0.7),
            (r"requires root privileges", 0.9)
        ],
        "network": [
            (r"connection refused", 0.9),
            (r"connection timed out", 0.8),
            (r"name or service not known", 0.8),
            (r"host unreachable", 0.8),
            (r"no route to host", 0.8),
            (r"temporary failure in name resolution", 0.9),
            (r"socket:.*failed", 0.7)
        ],
        "resource": [
            (r"no space left on device", 0.95),
            (r"write error", 0.6),
            (r"memory exhausted", 0.9),
            (r"out of memory", 0.9),
            (r"disk quota exceeded", 0.9),
            (r"failed to fork", 0.8)
        ],
        "syntax": [
            (r"invalid option", 0.85),
            (r"unrecognized option", 0.85),
            (r"usage:", 0.6), # Helpful, but might just mean help was printed
            (r"syntax error", 0.9),
            (r"unexpected token", 0.8),
            (r"parse error", 0.8)
        ],
        "service": [
            (r"failed to start .* service", 0.9),
            (r"unit .* not found", 0.8),
            (r"service .* not loaded", 0.8)
        ]
    }

    @staticmethod
    def classify(cmd: str, exit_code: int, stderr: str, stdout: str = "") -> Dict[str, Any]:
        """
        Classifies the error based on exit code, stderr analysis, and deterministic probes.
        Returns a dictionary with 'error_scope', 'confidence', and 'evidence'.
        """
        scores = {k: 0.0 for k in ErrorClassifier.PATTERNS.keys()}
        evidence = []
        full_output = (stderr + "\n" + stdout if stdout else stderr).lower()
        
        # 1. EXIT CODE SIGNALS
        # mapped approximations for bash/standard utilities
        if exit_code == 127:
            scores["command_not_found"] += 0.8
            evidence.append("Exit Code 127 (Command Not Found)")
        elif exit_code == 126:
            scores["permission"] += 0.8
            evidence.append("Exit Code 126 (Permission Denied)")
        elif exit_code == 2:
            scores["syntax"] += 0.4
            evidence.append("Exit Code 2 (Likely Syntax/Usage)")

        # 2. REGEX PATTERN MATCHING
        for scope, patterns in ErrorClassifier.PATTERNS.items():
            for pattern, weight in patterns:
                if re.search(pattern, full_output):
                    # We employ a 'max' strategy per scope to avoid over-counting repeated lines
                    if weight > scores[scope]:
                         scores[scope] = weight
                         # Only add evidence if new
                         if f"Matched '{pattern}'" not in "".join(evidence):
                             evidence.append(f"Matched pattern '{pattern}' for {scope}")
                    elif weight == scores[scope]:
                         # Boost slightly if multiple independent patterns match (capped)
                         scores[scope] = min(scores[scope] + 0.1, 1.0)

        # 3. CONTEXT PROBES (Tie-Breakers)
        
        # Probe: Permission check if generic failure but user is not root
        if scores["permission"] > 0.3 and scores["permission"] < 0.9:
            try:
                if os.geteuid() != 0:
                    scores["permission"] += 0.2
                    evidence.append("User is not ROOT (uid != 0)")
            except Exception:
                pass

        # Probe: Command missing check if 127 ambiguous (some shells print customized errors)
        if scores["command_not_found"] > 0.3:
            import shutil
            cmd_name = cmd.split()[0] if cmd else ""
            if cmd_name and not shutil.which(cmd_name):
                 scores["command_not_found"] += 0.5
                 evidence.append(f"Binary '{cmd_name}' not found in PATH")

        # 4. WINNER SELECTION
        best_scope = "unknown"
        best_score = 0.0
        
        # Iterate to find max
        for scope, score in scores.items():
            if score > best_score:
                best_score = score
                best_scope = scope
        
        # Threshold for "Unknown"
        if best_score < 0.4:
            best_scope = "unknown"

        return {
            "error_scope": best_scope,
            "confidence": round(min(best_score, 1.0), 2),
            "evidence": evidence
        }
