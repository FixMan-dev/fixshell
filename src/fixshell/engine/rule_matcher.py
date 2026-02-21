import re
from typing import List, Dict, Any, Optional

class RuleMatcher:
    """
    Deterministic regex-based rule matcher for system errors.
    Supports priority scoring and multiple pattern matching.
    """
    
    def __init__(self, dataset: List[Dict[str, Any]]):
        self.dataset = dataset

    def find_matches(self, output: str) -> List[Dict[str, Any]]:
        """
        Matches stderr/stdout against the dataset.
        Returns a list of matching error entries.
        """
        matches = []
        output_lower = output.lower()

        for entry in self.dataset:
            pattern = entry.get("error_pattern", "")
            try:
                # Capture groups to support template replacement ({MATCH_1}, etc.)
                match_obj = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
                if match_obj:
                    entry_copy = entry.copy()
                    entry_copy["matches"] = list(match_obj.groups())
                    matches.append(entry_copy)
            except re.error:
                # Fallback to literal search
                if pattern.lower() in output_lower:
                    entry_copy = entry.copy()
                    entry_copy["matches"] = []
                    matches.append(entry_copy)
        
        return matches

    def get_best_match(self, output: str) -> Optional[Dict[str, Any]]:
        """
        Returns the best match based on pattern length (specificity) or explicit priority.
        """
        matches = self.find_matches(output)
        if not matches:
            return None
        
        # Sort by pattern length descending as a proxy for specificity
        # If the dataset had a 'priority' field, we would use that.
        return sorted(matches, key=lambda x: len(x.get("error_pattern", "")), reverse=True)[0]
