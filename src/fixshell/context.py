import os
import getpass
import platform
import subprocess
import re
import shutil
from typing import List, Dict, Any

def filter_logs(text: str) -> str:
    """Advanced log filtering (v2): Extract stack traces, remove noise & timestamps."""
    keywords = ["error", "fatal", "failed", "denied", "exception", "refused", "no space", "traceback"]
    lines = text.splitlines()
    
    filtered = []
    seen_patterns = set()
    
    in_traceback = False
    for line in lines:
        clean_line = line.strip()
        lower_line = clean_line.lower()
        
        # 1. Detect Stack Trace start
        if "traceback" in lower_line or "stack trace:" in lower_line:
            in_traceback = True
            
        # 2. Extract if keyword found or inside traceback
        if any(kw in lower_line for kw in keywords) or in_traceback:
            # Remove timestamps (heuristic: [HH:MM:SS] or YYYY-MM-DD HH:MM:SS)
            line_no_ts = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,\.]?\d*', '', clean_line)
            line_no_ts = re.sub(r'\[\d{2}:\d{2}:\d{2}\]', '', line_no_ts).strip()
            
            # 3. Deduplicate recurring patterns (e.g. repeated connection errors)
            pattern = re.sub(r'0x[0-9a-f]+', '0xADDR', line_no_ts) # Anonymize hex addrs
            pattern = re.sub(r'\d+\.\d+\.\d+\.\d+', 'IP', pattern) # Anonymize IPs
            
            if pattern not in seen_patterns:
                filtered.append(line_no_ts)
                seen_patterns.add(pattern)
        
        # Stop traceback if we see a line that looks like a new normal log
        if in_traceback and len(clean_line) > 0 and not clean_line.startswith((" ", "File", "at ")):
             if not any(kw in lower_line for kw in keywords):
                 in_traceback = False

    if not filtered:
        return "\n".join(lines[-10:])
    return "\n".join(filtered[:50]) # Max 50 intelligence lines

def run_cmd(cmd_list: List[str], filter_errors: bool = False) -> str:
    """Run a context command safely and return truncated/filtered output."""
    try:
        # Timeout to prevent hanging
        res = subprocess.run(cmd_list, capture_output=True, text=True, timeout=5)
        output = res.stdout + res.stderr
        
        if filter_errors:
            output = filter_logs(output)
            
        lines = output.splitlines()
        max_lines = 50
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + f"\n... (truncated {len(lines) - max_lines} lines)"
        return output.strip()
    except Exception as e:
        return f"Error running context command {' '.join(cmd_list)}: {e}"

def get_env_info() -> Dict[str, Any]:
    """Detects Linux distro, package manager, and advanced system state (Week 2/v3)."""
    info = {
        "distro": "unknown",
        "pkg_manager": "unknown",
        "is_container": os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"),
        "is_root": os.geteuid() == 0,
        "has_systemd": os.path.isdir("/run/systemd/system"),
        "selinux": "disabled"
    }
    
    # SELinux detection
    if os.path.exists("/usr/sbin/getenforce"):
        try:
            res = subprocess.run(["getenforce"], capture_output=True, text=True, timeout=1)
            info["selinux"] = res.stdout.strip().lower()
        except Exception:
            pass

    # Distro detection
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            content = f.read()
            if 'ID=' in content:
                m = re.search(r'^ID=(.*)$', content, re.M)
                if m: info["distro"] = m.group(1).strip('"')
                
    # PKG Manager detection (Primary Distro Mapping)
    distro_id = info["distro"].lower()
    if any(d in distro_id for d in ["fedora", "rhel", "centos"]):
        if shutil.which("dnf"): info["pkg_manager"] = "dnf"
        elif shutil.which("yum"): info["pkg_manager"] = "yum"
    elif any(d in distro_id for d in ["ubuntu", "debian", "kali", "mint"]):
        if shutil.which("apt"): info["pkg_manager"] = "apt"
    elif "arch" in distro_id:
        if shutil.which("pacman"): info["pkg_manager"] = "pacman"
    
    # Fallback to binary search if distro mapping didn't set it
    if info["pkg_manager"] == "unknown":
        if shutil.which("dnf"): info["pkg_manager"] = "dnf"
        elif shutil.which("apt"): info["pkg_manager"] = "apt"
        elif shutil.which("pacman"): info["pkg_manager"] = "pacman"
        elif shutil.which("yum"): info["pkg_manager"] = "yum"
        elif shutil.which("zypper"): info["pkg_manager"] = "zypper"
    
    return info

