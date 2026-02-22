import json
import os
from typing import Dict, Any, List, Optional
from .rule_matcher import RuleMatcher

class ErrorCategory:
    FATAL = "FATAL"
    RECOVERABLE = "RECOVERABLE"
    INFORMATIONAL = "INFORMATIONAL"

class Classifier:
    """
    Modular error classification engine using deterministic datasets.
    """
    
    def __init__(self, dataset_dir: str):
        self.dataset_dir = dataset_dir
        self.matchers = self._load_matchers()

    def _load_matchers(self) -> Dict[str, RuleMatcher]:
        matchers = {}
        dataset_files = {
            "docker": "docker_errors.json",
            "git": "git_errors.json",
            "github": "github_errors.json",
            "linux": "linux_errors.json"
        }
        
        for key, filename in dataset_files.items():
            path = os.path.join(self.dataset_dir, filename)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    matchers[key] = RuleMatcher(data)
            else:
                matchers[key] = RuleMatcher([])
        
        return matchers

    def classify(self, output: str, mode: Optional[str] = None) -> Dict[str, Any]:
        """
        Classifies error output. If mode is provided, prioritizes that matcher.
        """
        if mode and mode in self.matchers:
            best_match = self.matchers[mode].get_best_match(output)
            if best_match:
                return best_match

        # If no mode or no match in mode, search all
        best_overall = None
        for matcher in self.matchers.values():
            match = matcher.get_best_match(output)
            if match:
                if not best_overall or len(match["error_pattern"]) > len(best_overall["error_pattern"]):
                    best_overall = match
        
        if best_overall:
            return best_overall
            
        return {
            "error_pattern": "unknown",
            "category": "unknown",
            "scope": "UNKNOWN",
            "recommended_checks": ["Check manual logs", "Verify syntax"],
            "suggested_fix": ["No automated fix available for this error."],
            "severity": "medium"
        }
