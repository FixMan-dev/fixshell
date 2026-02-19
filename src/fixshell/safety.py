import re
from typing import List, Tuple

# Dangerous patterns based on Week 6 rules
DANGEROUS_PATTERNS = [
    (r"rm\s+-rf\s+/", "Recursive delete of root directory"),
    (r"rm\s+-rf\s+\*", "Recursive delete of current directory"),
    (r"chmod\s+777\s+/", "Setting global write permissions on root"),
    (r"mkfs", "Filesystem creation (format)"),
    (r"shutdown", "System shutdown"),
    (r"reboot", "System reboot"),
    (r"mv\s+.*\s+/\s*$", "Moving files into root without target safety"),
    (r"> /dev/sd[a-z]", "Writing directly to block device"),
    (r"dd\s+if=.*of=/dev/sd[a-z]", "Low-level disk write"),
    # New strict safety rules (Week 10)
    (r"chmod\s+.*(/etc/shadow|/etc/passwd|/boot|/usr/bin|/usr/sbin)", "Modifying permissions of critical system files"),
    (r"chown\s+.*(/etc/shadow|/etc/passwd|/boot|/usr/bin|/usr/sbin)", "Changing ownership of critical system files"),
    (r"setenforce\s+0", "Disabling SELinux (Security Risk)"),
    (r"echo\s+.*\s+>\s+(/etc/shadow|/etc/passwd)", "Overwriting critical system files"),
]

def validate_commands(commands: List[str]) -> List[Tuple[str, bool, str]]:
    """
    Validates a list of commands against dangerous patterns.
    Returns a list of (command, is_safe, warning_message).
    """
    validated = []
    for cmd in commands:
        is_safe = True
        warning = ""
        for pattern, desc in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd):
                is_safe = False
                warning = f"BLOCKED: {desc}"
                break
        validated.append((cmd, is_safe, warning))
    return validated
