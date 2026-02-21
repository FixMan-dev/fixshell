
import os
import re
from typing import List, Dict, Any

def extract_rules_from_thefuck(rules_dir: str) -> List[Dict[str, Any]]:
    extracted = []
    if not os.path.exists(rules_dir): return []
    for filename in os.listdir(rules_dir):
        if filename.startswith("git_") and filename.endswith(".py"):
            path = os.path.join(rules_dir, filename)
            with open(path, 'r') as f:
                content = f.read()
                patterns = re.findall(r"'(.*?)' in command\.output", content)
                if not patterns:
                    patterns = re.findall(r"\"(.*?)\" in command\.output", content)
                
                if patterns:
                    combined_pattern = ".*".join(patterns)
                    extracted.append({
                        "filename": filename,
                        "potential_pattern": combined_pattern,
                        "category": filename.replace(".py", "").upper()
                    })
    return extracted

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    thefuck_rules = os.path.join(base_dir, "external/thefuck/thefuck/rules")
    
    if os.path.exists(thefuck_rules):
        print(f"🔍 Analyzing rules in {thefuck_rules}...")
        rules = extract_rules_from_thefuck(thefuck_rules)
        print(f"✅ Found {len(rules)} potential Git rules to adapt.")
        for r in rules[:5]:
            print(f"  - {r['filename']}: {r['potential_pattern']}")
    else:
        print(f"❌ Could not find thefuck rules at {thefuck_rules}")