def collect_basic_context(cmd_list: List[str], result: subprocess.CompletedProcess) -> Dict[str, Any]:
    """
    Collects basic system context upon command failure (Week 2/v2).
    """
    try:
        uname_output = platform.uname()
        uname_str = f"{uname_output.system} {uname_output.release}"
    except Exception:
        uname_str = "unknown"

    return {
        "command": " ".join(cmd_list),
        "exit_code": result.returncode,
        "stderr": result.stderr.strip(),
        "user": getpass.getuser(),
        "cwd": os.getcwd(),
        "uname": uname_str,
        "env": get_env_info()
    }

def collect_smart_context(cmd_list: List[str], stderr: str) -> Dict[str, Any]:
    """
    Collects additional rule-based context logs (Week 3).
    """
    smart_data = {}
    stderr_lower = stderr.lower()
    cmd_str = " ".join(cmd_list)

    # 1. Permission denied -> ls -l <file>
    if "permission denied" in stderr_lower:
        target = None
        # Regex heuristics for common errors
        # 'ls: cannot access '/root': Permission denied'
        # 'ls: cannot open directory '/root': Permission denied'
        m = re.search(r"cannot (?:access|open directory) '([^']+)'", stderr)
        if m: 
            target = m.group(1)
        else:
            # 'bash: /root: Permission denied'
            m = re.search(r": ([^:]+): Permission denied", stderr)
            if m:
                target = m.group(1)
        
        # Fallback: check command arguments for existing paths
        if not target and cmd_list:
            for arg in reversed(cmd_list):
                # Ignore flags
                if not arg.startswith('-') and len(arg) > 1:
                     # Check if parth exists or parent exists
                     if os.path.exists(arg) or os.path.exists(os.path.dirname(arg) or '.'):
                         target = arg
                         break
        
        if target:
            smart_data["ls_l_target"] = run_cmd(["ls", "-ld", target])

    # 2. Address already in use -> ss -tulpn
    if "address already in use" in stderr_lower or "bind" in stderr_lower:
        smart_data["ss_output"] = run_cmd(["ss", "-tulpn"])

    # 3. No space left on device -> df -h
    if "no space left" in stderr_lower:
        smart_data["df_output"] = run_cmd(["df", "-h"])

    # 4. Connection refused -> ip a, ss -tulpn
    if "connection refused" in stderr_lower:
        smart_data["ip_a_output"] = run_cmd(["ip", "a"])
        if "ss_output" not in smart_data: # Don't run twice
            smart_data["ss_output"] = run_cmd(["ss", "-tulpn"])

    # 5. Systemctl / Service failure
    is_systemctl = "systemctl" in cmd_str or "systemctl" in stderr_lower or ".service" in stderr_lower
    if is_systemctl:
        service = None
        # Helper to extract service name from cmd args usually after start/restart/etc
        if "systemctl" in cmd_list:
            for i, arg in enumerate(cmd_list):
                if arg in ["start", "restart", "status", "enable", "disable", "stop", "reload"]:
                    if i + 1 < len(cmd_list):
                        service = cmd_list[i+1]
                        break
        
        # Helper to extract from stderr: "Job for nginx.service failed..."
        if not service:
            m = re.search(r"Job for ([^ ]+) failed", stderr)
            if m:
                service = m.group(1)
            else:
                 # Check for 'unit not found' e.g. "Unit nginx.service could not be found."
                 m = re.search(r"Unit ([^ ]+) could not be found", stderr)
                 if m:
                     service = m.group(1)

        if service:
            # Clean service name if needed
            if not service.endswith('.service') and '.' not in service:
                service += ".service"
            
            smart_data[f"systemctl_status_{service}"] = run_cmd(["systemctl", "status", service], filter_errors=True)
            smart_data[f"journalctl_{service}"] = run_cmd(["journalctl", "-u", service, "-n", "100", "--no-pager"], filter_errors=True)

    # 6. AVC Denial Check (Week 10)
    if "permission denied" in stderr_lower:
        try:
             # Check dmesg for recent AVC denials (last 50 lines)
             dmesg_out = run_cmd(["dmesg"])
             if "avc: denied" in "\n".join(dmesg_out.splitlines()[-50:]):
                 smart_data["avc_denials"] = "Found 'avc: denied' in dmesg."
        except Exception:
             pass

    return smart_data
